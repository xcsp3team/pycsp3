from types import GeneratorType

from pycsp3.classes.auxiliary.ptypes import TypeConditionOperator
from pycsp3.classes.main.variables import Variable
from pycsp3.tools.inspector import checkType


class Condition:
    def __init__(self, operator):
        self.operator = operator

    @staticmethod
    def build_condition(condition):
        if condition is None:
            return None  # it may occur when building a partial constraint
        condition = tuple(condition) if isinstance(condition, list) else condition  # we expect a condition to be given as a tuple (or a list)
        assert isinstance(condition, tuple) and len(condition) == 2, "a condition must a pair, given as a tuple (or a list)"
        operator = TypeConditionOperator.value_of(condition[0]) if isinstance(condition[0], str) else condition[0]
        assert isinstance(operator, TypeConditionOperator), "the operator " + str(operator) + " is not correct (should be of type TypeConditionOperator)"
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

    def right_operand(self):
        pass

    def __str__(self):
        return "(" + str(self.operator) + "," + str(self.right_operand()) + ")"


class ConditionValue(Condition):
    def __init__(self, operator, value):
        super().__init__(operator)
        self.value = value

    def right_operand(self):
        return self.value

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


class ConditionVariable(Condition):
    def __init__(self, operator, variable):
        super().__init__(operator)
        self.variable = variable

    def right_operand(self):
        return self.variable


class ConditionInterval(Condition):
    def __init__(self, operator, min, max):
        super().__init__(operator)
        self.min = min
        self.max = max

    def right_operand(self):
        return str(self.min) + ".." + str(self.max)


class ConditionSet(Condition):
    def __init__(self, operator, t):
        super().__init__(operator)
        self.t = t

    def right_operand(self):
        return "{" + ",".join(str(v) for v in self.t) + "}"


def ne(v):
    return ConditionValue(TypeConditionOperator.NE, v)
