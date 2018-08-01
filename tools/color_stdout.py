import itertools
import math
import subprocess
import sys
import re
import os
import argparse
import shutil
from utils import style_unique, N_COLOR, get_bin, style

LINESEP = os.linesep

def get_prefix(texts):
    prefix = []
    for x in map(set, zip(*texts)):
        if len(x) == 1:
            prefix.append(x.pop())
        else:
            return "".join(prefix)
    return "".join(prefix)

def unprefix(texts):
    prefix = get_prefix(texts)
    np = len(prefix)
    return prefix, [x[np:] for x in texts if x[np:]]

def replace_by_len(text, original, replacement, previous = []):
    ordered = sorted(zip(original, replacement), key=lambda x: len(x[0]))
    for old, new in ordered:
        for sub_pattern, sub_colored in previous:
            old = old.replace(sub_pattern, sub_colored)
        text = text.replace(old, new)
        previous.append((old, new))

    return text

def get_prefixes(original, max_n_prefixes, min_len=4, min_match=3):

    def _group_by_first(lst, min_len):
        out = []
        non_empty = sorted([x for x in lst if len(x)>min_len])
        for k, v in itertools.groupby(non_empty, key = lambda x: x[0]):
            out.append(list(v))
        return out

    prefixes = []
    text = _group_by_first(original, min_len)
    while len(prefixes) < max_n_prefixes and text:
        ongoing = []
        for group in text:
            if len(group) >= min_match:
                prefix, cut = unprefix(group)
                if len(prefix.strip()) >= min_len:
                    prefixes.append(prefix)
                ongoing.extend(cut)
        text = _group_by_first(ongoing, min_len)
    return prefixes


def check_for_dir(output):
    files, subdirs = set(), set()
    current_dir = ""
    for line in output:
        if line.endswith(":"):
            subdirs.add(line)
            current_dir = line[:-1]
        elif os.path.isdir(os.path.abspath(os.path.join(current_dir, line))):
            subdirs.add(line)
        else:
            files.add(line)
    return list(files), list(subdirs)

def skip_pattern(pattern, output):
    pattern_match, remaining = [], []
    for line in output:
        match = re.match(pattern, line)
        i = match.end() if match else 0
        pattern_match.append(line[:i])
        remaining.append(line[i:])
    return pattern_match, remaining


def lsc(stdout):

    def style_dir(matchobj):
        return style(matchobj.group(), "DARKBLUE")

    clean = [x.strip().split() for x in stdout.split(LINESEP)]
    flat = [x for y in clean for x in y if x]
    PERMISSIONS = r"[-dclpsbD][-rwxsStTlL]{9}\+?(\s+\w+){6}\s+(\d+:\d+|\d{4})\s+"
    perms, items = skip_pattern(PERMISSIONS, flat)
    files, subdirs = check_for_dir(items)
    prefixes = get_prefixes(files+perms, N_COLOR)
    styled = style_unique(*prefixes)
    regex_dirs = [f"\\b{d}\\b" for d in subdirs]
    for d in regex_dirs:
        stdout = re.sub(d, style_dir, stdout)

    return replace_by_len(stdout, prefixes, styled)



def grepc(stdout):
    results = [x.split(":", 1) for x in stdout.split(LINESEP)]
    zipped = list(itertools.zip_longest(*results, fillvalue=""))
    flat = [x.strip() for y in zipped for x in y]
    prefixes = get_prefixes(flat, N_COLOR)
    styled = style_unique(*prefixes)
    return replace_by_len(stdout, prefixes, styled)


def defaultc(stdout):
    clean = [x.strip() for x in stdout.split(LINESEP) if x]
    prefixes = get_prefixes(clean, N_COLOR)
    styled = style_unique(*prefixes)
    return replace_by_len(stdout, prefixes, styled)



column_width, rows = shutil.get_terminal_size((120, 60))

func = dict(
    ls=lsc,
    grep=grepc,
    cat=defaultc
    )

flags = dict(
    ls=["-C"]
    )

environment = dict(**os.environ)
environment["COLUMNS"] = str(column_width)
encoding = sys.stdout.encoding

def color_stdout(cmd, text):
    exe = get_bin(cmd)
    exe_sub = [exe] + flags.get(cmd, []) + text
    p = subprocess.run(exe_sub, stdout=subprocess.PIPE, encoding=encoding, env=environment)
    color_stdout = func.get(cmd, defaultc)(p.stdout)
    sys.stdout.write(color_stdout)

def hst(text):
    parser = argparse.ArgumentParser(add_help=True, description = 'print history')
    parser.add_argument('-a', '--all', 
                            action='store_true',
                            dest='show_all',
                            help="don't skip ls, less, cd, etc")
    parser.add_argument('-c', '--cond',  
                            default="all",
                            dest="cond_",
                            choices=["any", "all"],
                            help='Show commands that fulfill all vs. any the requirements. (Default: all)'
                            )
    parser.add_argument('match',
                            nargs="*",
                            help="Match these patterns to show."
                            )
    args = parser.parse_args(text)
    dct = vars(args)

    cond_to_python = dict(
                    any=any,
                    all=all
                    )
    cond = cond_to_python[dct.pop("cond_")]
    return history(cond=cond, **dct)


def safe_zip(lst, n=2):
    if lst:
        return zip(*lst)
    else:
        return itertools.repeat([], n)


def history(match=[], cond=all, show_all=False, _print=True):
    exe_sub = ["bash", "-i", "-c", "history -r; history"]
    ALWAYS_SKIP = ["hst", "hsx"]
    SKIP = ["history", "ls", "less", "python3", "python", "cd", "vim", "sublime", "subl"]
    p = subprocess.run(exe_sub, stdout=subprocess.PIPE, encoding=encoding, env=environment)
    history_entries = p.stdout.split('\n')
    history_split = [x.split() for x in history_entries if x]
    idx = list(range(len(history_entries)))


    idx, history_split = safe_zip([(i, x) for i, x in zip(idx, history_split) if x[1] not in ALWAYS_SKIP], 2)

    if not show_all:
        idx, history_split = safe_zip([(i, x) for i, x in zip(idx, history_split) if x[1] not in SKIP], 2)


    line_entries = [" ".join(x) for x in history_split]
    if match:
        idx, line_entries = safe_zip([(i, x) for i, x in zip(idx, line_entries) if cond(m in x for m in match)], 2)

    cmd_lists = [x.split()[1:] for x in line_entries]
    numbers_none = [" ".join(x) for x in cmd_lists]
    numbers_show = LINESEP.join([history_entries[i] for i in idx])
    
    if _print:
        prefixes = get_prefixes(numbers_none, N_COLOR)
        styled = style_unique(*prefixes)
        colored = replace_by_len(numbers_show, prefixes, styled)
        print(colored)

    return cmd_lists

def hstx(text):
    parser = argparse.ArgumentParser(add_help=True, description = 'execute historical command')
    parser.add_argument('-a', '--all', 
                            action='store_true',
                            dest='show_all',
                            help="don't skip ls, less, cd, etc")
    parser.add_argument('-c', '--cond',  
                            default="all",
                            dest="cond_",
                            choices=["any", "all"],
                            help='Show commands that fulfill all vs. any the requirements. (Default: all)'
                            )
    parser.add_argument('match',
                            nargs="*",
                            help="Match these patterns to execute."
                            )
    args = parser.parse_args(text)
    dct = vars(args)

    cond_to_python = dict(
                    any=any,
                    all=all
                    )
    cond = cond_to_python[dct.pop("cond_")]
    cmd_list =  history(cond=cond, **dct, _print=False)
    if cmd_list:
        p = subprocess.run(cmd_list[-1], timeout=2)


history_func = dict(
    hst = hst,
    hsx = hstx
    )


def color_all(cmd, text):
    try:
        color_stdout(cmd[:-1], text)
    except FileNotFoundError:
        history_func[cmd](text)


