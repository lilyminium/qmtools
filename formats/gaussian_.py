import numpy as np
from utils import section_by_pattern, lines_to_dct

class QMOut:
    thermal = None
    zero_point = None
    hlc = 0
    entropy = None
    temperature = None

    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'r') as f:
            contents = [x.strip() for x in f.readlines()]
        self.contents = [x for x in contents if x]
        self.get_standard_orientation()
        self.get_summary()
        self.get_method()
        

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

    @staticmethod
    def get_value(line):
        return np.float64(line.split("=")[-1].strip())



class GaussianLog(QMOut):

    def get_n_basis(self):
        basis_line = section_by_pattern(self.contents, pattern="basis functions,")[1][0]
        self.n_basis = int(basis_line.strip().split()[0].strip())
        return self.n_basis

    def get_summary(self):
        super().get_summary()
        self.env, self.header, name, self.cmcoords, self.final = self.summary.split("\\\\")[:5]
        self.base_name = name.split(".")[0]
        self.get_n_basis()
        self.get_dft_details()

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
                self.zero_point = np.float64(line.split("=")[-1].strip())
            if "thermal" in line.lower():
                self.thermal = np.float64(line.split("=")[-1].strip())
                self.get_entropy()
        return dict(base_name=self.base_name, zpve=self.zero_point, 
                    tc=self.thermal, hlc=self.hlc, entropy=self.entropy, 
                    temperature=self.temperature, elements=self.elements)

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
        
        if "SCRF" in self.header:
            self.solvate = True
            scrf = [x for x in self.contents if "scrf" in x.lower()][0]
            smodel, solvent_ = scrf.split("SCRF=(")[-1].strip().split(",")
            self.solvent_model = smodel

            solvent = solvent_.split("=")[1].strip().split(")")[0].strip()
            if solvent == "h2o":
                self.solvent = "water"
            else:
                self.solvent = solvent
        else:
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
        self.std_coords = np.array(arr_cols, dtype=np.float64)
        self.elements = parsed['at_z']

    def get_all(self):
        dct = self.get_solvation()
        dct.update(self.get_dft_details())
        return dct



class QChemOut(QMOut):

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
            for line in rembody:
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








output = dict(
    out=QChemOut,
    log=GaussianLog)

def read_output(filename):
    return output[filename[-3:]](filename)

