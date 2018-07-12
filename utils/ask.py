import inspect

class Ask:
    """
    Asking questions with a default answer and a list of options.
    """
    valid_text = ""
    def __init__(self, ask="?", default=None, options=None, valid=None):
        self.default = default
        self.valid = valid
        self.make_default_text()
        self.make_options(options)
        self.make_valid_text()
        self.make_ask_text(ask)

    def ask(self):
        while True:
            answer = input(self.ask_text)
            if not answer:
                print(f"Picked: {self.default}\n")
                return self.default
            elif self.is_option(answer):
                print(f"Picked: {answer}\n")
                return answer
            else:
                print("Invalid answer.")
            
    def is_option(self, answer):
        if self.options:
            return answer in self.options
        if self.valid is not None:
            try:
                return self.valid(answer)
            except:
                return False
        return True

    def make_default_text(self):
        if self.default is None:
            self.default_text = "No default value."
        else:
            self.default_text = f"Default: {self.default}"

    def make_valid_text(self):
        pass
        # if self.valid is None:
        #     self.valid_text = ""
        # else:
        #     self.valid_text = f"""
        #     Key:{inspect.getsourcelines(self.valid)[0][0]}"""
        

    def make_options(self, options):
        if options:
            self.options = list(options)
            if self.default:
                try:
                    self.options.remove(self.default)
                except:
                    pass
                self.options.insert(0, self.default)
            self.options_text = "[" + "] [".join(map(str, self.options)) + "]"

        elif options is None:
            self.options = []
            self.options_text = "No predefined options."

    def make_ask_text(self, ask):
        self.ask_text = f"""{ask}
        {self.default_text}
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
                print(f"Picked: {self.default}\n")
                return self.default

            elif answer.lower() in ["t", "y", "true", "ture", "tru"]:
                print("Picked: True\n")
                return True

            elif answer.lower() in ["f", "n", "false", "flase", "flse"]:
                print("Picked: False\n")
                return False

            else:
                print("Invalid answer.")