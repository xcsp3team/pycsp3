from enum import Enum, unique


def auto(n_occurrences=1):
    def _auto():  # To be replaced by auto() in python 3.6 ?
        if not hasattr(auto, "cnt"):
            auto.cnt = 0
        auto.cnt += 1
        return auto.cnt

    return _auto() if n_occurrences == 1 else (_auto() for _ in range(n_occurrences))


@unique
class TypeFramework(Enum):
    CSP, COP = auto(2)

    def __str__(self):
        return self.name


class AbstractType(Enum):
    def __str__(self):
        if hasattr(self, 'ccname'):  # camel case name
            return self.ccname
        t = self.name.split("_")
        self.ccname = t[0].lower() + ''.join(t[i][0] + t[i][1:].lower() for i in range(1, len(t)))
        return self.ccname


@unique
class TypeVar(AbstractType):
    INTEGER, SYMBOLIC, REAL = auto(3)
    STOCHASTIC, SYMBOLIC_STOCHASTIC = auto(2)
    SET, SYMBOLIC_SET = auto(2)
    UNDIRECTED_GRAPH, DIRECTED_GRAPH = auto(2)
    POINT, INTERVAL, REGION = auto(3)

    def is_basic(self):
        return self in {TypeVar.INTEGER, TypeVar.SYMBOLIC, TypeVar.REAL} or self.is_stochastic()

    def is_stochastic(self):
        return self in {TypeVar.STOCHASTIC, TypeVar.SYMBOLIC_STOCHASTIC}

    def is_set(self):
        return self in {TypeVar.SET, TypeVar.SYMBOLIC_SET}

    def is_graph(self):
        return self in {TypeVar.UNDIRECTED_GRAPH, TypeVar.DIRECTED_GRAPH}

    def is_qualitative(self):
        return self in {TypeVar.POINT, TypeVar.INTERVAL, TypeVar.REGION}


@unique
class TypeCtr(AbstractType):
    EXTENSION, INTENSION, SMART = auto(3)
    REGULAR, GRAMMAR, MDD = auto(3)
    ALL_DIFFERENT, ALL_EQUAL, ALL_DISTANT, ORDERED, LEX, ALL_INTERSECTING = auto(6)
    SUM, COUNT, N_VALUES, CARDINALITY, BALANCE, SPREAD, DEVIATION, SUM_COSTS, RANGE, ROOTS = auto(10)
    MINIMUM, MAXIMUM, ELEMENT, CHANNEL, PERMUTATION, PRECEDENCE, PARTITION = auto(7)
    STRETCH, NO_OVERLAP, CUMULATIVE, BIN_PACKING, KNAPSACK, NETWORK_FLOW = auto(6)
    CIRCUIT, N_CIRCUITS, PATH, N_PATHS, TREE, N_TREES, ARBO, N_ARBOS, N_CLIQUES = auto(9)
    CLAUSE, INSTANTIATION = auto(2)
    AND, OR, NOT, IFF, IF_THEN, IF_THEN_ELSE = auto(6)
    SLIDE, SEQBIN = auto(2)
    MINIMIZE, MAXIMIZE = auto(2)  # used for posting objectives (not exactly constraints)


@unique
class TypeCtrArg(AbstractType):
    LIST, SET, MSET, MATRIX = auto(4)
    FUNCTION, SUPPORTS, CONFLICTS = auto(3)
    EXCEPT, VALUE, VALUES, TOTAL, COEFFS, CONDITION = auto(6)
    COST, OPERATOR, NUMBER = auto(3)
    TRANSITIONS, START, FINAL, TERMINAL, RULES = auto(5)
    INDEX = auto()
    MAPPING = auto()
    OCCURS, ROW_OCCURS, COL_OCCURS = auto(3)
    WIDTHS, PATTERNS = auto(2)
    ORIGINS, LENGTHS, ENDS, HEIGHTS, MACHINES, CONDITIONS = auto(6)
    SIZES, WEIGTHS, PROFITS = auto(3)
    SIZE, ROOT, IMAGE, GRAPH, ROW, EXPRESSION, TYPE = auto(7)
    START_INDEX, START_ROW_INDEX, START_COL_INDEX = auto(3)


@unique
class TypeXML(AbstractType):
    FORMAT, TYPE, ID, CLASS = auto(4)
    NOTE, AS, SIZE = auto(3)
    VIOLATION_MEASURE, VIOLATION_PARAMETERS, DEFAULT_COST, VIOLATION_COST, COST = auto(5)
    REIFIED_BY, HREIFIED_FROM, HREIFIED_TO = auto(3)
    CLOSED, FOR, RESTRICTION, RANK = auto(4)
    START_INDEX, ZERO_IGNORED, CASE, ORDER, CIRCULAR, OFFSET, COLLECT, VIOLABLE = auto(8)
    LB, UB, COMBINATION = auto(3)
    INSTANCE = auto()
    VARIABLES, VAR, ARRAY, DOMAIN, REQUIRED, POSSIBLE = auto(6)
    CONSTRAINTS, BLOCK, GROUP, ARGS = auto(4)
    OBJECTIVES, OBJECTIVE, MINIMIZE, MAXIMIZE = auto(4)
    SOFT = auto()
    ANNOTATIONS, DECISION, OUTPUT, VAR_HEURISTIC, VAL_HEURISTIC, PREPRO, SEARCH, RESTARTS, FILTERING = auto(9)


@unique
class TypeConditionOperator(AbstractType):
    LT, LE, GE, GT, EQ, NE, IN, NOTIN = auto(8)

    @staticmethod
    def value_of(s):
        assert isinstance(s, str)
        try:
            return TypeConditionOperator[s.upper()]
        except KeyError:
            if s == "<":
                return TypeConditionOperator.LT
            if s == "<=":
                return TypeConditionOperator.LE
            if s == ">=":
                return TypeConditionOperator.GE
            if s == ">":
                return TypeConditionOperator.GT
            if s in {"=", "=="}:
                return TypeConditionOperator.EQ
            if s == "!=":
                return TypeConditionOperator.NE
        raise ValueError


@unique
class TypeOrderedOperator(Enum):
    STRICTLY_INCREASING, INCREASING, DECREASING, STRICTLY_DECREASING = auto(4)

    def __str__(self):
        if self == TypeOrderedOperator.STRICTLY_INCREASING:
            return "lt"
        if self == TypeOrderedOperator.INCREASING:
            return "le"
        if self == TypeOrderedOperator.DECREASING:
            return "ge"
        assert self == TypeOrderedOperator.STRICTLY_DECREASING
        return "gt"


@unique
class TypeRank(Enum):
    FIRST, LAST, ANY = auto(3)
