import itertools

from .interaction import InteractionBase
import mdtraj as md


class GeometryFile(InteractionBase):
    questions = dict(
        charge=dict(
            ask="What is the charge of this molecule?",
            valid=lambda x: isinstance(x, int)),
        multiplicity=dict(
            ask="What is the multiplicity of this molecule?",
            valid=lambda x: isinstance(x, int) and x > 0
            ))

    def __init__(self, file):
        self.file = file
        self.split_path_and_file(*file.split("/")[::-1])

    def read(self):
        try:
            self.structure = md.load(self.file)
        except OSError:
            self.structure = self.read_log_file()

    def split_path_and_file(self, file_name, *path_to_file):
        self.path_to_file = "/".join(path_to_file[::-1]) + "/"
        self.file_name = file_name
        self.split_file(*file_name.split(".")[::-1])

    def split_file(self, extension, *file_name_parts):
        self.extension = extension
        self.base_name = ".".join(file_name_parts[::-1])

    def read_log_file(self):
        with open(self.file, 'r') as f:
            text = f.readlines()

        stripped = [x.strip() for x in text]
        not_empty = [x for x in stripped if x]

        sections = section_by_pattern(not_empty,
                                        pattern="Input orientation")
        geometry = section_by_pattern(sections[-1],
                                        pattern="------------")[2][1:]

    def guess_charge(self):
        pass

    def guess_multiplicity(self):
        pass

    
    def ask_cm(self):
        self.ask('charge')
        self.ask('multiplicity')



class QMInp(InteractionBase):
    theory = "M062X"
    basis = "6-31+G*"
    rassolov = True


    questions = dict(
        theory=dict(
            ask="What level of theory do you want to use?",
            )
        )
    def __init__(self, file):
        self.process_geometry(file)

    def process_geometry(self, file):
        self.geometry = GeometryFile(file)
        self.geometry.ask_cm()

    

        

class GaussianInp(QMInp):

    def __init__(self, geometry):
        pass

class QChemInp(QMInp):
    pass
