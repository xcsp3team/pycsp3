import re
from enum import unique

from pycsp3.classes.auxiliary.enums import auto, AbstractType, TypeAnn
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
        super().__init__(TypeAnn.DECISION)
        variables = flatten(variables)
        checkType(variables, [Variable])
        self.arg(TypeAnn.DECISION, variables)


class AnnotationOutput(Annotation):
    def __init__(self, variables):
        super().__init__(TypeAnn.OUTPUT)
        variables = flatten(variables)
        checkType(variables, [Variable])
        self.arg(TypeAnn.OUTPUT, variables)


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
        super().__init__(TypeAnn.VAR_HEURISTIC)
        checkType(h, VarHeuristic)
        if h.lc is not None:  # otherwise, the attribute would be written as lc="None"
            self.attributes.append((TypeAnnArg.LC, h.lc))
        if h.staticParts:
            self.arg(TypeAnnArg.STATIC, h.staticParts[0])
        self.add_arguments(h.randomPart, h.minPart, h.maxPart)


class AnnotationValHeuristic(AnnotationHeuristic):
    def __init__(self, h):
        super().__init__(TypeAnn.VAL_HEURISTIC)
        checkType(h, ValHeuristic)
        if h.staticParts:
            self.arg(TypeAnnArg.STATICS, h.staticParts)
            # for k,v in h.staticParts:
            #     self.arg(TypeAnnArg.STATIC, k, attributes=[(TypeAnnArg.ORDER, " ".join(str(ele) for ele in v))])
        self.add_arguments(h.randomPart, h.minPart, h.maxPart)


class AnnotationFiltering(Annotation):
    def __init__(self, consistency):
        super().__init__(TypeAnn.FILTERING)
        checkType(consistency, TypeConsistency)
        self.attributes.append((TypeAnnArg.TYPE, consistency))


class AnnotationPrepro(Annotation):
    def __init__(self, consistency):
        super().__init__(TypeAnn.PREPRO)
        checkType(consistency, TypeConsistency)
        self.attributes.append((TypeAnnArg.CONSISTENCY, consistency))


class AnnotationSearch(Annotation):
    def __init__(self, search):
        super().__init__(TypeAnn.SEARCH)
        checkType(search, Search)
        self.attributes = [(TypeAnnArg.CONSISTENCY, search.consistency), (TypeAnnArg.BRANCHING, search.branching)]


class AnnotationRestarts(Annotation):
    def __init__(self, restarts):
        super().__init__(TypeAnn.RESTARTS)
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
    def __init__(self, *, r_type, cutoff, factor=1):
        assert isinstance(type, TypeRestart) and isinstance(cutoff, int) and isinstance(factor, float)
        self.type = r_type
        self.cutoff = cutoff
        self.factor = factor


class VHeuristic:
    """
    The base class of the annotations about heuristics, VarHeuristic and ValHeuristic.
    Its methods random(), min() and max() are shared by both, and return the heuristic itself, so that calls can be chained.

    :example:
        from pycsp3.classes.main.annotations import VarHeuristic

        x = VarArray(size=5, dom=range(5))

        satisfy(
           AllDifferent(x)
        )

        # x[0] is selected first, and then the other variables are selected randomly
        annotate(varHeuristic=VarHeuristic().static(x[0]).random(x[1:]))
    """

    def __init__(self):
        self.staticParts = []
        self.randomPart = None
        self.minPart = None
        self.maxPart = None

    def random(self, variables=None):
        """
        Specifies that choices are made randomly for the specified variables (or for all variables if None):
        the next variable is selected randomly (VarHeuristic), or the next value to be assigned is selected randomly (ValHeuristic).

        :param variables: a list of variables, or None
        :return: this heuristic, so that calls can be chained
        :example:
            from pycsp3.classes.main.annotations import VarHeuristic

            x = VarArray(size=5, dom=range(5))

            satisfy(
               AllDifferent(x)
            )

            # the variables of x are selected randomly
            annotate(varHeuristic=VarHeuristic().random(x))
        """
        variables = flatten(variables)
        checkType(variables, ([Variable], type(None)))
        self.randomPart = (variables,)
        return self

    def _opt(self, variables, h_type):
        if variables:
            variables = flatten(variables)
            checkType(variables, [Variable])
        types = TypeVarHeuristic if isinstance(self, VarHeuristic) else TypeValHeuristic
        assert isinstance(h_type, str) and all(p in [t.name for t in types] for p in re.split(r'/|\+', h_type)), "Bad value for " + str(h_type)
        return variables, h_type

    def min(self, variables=None, *, h_type):
        """
        Specifies that the choice minimizing the specified criterion is made, for the specified variables (or for all variables if None).
        Criteria are named after TypeVarHeuristic (LEXICO, DOM, DEG, DDEG, WDEG, IMPACT, ACTIVITY) for a VarHeuristic,
        and after TypeValHeuristic (CONFLICTS, VALUE) for a ValHeuristic; they can be combined with the symbols / and +, as in "DOM/WDEG".

        :param variables: a list of variables, or None
        :param h_type: the criterion to be minimized
        :return: this heuristic, so that calls can be chained
        :example:
            from pycsp3.classes.main.annotations import VarHeuristic

            x = VarArray(size=5, dom=range(5))

            satisfy(
               AllDifferent(x)
            )

            # the variable with the smallest ratio of its domain size to its weighted degree is selected
            annotate(varHeuristic=VarHeuristic().min(x, h_type="DOM/WDEG"))
        """
        self.minPart = self._opt(variables, h_type)
        return self

    def max(self, variables=None, *, h_type):
        """
        Specifies that the choice maximizing the specified criterion is made, for the specified variables (or for all variables if None).
        Criteria are named after TypeVarHeuristic (LEXICO, DOM, DEG, DDEG, WDEG, IMPACT, ACTIVITY) for a VarHeuristic,
        and after TypeValHeuristic (CONFLICTS, VALUE) for a ValHeuristic; they can be combined with the symbols / and +, as in "DOM/WDEG".

        :param variables: a list of variables, or None
        :param h_type: the criterion to be maximized
        :return: this heuristic, so that calls can be chained
        :example:
            from pycsp3.classes.main.annotations import VarHeuristic

            x = VarArray(size=5, dom=range(5))

            satisfy(
               AllDifferent(x)
            )

            # the variable with the greatest degree is selected
            annotate(varHeuristic=VarHeuristic().max(x, h_type="DEG"))
        """
        self.maxPart = self._opt(variables, h_type)
        return self


class VarHeuristic(VHeuristic):
    """
    An annotation about the variable ordering heuristic, to be given to annotate() with the parameter varHeuristic.
    The heuristic is specified by chaining calls to static(), random(), min() and max().

    :example:
        from pycsp3.classes.main.annotations import VarHeuristic

        x = VarArray(size=5, dom=range(5))
        y = VarArray(size=5, dom=range(5))

        satisfy(
           AllDifferent(x),
           AllDifferent(y)
        )

        # the variables of x are selected first; then, the variable of y with the smallest ratio dom/wdeg is selected
        annotate(varHeuristic=VarHeuristic().static(x).min(y, h_type="DOM/WDEG"))
    """

    def __init__(self, *, lc=None):
        """
        Builds an annotation about the variable ordering heuristic.

        :param lc: the level of last-conflict reasoning, or None
        """
        super().__init__()
        self.lc = lc

    def static(self, variables):
        """
        Specifies that the specified variables are selected first, in the order they are given.

        :param variables: a list of variables
        :return: this heuristic, so that calls can be chained
        :example:
            from pycsp3.classes.main.annotations import VarHeuristic

            x = VarArray(size=5, dom=range(5))

            satisfy(
               AllDifferent(x)
            )

            # the variables of x are selected from the last one to the first one
            annotate(varHeuristic=VarHeuristic().static(reversed(x)))
        """
        variables = flatten(variables)
        checkType(variables, [Variable])
        self.staticParts.append(variables)
        return self


class ValHeuristic(VHeuristic):
    """
    An annotation about the value ordering heuristic, to be given to annotate() with the parameter valHeuristic.
    The heuristic is specified by chaining calls to static(), random(), min() and max().

    :example:
        from pycsp3.classes.main.annotations import ValHeuristic

        x = VarArray(size=5, dom=range(5))

        satisfy(
           AllDifferent(x)
        )

        # the values of the variables of x are tried from the greatest one to the smallest one
        annotate(valHeuristic=ValHeuristic().static(x, order=[4, 3, 2, 1, 0]))
    """

    def __init__(self):
        super().__init__()

    def static(self, variables, *, order):
        """
        Specifies that the values of the specified variables are tried in the specified order.

        :param variables: a list of variables
        :param order: the list of values, in the order they must be tried
        :return: this heuristic, so that calls can be chained
        :example:
            from pycsp3.classes.main.annotations import ValHeuristic

            x = VarArray(size=5, dom=range(5))

            satisfy(
               AllDifferent(x)
            )

            # for the variables of x, the value 0 is tried last
            annotate(valHeuristic=ValHeuristic().static(x, order=[1, 2, 3, 4, 0]))
        """
        variables = flatten(variables)
        checkType(variables, [Variable])
        order = flatten(order)
        checkType(order, [int])
        self.staticParts.append((variables, order))
        return self
