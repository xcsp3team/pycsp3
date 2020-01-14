from pycsp3 import functions
from pycsp3.classes import entities
from pycsp3.classes import main
from pycsp3.libs.forbiddenfruit import curse
from pycsp3.tools import utilities

''' __add__ method of dict (To merge dictionaries) in sum) '''


def _dict_add(self, other):
    if isinstance(other, dict):
        d = self.copy()
        d.update(other)
        return d
    raise NotImplementedError  # return save_dict_add(self, other)


''' __mul__ method of list (To represent coeffs in sum) '''


def _list_mul(self, other):
    if utilities.is_containing(self, (main.variables.Variable, entities.Node), check_first_only=True):
        return main.constraints.ScalarProduct(self, other)
    return list.__mul__(self, other)


''' __contains__ method of range (To use the keyword "in" of python as a comparison operator in conditions of XCSP)'''


def _range_in(self, other):
    if not OpOverrider.activated:
        return range.__contains__(other)
    if isinstance(other, (main.constraints.ScalarProduct)):
        other = functions.Sum(other)
    if isinstance(other, (main.constraints.PartialConstraint, main.variables.Variable)):
        functions.queue_in.append((self, other))
        return True
    return range.__contains__(self, other)


''' __contains__ method of set (to be able to use the Python keyword "in" for intension and extension constraints) '''


def _set_in(self, other):
    if not OpOverrider.activated:
        return self.__contains__(other)
    if isinstance(other, (main.constraints.PartialConstraint, main.variables.Variable)):
        functions.queue_in.append((self, other))
        return True
    if utilities.is_1d_tuple(other, main.variables.Variable) or utilities.is_1d_list(other, main.variables.Variable):  # this is a table constraint
        functions.queue_in.append((list(self), other))
        return True
    return self.__contains__(other)


''' __contains__ method of list (to be able to use the Python keyword "in" for table constraints) '''


def _list_in(self, other):
    if not OpOverrider.activated:
        return self.__contains__(other)
    if utilities.is_containing(other, main.variables.Variable) and len(self) > 0 and isinstance(self[0], (list, tuple, int)):
        functions.queue_in.append((self, other))
        return True
    return self.__contains__(other)


def _tuple_in(self, other):
    if not OpOverrider.activated:
        return self.__contains__(other)
    if utilities.is_containing(other, main.variables.Variable) and len(self) > 0 and isinstance(self[0], (tuple, int)):
        functions.queue_in.append((list(self), other))
        return True
    return self.__contains__(other)


def _enumerate_in(self, other):
    if not OpOverrider.activated:
        return self.__contains__(other)
    if utilities.is_containing(other, main.variables.Variable):
        tmp = list(self)
        if len(tmp) > 0 and isinstance(tmp[0], (tuple, int)):
            functions.queue_in.append((tmp, other))
            return True
    return self.__contains__(other)


curse(dict, "__add__", _dict_add)
curse(list, "__mul__", _list_mul)
curse(list, "__contains__", _list_in)
curse(tuple, "__contains__", _tuple_in)
curse(enumerate, "__contains__", _enumerate_in)
curse(range, "__contains__", _range_in)
curse(set, "__contains__", _set_in)


class OpOverrider:
    activated = False

    @staticmethod
    def enable():
        OpOverrider.activated = True

        ListVar.__eq__ = OpOverrider.__eq__lv
        ListVar.__getitem__ = OpOverrider.__getitem__lv
        ListInt.__getitem__ = OpOverrider.__getitem__li
        ListInt.__contains__ = OpOverrider.__contains__li

        main.variables.Variable.__eq__ = entities.Node.__eq__ = OpOverrider.__eq__
        main.variables.Variable.__ne__ = entities.Node.__ne__ = OpOverrider.__ne__
        main.variables.Variable.__lt__ = entities.Node.__lt__ = OpOverrider.__lt__
        main.variables.Variable.__le__ = entities.Node.__le__ = OpOverrider.__le__
        main.variables.Variable.__ge__ = entities.Node.__ge__ = OpOverrider.__ge__
        main.variables.Variable.__gt__ = entities.Node.__gt__ = OpOverrider.__gt__

        main.variables.Variable.__add__ = entities.Node.__add__ = OpOverrider.__add__
        main.variables.Variable.__radd__ = entities.Node.__radd__ = OpOverrider.__radd__
        main.variables.Variable.__sub__ = entities.Node.__sub__ = OpOverrider.__sub__
        main.variables.Variable.__rsub__ = entities.Node.__rsub__ = OpOverrider.__rsub__
        main.variables.Variable.__mul__ = entities.Node.__mul__ = OpOverrider.__mul__
        main.variables.Variable.__rmul__ = entities.Node.__rmul__ = OpOverrider.__rmul__
        main.variables.Variable.__pow__ = entities.Node.__pow__ = OpOverrider.__pow__
        main.variables.Variable.__mod__ = entities.Node.__mod__ = OpOverrider.__mod__
        main.variables.Variable.__floordiv__ = entities.Node.__floordiv__ = OpOverrider.__floordiv__
        main.variables.Variable.__rfloordiv__ = entities.Node.__rfloordiv__ = OpOverrider.__rfloordiv__

        main.variables.Variable.__and__ = entities.Node.__and__ = OpOverrider.__and__
        main.variables.Variable.__or__ = entities.Node.__or__ = OpOverrider.__or__
        main.variables.Variable.__invert__ = entities.Node.__invert__ = OpOverrider.__invert__
        main.variables.Variable.__xor__ = entities.Node.__xor__ = OpOverrider.__xor__

    @staticmethod
    def disable():
        OpOverrider.activated = False

        ListVar.__eq__ = list.__eq__
        ListVar.__getitem__ = list.__getitem__
        ListInt.__getitem__ = list.__getitem__
        ListInt.__contains__ = list.__contains__

        main.variables.Variable.__eq__ = entities.Node.__eq__ = object.__eq__
        main.variables.Variable.__ne__ = entities.Node.__ne__ = object.__ne__
        main.variables.Variable.__lt__ = entities.Node.__lt__ = object.__lt__
        main.variables.Variable.__le__ = entities.Node.__le__ = object.__le__
        main.variables.Variable.__ge__ = entities.Node.__ge__ = object.__ge__
        main.variables.Variable.__gt__ = entities.Node.__gt__ = object.__gt__

        main.variables.Variable.__add__ = entities.Node.__add__ = None
        main.variables.Variable.__radd__ = entities.Node.__radd__ = None
        main.variables.Variable.__sub__ = entities.Node.__sub__ = None
        main.variables.Variable.__rsub__ = entities.Node.__rsub__ = None
        main.variables.Variable.__mul__ = entities.Node.__mul__ = None
        main.variables.Variable.__rmul__ = entities.Node.__rmul__ = None
        main.variables.Variable.__pow__ = entities.Node.__pow__ = None
        main.variables.Variable.__mod__ = entities.Node.__mod__ = None
        main.variables.Variable.__floordiv__ = entities.Node.__floordiv__ = None
        main.variables.Variable.__rfloordiv__ = entities.Node.__rfloordiv__ = None

        main.variables.Variable.__and__ = entities.Node.__and__ = None
        main.variables.Variable.__or__ = entities.Node.__or__ = None
        main.variables.Variable.__invert__ = entities.Node.__invert__ = None
        main.variables.Variable.__xor__ = entities.Node.__xor__ = None

        return OpOverrider

    @staticmethod
    def execute(arg):
        OpOverrider.enable()
        return arg

    @staticmethod
    def project_recursive(t, indexes, dimension):
        index = slice(None, None, None) if indexes[dimension] == functions.ANY else indexes[dimension]
        if isinstance(index, int):
            if isinstance(t, list):
                t = t[index]  #  to keep the shape (dimensions), we need to do that
            else:
                return t
        elif isinstance(index, slice):
            t = list.__getitem__(t, index)
        else:
            raise TypeError()
        if isinstance(t, list) and dimension + 1 < len(indexes):
            if not isinstance(index, int):
                for i, element in enumerate(t):
                    t[i] = OpOverrider.project_recursive(element, indexes, dimension + 1)
            else:
                t = OpOverrider.project_recursive(t, indexes, dimension + 1)
        return t

    def __add__(self, other):
        if isinstance(other, main.constraints.PartialConstraint):
            return main.constraints.PartialConstraint.combine_partial_objects(self, entities.TypeNode.ADD, other)
        return functions.add(self, other)

    def __radd__(self, other):
        return functions.add(other, self)

    def __sub__(self, other):
        if isinstance(other, main.constraints.PartialConstraint):
            return main.constraints.PartialConstraint.combine_partial_objects(self, entities.TypeNode.SUB, other)
        return functions.sub(self, other)

    def __rsub__(self, other):
        return functions.sub(other, self)

    def __mul__(self, other):
        return functions.mul(self, other)

    def __rmul__(self, other):
        return functions.mul(other, self)

    def __mod__(self, other):
        return functions.mod(self, other)

    def __pow__(self, other):
        return functions.power(self, other)

    def __floordiv__(self, other):
        return functions.div(self, other)

    def __rfloordiv__(self, other):
        return functions.div(other, self)

    def __le__(self, other):
        return object.__le__(self, other) if None in {self, other} else functions.le(self, other)

    def __lt__(self, other):
        return object.__lt__(self, other) if None in {self, other} else functions.lt(self, other)

    def __ge__(self, other):
        return object.__ge__(self, other) if None in {self, other} else functions.ge(self, other)

    def __gt__(self, other):
        return object.__gt__(self, other) if None in {self, other} else functions.gt(self, other)

    def __eq__(self, other):
        return object.__eq__(self, other) if None in {self, other} else functions.eq(self, other)

    def __ne__(self, other):
        return object.__ne__(self, other) if None in {self, other} else functions.ne(self, other)

    def __or__(self, other):
        return object.__or__(self, other) if None in {self, other} else functions.disjunction(self, other)

    def __and__(self, other):
        return object.__and__(self, other) if None in {self, other} else functions.conjunction(self, other)

    def __invert__(self):
        return main.variables.NotVariable(self) if isinstance(self, main.variables.VariableInteger) else functions.lnot(self)

    def __xor__(self, other):
        return object.__xor__(self, other) if None in {self, other} else functions.xor(self, other)

    def __eq__lv(self, other):  # lv for ListVar
        if isinstance(other, list) and any(isinstance(v, int) for v in other):
            return functions.Instantiation(variables=self, values=other)
        return list.__eq__(self, other)

    def __getitem__lv(self, indexes):
        if isinstance(indexes, main.variables.Variable):
            return main.constraints.PartialConstraint(main.constraints.ConstraintElement(self, indexes))
        if isinstance(indexes, tuple) and len(indexes) > 0:
            if any(isinstance(i, main.variables.Variable) for i in indexes):  # this must be a constraint Element-Matrix
                assert utilities.is_matrix(self) and len(indexes) == 2, "A matrix is expected, with two indexes"
                if all(isinstance(i, main.variables.Variable) for i in indexes):
                    return main.constraints.PartialConstraint(main.constraints.ConstraintElementMatrix(self, indexes[0], indexes[1]))
                else:
                    assert isinstance(indexes[0], main.variables.Variable) and isinstance(indexes[1], int)
                    return main.constraints.PartialConstraint(main.constraints.ConstraintElement(self[:, indexes[1]], indexes[0]))
            result = OpOverrider.project_recursive(self, indexes, 0)
            try:
                return ListVar(result)  # TODO are sublists also guaranteed to be ListVar?
            except TypeError:
                return result
        result = list.__getitem__(self, indexes)
        try:
            return ListVar(result)
        except TypeError:
            return result

    def __getitem__li(self, indexes):  # li for ListInt
        if isinstance(indexes, main.variables.Variable):
            return main.constraints.PartialConstraint(main.constraints.ConstraintElement(self, indexes))
        if isinstance(indexes, tuple) and len(indexes) > 0:
            if any(isinstance(i, main.variables.Variable) for i in indexes):  # this must be a constraint Element-Matrix
                assert utilities.is_matrix(self) and len(indexes) == 2, "A matrix is expected, with two indexes"
                if all(isinstance(i, main.variables.Variable) for i in indexes):
                    return main.constraints.PartialConstraint(main.constraints.ConstraintElementMatrix(self, indexes[0], indexes[1]))
                else:
                    assert isinstance(indexes[0], main.variables.Variable) and isinstance(indexes[1], int)
                    return main.constraints.PartialConstraint(main.constraints.ConstraintElement(self[:, indexes[1]], indexes[0]))
            result = OpOverrider.project_recursive(self, indexes, 0)
            try:
                return ListVar(result)  # TODO is it ListVar or ListInt ?
            except TypeError:
                return result
        result = list.__getitem__(self, indexes)
        try:
            return ListInt(result)
        except TypeError:
            return result

    def __contains__li(self, other):
        if utilities.is_containing(other, main.variables.Variable) and len(self) > 0 and isinstance(self[0], (tuple, int)):
            functions.queue_in.append((self, other))
            return True
        return list.__contains__(self, other)


class ListInt(list):
    def __init__(self, integers):
        self.extend(integers)

    def __getslice__(self, i, j):
        return ListInt(list.__getslice__(self, i, j))

    def __add__(self, other):
        return ListInt(list.__add__(self, other))

    def __mul__(self, other):
        if utilities.is_containing(other, (main.variables.Variable, entities.Node)):
            return main.constraints.ScalarProduct(other, self)
        assert utilities.is_containing(self, (main.variables.Variable, entities.Node))
        return main.constraints.ScalarProduct(self, other)

    def __rmul__(self, other):
        return ListInt.__mul__(other, self)


class ListVar(list):
    def __init__(self, variables):
        self.extend(variables)

    def __getslice__(self, i, j):
        return ListVar(list.__getslice__(self, i, j))

    def __add__(self, other):
        return ListVar(list.__add__(self, other))

    def __mul__(self, other):
        assert utilities.is_containing(self, (main.variables.Variable, entities.Node))
        return main.constraints.ScalarProduct(self, other)

    # def __rmul__(self, other): return ListVar.__mul__(other, self)

    def columns(self):
        return functions.columns(self)
