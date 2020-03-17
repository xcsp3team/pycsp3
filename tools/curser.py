from collections import deque

from pycsp3.classes.entities import Node, TypeNode
from pycsp3.classes.main.constraints import ScalarProduct, PartialConstraint, ConstraintAllDifferent, ConstraintSum, ConstraintCount, ConstraintElement, \
    ConstraintElementMatrix, \
    ConstraintInstantiation, ECtr
from pycsp3.classes.main.variables import Variable, VariableInteger, NotVariable
from pycsp3.libs.forbiddenfruit import curse
from pycsp3.tools.inspector import checkType
from pycsp3.tools.utilities import flatten, is_containing, unique_type_in, is_1d_tuple, is_1d_list, is_2d_list, is_matrix, ANY

from collections import OrderedDict, namedtuple

queue_in = deque()  # To store partial constraints when using the IN operator


def cursing():
    def _dict_add(self, other):  # for being able to merge dictionaries
        if isinstance(other, dict):
            d = self.copy()
            d.update(other)
            return d
        raise NotImplementedError  # return save_dict_add(self, other)

    def _list_mul(self, other):  # for being able to use scalar products
        if is_containing(self, (Variable, Node), check_first_only=True):
            return ScalarProduct(self, other)
        return list.__mul__(self, other)

    def _tuple_contains(self, other):
        if not OpOverrider.activated:
            return self.__contains__(other)
        if is_containing(other, Variable) and len(self) > 0 and isinstance(self[0], (tuple, int)):
            queue_in.append((list(self), other))
            return True
        if isinstance(other, int) and (is_1d_list(self, Variable) or is_1d_tuple(self, Variable)):  # member/element constraint
            queue_in.append((self, other))
            return True
        return self.__contains__(other)

    def _list_contains(self, other):  # for being able to use 'in' when expressing extension constraints
        if not OpOverrider.activated:
            return self.__contains__(other)
        if is_containing(other, Variable) and len(self) > 0 and isinstance(self[0], (list, tuple, int)):
            queue_in.append((self, other))
            return True
        if isinstance(other, int) and (is_1d_list(self, Variable) or is_1d_tuple(self, Variable)):  # member/element constraint
            queue_in.append((self, other))
            return True
        return self.__contains__(other)

    def _set_contains(self, other):  # for being able to use 'in' when expressing intension/extension constraints
        if not OpOverrider.activated:
            return self.__contains__(other)
        tself = unique_type_in(self)
        # if isinstance(other, Variable) and len(self) > 0 and is_containing(self, int):  # unary table constraint
        if isinstance(other, Variable) and tself in {int, str}:  # unary table constraint
            queue_in.append((list(self), other))
            return True
        # if isinstance(other, (Variable, PartialConstraint)) or isinstance(other, (int, str)) and is_containing(self, Variable):  # intension constraint
        if isinstance(other, (Variable, PartialConstraint)) or isinstance(other, (int, str)) and tself and issubclass(tself, Variable):  # intension constraint
            queue_in.append((self, other))
            return True
        # if is_1d_tuple(other, Variable) or is_1d_list(other, Variable):  # non-unary table constraint
        #     queue_in.append((list(self), other))
        #     return True
        if is_containing(other, Variable):  # non-unary table constraint
            queue_in.append((list(self), flatten(other)))
            return True
        return self.__contains__(other)

    def _range_contains(self, other):  # for being able to use 'in' when expressing conditions of constraints
        if not OpOverrider.activated:
            return range.__contains__(other)
        if isinstance(other, ScalarProduct):
            other = PartialConstraint(ConstraintSum(other.variables, other.coeffs, None))  # functions.Sum(other)
        if isinstance(other, (PartialConstraint, Variable)):
            queue_in.append((self, other))
            return True
        return range.__contains__(self, other)

    def _enumerate_contains(self, other):
        if not OpOverrider.activated:
            return self.__contains__(other)
        if is_containing(other, Variable):
            tmp = list(self)
            if len(tmp) > 0 and isinstance(tmp[0], (tuple, int)):
                queue_in.append((tmp, other))
                return True
        return self.__contains__(other)

    curse(dict, "__add__", _dict_add)
    curse(list, "__mul__", _list_mul)
    curse(tuple, "__contains__", _tuple_contains)
    curse(list, "__contains__", _list_contains)
    curse(set, "__contains__", _set_contains)
    curse(range, "__contains__", _range_contains)
    curse(enumerate, "__contains__", _enumerate_contains)


cursing()


class OpOverrider:
    activated = False

    @staticmethod
    def enable():
        OpOverrider.activated = True

        ListVar.__eq__ = OpOverrider.__eq__lv
        ListVar.__getitem__ = OpOverrider.__getitem__lv
        ListInt.__getitem__ = OpOverrider.__getitem__li
        ListInt.__contains__ = OpOverrider.__contains__li

        Variable.__eq__ = Node.__eq__ = OpOverrider.__eq__
        Variable.__ne__ = Node.__ne__ = OpOverrider.__ne__
        Variable.__lt__ = Node.__lt__ = OpOverrider.__lt__
        Variable.__le__ = Node.__le__ = OpOverrider.__le__
        Variable.__ge__ = Node.__ge__ = OpOverrider.__ge__
        Variable.__gt__ = Node.__gt__ = OpOverrider.__gt__

        Variable.__add__ = Node.__add__ = OpOverrider.__add__
        Variable.__radd__ = Node.__radd__ = OpOverrider.__radd__
        Variable.__sub__ = Node.__sub__ = OpOverrider.__sub__
        Variable.__rsub__ = Node.__rsub__ = OpOverrider.__rsub__
        Variable.__mul__ = Node.__mul__ = OpOverrider.__mul__
        Variable.__rmul__ = Node.__rmul__ = OpOverrider.__rmul__
        Variable.__pow__ = Node.__pow__ = OpOverrider.__pow__
        Variable.__mod__ = Node.__mod__ = OpOverrider.__mod__
        Variable.__floordiv__ = Node.__floordiv__ = OpOverrider.__floordiv__
        Variable.__rfloordiv__ = Node.__rfloordiv__ = OpOverrider.__rfloordiv__

        Variable.__and__ = Node.__and__ = OpOverrider.__and__
        Variable.__or__ = Node.__or__ = OpOverrider.__or__
        Variable.__invert__ = Node.__invert__ = OpOverrider.__invert__
        Variable.__xor__ = Node.__xor__ = OpOverrider.__xor__

    @staticmethod
    def disable():
        OpOverrider.activated = False

        ListVar.__eq__ = list.__eq__
        ListVar.__getitem__ = list.__getitem__
        ListInt.__getitem__ = list.__getitem__
        ListInt.__contains__ = list.__contains__

        Variable.__eq__ = Node.__eq__ = object.__eq__
        Variable.__ne__ = Node.__ne__ = object.__ne__
        Variable.__lt__ = Node.__lt__ = object.__lt__
        Variable.__le__ = Node.__le__ = object.__le__
        Variable.__ge__ = Node.__ge__ = object.__ge__
        Variable.__gt__ = Node.__gt__ = object.__gt__

        Variable.__add__ = Node.__add__ = None
        Variable.__radd__ = Node.__radd__ = None
        Variable.__sub__ = Node.__sub__ = None
        Variable.__rsub__ = Node.__rsub__ = None
        Variable.__mul__ = Node.__mul__ = None
        Variable.__rmul__ = Node.__rmul__ = None
        Variable.__pow__ = Node.__pow__ = None
        Variable.__mod__ = Node.__mod__ = None
        Variable.__floordiv__ = Node.__floordiv__ = None
        Variable.__rfloordiv__ = Node.__rfloordiv__ = None

        Variable.__and__ = Node.__and__ = None
        Variable.__or__ = Node.__or__ = None
        Variable.__invert__ = Node.__invert__ = None
        Variable.__xor__ = Node.__xor__ = None

        return OpOverrider

    @staticmethod
    def execute(arg):
        OpOverrider.enable()
        return arg

    @staticmethod
    def project_recursive(t, indexes, dimension):
        index = slice(None, None, None) if indexes[dimension] == ANY else indexes[dimension]
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
        if isinstance(other, PartialConstraint):
            return PartialConstraint.combine_partial_objects(self, TypeNode.ADD, other)
        return Node.build(TypeNode.ADD, self, other)

    def __radd__(self, other):
        return Node.build(TypeNode.ADD, other, self)

    def __sub__(self, other):
        if isinstance(other, PartialConstraint):
            return PartialConstraint.combine_partial_objects(self, TypeNode.SUB, other)
        return Node.build(TypeNode.SUB, self, other)

    def __rsub__(self, other):
        return Node.build(TypeNode.SUB, other, self)

    def __mul__(self, other):
        return Node.build(TypeNode.MUL, self, other)

    def __rmul__(self, other):
        return Node.build(TypeNode.MUL, other, self)

    def __mod__(self, other):
        return Node.build(TypeNode.MOD, self, other)

    def __pow__(self, other):
        return Node.build(TypeNode.POW, self, other)

    def __floordiv__(self, other):
        return Node.build(TypeNode.DIV, self, other)

    def __rfloordiv__(self, other):
        return Node.build(TypeNode.DIV, other, self)

    def __lt__(self, other):
        return object.__lt__(self, other) if None in {self, other} else Node.build(TypeNode.LT, self, other)

    def __le__(self, other):
        return object.__le__(self, other) if None in {self, other} else Node.build(TypeNode.LE, self, other)

    def __ge__(self, other):
        return object.__ge__(self, other) if None in {self, other} else Node.build(TypeNode.GE, self, other)

    def __gt__(self, other):
        return object.__gt__(self, other) if None in {self, other} else Node.build(TypeNode.GT, self, other)

    def __eq__(self, other):
        return object.__eq__(self, other) if None in {self, other} else Node.build(TypeNode.EQ, self, other)

    def __ne__(self, other):
        return object.__ne__(self, other) if None in {self, other} else Node.build(TypeNode.NE, self, other)

    def __or__(self, other):
        return object.__or__(self, other) if None in {self, other} else Node.disjunction(self, other)

    def __and__(self, other):
        return object.__and__(self, other) if None in {self, other} else Node.conjunction(self, other)

    def __invert__(self):
        return NotVariable(self) if isinstance(self, VariableInteger) else Node.build(TypeNode.NOT, self)

    def __xor__(self, other):
        return object.__xor__(self, other) if None in {self, other} else Node.build(TypeNode.XOR, self, other)

    def __eq__lv(self, other):  # lv for ListVar
        def Instantiation(*, variables, values):
            variables = flatten(variables)
            values = flatten(values) if not isinstance(values, range) else list(values)
            checkType(variables, [Variable])
            checkType(values, (int, [int]))
            if len(variables) == 0:
                return None
            if len(values) == 1 and len(variables) > 1:
                values = [values[0]] * len(variables)
            return ConstraintInstantiation(variables, values)

        if isinstance(other, (list, tuple)) and any(isinstance(v, int) for v in other):
            return ECtr(Instantiation(variables=self, values=other))
        return list.__eq__(self, other)

    def __getitem__lv(self, indexes):
        if isinstance(indexes, Variable):
            return PartialConstraint(ConstraintElement(self, indexes))
        if isinstance(indexes, tuple) and len(indexes) > 0:
            if any(isinstance(i, Variable) for i in indexes):  # this must be a constraint Element-Matrix
                assert is_matrix(self) and len(indexes) == 2, "A matrix is expected, with two indexes"
                if all(isinstance(i, Variable) for i in indexes):
                    return PartialConstraint(ConstraintElementMatrix(self, indexes[0], indexes[1]))
                else:
                    assert isinstance(indexes[0], Variable) and isinstance(indexes[1], int)
                    return PartialConstraint(ConstraintElement(self[:, indexes[1]], indexes[0]))
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
        if isinstance(indexes, Variable):
            return PartialConstraint(ConstraintElement(self, indexes))
        if isinstance(indexes, tuple) and len(indexes) > 0:
            if any(isinstance(i, Variable) for i in indexes):  # this must be a constraint Element-Matrix
                assert is_matrix(self) and len(indexes) == 2, "A matrix is expected, with two indexes"
                if all(isinstance(i, Variable) for i in indexes):
                    return PartialConstraint(ConstraintElementMatrix(self, indexes[0], indexes[1]))
                else:
                    assert isinstance(indexes[0], Variable) and isinstance(indexes[1], int)
                    return PartialConstraint(ConstraintElement(self[:, indexes[1]], indexes[0]))
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
        if is_containing(other, Variable) and len(self) > 0 and isinstance(self[0], (tuple, int)):
            queue_in.append((self, other))
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
        if is_containing(other, (Variable, Node)):
            return ScalarProduct(other, self)
        assert is_containing(self, (Variable, Node))
        return ScalarProduct(self, other)

    def __rmul__(self, other):
        return ListInt.__mul__(other, self)


def columns(m):
    def column(j):
        assert is_2d_list(m), "column() can only be called on 2-dimensional lists"
        assert all(len(row) > j for row in m), "one row has not at least j+1 elements"
        return ListVar(row[j] for row in m)

    assert is_matrix(m), "columns() can only be called on matrices"
    return ListVar(column(j) for j in range(len(m[0])))


class ListVar(list):
    def __init__(self, variables):
        self.extend(variables)

    def __getslice__(self, i, j):
        return ListVar(list.__getslice__(self, i, j))

    def __add__(self, other):
        return ListVar(list.__add__(self, other))

    def __mul__(self, other):
        assert is_containing(self, (Variable, Node))
        return ScalarProduct(self, list(other))

    def __contains__(self, other):
        if isinstance(other, int) and (is_1d_list(self, Variable) or is_1d_tuple(self, Variable)):  # member constraint
            queue_in.append((self, other))
            return True
        return list.__contains__(self, other)

    # def __rmul__(self, other): return ListVar.__mul__(other, self)

    def columns(self):
        return columns(self)


def dicts_values(ds):
    def value_for(v):
        return ListInt(v) if is_1d_list(v, int) else ListVar(v) if is_1d_list(v, Variable) else dicts_values(v) if is_1d_list(v, OrderedDict) else v

    assert is_1d_list(ds, OrderedDict)
    if not hasattr(dicts_values, "cnt"):
        dicts_values.cnt = 0
    nt = namedtuple("ds" + str(dicts_values.cnt), ds[0].keys())
    dicts_values.cnt += 1
    # return [nt(*(v for (k, v) in d.items())) for d in ds]
    return [nt(*(value_for(v) for (k, v) in d.items())) for d in ds]
