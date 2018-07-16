# qmtools

qmin: crin2

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