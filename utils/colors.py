
__COLORS = dict(    MAGENTA = '\033[95m',
                    DARKMAGENTA = '\033[35m',
                    CYAN = '\033[96m',
                    DARKCYAN = '\033[36m',
                    BLUE = '\033[94m',
                    DARKBLUE = '\033[34m',
                    GREEN = '\033[92m',
                    DARKGREEN = '\033[32m',
                    YELLOW = '\033[93m',
                    DARKYELLOW = '\033[33m',
                    RED = '\033[91m',
                    DARKRED = '\033[31m',
                    BOLD = '\033[1m',
                    UNDERLINE = '\033[4m',
                    END = '\033[0m')

__JUST_COLORS = dict(MAGENTA = '\033[95m',
                    CYAN = '\033[96m',
                    BLUE = '\033[94m',
                    GREEN = '\033[92m',
                    YELLOW = '\033[93m',
                    RED = '\033[91m',)


def style(text, *color):
    colors = [__COLORS.get(x.upper(), '') for x in color if x]
    n_colors = len([x for x in colors if x])
    return f"{''.join(colors)}{text}{''.join([__COLORS['END']]*n_colors)}"

def style_unique(*text):
    return [style(x, col) for x, col in zip(text, __JUST_COLORS.keys())]

N_COLOR = len(__JUST_COLORS)

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