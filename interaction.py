from .utils import Ask, AskBool

class InteractionBase:
    def ask(self, attr):
        default = getattr(self, attr)
        value = Ask(**self.questions[attr], default=default)
        setattr(self, attr, value)
