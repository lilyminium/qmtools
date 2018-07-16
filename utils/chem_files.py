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
    print(geometry)
    keys = ["element", "x", "y", "z"]
    return lines_to_dct(geometry, keys, delimiter=",")

def coordinate_lines_from_xyz(file):
    lines = clean_text_from_file(file)
    coordinate_lines = read_coordinate_lines(lines)
    keys = ["element", "x", "y", "z"]
    return lines_to_dct(coordinate_lines, keys)

