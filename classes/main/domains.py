from pycsp3.classes.auxiliary.types import TypeVar
from pycsp3.classes.auxiliary.values import IntegerValue, IntegerInterval, SymbolicValue


class Domain:
    def __init__(self, *args):
        self.type = None
        self.values = []
        self._add_value(*args)
        assert self.type
        self.values.sort()

    def set_type(self, type):
        if self.type is None:
            self.type = type
        assert self.type == type, "In a domain, values must be either all integer or all symbolic values"

    def get_type(self):
        return self.type

    def _add_value(self, arg):
        assert isinstance(arg, (list, set, range, int, str)), "Bad type for the domain " + str(arg) + " of type " + str(type(arg))
        if isinstance(arg, (list, set)):
            for a in arg:
                self._add_value(a)
        elif isinstance(arg, range):
            if arg.step == 1 and arg.stop - arg.start > 2:
                self.values.append(IntegerInterval(arg.start, arg.stop - 1))
                self.set_type(TypeVar.INTEGER)
            else:
                self._add_value(set(arg))
        elif isinstance(arg, int):
            self.values.append(IntegerValue(arg))
            self.set_type(TypeVar.INTEGER)
        elif isinstance(arg, str):
            self.values.append(SymbolicValue(arg))
            self.set_type(TypeVar.SYMBOLIC)

    def __iter__(self):
        return self.values[0].__iter__() \
            if len(self.values) == 1 and isinstance(self.values[0], IntegerInterval) else self.values.__iter__()

    def __getitem__(self, item):
        return self.values[0].__getitem__(item) \
            if len(self.values) == 1 and isinstance(self.values[0], IntegerInterval) else self.values.__getitem__(item)

    def __hash__(self):
        return super().__hash__()

    def __repr__(self):
        return " ".join(str(v) for v in self.values)

    def is_binary(self):
        zero, one = False, False
        for v in self.values:
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
