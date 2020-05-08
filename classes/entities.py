import types
# import itertools
import numpy
import re

from enum import Enum, unique
from functools import reduce
from itertools import product

from pycsp3.classes.auxiliary.ptypes import auto
from pycsp3.classes.main.variables import Variable, NotVariable, NegVariable
from pycsp3.classes import main
from pycsp3.dashboard import options
from pycsp3.tools.utilities import flatten, is_containing
from pycsp3.tools.inspector import checkType


class Entity:
    def __init__(self, name, comment=None, tags=[]):
        self.id = name
        self.comment = None
        self.note(comment)  # we use comment instead of note because we need method note()
        self.tags = []
        self.tag(tags)

    def note(self, comment):
        if comment is not None and comment.strip() != "":
            self.comment = comment.strip() if self.comment is None else self.comment + " - " + comment.strip()
        return self

    def tag(self, tags):
        if tags is not None:
            toks = (tok.strip() for tok in tags.strip().split(" ")) if isinstance(tags, str) else (tok.strip() for tok in tags)
            self.tags.extend([tok for tok in toks if tok != "" and tok not in self.tags])
        return self

    def same_type_and_basic_attributes(self, other):
        return type(self) == type(other) and self.comment == other.comment and self.tags == other.tags

    def mergeable_with(self, other):
        return (type(self) == type(other) and (self.comment == other.comment or None in {self.comment, other.comment})
                and (self.tags == other.tags or 0 in {len(self.tags), len(other.tags)}))

    def blank_basic_attributes(self):
        return self.comment is None and self.tags == []

    def clear_basic_attributes(self):
        self.comment = None
        self.tags = []

    def copy_basic_attributes_of(self, other):
        assert isinstance(other, Entity)
        self.comment = other.comment
        self.tags = other.tags
        return self


class EVar(Entity):
    def __init__(self, x, comment=None, tags=[]):
        super().__init__(x.id, comment, tags)
        self.variable = x
        VarEntities.items.append(self)
        VarEntities.varToEVar[x] = self

    def get_type(self):
        return self.variable.dom.get_type()

    def __call__(self):
        return self.variable


class EVarArray(Entity):
    def __init__(self, X, name, comment=None, tags=[]):
        super().__init__(name, comment, tags)
        self.name = name
        self.variables = X
        self.flatVars = flatten(X)
        assert len(self.flatVars) != 0, "Array of variable empty !"
        self.containing_hole = None  # undefined until we ask  #flatVarsKeepingNone = flatten(X, keep_none=True)
        self.size = []
        curr = self.variables
        while isinstance(curr, list):
            self.size.append(len(curr))
            curr = curr[0]
        VarEntities.items.append(self)
        for x in self.flatVars:
            VarEntities.varToEVarArray[x] = self
        VarEntities.prefixToEVarArray[name] = self

    def is_containing_hole(self):
        if self.containing_hole is None:
            self.containing_hole = is_containing(self.variables, type(None), check_first_only=True)
        return self.containing_hole

    def extend_with(self, var):  # used when building auxiliary variables (to be used with global constraints)
        self.variables.append(var)
        self.flatVars.append(var)
        self.size[0] += 1
        VarEntities.varToEVarArray[var] = self

    def get_type(self):
        return self.flatVars[0].dom.get_type()

    def __getitem__(self, i):
        return self.variables[i]

    def __len__(self):
        return len(self.variables)

    def __iter__(self):
        yield self.variables.__iter__()

    def __next__(self):
        return self.variables.__next__()

    def size_to_string(self):
        return "".join("[" + str(v) + "]" for v in self.size)


""" Class to represent stand-alone constraints """


class ECtr(Entity):
    def __init__(self, c):
        super().__init__(None)  # no need to have an id here
        if c is None:
            self.constraint = None
            print("Warning: a constraint is None")
        else:
            self.constraint = c
            # CtrEntities.allEntities.append(self)


class ECtrs(Entity):
    """ Class for representing sets of constraints """

    def __init__(self, constraints=None):
        super().__init__(None)  # no need to have an id here
        assert constraints is not None and isinstance(constraints, list)
        self.entities = [c for c in constraints if c is not None]


class EToGather(ECtrs):
    ''' Constraints possibly stored in a group (the user asked to gather these constraints)'''

    def __init__(self, constraints):
        super().__init__(constraints)


class EToSatisfy(ECtrs):
    ''' Constraints possibly stored in several groups or several blocks (block built when a group is not possible) or stand-alone constraints'''

    def __init__(self, constraints):
        assert constraints is not None
        constraints = [c for c in constraints if c is not None]
        if len(constraints) > 0:
            CtrEntities.items.append(self)
            super().__init__(constraints)


class EGroup(ECtrs):
    ''' Constraints in a group '''

    def __init__(self):
        super().__init__([])
        self.abstraction = ""
        self.all_args = []


class EBlock(ECtrs):
    def __init__(self, constraints):
        super().__init__(constraints)


class ESlide(ECtrs):
    ''' Constraints possibly stored as a slide meta-constraint (the user asked to slide the constraints)'''

    def __init__(self, constraints):
        super().__init__(constraints)
        self.scope = []
        self.offset = False
        self.circular = False


class EIfThenElse(ECtrs):
    def __init__(self, constraints):
        checkType(constraints, [ECtr])
        assert len(constraints) == 3, "Error: three components must be specified in ifThenElse"
        super().__init__(constraints)


class EObjective(Entity):
    def __init__(self, c):
        if c is None:
            return
        super().__init__(None)  # no need to have an id here
        self.constraint = c
        ObjEntities.items.append(self)


class EAnnotation(Entity):
    def __init__(self, c):
        if c is None:
            return
        super().__init__(None)  # no need to have an id here
        self.constraint = c
        AnnEntities.items.append(self)
        AnnEntities.items_types.append(type(c))


class VarEntities:
    items = []
    varToEVar = dict()
    varToEVarArray = dict()
    prefixToEVarArray = dict()

    @staticmethod
    def get_item_with_name(s):
        if '[' in s:  # we need to look for arrays
            pos = s.index("[")
            prefix, suffix = s[:pos], s[pos:]
            assert prefix in VarEntities.prefixToEVarArray
            va = VarEntities.prefixToEVarArray[prefix]
            indexes = [int(v) if len(v) > 0 else None for v in re.split("\]\[", suffix[1:-1])]
            if is_containing(indexes, int):
                res = va.variables
                for v in indexes:
                    res = res[v]
                return res
            else:
                assert is_containing(indexes, type(None))
                return va
        else:
            for item in VarEntities.items:
                if isinstance(item, EVar) and item.name == s:
                    return item
        return None


class CtrEntities:
    items = []


class ObjEntities:
    items = []


class AnnEntities:
    items = []
    items_types = []


@unique
class TypeNode(Enum):
    def __init__(self, id, min_arity, max_arity):
        self.id = id
        self.min_arity = min_arity
        self.max_arity = max_arity
        self.lowercase_name = self.name.lower()

    def __str__(self):
        return self.lowercase_name

    ''' 0-ary '''
    VAR, PAR, INT, RATIONAL, DECIMAL, SYMBOL, PARTIAL = ((id, 0, 0) for id in auto(7))

    ''' Unary'''
    NEG, ABS, SQR, NOT, CARD, HULL, CONVEX, SQRT, EXP, LN, SIN, COS, TAN, ASIN, ACOS, ATAN, SINH, COSH, TANH = ((id, 1, 1) for id in auto(19))

    ''' Binary '''
    SUB, DIV, MOD, POW, DIST, LT, LE, GE, GT, IN, NOTIN, IMP, DIFF, DJOINT, SUBSET, SUBSEQ, SUPSEQ, SUPSET, FDIV, FMOD, = ((id, 2, 2) for id in auto(20))

    ''' Ternary '''
    IF = (auto(), 3, 3)

    ''' N-ary (2 to infinity)'''
    ADD, MUL, MIN, MAX, NE, EQ, AND, OR, XOR, IFF, UNION, INTER, SDIFF = ((id, 2, float("inf")) for id in auto(13))

    SET = (auto(), 0, float("inf"))

    SPECIAL = (auto(), 0, float("inf"))

    def is_leaf(self):
        return self == TypeNode.SPECIAL or (self.min_arity == self.max_arity == 0)

    def is_valid_arity(self, k):
        return self.min_arity <= k <= self.max_arity

    def is_logical_operator(self):
        return self in {TypeNode.NOT, TypeNode.AND, TypeNode.OR, TypeNode.XOR, TypeNode.IFF, TypeNode.IMP}

    def is_relational_operator(self):
        return self in {TypeNode.LT, TypeNode.LE, TypeNode.GE, TypeNode.GT, TypeNode.EQ, TypeNode.NE}

    def is_predicate_operator(self):
        return self.is_logical_operator() or self.is_relational_operator() or self in {TypeNode.IN, TypeNode.NOTIN}


def neg_range(r):
    assert isinstance(r, range) and r.step == 1
    return range(-r.stop + 1, -r.start + 1)


def abs_range(r):
    assert isinstance(r, range) and r.step == 1
    return range(0 if 0 in r else min(abs(r.start), abs(r.stop - 1)), max(abs(r.start), abs(r.stop - 1)) + 1)


def add_range(r1, r2):
    assert isinstance(r1, range) and r1.step == 1 and isinstance(r2, range) and r2.step == 1
    return range(r1.start + r2.start, r1.stop + r2.stop - 1)


def possible_range(s, control_int=False):
    assert isinstance(s, set) and (not control_int or all(isinstance(v, int) for v in s))
    l = sorted(s)
    return range(l[0], l[-1] + 1) if 1 < l[-1] - l[0] + 1 == len(l) else l


class Node(Entity):
    all_nodes = []

    def __init__(self, type, args):
        super().__init__(None)
        Node.all_nodes.append(self)
        self.used = False
        self.type = type
        self.leaf = type.is_leaf()
        self.sons = args  # TODO sons is used whatever this is a parent or a leaf node; not a good choice. change the name of this field ??? to content ??
        self.abstractTree = None
        self.abstractValues = None

    def __str__(self):
        return str(self.sons) if self.type.is_leaf() else str(self.type) + "(" + ",".join(str(son) for son in self.sons) + ")"

    def possible_values(self):
        if self.type.is_predicate_operator():
            return range(0, 2)  # we use a range instead of [0,1] because it simplifies computation (see code below)
        if self.type.min_arity == self.type.max_arity == 0:
            if self.type == TypeNode.VAR:
                av = self.sons.dom.all_values()  # either a range or a sorted list of integers is returned
                if isinstance(av, range):
                    return av
                return range(av[0], av[0] + 1) if len(av) == 1 else range(av[0], av[1] + 1) if len(av) == 2 and av[0] + 1 == av[1] else av
            if self.type == TypeNode.INT:
                return range(self.sons, self.sons+1)  # we use a range instead of a singleton list because it simplifies computation (see code below)
            assert False, "no such 0-ary type " + str(self.type) + " is expected"
        if self.type.min_arity == self.type.max_arity == 1:
            pv = self.sons[0].possible_values()
            if self.type == TypeNode.NEG:
                return neg_range(pv) if isinstance(pv, range) else [-v for v in reversed(pv)]
            if self.type == TypeNode.ABS:
                return abs_range(pv) if isinstance(pv, range) else possible_range({abs(v) for v in pv})
            if self.type == TypeNode.SQR:
                return possible_range({v * v for v in pv})
            assert False, "no such 1-ary type " + str(self.type) + " is expected"
        if self.type.min_arity == self.type.max_arity == 2:
            pv1, pv2 = self.sons[0].possible_values(), self.sons[1].possible_values()
            all_ranges = isinstance(pv1, range) and isinstance(pv2, range)
            if self.type == TypeNode.SUB:
                return add_range(pv1, neg_range(pv2)) if all_ranges else possible_range({v1 - v2 for v1 in pv1 for v2 in pv2})
            if self.type == TypeNode.DIV:
                return possible_range({v1 // v2 for v1 in pv1 for v2 in pv2})
            if self.type == TypeNode.MOD:
                return possible_range({v1 % v2 for v1 in pv1 for v2 in pv2})
            if self.type == TypeNode.POW:
                return possible_range({v1 ** v2 for v1 in pv1 for v2 in pv2}, control_int=True)
            if self.type == TypeNode.DIST:
                return abs_range(add_range(pv1, neg_range(pv2))) if all_ranges else possible_range({abs(v1 - v2) for v1 in pv1 for v2 in pv2})
            assert False, "no such 2-ary type " + str(self.type) + " is expected"
        if self.type == TypeNode.IF:
            pv1, pv2 = self.sons[1].possible_values(), self.sons[2].possible_values()  # sons[0] is for the condition
            if isinstance(pv1, range) and isinstance(pv2, range) and len(range(max(pv1.start, pv2.start), min(pv1.stop, pv2.stop))) > 0:
                return range(min(pv1.start, pv2.start), max(pv1.stop, pv2.stop))
            return possible_range({v1 for v1 in pv1} | {v2 for v2 in pv2})
        if self.type.min_arity == 2 and self.type.max_arity == float("inf"):
            pvs = [son.possible_values() for son in self.sons]
            all_ranges = all(isinstance(pv, range) for pv in pvs)
            if self.type == TypeNode.ADD:
                return reduce(add_range, pvs) if all_ranges else possible_range({sum(p) for p in product(*(pv for pv in pvs))})
            if self.type == TypeNode.MUL:
                return possible_range({numpy.prod(p) for p in product(*(pv for pv in pvs))})
            # TODO: in case of all_ranges being False, possibility of improving the efficiency of the code below for MIN and MAX
            if self.type == TypeNode.MIN:
                return range(min(pv.start for pv in pvs), min(pv.stop for pv in pvs)) if all_ranges \
                    else possible_range({min(p) for p in product(*(pv for pv in pvs))})
            if self.type == TypeNode.MAX:
                return range(max(pv.start for pv in pvs), max(pv.stop for pv in pvs)) if all_ranges \
                    else possible_range({max(p) for p in product(*(pv for pv in pvs))})
        assert False, "The operator " + str(self.type) + " currently not implemented"

    def mark_as_used(self):
        self.used = True
        if isinstance(self.sons, list):
            for son in self.sons:
                Node.mark_as_used(son)

    def _abstraction_recursive(self, cache, harvest_values):
        if self.type in {TypeNode.VAR, TypeNode.INT, TypeNode.SYMBOL}:
            key = id(self)
            if key not in cache:
                cache[key] = len(harvest_values)  # can it be a problem to use it as a key?
                harvest_values.append(self.sons)
            return "%" + str(cache[key]), harvest_values
        return str(self.type) + "(" + ",".join(son._abstraction_recursive(cache, harvest_values)[0] for son in self.sons) + ")", harvest_values

    def _abstraction(self):
        if self.abstractTree is None:
            self.abstractTree, self.abstractValues = self._abstraction_recursive(dict(), [])

    def abstract_tree(self):
        self._abstraction()
        return self.abstractTree

    def abstract_values(self):
        self._abstraction()
        return self.abstractValues

    def _variables_recursive(self, harvest):
        if isinstance(self.sons, list):
            for son in self.sons:
                son._variables_recursive(harvest)
        if self.leaf and self.type == TypeNode.VAR:
            if self.sons not in harvest:
                harvest.add(self.sons)
        return harvest

    def variables(self):
        return self._variables_recursive([])

    def variable(self, i):
        return self.variables()[i]

    def flatten_by_associativity(self, node_type):
        while True:
            for i, son in enumerate(self.sons):
                if self.type == son.type == node_type:
                    self.sons.pop(i)
                    for s in reversed(son.sons):
                        self.sons.insert(i, s)
                    break
            else:  # no break
                break

    def reduce_integers(self):
        if self.type not in {TypeNode.ADD, TypeNode.MUL}:
            return
        ints, sons = [], []
        for son in self.sons:
            if son.type == TypeNode.INT:
                ints.append(son.sons)
            else:
                sons.append(son)
        if len(ints) > 1:
            value = reduce(lambda x, y: x + y, ints, 0) if self.type == TypeNode.ADD else reduce(lambda x, y: x * y, ints, 1)
            sons.append(Node(TypeNode.INT, value))
            self.sons = sons

    def var_val_if_binary_type(self, t):
        if self.type != t or len(self.sons) != 2 or self.sons[0].type == self.sons[1].type:
            return None
        if self.sons[0].type == TypeNode.VAR and self.sons[1].type == TypeNode.INT:
            return self.sons[0].sons, self.sons[1].sons
        elif self.sons[0].type == TypeNode.INT and self.sons[1].type == TypeNode.VAR:
            return self.sons[1].sons, self.sons[0].sons
        else:
            return None

    def tree_val_if_binary_type(self, t):
        if self.type != t or len(self.sons) != 2 or self.sons[0].type == self.sons[1].type:
            return None
        if self.sons[0].type != TypeNode.INT and self.sons[1].type == TypeNode.INT:
            return self.sons[0].sons if self.sons[0].type == TypeNode.VAR else self.sons[0], self.sons[1].sons
        elif self.sons[0].type == TypeNode.INT and self.sons[1].type != TypeNode.INT:
            return self.sons[1].sons if self.sons[1].type == TypeNode.VAR else self.sons[1], self.sons[0].sons
        else:
            return None

    """
      Static methods
    """

    @staticmethod
    def _create_sons(*args):
        t = []
        for arg in args:
            if isinstance(arg, Node):
                t.append(arg)
            elif isinstance(arg, EVar):
                t.append(Node(TypeNode.VAR, arg.variable))
            elif isinstance(arg, NotVariable):
                t.append(Node(TypeNode.NOT, [Node(TypeNode.VAR, arg.variable)]))
            elif isinstance(arg, NegVariable):
                t.append(Node(TypeNode.NEG, [Node(TypeNode.VAR, arg.variable)]))
            elif isinstance(arg, Variable):
                t.append(Node(TypeNode.VAR, arg))
            elif isinstance(arg, int):
                t.append(Node(TypeNode.INT, arg))
            elif isinstance(arg, str):
                t.append(Node(TypeNode.SYMBOL, arg))
            elif isinstance(arg, main.constraints.PartialConstraint):
                t.append(Node(TypeNode.PARTIAL, arg))
            else:
                raise ValueError("Problem: bad form of predicate " + str(arg))
        return t

    @staticmethod
    def build(type, *args):
        if isinstance(type, str):
            if type == "<":
                type = TypeNode.LT
            elif type == "<=":
                type = TypeNode.LE
            elif type == ">=":
                type = TypeNode.GE
            elif type == ">":
                type = TypeNode.GT
            elif type in {"=", "=="}:
                type = TypeNode.EQ
            elif type == "!=":
                type = TypeNode.NE
            else:
                type = TypeNode[type.upper()]
        if type is TypeNode.SET:
            assert len(args) == 1
            elements = list(args[0])
            sorted_sons = sorted(elements, key=lambda v: str(v)) if len(elements) > 0 and not isinstance(elements[0], int) else sorted(elements)
            return Node(type, Node._create_sons(*sorted_sons))  # *sorted(args[0])))
        args = flatten(Node.build(TypeNode.SET, arg) if isinstance(arg, (set, range, frozenset)) else arg for arg in args)
        assert type.is_valid_arity(len(args)), "Problem: Bad arity for node " + type.name + ". It is " + str(
            len(args)) + " but it should be between " + str(type.arityMin) + " and " + str(type.arityMax)
        node = Node(type, Node._create_sons(*args))
        if type == TypeNode.EQ and all(son.type.is_predicate_operator() for son in node.sons):
            node = Node(TypeNode.IFF, node.sons)
        # Reducing the node
        for t in {TypeNode.ADD, TypeNode.MUL, TypeNode.OR, TypeNode.AND, TypeNode.EQ, TypeNode.IFF}:
            node.flatten_by_associativity(t)
        node.reduce_integers()
        return node

    @staticmethod
    def set(*args):
        return Node.build(TypeNode.SET, *args)

    @staticmethod
    def _and_or(t, *args):
        assert t in {TypeNode.AND, TypeNode.OR}
        if len(args) == 1:
            if isinstance(args[0], list):
                args = tuple(args[0])
            if isinstance(args[0], types.GeneratorType):
                args = tuple(list(args[0]))
        return Node.build(t, *args) if len(args) > 1 else args[0]

    @staticmethod
    def conjunction(*args):
        return Node._and_or(TypeNode.AND, *args)

    @staticmethod
    def disjunction(*args):
        return Node._and_or(TypeNode.OR, *args)
