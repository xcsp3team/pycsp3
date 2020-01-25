class _Options:
    def __init__(self):
        self.values = tuple()  # options with non-Boolean values (strings or numbers)
        self.flags = tuple()  # Boolean options
        self.parameters = []
        self.parameters_cursor = 0

    def set_values(self, *values):
        self.values = values
        for option in values:
            vars(self)[option] = None

    def set_flags(self, *flags):
        self.flags = flags
        for option in flags:
            vars(self)[option] = False

    def get(self, name):
        return vars(self)[name]

    def consume_parameter(self):
        if self.parameters_cursor < len(self.parameters):
            parameter = self.parameters[self.parameters_cursor]
            self.parameters_cursor += 1
            return parameter
        else:
            return None

    def parse(self, args):
        for arg in args:
            if arg[0] == '-':
                t = arg[1:].split('=', 1)
                if len(t) == 1:
                    if t[0] in self.flags:
                        vars(self)[t[0]] = True
                        assert t[0] not in self.values or t[0] == 'dataexport', "You have to specify a value for the option -" + t[0]
                    else:
                        print("Warning: Unknown option", arg)
                else:
                    assert len(t) == 2
                    if t[0] in self.values:
                        assert len(t[1]) > 0, "The value specified for the option -" + t[0] + " is the empty string"
                        vars(self)[t[0]] = t[1]
                    else:
                        print("Warning: Unknown option", arg)
            else:
                self.parameters.append(arg)


options = _Options()
