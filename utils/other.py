import os

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