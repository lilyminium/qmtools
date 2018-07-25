
__COLORS = dict(PURPLE = '\033[95m',
                    CYAN = '\033[96m',
                    DARKCYAN = '\033[36m',
                    BLUE = '\033[94m',
                    GREEN = '\033[92m',
                    YELLOW = '\033[93m',
                    RED = '\033[91m',
                    BOLD = '\033[1m',
                    UNDERLINE = '\033[4m',
                    END = '\033[0m')

def style(text, *color):
    colors = [__COLORS.get(x.upper(), '') for x in color if x]
    n_colors = len([x for x in colors if x])
    return f"{''.join(colors)}{text}{__COLORS['END']}{''.join([__COLORS['END']]*n_colors)}"

def printyellow(text):
    print(style(text, "yellow"))

def printred(text):
    print(style(text, "red"))

def printdarkcyan(text):
    print(style(text, "darkcyan"))

def printgreen(text):
    print(style(text, "green"))

def styleyellow(text):
    return style(text, "yellow")

def styledarkcyan(text):
    return style(text, "darkcyan")

def stylered(text):
    return style(text, "red")