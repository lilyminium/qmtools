N_ATOMS_10 = dict(
                molpro = dict(
                            vmem_mb  = 5000,
                            ncpus    = 4,
                            jobfs_mb = 10000,
                            walltime = 48
                            ),
                qchem = dict(
                            queue    = "normalbw",
                            vmem_mb  = 4000,
                            ncpus    = 1,
                            jobfs_mb = 20000,
                            walltime = 60
                            ),
                )

N_ATOMS_20 = dict(
                molpro = dict(
                            vmem_mb  = 8500,
                            ncpus    = 4,
                            jobfs_mb = 20000,
                            walltime = 48
                            ),
                qchem = dict(
                            queue    = "normalbw",
                            vmem_mb  = 8000,
                            ncpus    = 4,
                            jobfs_mb = 80000,
                            walltime = 96
                            ),
                )

N_ATOMS_40 = dict(
                molpro = dict(
                            vmem_mb  = 8500,
                            ncpus    = 4,
                            jobfs_mb = 20000,
                            walltime = 48
                            ),
                qchem = dict(
                            queue    = "normalbw",
                            vmem_mb  = 10000,
                            ncpus    = 1,
                            jobfs_mb = 80000,
                            walltime = 96
                            ),
                )

N_ATOMS_MORE = dict(
                    molpro = dict(
                            vmem_mb  = 40000,
                            ncpus    = 4,
                            jobfs_mb = 200000,
                            walltime = 150
                            ),
                    qchem = dict(
                            queue    = "normalbw",
                            vmem_mb  = 4000,
                            ncpus    = 1,
                            jobfs_mb = 20000,
                            walltime = 96
                            ),
                )

GAUSSIAN = dict(
    pm6 = dict(
            vmem_mb  = 1500,
            ncpus    = 4,
            jobfs_mb = 1000,
            walltime = 1
            ),
    m062x = dict(
            vmem_mb  = 1500,
            ncpus    = 1,
            jobfs_mb = 4,
            walltime = lambda x: x*3
            ),
    ccsd = dict(
            vmem_mb  = 40000,
            ncpus    = 4,
            jobfs_mb = 40000,
            walltime = lambda x: x*3
            ),
    mp2 = dict(
            vmem_mb  = 8500,
            ncpus    = 4,
            jobfs_mb = lambda x: x*4,
            walltime = lambda x: x/2,
            ),
    gtmp2large = dict(
            vmem_mb  = 8500,
            ncpus    = 4,
            jobfs_mb = lambda x: x*20,
            walltime = lambda x: x*4,
            ),
        )
GAUSSIAN["lyp"] = GAUSSIAN["m062x"]
GAUSSIAN["bmk"] = GAUSSIAN["m062x"]
GAUSSIAN["m05"] = GAUSSIAN["m062x"]


def get_params(n_heavy_atoms, theory, program="gaussian"):
    if program == "gaussian":
        order = "ccsd gtmp2large mp2 m062x".split()
        for t in order:
            if t in theory.lower():
                return GAUSSIAN[t]
        for k, v in GAUSSIAN.items():
            if k.lower() in theory.lower():
                return v
        #return GAUSSIAN[theory.lower()]
    else:
        if n_heavy_atoms <= 10:
            return N_ATOMS_10[program]
        if n_heavy_atoms <= 20:
            return N_ATOMS_20[program]
        if n_heavy_atoms <= 40:
            return N_ATOMS_40[program]
        return N_ATOMS_MORE[program]
