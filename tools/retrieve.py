
#!/usr/bin/env python3

import argparse
import sys
import subprocess
from datetime import datetime, timedelta
from utils import get_environment
from collections import defaultdict


class CopyFilesBack:
    def __init__(self, after=None):
        self.now = datetime.utcnow()
        self.tracked_remote_paths = defaultdict(dict)
        self.__dict__.update(get_environment())
        self.remote = f"{self.RJ_UNAME}@raijin.nci.org.au"
        self.get_after_time(after)
        self.get_files()

    def get_after_time(self, after):
        if after is None:
            with open(f"{self.HOME}/.recordfile_last_checked", 'r') as f:
                contents = f.readlines()
            last_checked_str = [x for x in contents if x][0].strip()
            self.after = datetime.strptime(last_checked_str, "%a %b %d %H:%M:%S UTC %Y")
        else:
            negative = {}
            for k, v in after.items():
                try:
                    if v > 0:
                        v *= -1
                    negative[k] = v
                except:
                    pass

            self.after = self.now - timedelta(**negative)

    def get_home_recordfile(self):
        with open(f"{self.HOME}/.recordfile", 'r') as f:
            contents = f.readlines()
        clean = [x.strip() for x in contents if x]
        split = [x.split("|||") for x in clean]
        for remote, outfile, home_dir in split:
            self.tracked_remote_paths[remote][outfile] = home_dir


    def get_remote_recordfile(self):
        remote_record = f"{self.RJ_UNAME}@raijin.nci.org.au:/home/{self.REMOTE_DIR}/{self.RJ_UNAME}/.recordfile"
        subprocess.call(f"scp -q {remote_record} ._tmp", shell=True)
        with open("._tmp", r) as f:
            contents = f.readlines()
        subprocess.call(f"rm -f ._tmp", shell=True)

        clean = [x.strip() for x in contents if x]
        self.remote = [x.split("|||") for x in clean]

    def get_files(self):
        self.get_home_recordfile()
        self.get_remote_recordfile()

        for date_str, pbs_jobid, remote_path, outfile in self.remote:
            date = datetime.strptime(date_str, "%a %b %d %H:%M:%S UTC %Y")
            if date > self.after:
                try:
                    expected_err = subprocess.check_output(f"ssh -q -t {remote} 'qstat -f {pbs_jobid}'")
                    output = ""
                except subprocess.CalledProcessError as e:
                    output = e.output

                if "Job has finished" in output:
                    try:
                        home_dir = self.tracked_remote_paths[remote_path][outfile]
                        subprocess.check_output(f"scp -q {self.remote}:{remote_path}/{outfile} {home_dir}")
                        print(f"{home_dir}/{outfile}")
                    except:
                        pass