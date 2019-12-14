from pycsp3.classes.auxiliary.types import TypeCtr, TypeCtrArg
from pycsp3.classes.main.constraints import Constraint


class Objective(Constraint):
    def __init__(self, way):
        assert way in {TypeCtr.MINIMIZE, TypeCtr.MAXIMIZE}
        super().__init__(way)

    def close_to(self, other):
        return False


class ObjectiveExpression(Objective):
    def __init__(self, way, expression):
        super().__init__(way)
        self.arg(TypeCtrArg.EXPRESSION, expression)


class ObjectivePartial(Objective):
    def __init__(self, way, partial):
        super().__init__(way)
        self.attributes.append((TypeCtrArg.TYPE, partial.constraint.name))
        self.arguments = partial.constraint.arguments
