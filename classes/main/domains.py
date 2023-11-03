from pycsp3.classes.auxiliary.ptypes import TypeVar
from pycsp3.classes.auxiliary.values import IntegerValue, IntegerInterval, SymbolicValue

import math


class Domain:
    def __init__(self, *args):
        if len(args) == 1 and args[0] == math.inf:  # special integer variable with an infinite domain
            self.type = TypeVar.INTEGER
            self.original_values = [math.inf]
            self.values = [math.inf]
        else:
            self.type = None
            self.original_values = []
            self._add_value(*args)
            assert self.type, "You have defined a variable with an empty domain; fix this"
            self.original_values.sort()
            self.values = []

    def set_type(self, type):
        if self.type is None:
            self.type = type
        assert self.type == type, "In a domain, values must be either all integer or all symbolic values"

    def get_type(self):
        return self.type

    def _add_value(self, arg):
        assert isinstance(arg, (tuple, list, set, range, int, str)), "Bad type for the domain " + str(arg) + " of type " + str(type(arg))
        if isinstance(arg, (tuple, list, set)):
            for a in arg:
                self._add_value(a)
        elif isinstance(arg, range):
            if arg.step == 1 and arg.stop - arg.start > 2:
                self.original_values.append(IntegerInterval(arg.start, arg.stop - 1))
                self.set_type(TypeVar.INTEGER)
            else:
                self._add_value(set(arg))
        elif isinstance(arg, int):
            self.original_values.append(IntegerValue(arg))
            self.set_type(TypeVar.INTEGER)
        elif isinstance(arg, str):
            self.original_values.append(SymbolicValue(arg))
            self.set_type(TypeVar.SYMBOLIC)

    def __iter__(self):
        if len(self.original_values) == 1 and isinstance(self.original_values[0], IntegerInterval):
            return self.original_values[0].__iter__()
        return self.all_values().__iter__()  # original_values.__iter__()

    def __getitem__(self, item):
        if len(self.original_values) == 1 and isinstance(self.original_values[0], IntegerInterval):
            return self.original_values[0].__getitem__(item)
        return self.original_values.__getitem__(item)

    def __eq__(self, other):
        return isinstance(other, Domain) and self.type == other.type and self.original_values == other.original_values

    def __hash__(self):
        return super().__hash__()

    def __repr__(self):
        if len(self.original_values) == 1 and self.original_values[0] == math.inf:
            return "-infinity..+infinity"
        return " ".join(str(v) for v in self.original_values)

    def smallest_value(self):
        return self.original_values[0].smallest()

    def greatest_value(self):
        return self.original_values[-1].greatest()

    def all_values(self):
        if len(self.values) == 0:
            if len(self.original_values) == 1 and isinstance(self.original_values[0], IntegerInterval):
                self.values = range(self.original_values[0].inf, self.original_values[0].sup + 1)
            else:
                self.values = sorted(v.value if isinstance(v, IntegerValue) else v for v in self.original_values)
        return self.values

    def is_binary(self):
        zero, one = False, False
        for v in self.original_values:
            if isinstance(v, IntegerInterval):
                if not v.is_binary():
                    return False
                else:
                    zero = one = True
            elif isinstance(v, IntegerValue):
                if v.value == 0:
                    zero = True
                elif v.value == 1:
                    one = True
                else:
                    return False
        return zero and one

    def is_empty(self):
        return len(self.original_values) == 0
