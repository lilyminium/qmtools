import re
import datetime
from utils import regex_coords, get_environment, file_details, printyellow, printdarkcyan
from data import rj_template, raijin, raijin, get_params
import subprocess

JOBFS_MIN = 5000
JOBFS_MAX = 250000

WALLTIME_MAX = 96
WALLTIME_MIN = 1

NCPUS_MIN = 1
NGPUS_MIN = 0

CPUS_FOR_20_ATOMS = 8

class QJob:
    _walltime = WALLTIME_MIN
    _ncpus    = NCPUS_MIN
    ngpus    = NGPUS_MIN
    _jobfs_mb    = JOBFS_MIN
    queue     = ""
    text = ""

    @property
    def jobfs_mb(self):
        if self._jobfs_mb < JOBFS_MIN:
            return JOBFS_MIN
        if self._jobfs_mb > JOBFS_MAX:
            return JOBFS_MAX
        return self._jobfs_mb

    @jobfs_mb.setter
    def jobfs_mb(self, value):
        try:
            self._jobfs_mb = int(value)
        except TypeError:
            self._jobfs_mb = int(1000*value(self.n_heavy_atoms))

    @property
    def walltime(self):
        if self._walltime < WALLTIME_MIN:
            return WALLTIME_MIN
        if self._walltime > WALLTIME_MAX:
            return WALLTIME_MAX
        return self._walltime

    @walltime.setter
    def walltime(self, value):
        try:
            self._walltime = int(value)
        except TypeError:
            self._walltime = int(value(self.n_heavy_atoms))

    @property
    def ncpus(self):
        if self.n_heavy_atoms > 20:
            return CPUS_FOR_20_ATOMS
        return abs(self._ncpus)

    @ncpus.setter
    def ncpus(self, value):
        self._ncpus = int(value)
    

    def __init__(self, program, elements, theory, out_extension, file_path="", subdir="",**kwargs):
        self.program = program
        self.theory = theory
        self.file_path = file_path
        self.out_extension = out_extension
        if subdir:
            if subdir[-1] != "/":
                subdir += "/"
        self.dir = subdir
        self.n_heavy_atoms = len([x for x in elements if x != "H"])
        self.guess_parameters()
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.get_template_kwargs()
        self.text = self.template.format(**self.dct)
        self.save_job()
        self.submit()
        self.update_recordfile()


    @classmethod
    def from_file(cls, file, **kwargs):
        printyellow(f"    Input: {file}")
        # get program
        extensions = {
            "com": ("gaussian", "log"),
            "ini": ("molpro", "out"),
            "in" : ("qchem", "out")
            }
        details = file_details(file)
        program, out_extension = extensions[details["extension"]]

        # get elements
        with open(file, 'r') as f:
            contents = f.readlines()
        clean = [x.strip() for x in contents]
        coords = []
        for line in clean:
            if re.fullmatch(f"[a-zA-Z]+\s+{regex_coords}", line):
                coords.append(line)
        elements = [x.split()[0] for x in coords]

        # get theory if program is Gaussian
        if program == "gaussian":
            theory_line = [x for x in clean if x.startswith("#")]
            theory = theory_line[0].split("/")[0].split("#")[1].strip()
        else:
            theory = None

        return cls(program, elements, theory, out_extension, **details, **kwargs)

    def get_template_kwargs(self):
        self.dct = get_environment()
        self.dct['walltime'] = f"{self.walltime}:00:00"
        self.dct['ncpus'] = self.ncpus
        self.dct['ngpus'] = self.ngpus
        self.dct['jobfs'] = self.jobfs_mb
        self.dct['vmem'] = self.vmem_mb
        self.dct["queue"] = self.queue
        self.dct['base_directory'] = self.base_directory
        self.dct['base_name'] = self.base_name
        self.dct['out_extension'] = self.out_extension
        txt = "    walltime={walltime}, jobfs={jobfs}MB, vmem={vmem}MB, queue={queue}, ncpus={ncpus}"
        if self.ngpus:
            txt.append(", ngpus={ngpus}")
        printdarkcyan(txt.format(**self.dct))

    def guess_parameters(self):
        for k, v in get_params(self.n_heavy_atoms, self.theory, self.program).items():
            setattr(self, k, v)

    def save_job(self):
        self.job_name = f"{self.directory}/{self.base_name}.job"

        with open(self.job_name, 'w') as f:
            f.write(self.text)

    def submit(self):
        subprocess.call("{ssh_home} 'mkdir -p {wdir}'".format(**self.dct), shell=True)
        subprocess.call(f"scp -q {self.job_name} {self.file_path} {self.dct['rj_wdir']} 2>/dev/null", shell=True)
        proc = subprocess.Popen("{ssh_home} 'cd {wdir} && qsub {base_name}.job'".format(**self.dct), shell=True, stdout=subprocess.PIPE)
        jobid = str(proc.communicate()[0]).split(".")[0][2:]
        printdarkcyan(f"    {jobid:<9} " + "{wdir}/{base_name}.job\n".format(**self.dct))

    def update_recordfile(self):
        with open(f"{self.dct['HOME']}/.recordfile", 'r') as f:
            contents = f.readlines()

        contents.append(f"{self.dct['wdir']} ||| {self.dct['base_name']}.{self.out_extension} ||| {self.directory}\n")
        newlines = []
        for c in contents:
            if c not in newlines:
                newlines.append(c)
        with open(f"{self.dct['HOME']}/.recordfile", 'w') as f:
            f.write("".join(contents))





class RaijinQJob(QJob):
    queue = "normal"
    template = rj_template

    def get_template_kwargs(self):
        super().get_template_kwargs()
        self.dct['wdir'] = "/short/{RJ_PROJ}/{RJ_UNAME}/{dir}{base_directory}".format(dir=self.dir,**self.dct)
        for k, v in raijin['constants'].items():
            self.dct[k] = v.format(**self.dct)
        #self.dct.update(raijin['constants'])
        self.dct['program_setup'] = raijin['setup'][self.program].format(**self.dct)
        self.dct['program_cmd'] = raijin['cmds'][self.program].format(**self.dct)
        





