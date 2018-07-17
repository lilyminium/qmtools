from .qminp import QMInp

class GaussianInp(QMInp):
    """
    For Gaussian input files.

    Note -- unsure when the z-matrix stuff is ever used.
    """
    ext = "com"
    program = "gaussian"

    grid = ""
    opt = ""
    freq = ""
    scrf = ""
    dovac = ""

    solvents = dict(
        water="h2o")

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
            if self._ask_questions:
                self.askbool("rassolov")
            if self.rassolov:
                self.genbasis = self.rassolov_version
                self._basis = "Gen 6D"
            else:
                self.genbasis = self._basis

        except KeyError:
            self.rassolov_version = self._basis
            self.rassolov = None
            self.genbasis = self._basis

    def make_string_options(self):
        if self.theory not in ["csd", "qci", "mp2", "hf"]:
            self.grid = " INT(grid=ultrafine)"

        if self.solvate:
            self.gaussian_solvent = self.solvents[self.solvent]
            if self.dGsolv:
                self.dovac = ",dovac,self"
            self.scrf = f" SCRF=(SMD,Solvent={self.gaussian_solvent})"
            self.scrf_dovac = f" SCRF=(SMD,Solvent={self.gaussian_solvent}{self.dovac})"

        if self.optimize:
            self.opt = " OPT IOP(2/17=4)"

        if self.calculate_frequencies:
            self.freq = " Freq=Noraman"

        if self.zmat:
            self.ts = "(z-matrix)"
            self.tszm = ",z-matrix"

        if self.transition_state:
            self.ts = f"(TS,calcfc{self.tszm},noeigentest,maxcyc=200)"



    def make_file_lines(self):
        basis = f"@/home/{self.REMOTE_DIR}/{self.RJ_UNAME}/Basis/{self.genbasis}.gbs/N\n\n"
        link = "\n--Link1--\n"
        header_ = f"%chk={self.jobid}.chk\n# {self.theory}/{self.basis} SCF={self.convergence}{self.grid}{self.opt}{self.freq}"
        geom = f"geom=check guess=read IOP(2/17=4)\n\n{self.jobid}\n\n{self.cm}\n\n"
        molspec = f"\n\n{self.cm}\n{self.coords}\n"

        header = header_[:]
        footer = basis + "\n"
        if self.optimize:
            header += f"{self.scrf_dovac}\n"
            footer += f"{link}{header_}{self.scrf}\n{geom}{basis}"
            if self.dGsolv:
                footer += f"{link}{header_}{self.scrf_dovac}\n{geom}{basis}"
        else:
            header += f"{self.scrf}\n"

        header += f"\n{self.jobid}"

        self.file_lines = header + molspec + footer
        