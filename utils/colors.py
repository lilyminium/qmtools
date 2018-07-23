
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
    colors = [__COLORS.get(x.upper(), '') for x in color]
    return f"{''.join(colors)}{text}{__COLORS['END']}{__COLORS['END']}"

def printyellow(text):
    print(style(text, "yellow"))

def printred(text):
    print(style(text, "red"))

def printdarkcyan(text):
    print(style(text, "darkcyan"))

def styleyellow(text):
    return style(text, "yellow")

def styledarkcyan(text):
    return style(text, "darkcyan")