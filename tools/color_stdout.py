import itertools
import math
import subprocess
import sys
import re
import os
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

# def color_wrt_dir(lines, indices, current_dir, original, replacement):
#     files, dirs = [], []
#     for idx, line in zip(indices, lines):
#         real_part = line[idx:].strip()
#         if '.' not in real_part:
#             dir_path = os.path.join(current_dir, real_part)
#             abs_path = os.path.abspath(dir_path)
#             if os.path.isdir(abs_path):
#                 dirs.append(replace_by_len(line, [real_part], [style(real_part, "DARKBLUE")]))
#             else:
#                 files.append(replace_by_len(line, original, replacement))
#         else:
#             files.append(replace_by_len(line, original, replacement))
#     return files + dirs

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

# def make_col(text, column_width=40):

#     textlen = max(len(x) for x in text)
#     column_width, rows = shutil.get_terminal_size((0, column_width))

#     number_of_columns = int(column_width / textlen)
#     rows_in_columns = math.ceil(len(text)/number_of_columns)
#     columns = []
#     pattern = "{x:<{textlen}}"
#     while len(text) > rows_in_columns:
#         columns.append([pattern.format(x=x, textlen=textlen) for x in text[:rows_in_columns]])
#         text = text[rows_in_columns:]
#     columns.append([pattern.format(x=x, textlen=textlen) for x in text])
#     zipped = list(itertools.zip_longest(*columns, fillvalue=''))
#     return zipped

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
    return replace_by_len(stdout, prefixes, styled)[0]


def catc(stdout):
    clean = [x.strip() for x in stdout.split(LINESEP) if x]
    prefixes = get_prefixes(clean, N_COLOR)
    styled = style_unique(*prefixes)
    return replace_by_len(stdout, prefixes, styled)[0]



column_width, rows = shutil.get_terminal_size((120, 60))

func = dict(
    ls=lsc,
    grep=grepc,
    cat=catc
    )

flags = dict(
    ls=["-C"]
    )

environment = dict(**os.environ)
environment["COLUMNS"] = str(column_width)

def color_stdout(cmd, text):
    exe = get_bin(cmd)
    exe_sub = [exe] + flags.get(cmd, []) + text
    encoding = sys.stdout.encoding
    p = subprocess.run(exe_sub, stdout=subprocess.PIPE, encoding=encoding, env=environment)
    color_stdout = func[cmd](p.stdout)
    # column = get_bin("column")
    # echo = get_bin("echo")
    # p = subprocess.run(column, input=color_stdout,)

    sys.stdout.write(color_stdout)
