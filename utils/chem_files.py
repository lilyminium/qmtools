import re

regex_float = '[-+]?[0-9]*\.?[0-9]+'
regex_coords = '\s+'.join([regex_float]*3)


def read_coordinate_lines(lines):
    return [x for x in lines if re.search(regex_coords, x)]


def lines_to_dct(lines, headings, delimiter=None):
    dct = {}
    for k in headings:
        dct[k] = []
    for line in lines:
        if delimiter is None:
            line_ = line.split()
        else:
            line_ = line.split(delimiter)
        for k, v in zip(headings, line_):
            dct[k].append(v)
    return dct

def section_by_pattern(lines, pattern="\["):
    out = []
    sub = []
    for line in lines:
        if re.search(pattern, line):
            if sub:
                out.append(sub)
            sub = []
        sub.append(line)
    out.append(sub)
    return out

def clean_text_from_file(file):
    with open(file, 'r') as f:
            text = f.readlines()
    stripped = [x.strip() for x in text]
    return [x for x in stripped if x]

def coordinate_lines_from_log(file):
    lines = clean_text_from_file(file)
    last = section_by_pattern(lines, pattern="Test job not archived.")
    sections = "".join([x.strip() for x in last[-1]]).split("\\\\")
    geometry = sections[3].split("\\")[1:]
    keys = ["element", "x", "y", "z"]
    return lines_to_dct(geometry, keys, delimiter=",")

def energy_from_log(file):
    lines = clean_text_from_file(file)
    infile = section_by_pattern(lines, pattern="\*\*\*\*\*\*\*\*\*\*\*")[2]
    cards = section_by_pattern(infile, pattern="-----------------------------------------------------")[1]
    theory = cards.strip().split()[1].split("/")[0]

    from_end = section_by_pattern(lines[::-1], pattern="moment")[0]
    joined = "".join([x.strip() for x in from_end[::-1]])
    for line in joined.split("\\")[::-1]:
        if re.search(f"{theory.upper()}=[-+]?[0-9]+\.[0-9]*", line):
            energy = float(line.split("=")[1])
            return {theory: energy}


def coordinate_lines_from_xyz(file):
    lines = clean_text_from_file(file)
    coordinate_lines = read_coordinate_lines(lines)
    keys = ["element", "x", "y", "z"]
    return lines_to_dct(coordinate_lines, keys)

def computersafe(txt):
    out = []
    for char in txt:
        if char == "(":
            out.append('-')
        elif char == "*":
            out.append("d")
        elif char == "+":
            out.append("p")
        elif char == " ":
            out.append("_")
        elif char != ")":
            out.append(char)
    return "".join(out)
