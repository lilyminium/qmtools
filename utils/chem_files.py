import re

regex_float = '[-+]?[0-9]*\.?[0-9]+'
regex_coords = '\s+'.join([regex_float]*3)


def read_coordinate_lines(lines):
    return [x for x in lines if re.search(regex_coords, x)]


def lines_to_dct(lines, headings):
    dct = {}
    for k in headings:
        dct[k] = []
    for line in lines:
        for k, v in zip(headings, line.split()):
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
            sub = [line]
        elif sub:
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
    last = section_by_pattern(lines, pattern="Input orientation")
    last_ = last[-1]

    geometry = section_by_pattern(last_, pattern="------------")
    geo_ = geometry[1][1:]
    coordinate_lines = read_coordinate_lines(geo_)

    keys = ["serial", "atomic_number", "atomic_type", "x", "y", "z"]
    return lines_to_dct(coordinate_lines, keys)

def coordinate_lines_from_xyz(file):
    lines = clean_text_from_file(file)
    coordinate_lines = read_coordinate_lines(lines)
    keys = ["element", "x", "y", "z"]
    return lines_to_dct(coordinate_lines, keys)

