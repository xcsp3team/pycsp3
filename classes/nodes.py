import types
from enum import Enum, unique
from functools import reduce, cmp_to_key
from itertools import product

from pycsp3.classes import main
from pycsp3.classes.auxiliary.enums import TypeConditionOperator, TypeOrderedOperator, TypeAbstractOperation
from pycsp3.classes.auxiliary.enums import auto
from pycsp3.classes.entities import Entity, EVar
from pycsp3.classes.main.variables import Variable
from pycsp3.tools.utilities import flatten, warning, neg_range, abs_range, add_range, possible_range


@unique
class TypeNode(Enum):
    def __init__(self, node_id, min_arity, max_arity):
        self.id = node_id
        self.min_arity = min_arity
        self.max_arity = max_arity
        self.lowercase_name = self.name.lower()

    def __invert__(self):
        if self == TypeNode.EQ:
            return TypeNode.NE
        if self == TypeNode.NE:
            return TypeNode.EQ
        if self == TypeNode.LT:
            return TypeNode.GE
        if self == TypeNode.LE:
            return TypeNode.GT
        if self == TypeNode.GT:
            return TypeNode.LE
        if self == TypeNode.GE:
            return TypeNode.LT
        if self == TypeNode.IN:
            return TypeNode.NOTIN
        if self == TypeNode.NOTIN:
            return TypeNode.IN
        return None

    def __str__(self):
        return self.lowercase_name

    ''' 0-ary '''
    VAR, INT, RATIONAL, DECIMAL, SYMBOL, PARTIAL, COL, PAR = ((id, 0, 0) for id in auto(8))  # PAR is used by the parser

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

    def is_symmetric_operator(self):
        return self in {TypeNode.ADD, TypeNode.MUL, TypeNode.MIN, TypeNode.MAX, TypeNode.DIST, TypeNode.NE, TypeNode.EQ, TypeNode.SET, TypeNode.AND,
                        TypeNode.OR, TypeNode.XOR, TypeNode.IFF, TypeNode.UNION, TypeNode.INTER, TypeNode.DJOINT}

    def is_unsymmetric_relational_operator(self):
        return self in {TypeNode.LT, TypeNode.LE, TypeNode.GE, TypeNode.GT}

    def is_relational_operator(self):
        return self in {TypeNode.LT, TypeNode.LE, TypeNode.GE, TypeNode.GT, TypeNode.EQ, TypeNode.NE}

    def is_arithmetic_operator(self):
        return self in {TypeNode.ADD, TypeNode.SUB, TypeNode.MUL, TypeNode.DIV, TypeNode.MOD, TypeNode.POW, TypeNode.DIST}

    def is_logical_operator(self):
        return self in {TypeNode.NOT, TypeNode.AND, TypeNode.OR, TypeNode.XOR, TypeNode.IFF, TypeNode.IMP}

    def is_predicate_operator(self):
        return self.is_logical_operator() or self.is_relational_operator() or self in {TypeNode.IN, TypeNode.NOTIN}

    def is_identity_when_one_operand(self):
        return self in {TypeNode.ADD, TypeNode.MUL, TypeNode.MIN, TypeNode.MAX, TypeNode.EQ, TypeNode.AND, TypeNode.OR, TypeNode.XOR, TypeNode.IFF}

    def arithmetic_inversion(self):  # when multiplied by -1
        if self == TypeNode.LT:
            return TypeNode.GT
        if self == TypeNode.LE:
            return TypeNode.GE
        if self == TypeNode.GE:
            return TypeNode.LE
        if self == TypeNode.GT:
            return TypeNode.LT
        if self == TypeNode.NE:
            return TypeNode.NE
        if self == TypeNode.EQ:
            return TypeNode.EQ
        return None

    def logical_inversion(self):
        if self == TypeNode.LT:
            return TypeNode.GE
        if self == TypeNode.LE:
            return TypeNode.GT
        if self == TypeNode.GE:
            return TypeNode.LT
        if self == TypeNode.GT:
            return TypeNode.LE
        if self == TypeNode.NE:
            return TypeNode.EQ
        if self == TypeNode.EQ:
            return TypeNode.NE
        if self == TypeNode.IN:
            return TypeNode.NOTIN
        if self == TypeNode.NOTIN:
            return TypeNode.IN
        if self == TypeNode.SUBSET:
            return TypeNode.SUPSEQ
        if self == TypeNode.SUBSEQ:
            return TypeNode.SUPSET
        if self == TypeNode.SUPSEQ:
            return TypeNode.SUBSET
        if self == TypeNode.SUPSET:
            return TypeNode.SUBSEQ
        return None

    def is_logically_invertible(self):
        return self.logical_inversion() is not None

    def is_flattenable(self):
        return self in {TypeNode.ADD, TypeNode.MUL, TypeNode.MIN, TypeNode.MAX, TypeNode.AND, TypeNode.OR}

    def is_mergeablew(self):
        return self.is_flattenable()

    @staticmethod
    def value_of(v):
        if isinstance(v, TypeNode):
            return v
        if isinstance(v, TypeOrderedOperator):
            v = str(v)  # to be intercepted just below
        if isinstance(v, str):
            if v in ("<", "lt"):
                return TypeNode.LT
            if v in ("<=", "le"):
                return TypeNode.LE
            if v in (">=", "ge"):
                return TypeNode.GE
            if v in (">", "gt"):
                return TypeNode.GT
            if v in ("=", "==", "eq"):
                return TypeNode.EQ
            if v in ("!=", "<>", "ne"):
                return TypeNode.NE
            return TypeNode[v.upper()]
        if isinstance(v, TypeConditionOperator):
            return TypeNode[str(v).upper()]
        return None  # other cases to handle?


class Node(Entity):
    all_nodes = []

    def __init__(self, node_type, args):
        super().__init__(None)
        Node.all_nodes.append(self)
        self.used = False
        self.type = node_type
        self.leaf = node_type.is_leaf()
        self.sons = [] if args is None else [args] if not self.leaf and not isinstance(args, list) else args  # for empty SET (we have None)
        assert (not self.leaf) == (isinstance(self.sons, list)) or isinstance(self, NodeSpecial)
        # if not self.leaf:
        #     print("kkkkkk", self.type)
        #     for son in self.sons:
        #         print("hhhhh2", str(son))
        # TODO sons is used whatever this is a parent or a leaf node; not a good choice. change the name of this field ??? to content ??

        self.abstractTree = None
        self.abstractValues = None

    def __bool__(self):
        warning("A node is evaluated as a Boolean (technically, __bool__ is called)."
                + "\n\tIt is likely a problem with the use of logical operators."
                + "\n\tFor example, you must write (x[0] == x[1])  | (x[0] == x[2]) instead of (x[0] == x[1])  or (x[0] == x[2])"
                + "\n\tIt is also possible that you write: If(cond, Then=...) while cond being not constraint-based"
                + "\n\t  that is, not involving a variable of the model; and this is not possible."
                + "\n\tSee also the end of section about constraint Intension in chapter 'Twenty popular constraints' of the guide."
                + "\n\tThis is: " + str(self) + "\n")
        # exit(1)
        return True

    def eq__safe(self, other):
        if not isinstance(other, Node) or self.type != other.type or self.leaf != other.leaf:
            return False
        if not self.leaf:
            return len(self.sons) == len(other.sons) and all(self.sons[i].eq__safe(other.sons[i]) for i in range(len(self.sons)))
        return self.sons.eq__safe(other.sons) if isinstance(self.sons, Variable) else self.sons == other.sons

    def __str_hybrid__(self):
        if self.type.is_leaf():
            if self.type == TypeNode.COL:
                return "c" + str(self.sons)  # return "%" + str(self.sons)
            return str(self.sons)
        if self.type == TypeNode.ADD or self.type == TypeNode.SUB:
            msg = "An hybrid tuple must be of the form {eq|lt|le|ge|gt|ne}{var|integer}{+|-}{var|integer}"
            assert len(self.sons) == 2, msg
            assert self.sons[0].type in (TypeNode.INT, TypeNode.COL) and self.sons[1].type in (TypeNode.INT, TypeNode.COL), msg
            return self.sons[0].__str_hybrid__() + ("+" if self.type == TypeNode.ADD else "-") + self.sons[1].__str_hybrid__()
        else:
            assert False, "An hybrid tuple must be of the form col(x)[+or-][integer]"

    def __str__(self):
        if self.type == TypeNode.COL:
            return "%" + str(self.sons)
        return str(self.sons) if self.type.is_leaf() else str(self.type) + "(" + ",".join(str(son) for son in self.sons) + ")"

    def __repr__(self):
        return self.__str__()

    def is_literal(self):
        if self.type == TypeNode.VAR:
            return self.sons.dom.is_binary()
        if self.type == TypeNode.NOT:
            return self.sons[0].type == TypeNode.VAR and self.sons[0].sons.dom.is_binary()
        return False

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
                return range(self.sons, self.sons + 1)  # we use a range instead of a singleton list because it simplifies computation (see code below)
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
                return possible_range({v1 // v2 for v1 in pv1 for v2 in pv2 if v2 != 0})
            if self.type == TypeNode.MOD:
                return possible_range({v1 % v2 for v1 in pv1 for v2 in pv2 if v2 != 0})
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
                def multiply(t):
                    res = 1
                    for v in t:
                        res *= v
                    return res

                if all_ranges and all(pv.start >= 0 and pv.step == 1 for pv in pvs):
                    return range(multiply(pv.start for pv in pvs), multiply(pv.stop - 1 for pv in pvs) + 1)
                return possible_range({multiply(p) for p in product(*(pv for pv in pvs))})  # or numpy.prod ?
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
                harvest.append(self.sons)
        return harvest

    def list_of_variables(self):
        return self._variables_recursive([])

    def variable(self, i):
        return self.list_of_variables()[i]

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

    def first_node_such_that(self, predicate):
        if predicate(self):
            return self
        if self.leaf:
            return None
        return next((son for son in self.sons if son.first_node_such_that(predicate) is not None), None)

    def all_nodes_such_that(self, predicate, harvest):
        if predicate(self):
            harvest.append(self)
        if not self.leaf:
            for son in self.sons:
                son.all_nodes_such_that(predicate, harvest)
        return harvest

    def list_of_vals(self):
        return [n.sons for n in self.all_nodes_such_that(lambda r: r.type == TypeNode.INT, [])]

    def max_parameter_number(self):
        if self.leaf:
            return self.sons if self.type == TypeNode.PAR else -1  # recall that % ... is not possible in predicates
        return max(son.max_parameter_number() for son in self.sons)

    def concretization(self, args):
        if self.leaf:
            value = self.sons
            if self.type != TypeNode.PAR:
                return Node(self.type, value)  # we return a similar object
            assert isinstance(value, int)  # we know that the value is an int
            arg = args[value]
            if isinstance(arg, int):
                return Node(TypeNode.INT, arg)
            # and decimal values in the future ?
            if isinstance(arg, str):
                return Node(TypeNode.SYMBOL, arg)
            if isinstance(arg, Node):
                return arg
            return Node(TypeNode.VAR, arg)  # kept at last position for avoiding importing specific parser class
        sons = [son.concretization(args) for son in self.sons]
        return Node(self.type, sons)

    def _augment(self, offset):
        assert self.type == TypeNode.INT
        return Node(self.type, self.sons + offset)

    def val(self, i):
        if i == 0:
            f = self.first_node_such_that(lambda n: n.type == TypeNode.INT)
            return f.sons if f is not None else None
        t = self.list_of_vals()
        return None if i >= len(t) else t[i]

    def canonization(self):
        if self.leaf:
            return Node(self.type, self.sons)  # we return a similar object
        # we will build the canonized form of the node, with the two following local variables
        t = self.type  # possibly, this initial value of type will be modified during canonization
        s = [son.canonization() for son in self.sons]
        if t.is_symmetric_operator():
            s = sorted(s, key=cmp_to_key(Node.compare_to))  # sons are sorted if the type of the node is symmetric
        # Now, sons are potentially sorted if the type corresponds to a non-symmetric binary relational operator (in
        # that case, we swap sons and arithmetically inverse the operator provided that the ordinal value of the reverse operator is smaller)
        if len(s) == 2 and t.is_unsymmetric_relational_operator():  # if LT,LE,GE,GT
            tt = t.arithmetic_inversion()
            if tt.value[0] < t.value[0] or (tt.value[0] == t.value[0] and Node.compare_to(s[0], s[1]) > 0):
                t = tt
                s = [s[1], s[0]]  # swap
        if len(s) == 1 and t.is_identity_when_one_operand():  # // add(x) becomes x, min(x) becomes x, ...
            return s[0]  # certainly can happen during the canonization process
        node = Node(t, s)

        rules = {
            abs_sub: lambda r: Node(TypeNode.DIST, r.sons[0].sons),  # abs(sub(a,b)) => dist(a,b)
            not_not: lambda r: r.sons[0].sons[0],  # not(not(a)) => a
            neg_neg: lambda r: r.sons[0].sons[0],  # neg(neg(a)) => a
            any_lt_k: lambda r: Node(TypeNode.LE, [r.sons[0], r.sons[1]._augment(-1)]),  # e.g., lt(x,5) => le(x,4)
            k_lt_any: lambda r: Node(TypeNode.LE, [r.sons[0]._augment(1), r.sons[1]]),  # e.g., lt(5,x) => le(6,x)
            not_logop: lambda r: Node(r.sons[0].type.logical_inversion(), r.sons[0].sons),  # e.g., not(lt(x)) = > ge(x)
            not_symrel_any: lambda r: Node(r.type.logical_inversion(), [r.sons[0].sons[0], r.sons[1]]),  # e.g., ne(not(x),y) => eq(x,y)
            any_symrel_not: lambda r: Node(r.type.logical_inversion(), [r.sons[0], r.sons[1].sons[0]]),  # e.g., ne(x,not(y)) => eq(x,y)
            x_mul_k__eq_l: lambda r: Node(TypeNode.EQ, [r.sons[0].sons[0], Node(TypeNode.INT, r.val(1) // r.val(0))]) if r.val(1) % r.val(0) == 0 else Node(
                TypeNode.INT, 0),  # e.g., eq(mul(x,4),8) => eq(x,2) and eq(mul(x,4),6) => 0 (false)
            l__eq_x_mul_k: lambda r: Node(TypeNode.EQ, [Node(TypeNode.INT, r.val(0) // r.val(1)), r.sons[1].sons[0]]) if r.val(0) % r.val(1) == 0 else Node(
                TypeNode.INT, 0),  # e.g., eq(8,mul(x,4)) => eq(2,x) and eq(6,mul(x,4)) => 0 (false)
            #  we flatten operators when possible; for example add(add(x,y),z) becomes add(x,y,z)
            flattenable: lambda r: Node(r.type, flatten([son.sons if son.type == r.type else son for son in r.sons]))
            # TODO to be continued
        }

        for k, v in rules.items():
            if k.matches(node):
                node = v(node).canonization()
        return node

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
            elif isinstance(arg, Variable):
                if arg.inverse:
                    t.append(Node(TypeNode.NEG, [Node(TypeNode.VAR, arg)]))
                elif arg.negation:
                    t.append(Node(TypeNode.NOT, [Node(TypeNode.VAR, arg)]))
                else:
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
    def build(node_type, *args):
        tn = TypeNode.value_of(node_type)  # for handling the cases where type is of type str or TypeConditionOperator
        if tn is TypeNode.SET:
            assert len(args) == 1
            elements = list(args[0])
            sorted_sons = sorted(elements, key=lambda v: str(v)) if len(elements) > 0 and not isinstance(elements[0], int) else sorted(elements)
            return Node(tn, Node._create_sons(*sorted_sons))  # *sorted(args[0])))
        args = flatten(Node.build(TypeNode.SET, arg) if isinstance(arg, (set, range, frozenset)) else arg for arg in args)
        assert tn.is_valid_arity(len(args)), "Problem: Bad arity for node " + tn.name + ". It is " + str(
            len(args)) + " but it should be between " + str(tn.min_arity) + " and " + str(tn.max_arity)
        # Do we activate these simple modifications below?
        # if len(args) == 2 and isinstance(args[0], Variable) and isinstance(args[1], int):
        #     if (args[1] == 1 and type in (TypeNode.MUL, TypeNode.DIV)) or (args[1] == 0 and type in (TypeNode.ADD, TypeNode.SUB)):
        #         return Node(TypeNode.VAR,args[0])
        node = Node(tn, Node._create_sons(*args))
        if tn == TypeNode.EQ and all(son.type.is_predicate_operator() for son in node.sons):
            node = Node(TypeNode.IFF, node.sons)
        # Reducing the node
        for t in {TypeNode.ADD, TypeNode.MUL, TypeNode.OR, TypeNode.AND}:
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
            if isinstance(args[0], (tuple, list, set, frozenset)):
                args = tuple(args[0])
            if len(args) > 0 and isinstance(args[0], types.GeneratorType):
                args = tuple(list(args[0]))
        args = [arg for arg in args if not (isinstance(arg, (tuple, list, set, frozenset)) and len(arg) == 0)]
        args = [arg[0] if isinstance(arg, (tuple, list, set, frozenset)) and len(arg) == 1 else arg for arg in args]
        if len(args) == 0:
            return t == TypeNode.AND
        args = [Node.conjunction(arg) if isinstance(arg, (tuple, list, set, frozenset)) else arg for arg in args]
        return Node.build(t, *args) if len(args) > 1 else args[0]

    @staticmethod
    def conjunction(*args):
        return Node._and_or(TypeNode.AND, *args)

    @staticmethod
    def disjunction(*args):
        return Node._and_or(TypeNode.OR, *args)

    @staticmethod
    def in_range(x, r):
        assert isinstance(r, range) and r.step == 1
        return Node.build(TypeNode.AND, Node.build(TypeNode.GE, x, r.start), Node.build(TypeNode.LT, x, r.stop))

    @staticmethod
    def not_in_range(x, r):
        assert isinstance(r, range) and r.step == 1
        return Node.build(TypeNode.OR, Node.build(TypeNode.LT, x, r.start), Node.build(TypeNode.GE, x, r.stop))

    @staticmethod
    def compare_to(node1, node2):
        if node1.type != node2.type:
            return node1.type.value[0] - node2.type.value[0]
        if node1.type.is_leaf():
            v1, v2 = node1.sons, node2.sons
            if node1.type == TypeNode.VAR:
                return -1 if v1.id < v2.id else 1 if v1.id > v2.id else 0
            if node1.type in (TypeNode.PAR, TypeNode.INT):
                return v1 - v2
            if node1.type == TypeNode.SYMBOL:
                return -1 if v1 < v2 else 1 if v1 > v2 else 0
            if node1.type == TypeNode.SET:
                return 0  # because two empty sets
            assert False
        if len(node1.sons) < len(node2.sons):
            return -1
        if len(node1.sons) > len(node2.sons):
            return 1
        for i in range(len(node1.sons)):
            res = Node.compare_to(node1.sons[i], node2.sons[i])
            if res != 0:
                return res
        return 0


class NodeSpecial(Node):

    def __init__(self, abstract_operation: TypeAbstractOperation, args):
        super().__init__(TypeNode.SPECIAL, args)
        self.abstract_operation = abstract_operation

    def __str__(self):
        return str(self.abstract_operation) + " :" + str(self.sons) if self.type.is_leaf() else str(self.type) + "(" + ",".join(
            str(son) for son in self.sons) + ")"


ANY = Node(TypeNode.SPECIAL, "any")
ANYc = Node(TypeNode.SPECIAL, "anyc")  # any under condition
var = Node(TypeNode.SPECIAL, "var")
val = Node(TypeNode.SPECIAL, "val")
varOrVal = Node(TypeNode.SPECIAL, "var-or-val")
any_add_val = Node(TypeNode.SPECIAL, "any-add-val")
var_add_val = Node(TypeNode.SPECIAL, "var-add-val")
sub = Node(TypeNode.SPECIAL, "sub")
nnot = Node(TypeNode.SPECIAL, "not")
set_vals = Node(TypeNode.SPECIAL, "set-vals")
min_vars = Node(TypeNode.SPECIAL, "min-vars")
max_vars = Node(TypeNode.SPECIAL, "max-vars")
logic_vars = Node(TypeNode.SPECIAL, "logic-vars")
add_vars = Node(TypeNode.SPECIAL, "add-vars")
mul_vars = Node(TypeNode.SPECIAL, "mul-vars")
add_mul_vals = Node(TypeNode.SPECIAL, "add-mul-vals")
add_mul_vars = Node(TypeNode.SPECIAL, "add-mul-vars")


class Matcher:

    def __init__(self, target: Node, p=None):
        self.target = target
        self.p = p

    def valid_for_special_target_node(self, node: Node, level: int):
        return self.p is None or self.p(node, level)

    def _matching(self, source: Node, target: Node, level: int):
        # print("matching ", str(source), str(target), level)
        if target is ANY:  # any node (i.e., full abstract node) => everything matches
            return True
        if target is ANYc:  # any node under condition (the difference with SPECIAL only, is that sons are not considered recursively)
            return self.valid_for_special_target_node(source, level)
        if target is var:
            return source.type == TypeNode.VAR
        if target is val:
            return source.type == TypeNode.INT
        if target is varOrVal:
            return source.type in (TypeNode.VAR, TypeNode.INT)
        if target is any_add_val:
            return source.type == TypeNode.ADD and len(source.sons) == 2 and source.sons[1].type == TypeNode.INT
        if target is var_add_val:
            return source.type == TypeNode.ADD and len(source.sons) == 2 and source.sons[0].type == TypeNode.VAR and source.sons[1].type == TypeNode.INT
        if target is sub:
            return source.type == TypeNode.SUB
        if target is nnot:
            return source.type == TypeNode.NOT
        if target is set_vals:  # abstract set => we control that source is either an empty set or a set built on only longs
            return source.type == TypeNode.SET and all(son.type == TypeNode.INT for son in source.sons)
        if target is min_vars:  # abstract min => we control that source is a min built on only variables
            return source.type == TypeNode.MIN and len(source.sons) >= 2 and all(son.type == TypeNode.VAR for son in source.sons)
        if target is max_vars:  # abstract max => we control that source is a max built on only variables
            return source.type == TypeNode.MAX and len(source.sons) >= 2 and all(son.type == TypeNode.VAR for son in source.sons)
        if target is logic_vars:
            return source.type.is_logical_operator() and len(source.sons) >= 2 and all(son.type == TypeNode.VAR for son in source.sons)
        if target is add_vars:
            return source.type == TypeNode.ADD and len(source.sons) >= 2 and all(son.type == TypeNode.VAR for son in source.sons)
        if target is mul_vars:
            return source.type == TypeNode.MUL and len(source.sons) >= 2 and all(son.type == TypeNode.VAR for son in source.sons)
        if target is add_mul_vals:
            return source.type == TypeNode.ADD and len(source.sons) >= 2 and all(son.type == TypeNode.VAR or x_mul_k.matches(son) for son in source.sons)
        if target is add_mul_vars:
            return source.type == TypeNode.ADD and len(source.sons) >= 2 and all(x_mul_y.matches(son) for son in source.sons)
        if target.type != TypeNode.SPECIAL:
            if target.type.is_leaf() != source.type.is_leaf() or target.type != source.type:
                return False
        else:
            if isinstance(target, NodeSpecial):
                ao = target.abstract_operation
                if ao == TypeAbstractOperation.ariop:
                    if not source.type.is_arithmetic_operator():
                        return False
                if ao == TypeAbstractOperation.relop:
                    if not source.type.is_relational_operator():
                        return False
                if ao == TypeAbstractOperation.setop:
                    if source.type not in (TypeNode.IN, TypeNode.NOTIN):
                        return False
                if ao == TypeAbstractOperation.unalop:
                    if source.type not in (TypeNode.ABS, TypeNode.NEG, TypeNode.SQR, TypeNode.NOT):
                        return False
                if ao == TypeAbstractOperation.symop:
                    if source.type not in (TypeNode.EQ, TypeNode.NE):
                        return False
            elif not self.valid_for_special_target_node(source, level):
                return False
        if not isinstance(target, NodeSpecial) and target.leaf:
            return True  # it seems that we have no more control to do
        return len(target.sons) == len(source.sons) and all(self._matching(source.sons[i], target.sons[i], level + 1) for i in range(len(target.sons)))

    def matches(self, tree: Node):
        return self._matching(tree, self.target, 0)

    def __str__(self):
        return str(self.target) + " : " + str(self.p)

    def __repr__(self):
        return self.__str__()


## Canonization

x_mul_k = Matcher(Node(TypeNode.MUL, [var, val]))
x_mul_y = Matcher(Node(TypeNode.MUL, [var, var]))
k_mul_x = Matcher(Node(TypeNode.MUL, [val, var]))  # used in some other contexts (when non canonized forms)
abs_sub = Matcher(Node(TypeNode.ABS, Node(TypeNode.SUB, [ANY, ANY])))
not_not = Matcher(Node(TypeNode.NOT, Node(TypeNode.NOT, ANY)))
neg_neg = Matcher(Node(TypeNode.NEG, Node(TypeNode.NEG, ANY)))
any_lt_k = Matcher(Node(TypeNode.LT, [ANY, val]))
k_lt_any = Matcher(Node(TypeNode.LT, [val, ANY]))
not_logop = Matcher(Node(TypeNode.NOT, ANYc), lambda node, level: level == 1 and node.type.is_logically_invertible())
not_symrel_any = Matcher(NodeSpecial(TypeAbstractOperation.symop, [nnot, ANY]))
any_symrel_not = Matcher(NodeSpecial(TypeAbstractOperation.symop, [ANY, nnot]))
x_mul_k__eq_l = Matcher(Node(TypeNode.EQ, [Node(TypeNode.MUL, [var, val]), val]))
l__eq_x_mul_k = Matcher(Node(TypeNode.EQ, [val, Node(TypeNode.MUL, [var, val])]))
flattenable = Matcher(ANYc, lambda node, level: level == 0 and node.type.is_flattenable() and any(son.type == node.type for son in node.sons))
mergeable = Matcher(ANYc, lambda node, level: level == 0 and node.type.is_mergeable() and len(node.sons) >= 2 and node.sons[-1].type == node.sons[
    - 2].type == TypeNode.INT)
sub_relop_sub = Matcher(NodeSpecial(TypeAbstractOperation.relop, [sub, sub]))
any_relop_sub = Matcher(NodeSpecial(TypeAbstractOperation.relop, [ANY, sub]))
sub_relop_any = Matcher(NodeSpecial(TypeAbstractOperation.relop, [sub, ANY]))
any_add_val__relop__any_add_val = Matcher(NodeSpecial(TypeAbstractOperation.relop, [any_add_val, any_add_val]))
var_add_val__relop__val = Matcher(NodeSpecial(TypeAbstractOperation.relop, [var_add_val, val]))
val__relop__var_add_val = Matcher(NodeSpecial(TypeAbstractOperation.relop, [val, var_add_val]))
imp_logop = Matcher(Node(TypeNode.IMP, [ANYc, ANY]), lambda node, level: level == 1 and node.type.is_logically_invertible())
imp_not = Matcher(Node(TypeNode.IMP, [Node(TypeNode.NOT, ANY), ANY]))

# unary
x_relop_k = Matcher(NodeSpecial(TypeAbstractOperation.relop, [var, val]))
k_relop_x = Matcher(NodeSpecial(TypeAbstractOperation.relop, [val, var]))
x_ariop_k__relop_l = Matcher(NodeSpecial(TypeAbstractOperation.relop, [NodeSpecial(TypeAbstractOperation.ariop, [var, val]), val]))
l_relop__x_ariop_k = Matcher(NodeSpecial(TypeAbstractOperation.relop, [val, NodeSpecial(TypeAbstractOperation.ariop, [var, val])]))
x_setop_S = Matcher(NodeSpecial(TypeAbstractOperation.setop, [var, set_vals]))
x_in_intvl = Matcher(Node(TypeNode.AND, [Node(TypeNode.LE, [var, val]), Node(TypeNode.LE, [val, var])]))
x_notin_intvl = Matcher(Node(TypeNode.OR, [Node(TypeNode.LE, [var, val]), Node(TypeNode.LE, [val, var])]))

# binary
x_relop_y = Matcher(NodeSpecial(TypeAbstractOperation.relop, [var, var]))
x_ariop_y__relop_k = Matcher(NodeSpecial(TypeAbstractOperation.relop, [NodeSpecial(TypeAbstractOperation.ariop, [var, var]), val]))
k_relop__x_ariop_y = Matcher(NodeSpecial(TypeAbstractOperation.relop, [val, NodeSpecial(TypeAbstractOperation.ariop, [var, var])]))
x_relop__y_ariop_k = Matcher(NodeSpecial(TypeAbstractOperation.relop, [var, NodeSpecial(TypeAbstractOperation.ariop, [var, val])]))
y_ariop_k__relop_x = Matcher(NodeSpecial(TypeAbstractOperation.relop, [NodeSpecial(TypeAbstractOperation.ariop, [var, val]), var]))
logic_y_relop_k__eq_x = Matcher(Node(TypeNode.EQ, [NodeSpecial(TypeAbstractOperation.relop, [var, val]), var]))
logic_k_relop_y__eq_x = Matcher(Node(TypeNode.EQ, [NodeSpecial(TypeAbstractOperation.relop, [val, var]), var]))
unalop_x__eq_y = Matcher(Node(TypeNode.EQ, [NodeSpecial(TypeAbstractOperation.unalop, var), var]))

# ternary
x_ariop_y__relop_z = Matcher(NodeSpecial(TypeAbstractOperation.relop, [NodeSpecial(TypeAbstractOperation.ariop, [var, var]), var]))
z_relop__x_ariop_y = Matcher(NodeSpecial(TypeAbstractOperation.relop, [var, NodeSpecial(TypeAbstractOperation.ariop, [var, var])]))
logic_y_relop_z__eq_x = Matcher(Node(TypeNode.EQ, [NodeSpecial(TypeAbstractOperation.relop, [var, var]), var]))

# logic
logic_X = Matcher(logic_vars);
logic_X__eq_x = Matcher(Node(TypeNode.EQ, [logic_vars, var]))
logic_X__ne_x = Matcher(Node(TypeNode.NE, [logic_vars, var]))

# extremum
min_relop = Matcher(NodeSpecial(TypeAbstractOperation.relop, [min_vars, varOrVal]))
max_relop = Matcher(NodeSpecial(TypeAbstractOperation.relop, [max_vars, varOrVal]))

# sum
add_vars__relop = Matcher(NodeSpecial(TypeAbstractOperation.relop, [add_vars, varOrVal]))
add_mul_vals__relop = Matcher(NodeSpecial(TypeAbstractOperation.relop, [add_mul_vals, varOrVal]))
add_mul_vars__relop = Matcher(NodeSpecial(TypeAbstractOperation.relop, [add_mul_vars, varOrVal]))
