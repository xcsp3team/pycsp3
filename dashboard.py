ORANGE, WHITE = '\033[93m', '\033[0m'


def warning(message):
    print("\n  " + ORANGE + "Warning: " + WHITE + message + "\n")


class _Options:
    def __init__(self):
        self.values = tuple()  # options with non-Boolean values (strings or numbers)
        self.flags = tuple()  # Boolean options
        self.parameters = []
        self.parameters_cursor = 0

    def set_values(self, *values):
        self.values = [value.lower() for value in values]
        for option in self.values:
            vars(self)[option] = None

    def set_flags(self, *flags):
        self.flags = [flag.lower() for flag in flags]
        for option in self.flags:
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
                    flag = t[0].lower()
                    flag = 'dataexport' if flag == 'export' else flag
                    if flag in self.flags:
                        vars(self)[flag] = True
                        assert flag not in self.values or flag == 'dataexport', "You have to specify a value for the option -" + flag
                    # else:
                    #     warning("Unknown option: " + arg)
                else:
                    assert len(t) == 2
                    value = t[0].lower()
                    value = 'dataparser' if value == 'parser' else value
                    if value in self.values:
                        assert len(t[1]) > 0, "The value specified for the option -" + value + " is the empty string"
                        vars(self)[value] = t[1]
                    # else:
                    #     warning("Unknown option: " + arg)
            else:
                self.parameters.append(arg)

    def __str__(self):
        s1 = ", ".join(str(value) + ":" + str(self.get(value)) for value in self.values)
        s2 = ", ".join(str(flag) + ":" + str(self.get(flag)) for flag in self.flags)
        return "\noptions=(" + s1 + ")\nflags=(" + s2 + ")"


options = _Options()
