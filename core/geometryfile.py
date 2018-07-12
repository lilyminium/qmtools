import mendeleev as meev
from .interaction import InteractionBase
from .filereader import FileReader

class GeometryFile(InteractionBase):
    charge = 0
    multiplicity = 1

    def __init__(self, file):
        read = FileReader(file)
        self.structure = read.structure
        self.topology = read.topology
        df, _ = read.topology
        self.elements = df['element']
        self.split_path_and_file(*file.split("/")[::-1])

    def split_path_and_file(self, file_name, *path_to_file):
        self.path_to_file = "/".join(path_to_file[::-1])
        if self.path_to_file:
            self.path_to_file+"/"
        self.file_name = file_name
        self.split_file(*file_name.split(".")[::-1])

    def split_file(self, extension, *file_name_parts):
        self.extension = extension
        self.base_name = ".".join(file_name_parts[::-1])

    def get_heavy_atoms(self):
        self.n_heavy_atoms = len([x for x in self.elements if x != "H"])

    def get_n_electrons(self):
        electrons = [meev.element(x).electrons for x in self.elements]
        self.n_electrons = sum(electrons)
        return self.n_electrons
