from enum import Enum, unique


# NB: This file is called ptypes because types is a reserved word in Python

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
    MINIMUM, MAXIMUM, MINIMUM_ARG, MAXIMUM_ARG, ELEMENT, CHANNEL, PERMUTATION, PRECEDENCE, PARTITION = auto(9)
    STRETCH, NO_OVERLAP, CUMULATIVE, BIN_PACKING, KNAPSACK, FLOW = auto(6)
    CIRCUIT, N_CIRCUITS, PATH, N_PATHS, TREE, N_TREES, ARBO, N_ARBOS, N_CLIQUES = auto(9)
    CLAUSE, INSTANTIATION = auto(2)
    AND, OR, NOT, XOR, IFF, IF_THEN, IF_THEN_ELSE = auto(7)
    SLIDE, SEQBIN = auto(2)
    MINIMIZE, MAXIMIZE = auto(2)  # used for posting objectives (not exactly constraints)
    SUBSET_ALL_DIFFERENT = auto(0)  # experimental

@unique
class TypeCtrArg(AbstractType):
    LIST, SET, MSET, MATRIX, SUBSETS = auto(5)
    FUNCTION, SUPPORTS, CONFLICTS = auto(3)
    EXCEPT, VALUE, VALUES, TOTAL, COEFFS, CONDITION = auto(6)
    COST, OPERATOR, NUMBER = auto(3)
    TRANSITIONS, START, FINAL, TERMINAL, RULES = auto(5)
    INDEX, RANK = auto(2)
    MAPPING = auto()
    OCCURS, ROW_OCCURS, COL_OCCURS = auto(3)
    WIDTHS, PATTERNS = auto(2)
    ORIGINS, LENGTHS, ENDS, HEIGHTS, MACHINES, CONDITIONS, LIMITS, LOADS, LIMIT = auto(9)
    SIZES, WEIGHTS, PROFITS, BALANCE, ARCS = auto(5)
    SIZE, ROOT, IMAGE, GRAPH, ROW, EXPRESSION, TYPE = auto(7)
    START_INDEX, START_ROW_INDEX, START_COL_INDEX = auto(3)
    COVERED = auto()
    INTENTION = auto()  # for slides directly posted


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


UTF_EQ = "\u003D"
UTF_NE = "\u2260"
UTF_LT = "\uFE64"  # ""\u227A"
UTF_LE = "\u2264"
UTF_GE = "\u2265"
UTF_GT = "\uFE65"  # "\u227B"
UTF_LTGT = "\u2276"
UTF_NOT_ELEMENT_OF = "\u00AC"  # ""\u2209"
UTF_COMPLEMENT = "\u2201"


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

    @staticmethod
    def to_utf(condition_operator):
        if condition_operator == TypeConditionOperator.LT:
            return UTF_LT
        if condition_operator == TypeConditionOperator.LE:
            return UTF_LE
        if condition_operator == TypeConditionOperator.GE:
            return UTF_GE
        if condition_operator == TypeConditionOperator.GT:
            return UTF_GT
        if condition_operator == TypeConditionOperator.EQ:
            return UTF_EQ
        if condition_operator == TypeConditionOperator.NE:
            return UTF_NE
        if condition_operator == TypeConditionOperator.NOTIN:
            return UTF_COMPLEMENT
        assert False

    def to_str(self):
        if self is TypeConditionOperator.LT:
            return "<"
        if self is TypeConditionOperator.LE:
            return "<="
        if self is TypeConditionOperator.GE:
            return ">="
        if self is TypeConditionOperator.GT:
            return ">"
        if self is TypeConditionOperator.EQ:
            return "="
        if self is TypeConditionOperator.NE:
            return "!="
        if self is TypeConditionOperator.IN:
            return "in"
        if self is TypeConditionOperator.NOTIN:
            return "not in"
        assert False

    def check(self, left_operand, right_operand):
        assert isinstance(left_operand, int)
        assert isinstance(right_operand, (tuple, list, set, frozenset)) if self in (TypeConditionOperator.IN, TypeConditionOperator.NOTIN) else isinstance(
            right_operand, int)
        if self is TypeConditionOperator.LT:
            return left_operand < right_operand
        if self is TypeConditionOperator.LE:
            return left_operand <= right_operand
        if self is TypeConditionOperator.GE:
            return left_operand >= right_operand
        if self is TypeConditionOperator.GT:
            return left_operand > right_operand
        if self is TypeConditionOperator.EQ:
            return left_operand == right_operand
        if self is TypeConditionOperator.NE:
            return left_operand != right_operand
        if self is TypeConditionOperator.IN:
            return left_operand in right_operand
        if self is TypeConditionOperator.NOTIN:
            return left_operand not in right_operand
        assert False


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

    def __str__(self):
        if self == TypeRank.FIRST:
            return "first"
        if self == TypeRank.LAST:
            return "last"
        return "any"


@unique
class TypeSolver(Enum):
    ACE, CHOCO = auto(2)


@unique
class TypeStatus(Enum):
    UNSAT, SAT, OPTIMUM, CORE, UNKNOWN = auto(5)

    def __str__(self):
        return self.name


@unique
class TypeSquareSymmetry(Enum):
    R90, R180, R270, FX, FY, FD1, FD2 = auto(7)  # R0 not indicated

    @staticmethod
    def rotations():
        return TypeSquareSymmetry.R9O, TypeSquareSymmetry.R18O, TypeSquareSymmetry.R270

    @staticmethod
    def reflections():  # 4 lines of symmetry (reflection)
        return TypeSquareSymmetry.FX, TypeSquareSymmetry.FY, TypeSquareSymmetry.FD1, TypeSquareSymmetry.FD2

    def is_rotation(self):
        return self in TypeSquareSymmetry.rotations()

    def is_reflection(self):
        return self in TypeSquareSymmetry.reflections()

    @staticmethod
    def symmetric_patterns(pattern):
        """
        Returns all symmetric patterns (including identity) of the specified one (can be useful for computing symmetric variants of polyominoes)

        :param pattern: a pattern given as a set of relative coordinates
        :return: all symmetric patterns of the specified one
        """

        def _normalize(p):
            minx, miny = min(i for i, _ in p), min(j for _, j in p)
            return tuple((i - minx, j - miny) for i, j in p) if minx != 0 or miny != 0 else tuple(p)

        pattern = _normalize(pattern)
        # computing the size of the square (so as to be able to produce symmetric patterns)
        n = max(max(i, j) for i, j in pattern) + 1  # +1 because starting at 0
        symmetries = [sym.apply_on(n) for sym in TypeSquareSymmetry]
        s1 = [tuple(sorted(pattern))] + [tuple(sorted(sym[i][j] for i, j in pattern)) for sym in symmetries]
        s2 = {_normalize(t) for t in s1}
        s3 = []
        for t in s2:
            assert min(i for i, _ in t) == 0
            gap = min(j for i, j in t if i == 0)
            s3.append(tuple((i, j - gap) for i, j in t))
        return s3  # [tuple(i * n + j for i, j in t) for t in s3]

    def apply_on(self, n):
        if not hasattr(TypeSquareSymmetry, '_cache'):
            TypeSquareSymmetry._cache = {}
        key = (self, n)
        if key not in TypeSquareSymmetry._cache:
            def rot(i, j):
                # if self is TypeSquareSymmetry.R0:
                #     return i, j
                if self is TypeSquareSymmetry.R90:
                    return j, n - 1 - i
                if self is TypeSquareSymmetry.R180:
                    return n - 1 - i, n - 1 - j
                if self is TypeSquareSymmetry.R270:
                    return n - 1 - j, i
                if self is TypeSquareSymmetry.FX:  # x flip
                    return n - 1 - i, j
                if self is TypeSquareSymmetry.FY:  # y flip
                    return i, n - 1 - j
                if self is TypeSquareSymmetry.FD1:  # d1 flip
                    return j, i
                assert self is TypeSquareSymmetry.FD2  # d2 flip
                return n - 1 - j, n - 1 - i

            TypeSquareSymmetry._cache[key] = [[rot(i, j) for j in range(n)] for i in range(n)]

        return TypeSquareSymmetry._cache[key]


@unique
class TypeRectangleSymmetry(Enum):
    R180, FX, FY = auto(3)  # R0 not indicated

    @staticmethod
    def rotations():
        return (TypeRectangleSymmetry.R18O,)

    @staticmethod
    def reflections():  # 2 lines of symmetry (reflection)
        return TypeRectangleSymmetry.FX, TypeRectangleSymmetry.FY

    def is_rotation(self):
        return self in TypeRectangleSymmetry.rotations()

    def is_reflection(self):
        return self in TypeRectangleSymmetry.reflections()

    def apply_on(self, n, m):
        if not hasattr(TypeRectangleSymmetry, '_cache'):
            TypeRectangleSymmetry._cache = {}
        key = (self, n)
        if key not in TypeRectangleSymmetry._cache:
            def rot(i, j):
                # if self is TypeRectangleSymmetry.R0:
                #     return i, j
                if self is TypeRectangleSymmetry.R180:  # not present in Minizinc models
                    return n - 1 - i, m - 1 - j
                if self is TypeRectangleSymmetry.FX:  # x flip
                    return n - 1 - i, j
                assert self is TypeRectangleSymmetry.FY  # y flip
                return i, m - 1 - j

            TypeRectangleSymmetry._cache[key] = [[rot(i, j) for j in range(m)] for i in range(n)]

        return TypeRectangleSymmetry._cache[key]


@unique
class TypeHexagonSymmetry(Enum):
    R60, R120, R180, R240, R300, L1, L2, L3, L4, L5, L6 = auto(11)  # R0 not included

    # _cache = {}  # not possible with enum (so, it is built dynamically in Method apply_on)

    @staticmethod
    def rotations():
        return (TypeHexagonSymmetry.R60, TypeHexagonSymmetry.R120,
                TypeHexagonSymmetry.R180, TypeHexagonSymmetry.R240, TypeHexagonSymmetry.R300)

    @staticmethod
    def reflections():  # 6 lines of symmetry (reflection)
        return (TypeHexagonSymmetry.L1, TypeHexagonSymmetry.L2, TypeHexagonSymmetry.L3,
                TypeHexagonSymmetry.L4, TypeHexagonSymmetry.L5, TypeHexagonSymmetry.L6)

    def is_rotation(self):
        return self in TypeHexagonSymmetry.rotations()

    def is_reflection(self):
        return self in TypeHexagonSymmetry.reflections()

    @staticmethod
    def ring_cells(ring):
        assert ring >= 2
        base = 2 * ring - 2
        return ([(0, j) for j in range(ring)]
                + [(i + 1, ring + i) for i in range(ring - 1)]
                + [(ring + i, base - i - 1) for i in range(ring - 1)]
                + [(base, ring - i - 2) for i in range(ring - 1)]
                + [(base - i - 1, 0) for i in range(base - 1)]
                )

    def apply_on(self, n):
        if not hasattr(TypeHexagonSymmetry, '_cache'):
            TypeHexagonSymmetry._cache = {}
        key = (self, n)
        if key not in TypeHexagonSymmetry._cache:
            w = 2 * n - 1  # maximal width
            widths = [w - abs(n - i - 1) for i in range(w)]
            rings = [[], [(0, 0)]] + [TypeHexagonSymmetry.ring_cells(ring) for ring in range(2, n + 1)]
            which_rings = [[n - min(i, w - 1 - i, j, widths[i] - 1 - j) for j in range(widths[i])] for i in range(w)]

            if self.is_rotation():
                def rot(i, j):
                    ring = which_rings[i][j]
                    skip = coeff * (ring - 1)
                    gap = n - ring
                    t = rings[ring]
                    idx = t.index((i - gap, j - gap))
                    k, l = t[(idx + skip) % len(t)]
                    return k + gap, l + gap

                coeff = 1 + TypeHexagonSymmetry.rotations().index(self)
                TypeHexagonSymmetry._cache[key] = [[rot(i, j) for j in range(widths[i])] for i in range(w)]
            else:
                def rot(i, j):
                    ring = which_rings[i][j]
                    center = (ring + 1) // 2 - 1
                    if self is TypeHexagonSymmetry.L1:
                        pivot, offset = (ring - 1, 0), 0
                    elif self is TypeHexagonSymmetry.L2:
                        pivot, offset = (center, 0), -1 if ring % 2 == 0 else 0
                    elif self is TypeHexagonSymmetry.L3:
                        pivot, offset = (0, 0), 0
                    elif self is TypeHexagonSymmetry.L4:
                        pivot, offset = (0, center), 1 if ring % 2 == 0 else 0
                    elif self is TypeHexagonSymmetry.L5:
                        pivot, offset = (0, ring - 1), 0
                    else:
                        assert self is TypeHexagonSymmetry.L6
                        pivot, offset = (center, ring - 1 + center), 1 if ring % 2 == 0 else 0
                    gap = n - ring
                    t = rings[ring]
                    ind_pivot = t.index(pivot)
                    ind_cell = t.index((i - gap, j - gap))
                    diff = abs(ind_pivot - ind_cell)
                    if ind_pivot <= ind_cell:  # pivot before
                        ind = ind_pivot - diff + offset
                    else:
                        ind = ind_pivot + diff + offset
                    k, l = t[(ind + len(t)) % len(t)]
                    return k + gap, l + gap

                TypeHexagonSymmetry._cache[key] = [[rot(i, j) for j in range(widths[i])] for i in range(w)]

        return TypeHexagonSymmetry._cache[key]
