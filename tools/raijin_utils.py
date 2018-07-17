#!/usr/bin/env python3

import subprocess
import os
import argparse
import sys
import re
from utils import get_environment, printyellow, printred

def get_rj_env():
    dct = get_environment()
    dct['RJ'] = "{RJ_UNAME}@raijin.nci.org.au".format(**dct)
    dct['RJ_HOME'] = "{RJ}:/home/{REMOTE_DIR}/{RJ_UNAME}".format(**dct)
    dct['RJ_SHORT'] = "{RJ}:/short/{RJ_PROJ}/{RJ_UNAME}".format(**dct)
    dct['RJ_RECORDFILE'] = "{RJ_HOME}/.recordfile".format(**dct)
    dct['QSTAT'] = "/opt/pbs/default/bin/qstat"
    dct['QDEL'] = "/opt/pbs/default/bin/qdel"
    dct['QUEUED'] = "{QSTAT} -u {RJ_UNAME} | grep {RJ_UNAME}".format(**dct)
    dct['SSH'] = "ssh -t -q {RJ}".format(**dct)
    return dct


def get_rj_queued(show=True):
    dct = get_rj_env()
    proc = subprocess.Popen("{SSH} '{QUEUED}'".format(**dct), shell=True, stdout=subprocess.PIPE)
    jobstr = str(proc.communicate()[0]).strip()[2:-1]
    jobs = jobstr.split("\n")[0].split("\\r\\n") # communicate() returns a tuple (stdout_data, stderr_data)
    real_jobs = [x for x in jobs if x]
    if show:
        if real_jobs:
            print("\n".join(real_jobs))
        else:
            printred("No jobs available.")
    return real_jobs


def rj_del_by_var(cond=any, **by_vars):
    dct = get_rj_env()
    SSH = dct['SSH']
    qdel = dct['QDEL']
    VARS = ["jobid", "username", "queue", "jobname", 
            "sessid", "nds", "tsk", "memory", "walltime", 
            "status", "runtime"]
    jobs = [x.split() for x in get_rj_queued()]
    if jobs:
        ordered_by_vars = [by_vars[k] for k in VARS]
        job_vars = [(line[0], zip(ordered_by_vars, line)) for line in jobs]

        translate = {".*":"*"}

        kwargs = "\n".join([f"      {k} = {translate.get(v, v)}" for k, v in by_vars.items()])
        printyellow(f"""  Deleting if {cond.__name__}: \n{kwargs}
            """)

        for jobid, params in job_vars:
            if cond([re.search(regex, txt) for regex, txt in params]):
                subprocess.Popen(f"{SSH} '{qdel}' {jobid}", shell=True)
                print(f"Deleted {jobid}")

        get_rj_queued()
    return
