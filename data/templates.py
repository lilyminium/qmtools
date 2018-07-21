rj_template = """#!/bin/bash
#PBS -P {RJ_PROJ}
#PBS -q {queue}
#PBS -l walltime={walltime}
#PBS -l mem={vmem}MB
#PBS -l jobfs={jobfs}MB
#PBS -l ngpus={ngpus}
#PBS -l ncpus={ncpus}
#PBS -l other=mpi:hyperthread
#PBS -l wd
#PBS -r y
#PBS -j oe

echo "$(date -u) ||| $PBS_JOBID ||| $PWD ||| {base_name}.{out_extension}" >> $HOME/.recordfile

rm -rf $PBS_JOBFS/{base_directory}
mkdir -p $PBS_JOBFS/{base_directory}
{program_setup}
echo 'machine   : Raijin'
echo 'queue     : {queue}'
echo 'jobfs     : {jobfs}MB'
echo 'ncpus     : {ncpus}'
echo 'ngpus     : {ngpus}'

{program_cmd}
echo "$(date -u) ||| $PBS_JOBID ||| $PWD ||| {base_name}.{out_extension}" >> $HOME/.recordfile

/opt/pbs/default/bin/pbs_rusage $PBS_JOBID >> $PBS_JOBID.log


"""