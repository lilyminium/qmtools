
#!/usr/bin/env python3

import subprocess
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from utils import get_environment, style


DEFAULT_DELTA_WEEKS = 10
COMMENT_LINES = """# Record file for pysub and retrieve.
# Do not delete or modify if you want to keep using above.
# Email lily.wang@anu.edu.au for questions.
# Lily Wang, 2018
"""
N_COMMENT_LINES_IN_RECORDFILE = len(COMMENT_LINES.split('\n'))
STYLE_INFO = "yellow"
STYLE_ERROR = "red"

TZ_UTC = timezone.utc

def printerr(err):
    print(style(err, STYLE_ERROR))

def printinfo(info):
    print(style(info, STYLE_INFO))


class CopyFilesBack:
    def __init__(self, clear_home=False, clear_remote=False, clear_all=False, include_oe=False, **after):
        self.now = datetime.utcnow()
        self.include_oe = include_oe
        self.__dict__.update(get_environment())
        self.remote = f"{self.RJ_UNAME}@raijin.nci.org.au"
        self.remote_record = f"{self.RJ_UNAME}@raijin.nci.org.au:/home/{self.REMOTE_DIR}/{self.RJ_UNAME}/.recordfile"
        self.review = []

        self.copy_files_back(after)

        if clear_home or clear_all:
            self.new_home_record()
        if clear_remote or clear_all:
            self.new_remote_record()


    def new_home_record(self):
        with open(f"{self.HOME}/.recordfile", 'w') as f:
            f.write(COMMENT_LINES)
        printerr("Wrote new local record.")
        self.update_last_checked()

    def new_remote_record(self):
        with open("._tmp", 'w') as f:
            f.write(COMMENT_LINES)
        subprocess.call(f"scp -q ._tmp {self.remote_record}", shell=True)
        subprocess.call("rm -f ._tmp", shell=True)
        printerr("Wrote new remote record.")


    def copy_files_back(self, after):
        self.tracked_remote_paths = defaultdict(dict)
        try:
            self.get_after_time(after)
            self.get_files()
            self.update_last_checked()
            self.write_review()
            printinfo("Done.")

        except:
            printerr("No files copied.")

    def write_review(self):
        with open(f"{self.HOME}/.review.json", 'w') as outfile:
            json.dump(self.review, outfile)


    def update_last_checked(self):
        with open(f"{self.HOME}/.recordfile_last_checked", 'w') as f:
            f.write(self.now.strftime("%a %b %d %H:%M:%S UTC %Y"))

    def get_after_time(self, after):
        if any([x is not None for x in after.values()]):
            self.get_time_from_delta(after)
        else:
            try:
                with open(f"{self.HOME}/.recordfile_last_checked", 'r') as f:
                    contents = f.readlines()
                last_checked_str = [x for x in contents if x][0].strip()
                self.after = datetime.strptime(last_checked_str, "%a %b %d %H:%M:%S UTC %Y")
            except (FileNotFoundError, IndexError):
                self.get_time_from_delta(dict(weeks=DEFAULT_DELTA_WEEKS))

        local = self.after.replace(tzinfo=TZ_UTC).astimezone(tz=None)
        printinfo(f"Looking for all jobs completed after {local.strftime('%a %b %d %H:%M:%S %Y')}")

    def get_time_from_delta(self, after):
        positive = dict((k, abs(v)) for k, v in after.items() if v is not None)
        self.after = self.now - timedelta(**positive)


    def get_home_recordfile(self):
        try:
            with open(f"{self.HOME}/.recordfile", 'r') as f:
                contents = f.readlines()[N_COMMENT_LINES_IN_RECORDFILE:]
            clean = [x.strip() for x in contents if x]
            split = [x.split("|||") for x in clean]
            stripped = [[y.strip() for y in x] for x in split]
            for remote, outfile, home_dir in stripped:
                self.tracked_remote_paths[remote][outfile] = home_dir
            return
        except FileNotFoundError:
            printerr(f"{self.HOME}/.recordfile not found; writing new one.")
            self.new_home_record()
            raise FileNotFoundError
        except IndexError:
            printerr(f"Something's wrong with the format of {self.HOME}/.recordfile\nPlease fix of use retrieve --clear-home to write a new one.")
            raise IndexError


    def get_remote_recordfile(self):
        try:
            subprocess.call(f"scp -q {self.remote_record} ._tmp", shell=True)
            with open("._tmp", 'r') as f:
                contents = f.readlines()[N_COMMENT_LINES_IN_RECORDFILE:]
            subprocess.call(f"rm -f ._tmp", shell=True)

            clean = [x.strip() for x in contents if x]
            split = [x.split("|||") for x in clean if x]
            self.remote_recordfile = [[y.strip() for y in x] for x in split]
        except FileNotFoundError:
            printerr(f"{self.remote_record} not found; writing new one.")
            self.new_remote_record()
            raise FileNotFoundError
        except IndexError:
            printerr(f"Something's wrong with the format of {self.HOME}/.recordfile\nYou probably deleted the comments telling you not to delete them!")
            raise IndexError

    def get_files(self):
        self.get_home_recordfile()
        self.get_remote_recordfile()

        for date_str, pbs_jobid, remote_path, outfile in self.remote_recordfile:
            date = datetime.strptime(date_str, "%a %b %d %H:%M:%S UTC %Y")
            if date > self.after:
                self.copy_job_back(pbs_jobid, remote_path, outfile)

    def copy_job_back(self, pbs_jobid, remote_path, outfile):
        try:
            expected_err = subprocess.check_output(f"ssh -q -t {self.remote} 'qstat -f {pbs_jobid}'", shell=True)
            output = ""
        except subprocess.CalledProcessError as e:
            output = str(e.output)
        if "Job has finished" in output:
            try:
                home_dir = self.tracked_remote_paths[remote_path][outfile]
                self.single_scp(remote_path, outfile, home_dir)
                if self.include_oe:
                    stripped_id = pbs_jobid.split(".")[0]
                    base = ".".join(outfile.split(".")[:-1])
                    stdout =  f"{base}.job.o{stripped_id}"
                    stderr =  f"{base}.job.e{stripped_id}"
                    self.single_scp(remote_path, stdout, home_dir)
                    self.single_scp(remote_path, stderr, home_dir)

            except KeyError:
                pass

    def single_scp(self, remote_path, file, home_dir):
        try:
            subprocess.check_output(f"scp -q {self.remote}:{remote_path}/{file} {home_dir} 2>/dev/null", shell=True)
            self.review.append(f"{home_dir}/{file}")
            print(f"{home_dir}/{file}")
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

