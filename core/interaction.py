from utils.ask import Ask, AskBool

class InteractionBase:
    def ask(self, attr):
        default = getattr(self, attr)
        qn = Ask(**self.question_options[attr], default=default)
        value = qn.ask()
        setattr(self, attr, value)

    def askbool(self, attr):
        default = getattr(self, attr)
        qn = AskBool(self.question_bools[attr], default=default)
        value = qn.ask()
        setattr(self, attr, value)
