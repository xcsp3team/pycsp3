from types import GeneratorType
from functools import total_ordering

from pycsp3.classes.auxiliary.ptypes import TypeConditionOperator
from pycsp3.classes.main.variables import Variable
from pycsp3.tools.inspector import checkType
from pycsp3.tools.utilities import is_1d_list, is_1d_tuple, ANY

UTF_NE = "\u2260"
UTF_LT = "\uFE64"  # ""\u227A"
UTF_LE = "\u2264"
UTF_GE = "\u2265"
UTF_GT = "\uFE65"  # "\u227B"
UTF_LTGT = "\u2276"
UTF_NOT_ELEMENT_OF = "\u00AC"  # ""\u2209"
UTF_COMPLEMENT = "\u2201"

@total_ordering
class Condition:
    def __init__(self, operator):
        self.operator = operator
        assert isinstance(operator, TypeConditionOperator), "the operator " + str(operator) + " is not correct (should be of type TypeConditionOperator)"

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

    def __str__(self):
        return "(" + str(self.operator) + "," + str(self.right_operand()) + ")"


class ConditionValue(Condition):
    def __init__(self, operator, value):
        super().__init__(operator)
        self.value = value

    def _key(self):
        return super()._key() + (self.value,)

    def filtering(self, values):
        if self.operator == TypeConditionOperator.NE:
            return (v for v in values if v != self.value)
        if self.operator == TypeConditionOperator.LT:
            return (v for v in values if v < self.value)
        if self.operator == TypeConditionOperator.LE:
            return (v for v in values if v <= self.value)
        if self.operator == TypeConditionOperator.GE:
            return (v for v in values if v >= self.value)
        if self.operator == TypeConditionOperator.GT:
            return (v for v in values if v > self.value)
        assert False

    def str_tuple(self):
        if self.operator == TypeConditionOperator.NE:
            return UTF_NE + str(self.value)
        if self.operator == TypeConditionOperator.LT:
            return UTF_LE + str(self.value - 1) if isinstance(self.value, int) else UTF_LT + str(self.value)
        if self.operator == TypeConditionOperator.LE:
            return UTF_LE + str(self.value)
        if self.operator == TypeConditionOperator.GE:
            return UTF_GE + str(self.value)
        if self.operator == TypeConditionOperator.GT:
            return UTF_GE + str(self.value + 1) if isinstance(self.value, int) else UTF_GT + str(self.value)
        assert False
    
    def __repr__(self):
        return self.str_tuple()

    def right_operand(self):
        return self.value


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
        if self.operator == TypeConditionOperator.IN:
            return (v for v in values if self.min <= v <= self.max)
        if self.operator == TypeConditionOperator.NOTIN:
            return (v for v in values if v < self.min or self.max < v)
        assert False

    def str_tuple(self):
        if self.operator == TypeConditionOperator.IN:
            return self.right_operand()
        if self.operator == TypeConditionOperator.NOTIN:
            return UTF_COMPLEMENT + self.right_operand()
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
        if self.operator == TypeConditionOperator.IN:
            return (v for v in values if v in self.t)
        if self.operator == TypeConditionOperator.NOTIN:
            return (v for v in values if v not in self.t)
        assert False

    def str_tuple(self):
        if self.operator == TypeConditionOperator.IN:
            return self.right_operand()
        if self.operator == TypeConditionOperator.NOTIN:
            return UTF_COMPLEMENT + self.right_operand()
        assert False

    def right_operand(self):
        return "{" + ",".join(str(v) for v in self.t) + "}"


def ne(v):
    return ConditionValue(TypeConditionOperator.NE, v)


def lt(v):
    return ConditionValue(TypeConditionOperator.LT, v)


def le(v):
    return ConditionValue(TypeConditionOperator.LE, v)


def ge(v):
    return ConditionValue(TypeConditionOperator.GE, v)


def gt(v):
    return ConditionValue(TypeConditionOperator.GT, v)


def _inside_outside(v, op):
    v = v if len(v) > 1 else v[0]
    if isinstance(v, range):
        return ConditionInterval(op, v.start, v.stop - 1)
    if isinstance(v, set):
        return ConditionSet(op, v)
    assert is_1d_list(v, int) or is_1d_tuple(v, int)
    return ConditionSet(op, set(v))


def inside(*v):
    return _inside_outside(v, TypeConditionOperator.IN)


def complement(*v):
    return _inside_outside(v, TypeConditionOperator.NOTIN)
