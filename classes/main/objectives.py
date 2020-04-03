from pycsp3.classes.auxiliary.ptypes import TypeCtr, TypeCtrArg
from pycsp3.classes.main.constraints import ConstraintUnmergeable


class Objective(ConstraintUnmergeable):
    def __init__(self, way):
        assert way in {TypeCtr.MINIMIZE, TypeCtr.MAXIMIZE}
        super().__init__(way)


class ObjectiveExpression(Objective):
    def __init__(self, way, expression):
        super().__init__(way)
        self.arg(TypeCtrArg.EXPRESSION, expression)


class ObjectivePartial(Objective):
    def __init__(self, way, partial):
        super().__init__(way)
        self.attributes.append((TypeCtrArg.TYPE, partial.constraint.name))
        self.arguments = partial.constraint.arguments
