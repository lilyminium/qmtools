from .qminp import QMInp
from utils.other import indent

class MolProInp(QMInp):
    """
    MolPro input. The z-matrix probably doesn't work.
    """
    ext = "ini"

    zmat_str = ""
    opt_str = ""
    coord_type="cartesian\n"

    def make_zmat_coords(self):
        out = []
        for el, (x, y, z) in zip(self.elements, self.xyz_arr):
            out.append(f"{el:2} {x:>16.5}{y:>16.5}{z:>16.5}")
        self.n_coords = len(out)
        self.coords = "\n".join(out) + "\n"


    def make_string_options(self):
        if self.zmat:
            # VERY IFFY. Need to incorporate variables, probably.
            self.make_zmat_coords()
            self.molspec = "angstrom\ngeometry=\{\n {self.n_coords}\n{self.coords}\}"
            self.coord_type = ""
        else:
            self.molspec = f"geometry={{\n {self.n_coords}\n{self.coords}}}"

        if self.optimize:
            self.opt_str = "optg\n"

    def make_file_lines(self):
        nelec = self.geometry.get_n_electrons()
        spin = int(self.multiplicity)-1
        name = f"*** {self.geometry.base_name} using {self.theory} and {self.basis}\n"
        geometry = f"symmetry,nosym\n{self.molspec}\n"
        wf = f"wf,NELEC={nelec},SYMMETRY=1,SPIN={spin},CHARGE={self.charge}\n"
        keywords=f"basis={self.basis}\n{self.coord_type}rhf\n{self.opt_str}{self.theory}"

        self.file_lines = name+geometry+wf+keywords




    