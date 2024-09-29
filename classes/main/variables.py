import math
import re

from pycsp3 import functions
from pycsp3.classes.auxiliary.enums import TypeVar
from pycsp3.classes import main
from pycsp3.tools.utilities import error_if, flatten


class Domain:
    def __init__(self, *args):
        def set_type(d_type):
            if self.type is None:
                self.type = d_type
            assert self.type == d_type, "In a domain, values must be either all integer or all symbolic values"

        def _add_value(arg):
            assert isinstance(arg, (tuple, list, set, frozenset, range, int, str)), "Bad type for the domain " + str(arg) + " of type " + str(type(arg))
            if isinstance(arg, (tuple, list, set, frozenset)):
                arg = list(arg)
                if len(arg) > 2 and all(arg[i] + 1 == arg[i + 1] for i in range(len(arg) - 1)):
                    arg = range(arg[0], arg[-1] + 1)
            if isinstance(arg, list):
                for a in arg:
                    _add_value(a)
            elif isinstance(arg, range):
                if arg.step == 1 and arg.stop - arg.start > 2:
                    self.original_values.append(arg)
                    set_type(TypeVar.INTEGER)
                else:
                    _add_value(set(arg))
            elif isinstance(arg, int):
                self.original_values.append(arg)
                set_type(TypeVar.INTEGER)
            elif isinstance(arg, str):
                self.original_values.append(arg)
                set_type(TypeVar.SYMBOLIC)

        if len(args) == 1 and args[0] == math.inf:  # special integer variable with an infinite domain
            self.type = TypeVar.INTEGER
            self.original_values = [math.inf]
            self.values = [math.inf]
        else:
            self.type = None
            self.original_values = []
            _add_value(*args)
            assert self.type, "You have defined a variable with an empty domain; fix this"
            self.original_values.sort(key=lambda v: v.start if isinstance(v, range) else v)
            for i in range(len(self.original_values) - 1):
                v, w = self.original_values[i], self.original_values[i + 1]
                if isinstance(v, range) and isinstance(w, range):
                    assert v.stop <= w.start
                elif isinstance(v, range):
                    assert v.stop <= w
                elif isinstance(w, range):
                    assert v < w.start
                else:
                    assert v < w
            self.values = None  # will be defined later if necessary as either a range, or a list of int or a list of str

    def __iter__(self):
        if len(self.original_values) == 1 and isinstance(self.original_values[0], range):
            return self.original_values[0].__iter__()
        return self.all_values().__iter__()  # original_values.__iter__()

    def __getitem__(self, item):
        if len(self.original_values) == 1 and isinstance(self.original_values[0], range):
            return self.original_values[0].__getitem__(item)
        return self.all_values().__getitem__(item)

    def __eq__(self, other):
        return isinstance(other, Domain) and self.type == other.type and self.original_values == other.original_values

    def __hash__(self):
        return super().__hash__()

    def __repr__(self):
        if len(self.original_values) == 1 and self.original_values[0] == math.inf:
            return "-infinity..+infinity"
        return " ".join(str(v.start) + ".." + str(v.stop - 1) if isinstance(v, range) else str(v) for v in self.original_values)

    def smallest_value(self):
        v = self.original_values[0]
        return v.start if isinstance(v, range) else v  # self.original_values[0].smallest()

    def greatest_value(self):
        v = self.original_values[-1]
        return v.stop - 1 if isinstance(v, range) else v  # self.original_values[-1].greatest()

    def all_values(self):
        if self.values is None:  # must then be computed
            if len(self.original_values) == 1 and isinstance(self.original_values[0], range):
                self.values = self.original_values[0]
            else:
                t = []
                for v in (list(v) if isinstance(v, range) else v for v in self.original_values):
                    if isinstance(v, list):
                        t.extend(v)
                    else:
                        t.append(v)
                self.values = t
        return self.values

    def is_binary(self):
        if self.type == TypeVar.SYMBOLIC:
            return False
        zero, one = False, False
        for v in self.original_values:
            if isinstance(v, range):
                if v.start != 0 or v.stop != 2:
                    return False  # because a stored range has at least two values (so, at least one not equal to 0 and 1)
                else:
                    zero = one = True
            elif isinstance(v, int):
                if v == 0:
                    zero = True
                elif v == 1:
                    one = True
                else:
                    return False
        return zero and one


class Variable:
    name2obj = dict()  # Dictionary (keys: names of variables - values: variable objects)

    arrays = []  # the arrays of variables, as introduced by the user in the model

    @staticmethod
    def build_names_array(name, sizes, mins, indexes=None):
        if indexes is None:
            indexes = []
        if sizes:
            t = []
            for i in range(sizes[0]):
                indexes.append(i + mins[len(indexes)])
                t.append(Variable.build_names_array(name, sizes[1:], mins, indexes))
                indexes.pop()
            return t
        return name + "[" + "][".join(str(i) for i in indexes) + "]"

    @staticmethod
    def build_domain(name, domain, indexes):
        if domain is None:
            return None
        if isinstance(domain, Domain):
            return domain
        if isinstance(domain, type(lambda: 0)):
            domain = domain(*indexes)
            if domain is None:
                return None
        if isinstance(domain, (tuple, list)):
            domain = flatten(domain)
            assert all(isinstance(v, int) for v in domain) or all(isinstance(v, str) for v in domain)  # possible, even if using a set is recommended
            return Domain(set(domain))
            # # at this point, it means that a specific domain for each variable is given in a list
            # for i in indexes:
            #     assert i < len(domain), "The number of domains is less than the specified index " + name + " - " + str(domain)
            #     domain = domain[i]
        if isinstance(domain, Domain):
            return domain
        if isinstance(domain, list) and (all(isinstance(v, int) for v in domain) or all(isinstance(v, str) for v in domain)):
            return Domain(set(domain))
        assert isinstance(domain, (range, set)), str(type(domain)) + " " + str(domain)
        # assert len(domain) > 0, "a domain is defined with an empty domain"
        return Domain(domain)

    @staticmethod
    def build_variable(name, domain, indexes):
        dom = Variable.build_domain(name, domain, indexes)
        if dom is None:
            return None
        var = VariableInteger(name, dom) if dom.type == TypeVar.INTEGER else VariableSymbolic(name, dom)
        Variable.name2obj[name] = var
        return var

    @staticmethod
    def build_variables_array(name, sizes, domain, indexes=None):
        if indexes is None:
            indexes = []
        if isinstance(name, list):
            # it means that several variables are declared with a single line
            assert len(sizes) == 1, "When using several declarations, only one-dimensional arrays are allowed."
            return [Variable.build_variable(var_name.strip(), domain, indexes) for var_name in name]
        if sizes:
            t = []
            for i in range(sizes[0]):
                indexes.append(i)
                t.append(Variable.build_variables_array(name, sizes[1:], domain, indexes))
                indexes.pop()
            return t
        var_name = name + "[" + "][".join(str(i) for i in indexes) + "]"
        return Variable.build_variable(var_name, domain, indexes)

    def __init__(self, name, dom, *, inverse=False, negation=False):
        self.id = name
        self.dom = dom
        pos = self.id.find("[")
        if pos == -1:
            self.indexes = None
        else:
            self.prefix, self.suffix = self.id[:pos], self.id[pos:]
            self.indexes = [int(v) for v in re.split("]\\[", self.suffix[1:-1])]
        self.inverse = inverse  # arithmetic inverse
        self.negation = negation  # logical negation
        self.value = None  # value of the last found solution
        self.values = []  # values of the successive found solutions

    def name(self, name):
        def _valid_identifier(s):
            return isinstance(s, str) and all(c.isalnum() or c == '_' for c in s)  # other characters to be allowed?

        error_if(not _valid_identifier(name), "The identifier " + str(name) + " is not valid")
        error_if(name in Variable.name2obj, "The identifier " + str(name) + " is used twice. This is not possible")
        Variable.name2obj[name] = self

    def eq__safe(self, other):
        return isinstance(other, Variable) and self.id == other.id

    def __eq__(self, other):
        return self.eq__safe(other)  # isinstance(other, Variable) and self.id == other.id

    def __invert__(self):
        return Variable(self.id, self.dom, negation=not self.negation)

    def __neg__(self):
        return Variable(self.id, self.dom, inverse=not self.inverse)

    def __hash__(self):
        return object.__hash__(self)  # , *args, **kwargs)

    def __repr__(self):
        return self.id


class VariableInteger(Variable):
    def __init__(self, name, dom):
        super().__init__(name, dom)

    def among(self, *values):
        values = flatten(values)
        if len(values) == 0:
            return main.constraints.ConstraintDummyConstant(0)
        assert len(values) > 0 and all(isinstance(v, int) for v in values)
        return functions.belong(self, values)

    def not_among(self, *values):
        values = flatten(values)
        if len(values) == 0:
            return main.constraints.ConstraintDummyConstant(1)
        assert len(values) > 0 and all(isinstance(v, int) for v in values)
        return functions.not_belong(self, values)


class VariableSymbolic(Variable):
    def __init__(self, name, dom):
        super().__init__(name, dom)
