# qmtools

qmin: crin2

qdelall: delete Raijin jobs by name/status/queue/whatever.

pysub: submit jobs from input files. Written to be very easy to link to qmin, which I will do at some point. Also will eventually dual submit to Iodine.

retrieve: retrieve output from Raijin. Will potentially make a daemon for this.

binlink: Got tired of manually simlinking everything, so binlink stuff for easy usage. You will have to simlink this to binlink anywhere. :(. This also assumes that $HOME/bin is in your path, which it should be.



qmin --help gives you all the command line options. Bulk create jobs without interactivity (which can still be turned on if needed). --show is a good way to check your job files without looking for them. 

Example:
```bash
>>ls *
```
```
    a_an:
    aryl_urea_nitro_a1.M062X.SMD.h2o.opt.log aryl_urea_nitro_a1.M062X.opt.log

    b_an:
    aryl_urea_nitro_a2.M062X.SMD.h2o.opt.log aryl_urea_nitro_a2.M062X.opt.log

    n:
    aryl_urea_nitro.M062X.SMD.h2o.opt.log aryl_urea_nitro.M062X.opt.log
```
```bash
>>qmin --solvate -c -1 a_an/aryl_urea_nitro_a1.M062X.SMD.h2o.opt.log b_an/aryl_urea_nitro_a2.M062X.SMD.h2o.opt.log
```
```
    #######################################
    #        STARTING   JOB  INPUT        #
    #######################################

    Software: Gaussian

    File: a_an/aryl_urea_nitro_a1.M062X.SMD.h2o.opt.log

                Theory  : MP2
                Basis   : Gen 6D 6-31pGd (Rassolov=True)
                Charge  : -1  Multiplicity: 1
                Optimize: False  Frequencies: False
                Solvate : True
                    Solvent model: SMD
                    Solvent      : water

Written to a_an/aryl_urea_nitro_a1.MP2_6-31pGd_water.com

    File: b_an/aryl_urea_nitro_a2.M062X.SMD.h2o.opt.log

                Theory  : MP2
                Basis   : Gen 6D 6-31pGd (Rassolov=True)
                Charge  : -1  Multiplicity: 1
                Optimize: False  Frequencies: False
                Solvate : True
                    Solvent model: SMD
                    Solvent      : water

Written to b_an/aryl_urea_nitro_a2.MP2_6-31pGd_water.com
```

```bash
>>> pysub *.com
    Input: aryl_urea_Cl_CF3_a1.MP2_6-31pGd.com
    walltime=48:00:00, jobfs=26000MB, vmem=8500MB, queue=normal, ncpus=4
    8502780   /short/q95/lxw507/a_an/aryl_urea_Cl_CF3_a1.MP2_6-31pGd.job

    Input: aryl_urea_Cl_CF3_a1.MP2_6-31pGd_water.com
    walltime=48:00:00, jobfs=26000MB, vmem=8500MB, queue=normal, ncpus=4
    8502781   /short/q95/lxw507/a_an/aryl_urea_Cl_CF3_a1.MP2_6-31pGd_water.job

    Input: aryl_urea_Cl_CF3_a1.MP2_GTMP2LARGE.com
    walltime=48:00:00, jobfs=26000MB, vmem=8500MB, queue=normal, ncpus=4
    8502782   /short/q95/lxw507/a_an/aryl_urea_Cl_CF3_a1.MP2_GTMP2LARGE.job

    Input: aryl_urea_Cl_CF3_a1.MP2_GTMP2LARGE_water.com
    walltime=48:00:00, jobfs=26000MB, vmem=8500MB, queue=normal, ncpus=4
    8502785   /short/q95/lxw507/a_an/aryl_urea_Cl_CF3_a1.MP2_GTMP2LARGE_water.job
```

```bash
>>> retrieve --oe
    Looking for all jobs completed after Wed Jul 18 09:14:23 2018
    /Users/lily/pydev/pka_new/clcf3/t1/aryl_urea_Cl_CF3_a1.MP2_6-31pGd_water.log
    /Users/lily/pydev/pka_new/clcf3/t1/aryl_urea_Cl_CF3_a1.MP2_6-31pGd_water.job.o8502881
    Done.
>>>retrieve --oe
    Looking for all jobs completed after Wed Jul 18 09:32:37 2018
    Done.
>>>retrieve -min 20
    Looking for all jobs completed after Wed Jul 18 09:16:25 2018
    /Users/lily/pydev/pka_new/clcf3/t1/aryl_urea_Cl_CF3_a1.MP2_6-31pGd_water.log
    Done.
```