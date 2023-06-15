import re
from enum import unique

from pycsp3.classes.auxiliary.ptypes import auto, AbstractType, TypeXML
from pycsp3.classes.main.constraints import ConstraintUnmergeable
from pycsp3.classes.main.variables import Variable
from pycsp3.tools.inspector import checkType
from pycsp3.tools.utilities import flatten


@unique
class TypeVarHeuristic(AbstractType):
    LEXICO, DOM, DEG, DDEG, WDEG, IMPACT, ACTIVITY = auto(7)


@unique
class TypeValHeuristic(AbstractType):
    CONFLICTS, VALUE = auto(2)


@unique
class TypeConsistency(AbstractType):
    FC, BC, AC, SAC, FPWC, PC, CDC, FDAC, EDAC, VAC = auto(10)

    def __str__(self):
        return self.name


@unique
class TypeBranching(AbstractType):
    TWO_WAY, D_WAY = auto(2)

    def __str__(self):
        return self.name.replace("_", "-").replace("TWO", "2").lower()


@unique
class TypeRestart(AbstractType):
    LUBY, GEOMETRIC = auto(2)


@unique
class TypeAnnArg(AbstractType):
    TYPE = auto()
    STATIC, STATICS, RANDOM, MIN, MAX = auto(5)
    LC = auto()
    ORDER = auto()
    CONSISTENCY, BRANCHING, CUTOFF, FACTOR = auto(4)
    START_INDEX, START_ROW_INDEX, START_COL_INDEX = auto(3)


class Annotation(ConstraintUnmergeable):
    pass


class AnnotationDecision(Annotation):
    def __init__(self, variables):
        super().__init__(TypeXML.DECISION)
        variables = flatten(variables)
        checkType(variables, [Variable])
        self.arg(TypeXML.DECISION, variables)


class AnnotationOutput(Annotation):
    def __init__(self, variables):
        super().__init__(TypeXML.OUTPUT)
        variables = flatten(variables)
        checkType(variables, [Variable])
        self.arg(TypeXML.OUTPUT, variables)


class AnnotationHeuristic(Annotation):
    def __init__(self, name):
        super().__init__(name)

    # To keep the good order
    def add_arguments(self, random_part, min_part, max_part):
        if random_part:
            self.arg(TypeAnnArg.RANDOM, random_part[0] if random_part[0] else [None])
        if min_part:
            self.arg(TypeAnnArg.MIN, min_part[0] if min_part[0] else [None], attributes=[(TypeAnnArg.TYPE, min_part[1])])
        if max_part:
            self.arg(TypeAnnArg.MAX, max_part[0] if max_part[0] else [None], attributes=[(TypeAnnArg.TYPE, max_part[1])])


class AnnotationVarHeuristic(AnnotationHeuristic):
    def __init__(self, h):
        super().__init__(TypeXML.VAR_HEURISTIC)
        checkType(h, VarHeuristic)
        self.attributes.append((TypeAnnArg.LC, h.lc))
        if h.staticParts:
            self.arg(TypeAnnArg.STATIC, h.staticParts[0])
        self.add_arguments(h.randomPart, h.minPart, h.maxPart)


class AnnotationValHeuristic(AnnotationHeuristic):
    def __init__(self, h):
        super().__init__(TypeXML.VAL_HEURISTIC)
        checkType(h, ValHeuristic)
        if h.staticParts:
            self.arg(TypeAnnArg.STATICS, h.staticParts)
            # for k,v in h.staticParts:
            #     self.arg(TypeAnnArg.STATIC, k, attributes=[(TypeAnnArg.ORDER, " ".join(str(ele) for ele in v))])
        self.add_arguments(h.randomPart, h.minPart, h.maxPart)


class AnnotationFiltering(Annotation):
    def __init__(self, consistency):
        super().__init__(TypeXML.FILTERING)
        checkType(consistency, TypeConsistency)
        self.attributes.append((TypeAnnArg.TYPE, consistency))


class AnnotationPrepro(Annotation):
    def __init__(self, consistency):
        super().__init__(TypeXML.PREPRO)
        checkType(consistency, TypeConsistency)
        self.attributes.append((TypeAnnArg.CONSISTENCY, consistency))


class AnnotationSearch(Annotation):
    def __init__(self, search):
        super().__init__(TypeXML.SEARCH)
        checkType(search, Search)
        self.attributes = [(TypeAnnArg.CONSISTENCY, search.consistency), (TypeAnnArg.BRANCHING, search.branching)]


class AnnotationRestarts(Annotation):
    def __init__(self, restarts):
        super().__init__(TypeXML.RESTARTS)
        checkType(restarts, Restarts)
        self.attributes = [(TypeAnnArg.TYPE, restarts.type), (TypeAnnArg.CUTOFF, restarts.cutoff), (TypeAnnArg.FACTOR, restarts.factor)]


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
        self.staticParts = []
        self.randomPart = None
        self.minPart = None
        self.maxPart = None

    def random(self, variables=None):
        variables = flatten(variables)
        checkType(variables, ([Variable], type(None)))
        self.randomPart = (variables,)
        return self

    def _opt(self, variables, type):
        if variables:
            variables = flatten(variables)
            checkType(variables, [Variable])
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
        checkType(variables, [Variable])
        self.staticParts.append(variables)
        return self


class ValHeuristic(VHeuristic):
    def __init__(self):
        super().__init__()

    def static(self, variables, *, order):
        variables = flatten(variables)
        checkType(variables, [Variable])
        order = flatten(order)
        checkType(order, [int])
        self.staticParts.append((variables, order))
        return self
