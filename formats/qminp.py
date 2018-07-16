from core.interaction import InteractionBase
from core.geometryfile import GeometryFile
from utils.colors import style

class QMInp(InteractionBase):
    """
    Base class for generating QM input files. Should be
    subclassed for actual usage.


    """
    # 
    # Defaults
    #

    theory = "M062X"
    _basis = "6-31+G*"
    genbasis = ""
    charge = 0
    multiplicity = 1
    _convergence = "Tight"
    _rassolov = True
    _solvate = False
    solvent_model = "SMD"
    solvent = "water"

    _optimize = False
    calculate_frequencies = False
    dGsolv = False
    zmat = False
    transition_state = False

    ext = None
    _ask_questions = True

    #
    # Questions to ask
    #

    question_options = dict(
        theory          = dict(
                            ask="What level of theory do you want to use?",
                            options=["M062X", "CSD", "QCI", "MP2", "HF"]
                            ),
        basis           = dict(
                            ask="Which basis do you want to use?",
                            options = ("sto3g", "321", "6-31G", "6-31G*", "6-31+G*", 
                                        "6-31G(d)", "6-31+G(d)", "G3largeXP", 
                                        "GTMP2LARGE", "HF6Z", "HFQZ", "Br.aug-cc-pvtz-DK",
                                        "Br.aug-cc-pvtz", "Br.cc-pvtz-DK", "Br.cc-pvtz",
                                        "C.6-311pG-3df", "C.g3mp2large", "H.6-311pG-2p",
                                        "H.g3mp2large", "g3xlarge")
                            ),
        solvent_model   = dict(
                            ask="What solvent model do you want?",
                            options=["SMD"]
                            ),
        solvent         = dict(
                            ask = "What is the solvent you want to use?",
                            options = ["toluene", "etac", "water"]),
        convergence     = dict(
                            ask = "Required convergence threshold?",
                            options = ["Tight"]
                            ),
        charge          = dict(
                            ask = "What is the charge of this molecule?",
                            valid = lambda x: int(x)),
        multiplicity    = dict(
                            ask = "What is the multiplicity of this molecule?",
                            valid = lambda x: int(x) > 0
            ),
        backend    = dict(
                            ask = "Which CC backend to use?",
                            options=["XM"]
            )

        )

    question_bools = dict(
        rassolov = "Do you want to use the Rassolov version?",
        solvate = "Do you want to use a solvent model?",
        optimize = "Do you want to optimise the geometry?",
        calculate_frequencies = "Do you want to calculate the frequencies?",
        dGsolv = "Do you want to calculate dGsolv?",
        zmat = "Optimise with Z matrix ?",
        transition_state = "Is it a transition state?"
        )

    def __init__(self, file, show=False, interactive=False, HOME=None, REMOTE_DIR=None, RJ_UNAME=None, **kwargs):
        self.HOME = HOME
        self.REMOTE_DIR = REMOTE_DIR
        self.RJ_UNAME = RJ_UNAME
        print(style(f"    File: {file}", "yellow"))
        self.process_geometry(file)

        if kwargs:
            if not interactive:
                self._ask_questions = False

            rassolov = kwargs.pop("rassolov", True)
            basis = kwargs.pop("basis", self.basis)
            theory = kwargs.pop("theory", self.theory)
            self.basis = basis
            self.theory = theory
            self.rassolov = rassolov
            self.jobid = f"{self.geometry.base_name}.{self.theory}_{self.rassolov_version}"
            
            for k, v in kwargs.items():
                setattr(self, k, v)

            

        self.make_coords()
        if self._ask_questions:
            self.ask_questions()
        else:
            print(f"""
                Theory  : {self.theory}
                Basis   : {self.basis} {("" if not self.rassolov else self.genbasis)} (Rassolov={self.rassolov})
                Charge  : {self.charge}  Multiplicity: {self.multiplicity}
                Optimize: {self.optimize}  Frequencies: {self.calculate_frequencies}
                Solvate : {self.solvate}""")
            if self.solvate:
                print(f"""
                    Solvent model: {self.solvent_model}
                    Solvent      : {self.solvent}
                    """[1:])
        
        self.make_string_options()
        self.make_file_lines()
        self.write_file()
        if show:
            print(f"""
                ------   {self.path}{self.jobid}.{self.ext}   ------\n{self.file_lines}
                """)

    def process_geometry(self, file):
        self.geometry = GeometryFile(file)
        self.jobid = self.geometry.base_name
        self.path = self.geometry.path_to_file
        self.xyz_arr = self.geometry.xyz
        self.elements = self.geometry.elements

    def ask_questions(self):
        self.ask("charge")
        self.ask("multiplicity")
        self.ask("theory")
        self.jobid += f".{self.theory}"
        self.ask("basis")
        self.jobid += f"_{self.rassolov_version}"
        self.askbool("solvate")
        self.askbool("optimize")

    def make_coords(self):
        out = []
        for el, (x, y, z) in zip(self.elements, self.xyz_arr):
            out.append(f"{el:2} {x:>16.10f}{y:>16.10f}{z:>16.10f}")
        self.n_coords = len(out)
        self.coords = "\n".join(out) + "\n"

    def write_file(self):
        filename = f"{self.path}{self.jobid}.{self.ext}"
        with open(filename, 'w') as f:
            f.write(self.file_lines)
        print(style(f"Written to {filename}\n", "bold", "green"))



    
    # Properties that ask further questions (or not) when set.
    # There's probably a better way of doing this.

    @property
    def cm(self):
        return f"{self.charge} {self.multiplicity}"
    
    
    @property
    def basis(self):
        return self._basis

    @basis.setter
    def basis(self, basis_set):
        self._basis = basis_set
        
        to_rass = {"6-31G*":"6-31Gd",
                    "6-31G(d)":"6-31Gd",
                    "6-31+G*": "6-31pGd",
                    "6-31+G(d)": "6-31pGd",
                    }
        try:
            self.rassolov_version = to_rass[self._basis]
        except KeyError:
            self.rassolov_version = self._basis


    @property
    def rassolov(self):
        return self._rassolov

    @rassolov.setter
    def rassolov(self, to_rassolov):
        self._rassolov = to_rassolov

        if self._rassolov:
            self.genbasis = self.rassolov_version
            self._basis = "Gen 6D"
        else:
            self.genbasis = self.basis

    @property
    def solvate(self):
        return self._solvate

    @solvate.setter
    def solvate(self, to_solvate):
        if to_solvate == []:
            to_solvate = True
        self._solvate = to_solvate
        if to_solvate:
            if self._ask_questions:
                self.ask("solvent_model")
                self.ask("solvent")
                self.askbool("dGsolv")
            else:
                try:
                    self.solvent = to_solvate[0]
                    self.solvent_model = to_solvate[1]
                except:
                    pass

            self.jobid += f"_{self.solvent}"

    @property
    def convergence(self):
        return self._convergence

    @convergence.setter
    def convergence(self, value):
        self._convergence = value
        self.threshold = 8

    @property
    def optimize(self):
        return self._optimize

    @optimize.setter
    def optimize(self, to_optimize):
        if to_optimize:
            self._optimize = True
            if self._ask_questions:
                self.askbool("zmat")
                self.askbool("transition_state")
                self.askbool("calculate_frequencies")
            self.jobid += "_opt"


    # 
    # Methods to be defined in subclasses 
    #

    def make_string_options(self):
        pass

    def make_file_lines(self):
        pass

    
    


    
    
    

    

        


