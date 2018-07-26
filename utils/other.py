import os
import subprocess
from .colors import printred

def indent(string, n=4):
    return f"{' '*n}{string}\n"

def get_environment():
    dct = {}
    needed = "HOME REMOTE_DIR RJ_UNAME RJ_PROJ".split()
    for n in needed:
        dct[n] = os.environ.get(n)
    if dct["RJ_UNAME"] is None:
        dct["RJ_UNAME"] = os.environ.get("REMOTE_USER")
    return dct

def get_script_path():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    printred(f"Current script directory:\n{script_dir}\n")

def get_bin(exe="ls"):
    paths = os.environ.get('PATH', '')
    if paths:
        split = paths.split(":")
        for path in split:
            joined = os.path.join(path, exe)
            if os.path.exists(joined):
                return joined.strip()
    return exe.strip()