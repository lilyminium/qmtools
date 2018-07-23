import numpy as np
from utils import section_by_pattern, lines_to_dct, printyellow, styledarkcyan

class QMOut:
    tc = None
    zpve = None
    hlc = 0
    entropy = None
    temperature = None

    def __init__(self, filename, verbose=2):
        self.filename = filename
        with open(filename, 'r') as f:
            contents = [x.strip() for x in f.readlines()]
        self.contents = [x for x in contents if x]
        self.get_summary()
        self.get_standard_orientation()
        self.get_coordinates()
        self.get_method()
        self.get_solvation()
        self.get_others()
        if verbose > 1:
            self.print_summary()

    def print_summary(self):
        printyellow(self.filename)
        print(f"""\
            {styledarkcyan("Method:")} {self.method}
            {styledarkcyan("Charge:")} {self.charge: <3d} {styledarkcyan("Multiplicity:")} {self.multiplicity}
             {styledarkcyan("Atoms:")} {self.n_atoms: <3d} {styledarkcyan("Basis functions:")} {self.n_basis}
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_others(self):
        self.get_n_basis()
        self.get_dft_details()

    def get_n_basis(self):
        basis_line = section_by_pattern(self.contents, pattern="basis functions,")[1][0]
        self.n_basis = int(basis_line.strip().split()[0].strip())
        return self.n_basis

    def get_summary(self):
        super().get_summary()
        self.env, self.header, name, self.cmcoords, self.final = self.summary.split("\\\\")[:5]
        self.base_name = name.split(".")[0]

    def get_method(self):
        self.method = self.env.split("\\")[4]
        return self.method

    def get_energy(self):
        # final value before RMSD
        energy = self.final.split("\\RMSD")[0].split("\\")[-1].split("=")[-1]
        self.energy = np.float64(energy)
        return self.energy

    def get_dft_details(self):
        split = self.final.split("\\")
        for line in split:
            if "zeropoint" in line.lower():
                self.zpve = np.float64(line.split("=")[-1].strip())
            if "thermal" in line.lower():
                self.tc = np.float64(line.split("=")[-1].strip())
                self.get_entropy()
                self.get_hlc()
        return 

    def get_entropy(self):
        corrections = [x for x in self.contents if "Thermal correction to" in x][-2:]
        self.temperature = float([x for x in self.contents if "Temperature" in x][0].split()[1])
        enthalpy, gibbs = map(self.get_value, corrections)
        self.entropy = -(gibbs - enthalpy)/self.temperature

    def get_hlc(self):
        ALPHA_CONST = 9.413/1000 # citation: LeafCompChem.pdf (now in hartrees)
        BETA_CONST = 3.969/1000 # LeafCompChem.pdf
        electrons = [x for x in self.contents if "alpha electrons" in x][0]
        split = electrons.split()
        alpha, beta = int(split[0]), int(split[3])
        self.hlc = -ALPHA_CONST*beta - (BETA_CONST*(alpha-beta))


    def get_coordinates(self):
        split = self.cmcoords.split("\\")
        self.charge, self.multiplicity = map(int, split[0].split(','))
        coordline = split[1].split(",")
        if len(coordline[0]) == 3:
            keys = ["element", "x", "y", "z"]
        else:
            keys = ["element", "_", "x", "y", "z"]
        self.parsed_coords = lines_to_dct(split[1:], keys, delimiter=",")

    def get_solvation(self):
        try:
            scrf = [x for x in self.contents if "scrf" in x.lower()][0]
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

    def get_others(self):
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
    return output[filename[-3:]](filename, verbose=verbose)

