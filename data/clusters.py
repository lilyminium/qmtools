

iodine = dict(
    gaussian_base="/apps/gaussian",
    gaussian_version="09b01", # usarj:  09b01,
    qchem_base="/apps/qchem",
    qchem_version="5.0-broadwell", # usarj:  4.3,
    molpro_base="/apps/molpro",
    molpro_version="2015.1",  # usarj:  2015.1,
    )

raijin = dict(
    constants = dict(
                    gaussian_base="/apps/gaussian",
                    gaussian_version="09b01", # usarj:  09b01,
                    qchem_base="/apps/qchem",
                    qchem_version="5.0-broadwell", # usarj:  4.3,
                    molpro_base="/apps/molpro",
                    molpro_version="2015.1",  # usarj:  2015.1,
                    ssh_home="ssh -t -q {RJ_UNAME}@raijin.nci.org.au",
                    rj_wdir = "{RJ_UNAME}@raijin.nci.org.au:{wdir}"
                    ),
    
    cmds = dict(
                    gaussian = "{gaussian_base}/{gaussian_version} < {base_name}.com >& {base_name}.log",
                    molpro = "molpro -o {jobdir}.out -I $PBS_JOBFS/{base_directory} -W $PBS_JOBFS/{base_directory} -d $PBS_JOBFS/{base_directory} -n $PBS_NCPUS {base_name}.ini",
                    qchem = "{qchem_base}/{qchem_version} {base_name}.in {base_name}.our {base_name}.mo"
                    ),

    setup = dict(
                    gaussian = "export GAUSS_SCRDIR=$PBS_JOBFS\nexport GAUSS_EXEDIR={gaussian_base}/{gaussian_version}/g09",
                    molpro = "module load molpro/{molpro_version}\nexport MOLPRO_SCRDIR=$PBS_JOBFS/{base_directory}\nexport MOLPRO_SAVDIR_INT=$PBS_JOBFS/{base_directory}\nexport MOLPRO_SAVDIR_WFU=$PBS_JOBFS/{base_directory}\n",
                    qchem = "module load qchem/{qchem_version}\n"
                    )
)