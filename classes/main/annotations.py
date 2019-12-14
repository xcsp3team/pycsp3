import re
from enum import unique

from pycsp3.classes.auxiliary.types import auto, AbstractType, TypeXML
from pycsp3.classes.main.constraints import ConstraintUnmergeable
from pycsp3.classes.main.variables import Variable
from pycsp3.tools.inspector import checkType
from pycsp3.tools.utilities import flatten


@unique
class TypeVarHeuristic(AbstractType):
    LEXICO, DOM, DEG, DDEG, WDEG, IMPACT, ACTIVITY = (auto() for _ in range(7))


@unique
class TypeValHeuristic(AbstractType):
    CONFLICTS, VALUE = auto(), auto()


@unique
class TypeConsistency(AbstractType):
    FC, BC, AC, SAC, FPWC, PC, CDC, FDAC, EDAC, VAC = (auto() for _ in range(10))

    def __str__(self):
        return super().__str__().upper()


@unique
class TypeBranching(AbstractType):
    TWO_WAY, D_WAY = auto(), auto()

    def __str__(self):
        return self.name.replace("_", "-").replace("TWO", "2").lower()


@unique
class TypeRestart(AbstractType):
    LUBY, GEOMETRIC = auto(), auto()


@unique
class TypeArg(AbstractType):
    TYPE = auto()
    STATIC, RANDOM, MIN, MAX = (auto() for _ in range(4))
    LC = auto()
    ORDER = auto()
    CONSISTENCY, BRANCHING, CUTOFF, FACTOR = (auto() for _ in range(4))
    START_INDEX, START_ROW_INDEX, START_COL_INDEX = (auto() for _ in range(3))


class AnnotationDecision(ConstraintUnmergeable):
    def __init__(self, variables):
        super().__init__(TypeXML.DECISION)
        variables = flatten(variables)
        checkType(variables, allowedTypes=([Variable]))
        self.arg(TypeXML.DECISION, variables)


class AnnotationOutput(ConstraintUnmergeable):
    def __init__(self, variables):
        super().__init__(TypeXML.OUTPUT)
        variables = flatten(variables)
        checkType(variables, allowedTypes=([Variable]))
        self.arg(TypeXML.OUTPUT, variables)


class AnnotationHeuristic(ConstraintUnmergeable):
    def __init__(self, name):
        super().__init__(name)

    # To keep the good order
    def add_arguments(self, random_part, min_part, max_part):
        if random_part:
            self.arg(TypeArg.RANDOM, random_part[0] if random_part[0] else [None])
        if min_part:
            self.arg(TypeArg.MIN, min_part[0] if min_part[0] else [None], attributes=[(TypeArg.TYPE, min_part[1])])
        if max_part:
            self.arg(TypeArg.MAX, max_part[0] if max_part[0] else [None], attributes=[(TypeArg.TYPE, max_part[1])])


class AnnotationVarHeuristic(AnnotationHeuristic):
    def __init__(self, h):
        super().__init__(TypeXML.VAR_HEURISTIC)
        checkType(h, allowedTypes=VarHeuristic)
        self.attributes.append((TypeArg.LC, h.lc))
        if h.staticData:
            self.arg(TypeArg.STATIC, h.staticData)
        self.add_arguments(h.randomPart, h.minPart, h.maxPart)


class AnnotationValHeuristic(AnnotationHeuristic):
    def __init__(self, h):
        super().__init__(TypeXML.VAL_HEURISTIC)
        checkType(h, allowedTypes=ValHeuristic)
        if h.staticData:
            self.arg(TypeArg.STATIC, h.staticData[0], attributes=[(TypeArg.ORDER, " ".join(str(ele) for ele in h.staticData[1]))])
        self.add_arguments(h.randomData, h.minData, h.maxData)


class AnnotationFiltering(ConstraintUnmergeable):
    def __init__(self, consistency):
        super().__init__(TypeXML.FILTERING)
        checkType(consistency, allowedTypes=TypeConsistency)
        self.attributes.append((TypeArg.TYPE, consistency))


class AnnotationPrepro(ConstraintUnmergeable):
    def __init__(self, consistency):
        super().__init__(TypeXML.PREPRO)
        checkType(consistency, allowedTypes=TypeConsistency)
        self.attributes.append((TypeArg.CONSISTENCY, consistency))


class AnnotationSearch(ConstraintUnmergeable):
    def __init__(self, search):
        super().__init__(TypeXML.SEARCH)
        checkType(search, allowedTypes=Search)
        self.attributes = [(TypeArg.CONSISTENCY, search.consistency), (TypeArg.BRANCHING, search.branching)]


class AnnotationRestarts(ConstraintUnmergeable):
    def __init__(self, restarts):
        super().__init__(TypeXML.RESTARTS)
        checkType(restarts, allowedTypes=Restarts)
        self.attributes = [(TypeArg.TYPE, restarts.type), (TypeArg.CUTOFF, restarts.cutoff), (TypeArg.FACTOR, restarts.factor)]


''' Annotations classes '''


class Search:
    def __init__(self, *, consistency=None, branching=None):
        assert consistency or branching
        assert isinstance(consistency, (TypeConsistency, type(None))) and isinstance(branching, (TypeBranching, type(None)))
        self.consistency = consistency
        self.branching = branching


class Restarts:
    def __init__(self, *, type, cutoff, factor=1):
        assert isinstance(type, TypeRestart) and isinstance(cutoff, int) and isinstance(factor, float)
        self.type = type
        self.cutoff = cutoff
        self.factor = factor


class VHeuristic:
    def __init__(self):
        self.staticPart = None
        self.randomPart = None
        self.minPart = None
        self.maxPart = None

    def random(self, variables=None):
        variables = flatten(variables)
        checkType(variables, allowedTypes=([Variable], type(None)))
        self.randomPart = (variables,)
        return self

    def _opt(self, variables, type):
        if variables:
            variables = flatten(variables)
            checkType(variables, allowedTypes=([Variable]))
        types = TypeVarHeuristic if isinstance(self, VarHeuristic) else TypeValHeuristic
        assert isinstance(type, str) and all(p in [t.name for t in types] for p in re.split(r'/|\+', type)), "Bad value for " + type
        return variables, type

    def min(self, variables=None, *, type):
        self.minPart = self._opt(variables, type)
        return self

    def max(self, variables=None, *, type):
        self.maxPart = self._opt(variables, type)
        return self


class VarHeuristic(VHeuristic):
    def __init__(self, *, lc=None):
        super().__init__()
        self.lc = lc

    def static(self, variables):
        variables = flatten(variables)
        checkType(variables, allowedTypes=([Variable]))
        self.staticPart = variables
        return self


class ValHeuristic(VHeuristic):
    def __init__(self):
        super().__init__()

    def static(self, variables, *, order):
        variables = flatten(variables)
        checkType(variables, allowedTypes=([Variable]))
        order = flatten(order)
        checkType(order, allowedTypes=([int]))
        self.staticPart = (variables, order)
        return self
