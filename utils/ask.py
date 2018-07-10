import inspect

class Ask:
    """
    Asking questions with a default answer and a list of options.
    """
    def __init__(self, ask="?", default=None, options=None, valid=None):
        self.default = default
        self.valid = valid
        self.make_default_text()
        self.make_options(options)
        self.make_valid_text(valid)
        self.make_ask_text(ask)
        self.ask()

    def ask(self):
        while True:
            answer = input(self.ask_text)
            if not answer:
                return self.default
            elif is_option(answer):
                return answer
            else:
                print("Invalid answer.")
            
    def is_option(self, answer):
        if self.options:
            return answer in self.options
        if self.valid is not None:
            return self.valid(answer)
        return True

    def make_default_text(self):
        if self.default is None:
            self.default_text = "No default value."
        else:
            self.default_text = f"Default: {self.default}"

    def make_valid_text(self):
        if self.valid is None:
            self.valid_text = ""
        else:
            self.valid_text = f"""
            Key: {inspect.getsourcelines(self.valid)[0][0]}"""
        

    def make_options(self, options):
        if options:
            self.options = options
            if self.default:
                self.options.insert(0, self.default)
            self.options_text = "[ " + " ] [ ".join(self.options) + " ]"

        elif options is None:
            self.options = []
            self.options_text = "No predefined options."

    def make_ask_text(self, ask):
        self.ask_text = f"""{ask}
        {default_text}
        Options:
        {self.options_text}{self.valid_text}
        """

class AskBool(Ask):
    def __init__(self, ask, default=None):
        options = [True, "T/t", "Y/y", False, "F/f", "N/n"]
        if default is None:
            default = False
        super().__init__(ask, default, options=options)

    def ask(self):
        while True:
            answer = input(self.ask_text)
            if not answer:
                return self.default
            elif answer.lower() in ["t", "y", "true", "ture", "tru"]:
                return True
            elif answer.lower() in ["f", "n", "false", "flase", "flse"]:
                return False
            else:
                print("Invalid answer.")