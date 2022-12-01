from functools import total_ordering
from types import GeneratorType

from pycsp3.classes.auxiliary.ptypes import TypeConditionOperator
from pycsp3.classes.entities import Node, TypeNode
from pycsp3.classes.main.variables import Variable
from pycsp3.tools.inspector import checkType
from pycsp3.tools.utilities import is_1d_list, is_1d_tuple, ANY

LT, LE, GE, GT, EQ, NE, IN, NOTIN = [t for t in TypeConditionOperator]


@total_ordering
class Condition:
    def __init__(self, operator):
        self.operator = operator
        assert isinstance(operator, TypeConditionOperator), "the operator " + str(operator) + " should be of type TypeConditionOperator"

    def _key(self):
        return str(type(self)), str(self.operator)

    def __hash__(self):
        return hash(self._key())

    def __eq__(self, other):
        return type(self) == type(other) and self._key() == other._key()

    def __lt__(self, other):
        return True if isinstance(other, (int, str)) or other == ANY else self._key() < other._key()

    @staticmethod
    def build_condition(condition):
        if condition is None:
            return None  # it may occur when building a partial constraint
        condition = tuple(condition) if isinstance(condition, list) else condition  # we expect a condition to be given as a tuple (or a list)
        assert isinstance(condition, tuple) and len(condition) == 2, "a condition must a pair, given as a tuple (or a list)"
        operator = TypeConditionOperator.value_of(condition[0]) if isinstance(condition[0], str) else condition[0]
        right_operand = list(condition[1]) if isinstance(condition[1], (set, frozenset, GeneratorType)) else condition[1]
        checkType(right_operand, (int, Variable, range, [int, Variable]))
        if isinstance(right_operand, range) and right_operand.step != 1:
            right_operand = list(right_operand)
        if isinstance(right_operand, int):
            return ConditionValue(operator, right_operand)
        if isinstance(right_operand, Variable):
            return ConditionVariable(operator, right_operand)
        if isinstance(right_operand, range):
            return ConditionInterval(operator, right_operand.start, right_operand.stop - 1)
        if isinstance(right_operand, list):
            return ConditionSet(operator, right_operand)

    def filtering(self, values):
        pass

    def str_tuple(self):
        pass

    def right_operand(self):
        pass

    def infix_string(self):
        return self.operator.to_str() + " " + str(self.right_operand())

    def __str__(self):
        return "(" + str(self.operator) + "," + str(self.right_operand()) + ")"


class ConditionValue(Condition):
    def __init__(self, operator, value):
        super().__init__(operator)
        self.value = value

    def _key(self):
        return super()._key() + (self.value,)

    def filtering(self, values):
        if self.operator == EQ:  # we should avoid calling this (by directly giving the value in the tuple: write 6 instead of (eq(6)))
            return (self.value,) if self.value in values else ()
        if self.operator == NE:
            return (v for v in values if v != self.value)
        if self.operator == LT:
            return (v for v in values if v < self.value)
        if self.operator == LE:
            return (v for v in values if v <= self.value)
        if self.operator == GE:
            return (v for v in values if v >= self.value)
        if self.operator == GT:
            return (v for v in values if v > self.value)
        assert False

    def str_tuple(self):
        op_utf = TypeConditionOperator.to_utf(self.operator)
        if self.operator in (EQ, NE, LE, GE):
            return op_utf + str(self.value)
        # <= and >= more readable than < and > (this is why we translate when possible)
        if self.operator == LT:
            return TypeConditionOperator.to_utf(LE) + str(self.value - 1) if isinstance(self.value, int) else op_utf + str(self.value)
        if self.operator == GT:
            return TypeConditionOperator.to_utf(GE) + str(self.value + 1) if isinstance(self.value, int) else op_utf + str(self.value)
        assert False

    def __repr__(self):
        return self.str_tuple()

    def right_operand(self):
        return self.value


class ConditionNode(Condition):
    def __init__(self, operator, node):
        super().__init__(operator)
        self.node = node

    def __hash__(self):
        return hash(self._key())

    def __eq__(self, other):
        return self.node.eq__safe(other)

    def _key(self):
        return super()._key() + (self.node,)

    def filtering(self, values):  # TODO not use it during the filtering
        return {self}

    def str_tuple(self):
        return (TypeConditionOperator.to_utf(self.operator) if self.operator != EQ else "") + self.node.__str_hybrid__()

    def right_operand(self):
        return self.node

    def evaluate(self, t, domains):  # used when converting hybrid tables to ordinary tables
        if self.node.type is TypeNode.COL:
            i = self.node.sons
            # assert t[i] is ANY or isinstance(t[i], int)
            values = domains[i] if t[i] is ANY else [t[i]]
            return [i], [(v, v) for v in values]  # v is evaluated as v
        if self.node.type in (TypeNode.ADD, TypeNode.SUB):
            sons = self.node.sons
            assert sons[0].type is TypeNode.COL and sons[1].type in (TypeNode.COL, TypeNode.INT)
            i = sons[0].sons
            # assert t[i] is ANY or isinstance(t[i], int)
            values0 = domains[i] if t[i] is ANY else [t[i]]
            if sons[1].type == TypeNode.INT:
                v1 = sons[1].sons
                return [i], [(v0, v0 + v1 if self.node.type is TypeNode.ADD else v0 - v1) for v0 in values0]
            j = sons[1].sons
            # assert t[j] is ANY or isinstance(t[j], int)
            values1 = domains[j] if t[j] is ANY else [t[j]]
            return [i, j], [(v0, v1, v0 + v1 if self.node.type is TypeNode.ADD else v0 - v1) for v0 in values0 for v1 in values1]
        assert False


class ConditionVariable(Condition):
    def __init__(self, operator, variable):
        super().__init__(operator)
        self.variable = variable

    def _key(self):
        return super()._key() + (self.variable,)

    def filtering(self, values):
        assert False, "Currently not implemented"

    def str_tuple(self):
        assert False, "Currently not implemented"

    def right_operand(self):
        return self.variable


class ConditionInterval(Condition):
    def __init__(self, operator, min, max):
        super().__init__(operator)
        self.min = min
        self.max = max

    def _key(self):
        return super()._key() + (self.min, self.max)

    def filtering(self, values):
        if self.operator == IN:
            return (v for v in values if self.min <= v <= self.max)
        if self.operator == NOTIN:
            return (v for v in values if v < self.min or self.max < v)
        assert False

    def str_tuple(self):
        if self.operator == IN:
            return self.right_operand()
        if self.operator == NOTIN:
            return TypeConditionOperator.to_utf(NOTIN) + self.right_operand()
        assert False

    def right_operand(self):
        return str(self.min) + ".." + str(self.max)


class ConditionSet(Condition):
    def __init__(self, operator, t):
        super().__init__(operator)
        self.t = t

    def _key(self):
        return super()._key() + tuple(self.t)

    def filtering(self, values):
        if self.operator == IN:
            return (v for v in values if v in self.t)
        if self.operator == NOTIN:
            return (v for v in values if v not in self.t)
        assert False

    def str_tuple(self):
        if self.operator == IN:
            return self.right_operand()
        if self.operator == NOTIN:
            return TypeConditionOperator.to_utf(NOTIN) + self.right_operand()
        assert False

    def right_operand(self):
        return "{" + ",".join(str(v) for v in self.t) + "}"

    def __repr__(self):
        return self.str_tuple()


def _build_condition(operator, v):
    if isinstance(v, int):
        return ConditionValue(operator, v)
    if isinstance(v, Variable):
        return ConditionVariable(operator, v)
    if isinstance(v, Node):
        # {eq|lt|le|ge|gt|ne}{var|interger}{+|-}{var|interger}
        return ConditionNode(operator, v)
    assert False, "The right argument following " + operator + " must be an integer or a node."


def lt(v):
    """
    Builds an object Condition whose operator is lt (strictly less than)
    and the (right operand) is the specified argument

    :param v: either an integer or the root node of an expression
    :return: an object Condition
    """
    return _build_condition(LT, v)


def le(v):
    """
    Builds an object Condition whose operator is le (less than or equal)
    and the (right operand) is the specified argument

    :param v: either an integer or the root node of an expression
    :return: an object Condition
    """
    return _build_condition(LE, v)


def ge(v):
    """
    Builds an object Condition whose operator is ge (greater than or equal)
    and the (right operand) is the specified argument

    :param v: either an integer or the root node of an expression
    :return: an object Condition
    """
    return _build_condition(GE, v)


def gt(v):
    """
    Builds an object Condition whose operator is gt (strictly greater than)
    and the (right operand) is the specified argument

    :param v: either an integer or the root node of an expression
    :return: an object Condition
    """
    return _build_condition(GT, v)


def eq(v):
    """
    Builds an object Condition whose operator is eq (equal to)
    and the (right operand) is the specified argument

    :param v: either an integer or the root node of an expression
    :return: an object Condition
    """
    return _build_condition(EQ, v)


def ne(v):
    """
    Builds an object Condition whose operator is ne (not equal to)
    and the (right operand) is the specified argument

    :param v: either an integer or the root node of an expression
    :return: an object Condition
    """
    return _build_condition(NE, v)


def _inside_outside(v, op):
    v = v if len(v) > 1 else v[0]
    if isinstance(v, range):
        return ConditionInterval(op, v.start, v.stop - 1)
    if isinstance(v, set):
        return ConditionSet(op, v)
    assert is_1d_list(v, int) or is_1d_tuple(v, int)
    return ConditionSet(op, set(v))


def inside(*v):
    """
    Builds an object Condition whose operator is 'in'
    and the (right operand) is defined from the specified argument(s)

    :param v: a range, a set, a tuple or a list of integers
    :return: an object Condition
    """
    return _inside_outside(v, IN)


def complement(*v):
    """
     Builds an object Condition whose operator is 'not in'
    and the (right operand) is defined from the specified argument(s)

    :param v: a range, a set, a tuple or a list of integers
    :return: an object Condition
    """
    return _inside_outside(v, NOTIN)
