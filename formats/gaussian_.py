import numpy as np
import glob, os
import math
from utils import section_by_pattern, lines_to_dct, printyellow, styledarkcyan, printred
from data import scaling_factors

C_LIGHT     =   2.99792458E+10
H_PLANCK    =   6.6260755E-34
KB          =   1.3806504E-23
R_UNI       =   8.314472
R_KJ        =   R_UNI/1000
PPA         =   101325
PI          =   3.1415926539
HARTREE_TO_KJ = 2625.5


class FileReader:
    contents = []

    def __init__(self, filename, verbose=2, **kwargs):
        self.get_file_environment(filename)
        if verbose > 1:
            printyellow(self.filename)
    
    def get_file_environment(self, filename):
        self.filename       = filename
        self.filename_abs   = os.path.abspath(filename)
        self.directory_abs  = "/".join(self.filename_abs.split("/")[:-1])
        self.directory      = self.filename_abs.split("/")[-1]

        split = filename.split("/")[-1].split(".")
        self.base_name      = ".".join(split[:-1])
        self.extension      = split[-1]

    def get_contents(self):
        with open(self.filename, 'r') as f:
            contents = [x.strip() for x in f.readlines()]
        self.contents = [x for x in contents if x]

    @property
    def file_environment(self):
        keys = ["filename", "filename_abs", "directory_abs", "directory", "base_name", "extension"]
        return dict((k, self.__dict__[k]) for k in keys)

    def search(self, pattern, lines=None, reverse=False):
        if lines is None:
            if self.contents is None:
                self.get_contents()
            lines = self.contents
        

        for line in lines[::int(reverse)-1]:
            if pattern in line:
                return line



    
class QMOut(FileReader):
    tc = None
    zpve = None
    hlc = 0
    entropy = None
    temperature = None
    solvent = None
    thermochem = ""

    def __str__(self):
        return self.filename

    def __init__(self, filename, verbose=2):
        super().__init__(filename, verbose=0)
        self.get_contents()
        self.get_summary()
        self.get_standard_orientation()
        self.get_coordinates()
        self.get_method()
        self.get_solvation()
        self.get_others(verbose=verbose)
        if verbose > 1:
            self.print_summary()

    def print_summary(self):
        print(f"""
            {styledarkcyan("Method:")} {self.method: <8} {styledarkcyan("Solvent:"):16} {self.solvent}
            {styledarkcyan("Charge:")} {self.charge: <8d} {styledarkcyan("Multiplicity:"):16} {self.multiplicity}
             {styledarkcyan("Atoms:")} {self.n_atoms: <8d} {styledarkcyan("Basis functions:"):16} {self.n_basis}{self.thermochem}
            """)
            
        

    def get_summary(self):
        last_parts_reversed = []
        for line in self.contents[::-1]:
            if "1\\1\\" not in line:
                last_parts_reversed.append(line)
            else:
                last_parts_reversed.append(line)
                break
        last_parts = last_parts_reversed[::-1]
        self.summary = "".join([x.strip() for x in last_parts]).split("@")[0]

    def similar_orientation_to(self, other, rtol=1e-4, atol=1e-5):
        try:

            return np.allclose(np.abs(self.std_coords), np.abs(other.std_coords), rtol=rtol, atol=atol)
        except ValueError:
            return False

    def get_solvation(self):
        pass

    @staticmethod
    def get_value(line):
        return np.float64(line.split("=")[-1].strip())



class GaussianLog(QMOut):
    """
    All atomic units
    Entropy: Hartrees/Particle
    TC: ?
    """

    def get_others(self, **kwargs):
        self.get_n_basis(**kwargs)
        self.get_dft_details(**kwargs)

    def get_n_basis(self, **kwargs):
        basis_line = self.search("basis functions,")
        self.n_basis = int(basis_line.strip().split()[0].strip())
        return self.n_basis

    def get_summary(self):
        super().get_summary()
        self.env, self.header, name, self.cmcoords, self.final = self.summary.split("\\\\")[:5]
        #self.base_name = name.split(".")[0]



    def get_method(self):
        split = self.env.split("\\")
        self.method = split[4][1:]
        self.basis = split[5]
        return self.method

    def get_energy(self):
        # final value before RMSD
        energy = self.final.split("\\RMSD")[0].split("\\")[-1].split("=")[-1]
        self.energy = np.float64(energy)
        return self.energy

    def get_dft_details(self, verbose=0, **kwargs):
        try:
            thermochem = section_by_pattern(self.contents, pattern="Thermochemistry")[1:][-1]
            try:
                self.__dict__.update(scaling_factors[self.method][self.basis])
            except KeyError:
                printred(f"{self.method} {self.basis} scaling factors not specified yet.")
            self.temperature = float(self.search("Temperature", lines=thermochem).split()[1])
            self.mass_total = float(self.search("Molecular mass", lines=thermochem).split(":")[1].strip().split()[0])
            atom_lines = [x for x in thermochem if "Atom " in x]
            self.mass_atoms = [float(x.strip().split()[-1]) for x in atom_lines]


            self.get_frequencies(verbose=verbose)
            self.get_entropy(verbose=verbose)
            self.get_zero_point(verbose=verbose)
            self.get_hlc(verbose=verbose)
            self.get_thermal_correction(verbose=verbose)
            self.thermochem = f"""
            {styledarkcyan("HLC:"):>30} {self.hlc:>12.8f} Hartrees
            {styledarkcyan("Thermal corr.:"):>30} {self.tc_kj:>12.8f} kJ/mol
            {styledarkcyan(" "):>30} {self.tc:>12.8f} Hartrees
            {styledarkcyan("ZPVE:"):>30} {self.zpve_kj:>12.8f} kJ/mol
            {styledarkcyan(" "):>30} {self.zpve:>12.8f} Hartrees
            {styledarkcyan("Entropy:"):>30} {self.entropy_kj:>12.8f} kJ/mol/K
            {styledarkcyan(" "):>30} {self.entropy:>12.8f} Hartrees
            """
        except:
            pass

    def get_entropy(self, verbose=0):
        """ Thermochem-auto's method
        imol: ' the eigenvalues of imatrix in its first n elements ', n = 3
        """

        ######### s_nutot #########
        snusc       = self.frequencies * C_LIGHT * self.sf_s
        theta       = (snusc * H_PLANCK/KB) / self.temperature # skipped a tchem step here
        exp_theta   = np.exp(-theta)
        snu         = R_UNI * ( theta  /  (  (np.exp(theta)-1) - np.log(1-exp_theta) )  )
        s_nutot     = np.sum(snu)

        ######### s_trans #########
        q_trans     = ((  (2*PI*self.mass_total*KB*self.temperature)/(H_PLANCK**2))**1.5 )*KB*self.temperature/PPA
        s_trans     = R_UNI * (np.log(q_trans) + 2.5)


        ######### s_rot #########
        if self.n_atoms <= 1: # assume molecules > 2 atoms are not linear
            qrot = 0
            s_rot = 0 # I think that's implied?
        else:
            self.get_imatrix(verbose=verbose)
            imol, _ = np.linalg.eig(self.imatrix)
            imolkg = imol*1.66054202E-27*((5.29177249E-11)**2)
            thetaxyz = (H_PLANCK**2) / (8*(PI**2)*KB*imolkg)
            sigma = int(float(self.search("Rotational symmetry number").split()[-1]))

            if self.n_atoms == 2:
                qrot = (self.temperature / thetaxyz[2])/sigma
                s_rot = R_UNI * (math.log(qrot) + 1.0)
            else: 
                qrot = (PI**0.5)*(self.temperature**1.5)/(np.prod(thetaxyz)**0.5)/sigma
                s_rot = R_UNI * (math.log(qrot) + 1.5)


        ######### s_elec #########
        q_elec = self.multiplicity
        s_elec = R_UNI * math.log(q_elec)

        if verbose > 3:
            print(f"""
                s_nutot = {s_nutot}
                s_trans = {s_trans}
                s_rot   = {s_rot}
                s_elec  = {s_elec}
                """)
                

        self.entropy_kj = (s_trans + s_elec + s_rot + s_nutot)/1000
        self.entropy = self.entropy_kj / HARTREE_TO_KJ
        if verbose > 3:
            print(f"""\
                Entropy total: {self.entropy}""")


    def get_frequencies(self, verbose=0):
        # Looks like this:
        #  Frequencies --      8.9179                14.7818                38.4795
        freq_lines = [x.split("--")[1].split() for x in self.contents if "Frequencies" in x]
        frequencies = [np.float64(y) for x in freq_lines for y in x]
        self.frequencies = np.array(frequencies)
        if verbose > 5:
            print(f"""\
                Frequencies: \n{self.frequencies}""")

    def check_frequencies(self, verbose=0):
        try:
            self.get_frequencies()
            if all(self.frequencies > 0):
                print(f"{self.base_name} has no imaginary frequencies.")
            else:
                print(f"{self.base_name} has imaginary frequencies.")
                if verbose:
                    print(f"    Frequencies:{self.frequencies}")

        except:
            pass



    def get_thermal_correction(self, verbose=0):
        """
        This is annoyingly complex. I could have written it more simply, but it
        follows the process of thermochem-auto for easier review. Variable names follow theirs.

        tc_total = tc_entropy + R_KJ*TEMP
        tc_entropy = tc_vibr + tc_trans + tc_rot + tc_elec
        kJ/mol
        """

        TEMP_R      =   R_KJ * self.temperature # used a lot...

        hnusc = self.frequencies * self.sf_tc * C_LIGHT
        quh   = hnusc * H_PLANCK/KB
        hnu   = R_KJ * quh   /  (np.exp(quh/self.temperature)-1)

        tc_vibr = np.sum(hnu)
        tc_trans = TEMP_R * 1.5
        tc_elec  = 0 # why? Ask thermochem-auto

        # checking for linearity -- I assume all molecules > 2 atoms are linear

        if self.n_atoms > 2:
            tc_rot = TEMP_R*1.5
        elif self.n_atoms == 2:
            tc_rot = TEMP_R
        else:
            tc_rot = 0

        tc_entropy = tc_vibr + tc_trans + tc_rot + tc_elec
        self.tc_kj = tc_entropy + TEMP_R
        self.tc = self.tc_kj / HARTREE_TO_KJ

        if verbose > 3:
            print(f"""
                tc_vibr  = {tc_vibr}
                tc_trans = {tc_trans}
                tc_rot   = {tc_rot}
                tc_elec  = {tc_elec}
                """)

        if verbose > 3:
            print(f"""\
                Thermal correction: {self.tc}""")

    def get_zero_point(self, verbose=0):
        """
        This is annoyingly complex. I could have written it more simply, but it
        follows the process of thermochem-auto for easier review. Variable names
        follow theirs.

        zpnusc = freq*clight*sfzpve
        kJ/mol
        """

        zpnusc  = self.frequencies * C_LIGHT * self.sf_zpve
        quzp    = zpnusc * H_PLANCK / KB
        zpnu    = R_KJ * quzp * 0.5

        self.zpve_kj = np.sum(zpnu)
        self.zpve    = self.zpve_kj / HARTREE_TO_KJ
        if verbose > 3:
            print(f"""\
                ZPVE: {self.zpve}""")



    def get_hlc(self, verbose=0):
        ALPHA_CONST = 9.413/1000 # citation: LeafCompChem.pdf (now in hartrees)
        BETA_CONST = 3.969/1000 # LeafCompChem.pdf
        electrons = [x for x in self.contents if "alpha electrons" in x][0]
        split = electrons.split()
        alpha, beta = int(split[0]), int(split[3])
        self.hlc = -ALPHA_CONST*beta - (BETA_CONST*(alpha-beta))/1000
        if verbose > 3:
            print(f"""\
                HLC: {self.hlc}""")


    def get_coordinates(self):
        split = self.cmcoords.split("\\")
        self.charge, self.multiplicity = map(int, split[0].split(','))
        coordline = split[1].split(",")
        if len(coordline) == 4:
            keys = ["element", "x", "y", "z"]
        else:
            keys = ["element", "_", "x", "y", "z"]
        self.parsed_coords = lines_to_dct(split[1:], keys, delimiter=",")
        xyzs = [self.parsed_coords[col] for col in ["x", "y", "z"]]
        coordinates = np.array(xyzs, dtype=np.float64)
        self.xyz = np.transpose(coordinates)

    def get_imatrix(self, verbose=0):
        xcm = np.zeros(3)
        for mass, coords in zip(self.mass_atoms, self.xyz):
            xcm += mass*coords
        xcm /= self.mass_total
        if verbose > 5:
            print(f"""\
                Center of mass: {xcm}""")

        ixx, iyy, izz, ixy, ixz, iyz = 0, 0, 0, 0, 0, 0
        for mass, coords in zip(self.mass_atoms, self.xyz):
            x2, y2, z2 = np.square(coords)
            xc, yc, zc = coords - xcm

            ixx += mass*(y2+z2)
            iyy += mass*(x2+z2)
            izz += mass*(x2+y2)
            ixy += mass*xc*yc
            ixz += mass*xc*zc
            iyz += mass*yc*zc

        self.imatrix = np.array([[ixx, ixy, ixz], 
                                [ixy, iyy, iyz], 
                                [ixz, iyz, izz]])
        if verbose > 4:
            print(f"""\
                imatrix: \n{self.imatrix}""")








    def get_solvation(self):
        try:
            scrf_lines = section_by_pattern(self.contents, pattern="SCRF")[1][:2]
            scrf = "".join(scrf_lines)
            smodel, solvent_ = scrf.split("SCRF=(")[-1].strip().split(",")
            self.solvate = True
            self.solvent_model = smodel

            solvent = solvent_.split("=")[1].strip().split(")")[0].strip()
            if solvent == "h2o":
                self.solvent = "water"
            else:
                self.solvent = solvent
        except (ValueError, IndexError):
            self.solvate = False
            self.solvent = None
            self.solvent_model = None
        return dict(solvate=self.solvate, solvent=self.solvent, solvent_model=self.solvent_model)

    def get_standard_orientation(self):
        sto = section_by_pattern(self.contents, pattern="Standard orientation")

        stdsect = section_by_pattern(self.contents, pattern="Standard orientation")[-1]
        coord_lines = section_by_pattern(stdsect, pattern="--------------------------------------")[2][1:]
        keys = ["center", "at_z", "at_type", "x", "y", "z"]
        parsed = lines_to_dct(coord_lines, keys)
        arr_cols = [parsed['x'], parsed['y'], parsed['z']]
        try:
            self.std_coords = np.array(arr_cols, dtype=np.float64)
        except ValueError:
            print(self.filename)
            raise ValueError
        self.elements = parsed['at_z']
        self.n_atoms = len(self.elements)

    def get_all(self):
        keys = ["base_name", "zpve", "tc", "hlc", "entropy", "temperature", "elements", "solvate", "solvent", "solvent_model"]
        dct = dict((k, self.__dict__[k]) for k in keys)
        return dct



class QChemOut(QMOut):

    def get_others(self, **kwargs):
        self.get_n_basis()

    def get_method(self):
        rem = section_by_pattern(self.contents, pattern="\$rem")[1]
        rembody = section_by_pattern(rem, pattern="\$end")[0]
        for line in rembody:
            if "method" in line.lower():
                self.method = line.split()[1].strip()
            if "basis" in line.lower():
                self.basis = line.split()[1].strip()
        return self.method

    def get_energy(self):
        method = self.get_method()
        for line in self.contents[::-1]:
            if method in line and "energy" in line:
                self.energy = np.float64(line.split("=")[-1].strip())
                return self.energy
        raise ValueError("No energies found.")

    def get_solvation(self):
        try:
            smx = section_by_pattern(self.contents, pattern="\$smx")[1]
            smxbody = section_by_pattern(smx, pattern="\$end")[0]
            for line in smxbody:
                if "solvent" in line.lower():
                    self.solvent = line.split()[1].strip()
                    self.solvate = True
        except IndexError:
            self.solvate = False
            self.solvent = None

    def get_standard_orientation(self):
        stdsect = section_by_pattern(self.contents, pattern="Standard Nuclear Orientation")[1]
        coord_lines = section_by_pattern(stdsect, pattern="--------------------------------------")[1][1:]
        keys = ["I", "element", "x", "y", "z"]
        parsed = lines_to_dct(coord_lines, keys)
        self.elements = parsed['element']
        arr_cols = [parsed['x'], parsed['y'], parsed['z']]
        self.std_coords = np.array(arr_cols, dtype=np.float64)
        self.n_atoms = len(self.elements)

    def get_coordinates(self):
        molecule = section_by_pattern(self.contents, pattern="\$molecule")[1]
        molbody = section_by_pattern(molecule, pattern="\$end")[0]
        mollines = [x.strip() for x in molbody]
        mollines = [x for x in mollines if x]

        self.charge, self.multiplicity = map(int, mollines[1].split())
        keys = ["element", "x", "y", "z"]
        self.parsed_coords = lines_to_dct(mollines[2:], keys)

    def get_n_basis(self):
        for line in self.contents:
            if "number of basis is" in line:
                self.n_basis = int(line.strip().split()[-1].strip())
                return
        self.n_basis = None







output = dict(
    out=QChemOut,
    log=GaussianLog)

def read_output(filename, verbose=1):
    try:
        return output[filename[-3:]](filename, verbose=verbose)
    except KeyError:
        pass

def mass_read(paths, verbose=2, action="summarise", **kwargs):
    files = []
    for path in paths:
        if os.path.isfile(path):
            files.append(os.path.realpath(path))
        elif os.path.isdir(path):
            files += glob.glob(path+"/**/*")

    for file in files:
        parsed = read_output(file, verbose=verbose)
        if parsed:
            if action == "checkopt":
                try:
                    parsed.check_frequencies(verbose=verbose)
                except:
                    pass


