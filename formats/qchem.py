from .qminp import QMInp
from utils.other import indent

class QChemInp(QMInp):
    """
    QChem input files. Fairly sraightforward.
    I have no idea what nbo is.
    """

    ext = "in"

    jobtype = "sp"
    jobtype2 = ""
    nbo = ""
    solvent_section = ""
    remsolv = ""
    backend = "XM"

    def ask_questions(self):
        super().ask_questions()
        self.ask("convergence")
        self.ask("backend")

    def make_coords(self):
        super().make_coords()
        self.coords = "".join([indent(x, n=4) for x in self.coords.split('\n')])

    def make_string_options(self):
        if self.optimize:
            self.jobtype = "opt"
            if self.calculate_frequencies:
                self.jobtype2 = "freq"

        if self.solvate:
            self.remsolv = indent(f"SOLVENT_METHOD {self.solvent_model}", n=4)
            self.solvent_section = indent(f"\n$smx\n  solvent {self.solvent}\n$end")

    def make_file_lines(self):
        jobstr      = f"JOBTYPE        {self.jobtype}"
        theory      = f"METHOD         {self.theory}"
        basis       = f"BASIS          {self.basis}"
        cc_backend  = f"CC_BACKEND     {self.backend}"
        mem_total   =  "MEM_TOTAL      60000"

        rem_lines = [jobstr, theory, basis, cc_backend, mem_total]
        rem_body = "".join([indent(x, n=4) for x in rem_lines])

        molspec = f"$molecule\n  {self.cm}\n{self.coords}$end\n"
        rem = f"\n$rem\n\n\n{rem_body}$end\n"

        self.file_lines = f"{molspec}{rem}{self.solvent_section}"
