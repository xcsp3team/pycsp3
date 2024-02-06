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

ARIOP, RELOP, SETOP, UNALOP, SYMOP = TypeAbstractOperation.ARIOP, TypeAbstractOperation.RELOP, TypeAbstractOperation.SETOP, TypeAbstractOperation.UNALOP, TypeAbstractOperation.SYMOP


@unique
class TypeNode(Enum):
    def __init__(self, node_id, min_arity, max_arity):
        self.id = node_id
        self.min_arity = min_arity
        self.max_arity = max_arity
        self.lowercase_name = self.name.lower()

    def __invert__(self):
        if self == EQ:
            return NE
        if self == NE:
            return EQ
        if self == LT:
            return GE
        if self == LE:
            return GT
        if self == GT:
            return LE
        if self == GE:
            return LT
        if self == IN:
            return NOTIN
        if self == NOTIN:
            return IN
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

    SET = (auto(), 0, float("inf"))  # SET is always considered as a parent with a (possibly empty) list of sons

    SPECIAL = (auto(), 0, float("inf"))

    def is_valid_arity(self, k):
        return self.min_arity <= k <= self.max_arity

    def is_symmetric_operator(self):
        return self in {ADD, MUL, MIN, MAX, DIST, NE, EQ, SET, AND, OR, XOR, IFF}  # , TypeNode.UNION, TypeNode.INTER, TypeNode.DJOINT}

    def is_not_symmetric_relational_operator(self):
        return self in {LT, LE, GE, GT}

    def is_relational_operator(self):
        return self in {LT, LE, GE, GT, EQ, NE}

    def is_arithmetic_operator(self):
        return self in {ADD, SUB, MUL, DIV, MOD, TypeNode.POW, DIST}

    def is_logical_operator(self):
        return self in {NOT, AND, OR, XOR, IFF, IMP}

    def is_predicate_operator(self):
        return self.is_logical_operator() or self.is_relational_operator() or self in {IN, NOTIN}

    def is_identity_when_one_operand(self):
        return self in {ADD, MUL, MIN, MAX, EQ, AND, OR, XOR, IFF}

    def arithmetic_inversion(self):  # when multiplied by -1
        if self == LT:
            return GT
        if self == LE:
            return GE
        if self == GE:
            return LE
        if self == GT:
            return LT
        if self == NE:
            return NE
        if self == EQ:
            return EQ
        return None

    def logical_inversion(self):
        if self == LT:
            return GE
        if self == LE:
            return GT
        if self == GE:
            return LT
        if self == GT:
            return LE
        if self == NE:
            return EQ
        if self == EQ:
            return NE
        if self == IN:
            return NOTIN
        if self == NOTIN:
            return IN
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
        return self in {ADD, MUL, MIN, MAX, AND, OR}

    def is_mergeable(self):
        return self.is_flattenable()

    @staticmethod
    def value_of(v):
        if isinstance(v, TypeNode):
            return v
        if isinstance(v, TypeOrderedOperator):
            v = str(v)  # to be intercepted just below
        if isinstance(v, str):
            if v in ("<", "lt"):
                return LT
            if v in ("<=", "le"):
                return LE
            if v in (">=", "ge"):
                return GE
            if v in (">", "gt"):
                return GT
            if v in ("=", "==", "eq"):
                return EQ
            if v in ("!=", "<>", "ne"):
                return NE
            return TypeNode[v.upper()]
        if isinstance(v, TypeConditionOperator):
            return TypeNode[str(v).upper()]
        return None  # other cases to handle?


# for member in TypeNode:
#     globals()[member.name] = member

VAR, INT, SYMBOL, COL, PAR = TypeNode.VAR, TypeNode.INT, TypeNode.SYMBOL, TypeNode.COL, TypeNode.PAR
NEG, ABS, NOT, SUB, DIV, MOD, DIST, IMP = TypeNode.NEG, TypeNode.ABS, TypeNode.NOT, TypeNode.SUB, TypeNode.DIV, TypeNode.MOD, TypeNode.DIST, TypeNode.IMP
LT, LE, GE, GT, IN, NOTIN = TypeNode.LT, TypeNode.LE, TypeNode.GE, TypeNode.GT, TypeNode.IN, TypeNode.NOTIN
ADD, MUL, MIN, MAX, NE, EQ = TypeNode.ADD, TypeNode.MUL, TypeNode.MIN, TypeNode.MAX, TypeNode.NE, TypeNode.EQ
AND, OR, XOR, IFF = TypeNode.AND, TypeNode.OR, TypeNode.XOR, TypeNode.IFF
SET, SPECIAL = TypeNode.SET, TypeNode.SPECIAL


class Node(Entity):
    all_nodes = []

    def __init__(self, node_type, args):
        super().__init__(None)
        Node.all_nodes.append(self)
        self.used = False
        self.type = node_type
        self.cnt = [args] if isinstance(args, Node) else args  # for empty SET (we have []])
        # cnt is for content (either a leaf value or a list of sons)
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

    def is_leaf(self):
        return not isinstance(self.cnt, list)  # when unary node, we have also a list  (SET is always with a list too)

    def eq__safe(self, other):
        if not isinstance(other, Node) or self.type != other.type or self.is_leaf() != other.is_leaf():
            return False
        if not self.is_leaf():
            return len(self.cnt) == len(other.cnt) and all(self.cnt[i].eq__safe(other.cnt[i]) for i in range(len(self.cnt)))
        return self.cnt.eq__safe(other.cnt) if isinstance(self.cnt, Variable) else self.cnt == other.cnt

    def __str_hybrid__(self):
        if self.is_leaf():
            if self.type == COL:
                return "c" + str(self.cnt)  # return "%" + str(self.sons)
            return str(self.cnt)
        if self.type == ADD or self.type == SUB:
            msg = "An hybrid tuple must be of the form {eq|lt|le|ge|gt|ne}{var|integer}{+|-}{var|integer}"
            assert len(self.cnt) == 2, msg
            assert self.cnt[0].type in (INT, COL) and self.cnt[1].type in (INT, COL), msg
            return self.cnt[0].__str_hybrid__() + ("+" if self.type == TypeNode.ADD else "-") + self.cnt[1].__str_hybrid__()
        else:
            assert False, "An hybrid tuple must be of the form col(x)[+or-][integer]"

    def __str__(self):
        if self.type == COL:
            return "%" + str(self.cnt)
        return str(self.cnt) if self.is_leaf() else str(self.type) + "(" + ",".join(str(son) for son in self.cnt) + ")"

    def __repr__(self):
        return self.__str__()

    def is_literal(self):
        if self.type == VAR:
            return self.cnt.dom.is_binary()
        if self.type == NOT:
            return self.cnt[0].type == VAR and self.cnt[0].cnt.dom.is_binary()
        return False

    def logical_inversion(self):
        assert self.type.is_logically_invertible()
        return Node(self.type.logical_inversion(), self.cnt)

    def possible_values(self):
        if self.type.is_predicate_operator():
            return range(0, 2)  # we use a range instead of [0,1] because it simplifies computation (see code below)
        if self.type.min_arity == self.type.max_arity == 0:
            if self.type == VAR:
                av = self.cnt.dom.all_values()  # either a range or a sorted list of integers is returned
                if isinstance(av, range):
                    return av
                return range(av[0], av[0] + 1) if len(av) == 1 else range(av[0], av[1] + 1) if len(av) == 2 and av[0] + 1 == av[1] else av
            if self.type == INT:
                return range(self.cnt, self.cnt + 1)  # we use a range instead of a singleton list because it simplifies computation (see code below)
            assert False, "no such 0-ary type " + str(self.type) + " is expected"
        if self.type.min_arity == self.type.max_arity == 1:
            pv = self.cnt[0].possible_values()
            if self.type == NEG:
                return neg_range(pv) if isinstance(pv, range) else [-v for v in reversed(pv)]
            if self.type == ABS:
                return abs_range(pv) if isinstance(pv, range) else possible_range({abs(v) for v in pv})
            if self.type == TypeNode.SQR:
                return possible_range({v * v for v in pv})
            assert False, "no such 1-ary type " + str(self.type) + " is expected"
        if self.type.min_arity == self.type.max_arity == 2:
            pv1, pv2 = self.cnt[0].possible_values(), self.cnt[1].possible_values()
            all_ranges = isinstance(pv1, range) and isinstance(pv2, range)
            if self.type == SUB:
                return add_range(pv1, neg_range(pv2)) if all_ranges else possible_range({v1 - v2 for v1 in pv1 for v2 in pv2})
            if self.type == DIV:
                return possible_range({v1 // v2 for v1 in pv1 for v2 in pv2 if v2 != 0})
            if self.type == MOD:
                return possible_range({v1 % v2 for v1 in pv1 for v2 in pv2 if v2 != 0})
            if self.type == TypeNode.POW:
                return possible_range({v1 ** v2 for v1 in pv1 for v2 in pv2}, control_int=True)
            if self.type == DIST:
                return abs_range(add_range(pv1, neg_range(pv2))) if all_ranges else possible_range({abs(v1 - v2) for v1 in pv1 for v2 in pv2})
            assert False, "no such 2-ary type " + str(self.type) + " is expected"
        if self.type == TypeNode.IF:
            pv1, pv2 = self.cnt[1].possible_values(), self.cnt[2].possible_values()  # sons[0] is for the condition
            if isinstance(pv1, range) and isinstance(pv2, range) and len(range(max(pv1.start, pv2.start), min(pv1.stop, pv2.stop))) > 0:
                return range(min(pv1.start, pv2.start), max(pv1.stop, pv2.stop))
            return possible_range({v1 for v1 in pv1} | {v2 for v2 in pv2})
        if self.type.min_arity == 2 and self.type.max_arity == float("inf"):
            pvs = [son.possible_values() for son in self.cnt]
            all_ranges = all(isinstance(pv, range) for pv in pvs)
            if self.type == ADD:
                return reduce(add_range, pvs) if all_ranges else possible_range({sum(p) for p in product(*(pv for pv in pvs))})
            if self.type == MUL:
                def multiply(t):
                    res = 1
                    for v in t:
                        res *= v
                    return res

                if all_ranges and all(pv.start >= 0 and pv.step == 1 for pv in pvs):
                    return range(multiply(pv.start for pv in pvs), multiply(pv.stop - 1 for pv in pvs) + 1)
                return possible_range({multiply(p) for p in product(*(pv for pv in pvs))})  # or numpy.prod ?
            # TODO: in case of all_ranges being False, possibility of improving the efficiency of the code below for MIN and MAX
            if self.type == MIN:
                return range(min(pv.start for pv in pvs), min(pv.stop for pv in pvs)) if all_ranges \
                    else possible_range({min(p) for p in product(*(pv for pv in pvs))})
            if self.type == MAX:
                return range(max(pv.start for pv in pvs), max(pv.stop for pv in pvs)) if all_ranges \
                    else possible_range({max(p) for p in product(*(pv for pv in pvs))})
        assert False, "The operator " + str(self.type) + " currently not implemented"

    def mark_as_used(self):
        self.used = True
        if isinstance(self.cnt, list):
            for son in self.cnt:
                Node.mark_as_used(son)

    def _abstraction_recursive(self, cache, harvest_values):
        if self.type in {VAR, INT, SYMBOL}:
            key = id(self)
            if key not in cache:
                cache[key] = len(harvest_values)  # can it be a problem to use it as a key?
                harvest_values.append(self.cnt)
            return "%" + str(cache[key]), harvest_values
        return str(self.type) + "(" + ",".join(son._abstraction_recursive(cache, harvest_values)[0] for son in self.cnt) + ")", harvest_values

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
        if isinstance(self.cnt, list):
            for son in self.cnt:
                son._variables_recursive(harvest)
        if self.type == VAR:
            if self.cnt not in harvest:
                harvest.append(self.cnt)
        return harvest

    def list_of_variables(self):
        return self._variables_recursive([])

    def variable(self, i):
        return self.list_of_variables()[i]

    def flatten_by_associativity(self, node_type):
        while True:
            for i, son in enumerate(self.cnt):
                if self.type == son.type == node_type:
                    self.cnt.pop(i)
                    for s in reversed(son.cnt):
                        self.cnt.insert(i, s)
                    break
            else:  # no break
                break

    def reduce_integers(self):
        if self.type not in {ADD, MUL}:
            return
        ints, sons = [], []
        for son in self.cnt:
            if son.type == INT:
                ints.append(son.cnt)
            else:
                sons.append(son)
        if len(ints) > 1:
            value = reduce(lambda x, y: x + y, ints, 0) if self.type == ADD else reduce(lambda x, y: x * y, ints, 1)
            sons.append(Node(INT, value))
            self.cnt = sons

    def var_val_if_binary_type(self, t):
        if self.type != t or len(self.cnt) != 2 or self.cnt[0].type == self.cnt[1].type:
            return None
        if self.cnt[0].type == VAR and self.cnt[1].type == INT:
            return self.cnt[0].cnt, self.cnt[1].cnt
        elif self.cnt[0].type == INT and self.cnt[1].type == VAR:
            return self.cnt[1].cnt, self.cnt[0].cnt
        else:
            return None

    def tree_val_if_binary_type(self, t):
        if self.type != t or len(self.cnt) != 2 or self.cnt[0].type == self.cnt[1].type:
            return None
        if self.cnt[0].type != INT and self.cnt[1].type == INT:
            return self.cnt[0].cnt if self.cnt[0].type == VAR else self.cnt[0], self.cnt[1].cnt
        elif self.cnt[0].type == INT and self.cnt[1].type != INT:
            return self.cnt[1].cnt if self.cnt[1].type == VAR else self.cnt[1], self.cnt[0].cnt
        else:
            return None

    def first_node_such_that(self, predicate):
        if predicate(self):
            return self
        if self.is_leaf():
            return None
        return next((son for son in self.cnt if son.first_node_such_that(predicate) is not None), None)

    def all_nodes_such_that(self, predicate, harvest):
        if predicate(self):
            harvest.append(self)
        if not self.is_leaf():
            for son in self.cnt:
                son.all_nodes_such_that(predicate, harvest)
        return harvest

    def list_of_vals(self):
        return [n.cnt for n in self.all_nodes_such_that(lambda r: r.type == INT, [])]

    def max_parameter_number(self):
        if self.is_leaf():
            return self.cnt if self.type == PAR else -1  # recall that % ... is not possible in predicates
        return max(son.max_parameter_number() for son in self.cnt)

    def concretization(self, args):
        if self.is_leaf():
            value = self.cnt
            if self.type != PAR:
                return Node(self.type, value)  # we return a similar object
            assert isinstance(value, int)  # we know that the value is an int
            arg = args[value]
            if isinstance(arg, int):
                return Node(INT, arg)
            # and decimal values in the future ?
            if isinstance(arg, str):
                return Node(SYMBOL, arg)
            if isinstance(arg, Node):
                return arg
            return Node(VAR, arg)  # kept at last position for avoiding importing specific parser class
        sons = [son.concretization(args) for son in self.cnt]
        return Node(self.type, sons)

    def _augment(self, offset):
        assert self.type == INT
        return Node(self.type, self.cnt + offset)

    def val(self, i):
        if i == 0:
            f = self.first_node_such_that(lambda n: n.type == INT)
            return f.cnt if f is not None else None
        t = self.list_of_vals()
        return None if i >= len(t) else t[i]

    def canonization(self):
        if self.is_leaf():
            return Node(self.type, self.cnt)  # we return a similar object
        # we will build the canonized form of the node, with the two following local variables
        t = self.type  # possibly, this initial value of type will be modified during canonization
        s = [son.canonization() for son in self.cnt]
        if t.is_symmetric_operator():
            s = sorted(s, key=cmp_to_key(Node.compare_to))  # sons are sorted if the type of the node is symmetric
        # Now, sons are potentially sorted if the type corresponds to a non-symmetric binary relational operator (in
        # that case, we swap sons and arithmetically inverse the operator provided that the ordinal value of the reverse operator is smaller)
        if len(s) == 2 and t.is_not_symmetric_relational_operator():  # if LT,LE,GE,GT
            tt = t.arithmetic_inversion()
            if tt.value[0] < t.value[0] or (tt.value[0] == t.value[0] and Node.compare_to(s[0], s[1]) > 0):
                t = tt
                s = [s[1], s[0]]  # swap
        if len(s) == 1 and t.is_identity_when_one_operand():  # // add(x) becomes x, min(x) becomes x, ...
            return s[0]  # certainly can happen during the canonization process
        node = Node(t, s)

        rules = {
            abs_sub:
                lambda r: Node(DIST, r.cnt[0].cnt),  # abs(sub(a,b)) => dist(a,b)
            not_not:
                lambda r: r.cnt[0].cnt[0],  # not(not(a)) => a
            neg_neg:
                lambda r: r.cnt[0].cnt[0],  # neg(neg(a)) => a
            any_lt_k:
                lambda r: Node(LE, [r.cnt[0], r.cnt[1]._augment(-1)]),  # e.g., lt(x,5) => le(x,4)
            k_lt_any:
                lambda r: Node(LE, [r.cnt[0]._augment(1), r.cnt[1]]),  # e.g., lt(5,x) => le(6,x)
            not_logop:
                lambda r: Node(r.cnt[0].type.logical_inversion(), r.cnt[0].cnt),  # e.g., not(lt(x)) = > ge(x)
            not_symop_any:
                lambda r: Node(r.type.logical_inversion(), [r.cnt[0].cnt[0], r.cnt[1]]),  # e.g., ne(not(x),y) => eq(x,y)
            any_symop_not:
                lambda r: Node(r.type.logical_inversion(), [r.cnt[0], r.cnt[1].cnt[0]]),  # e.g., ne(x,not(y)) => eq(x,y)
            x_mul_k__eq_l:  # e.g., eq(mul(x,4),8) => eq(x,2) and eq(mul(x,4),6) => 0 (false)
                lambda r: Node(EQ, [r.cnt[0].cnt[0], Node(INT, r.val(1) // r.val(0))]) if r.val(1) % r.val(0) == 0 else Node(INT, 0),
            l__eq_x_mul_k:  # e.g., eq(8,mul(x,4)) => eq(2,x) and eq(6,mul(x,4)) => 0 (false)
                lambda r: Node(EQ, [Node(INT, r.val(0) // r.val(1)), r.cnt[1].cnt[0]]) if r.val(0) % r.val(1) == 0 else Node(INT, 0),

            #  we flatten operators when possible; for example add(add(x,y),z) becomes add(x,y,z)
            flattenable:
                lambda r: Node(r.type, flatten([son.cnt if son.type == r.type else son for son in r.cnt])),
            mergeable:
                lambda r: Node(r.type, r.cnt[:-2] +
                               [Node(INT, r.cnt[-2].cnt + r.cnt[-1].cnt if r.type == ADD
                               else r.cnt[-2].cnt * r.cnt[-1].cnt if r.type == MUL
                               else min(r.cnt[-2].cnt, r.cnt[-1].cnt) if r.type in (MIN, AND)
                               else max(r.cnt[-2].cnt, r.cnt[-1].cnt))]),

            # we replace sub by add when possible
            sub_relop_sub:
                lambda r: Node(r.type, [Node(ADD, [r.cnt[0].cnt[0], r.cnt[1].cnt[1]]), Node(ADD, [r.cnt[1].cnt[0], r.cnt[0].cnt[1]])]),
            any_relop_sub:
                lambda r: Node(r.type, [Node(ADD, [r.cnt[0], r.cnt[1].cnt[1]]), r.cnt[1].cnt[0]]),
            sub_relop_any:
                lambda r: Node(r.type, [r.cnt[0].cnt[0], Node(ADD, [r.cnt[1], r.cnt[0].cnt[1]])]),

            # we remove add when possible
            any_add_val__relop__any_add_val:
                lambda r: Node(r.type, [Node(ADD, [r.cnt[0].cnt[0], Node(INT, r.cnt[0].cnt[1].val(0) - r.cnt[1].cnt[1].val(0))]), r.cnt[1].cnt[0]]),
            var_add_val__relop__val:
                lambda r: Node(r.type, [r.cnt[0].cnt[0], Node(INT, r.cnt[1].val(0) - r.cnt[0].cnt[1].val(0))]),
            val__relop__var_add_val:
                lambda r: Node(r.type, [Node(INT, r.cnt[0].val(0) - r.cnt[1].cnt[1].val(0)), r.cnt[1].cnt[0]]),

            imp_logop:
                lambda r: Node(OR, [r.cnt[0].logical_inversion(), r.cnt[1]]),  # seems better to do that
            imp_not:
                lambda r: Node(OR, [r.cnt[0].cnt[0], r.cnt[1]])
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
                t.append(Node(VAR, arg.variable))
            elif isinstance(arg, Variable):
                if arg.inverse:
                    t.append(Node(NEG, [Node(VAR, arg)]))
                elif arg.negation:
                    t.append(Node(NOT, [Node(VAR, arg)]))
                else:
                    t.append(Node(VAR, arg))
            elif isinstance(arg, int):
                t.append(Node(INT, arg))
            elif isinstance(arg, str):
                t.append(Node(SYMBOL, arg))
            elif isinstance(arg, main.constraints.PartialConstraint):
                t.append(Node(TypeNode.PARTIAL, arg))
            else:
                raise ValueError("Problem: bad form of predicate " + str(arg))
        return t

    @staticmethod
    def build(node_type, *args):
        tn = TypeNode.value_of(node_type)  # for handling the cases where type is of type str or TypeConditionOperator
        if tn is SET:
            assert len(args) == 1
            elements = list(args[0])
            sorted_sons = sorted(elements, key=lambda v: str(v)) if len(elements) > 0 and not isinstance(elements[0], int) else sorted(elements)
            return Node(tn, Node._create_sons(*sorted_sons))  # *sorted(args[0])))
        args = flatten(Node.build(SET, arg) if isinstance(arg, (set, range, frozenset)) else arg for arg in args)
        assert tn.is_valid_arity(len(args)), "Problem: Bad arity for node " + tn.name + ". It is " + str(
            len(args)) + " but it should be between " + str(tn.min_arity) + " and " + str(tn.max_arity)
        # Do we activate these simple modifications below?
        # if len(args) == 2 and isinstance(args[0], Variable) and isinstance(args[1], int):
        #     if (args[1] == 1 and type in (TypeNode.MUL, TypeNode.DIV)) or (args[1] == 0 and type in (TypeNode.ADD, TypeNode.SUB)):
        #         return Node(TypeNode.VAR,args[0])
        node = Node(tn, Node._create_sons(*args))
        if tn == EQ and all(son.type.is_predicate_operator() for son in node.cnt):
            node = Node(IFF, node.cnt)
        # Reducing the node
        for t in {ADD, MUL, OR, AND}:
            node.flatten_by_associativity(t)
        node.reduce_integers()
        return node

    @staticmethod
    def set(*args):
        return Node.build(SET, *args)

    @staticmethod
    def _and_or(t, *args):
        assert t in {AND, OR}
        if len(args) == 1:
            if isinstance(args[0], (tuple, list, set, frozenset)):
                args = tuple(args[0])
            if len(args) > 0 and isinstance(args[0], types.GeneratorType):
                args = tuple(list(args[0]))
        args = [arg for arg in args if not (isinstance(arg, (tuple, list, set, frozenset)) and len(arg) == 0)]
        args = [arg[0] if isinstance(arg, (tuple, list, set, frozenset)) and len(arg) == 1 else arg for arg in args]
        if len(args) == 0:
            return t == AND
        args = [Node.conjunction(arg) if isinstance(arg, (tuple, list, set, frozenset)) else arg for arg in args]
        return Node.build(t, *args) if len(args) > 1 else args[0]

    @staticmethod
    def conjunction(*args):
        return Node._and_or(AND, *args)

    @staticmethod
    def disjunction(*args):
        return Node._and_or(OR, *args)

    @staticmethod
    def in_range(x, r):
        assert isinstance(r, range) and r.step == 1
        return Node.build(AND, Node.build(GE, x, r.start), Node.build(LT, x, r.stop))

    @staticmethod
    def not_in_range(x, r):
        assert isinstance(r, range) and r.step == 1
        return Node.build(OR, Node.build(LT, x, r.start), Node.build(GE, x, r.stop))

    @staticmethod
    def compare_to(node1, node2):
        if node1.type != node2.type:
            return node1.type.value[0] - node2.type.value[0]
        if node1.is_leaf() != node2.is_leaf():
            return False
        if node1.is_leaf():
            v1, v2 = node1.cnt, node2.cnt
            if node1.type == VAR:
                return -1 if v1.id < v2.id else 1 if v1.id > v2.id else 0
            if node1.type in (PAR, INT):
                return v1 - v2
            if node1.type == SYMBOL:
                return -1 if v1 < v2 else 1 if v1 > v2 else 0
            if node1.type == SET:
                return 0  # because two empty sets
            assert False
        if len(node1.cnt) < len(node2.cnt):
            return -1
        if len(node1.cnt) > len(node2.cnt):
            return 1
        for i in range(len(node1.cnt)):
            res = Node.compare_to(node1.cnt[i], node2.cnt[i])
            if res != 0:
                return res
        return 0


class NodeAbstract(Node):

    def __init__(self, abstract_operation: TypeAbstractOperation, args):
        super().__init__(SPECIAL, args)
        self.abstract_operation = abstract_operation

    def __str__(self):
        return str(self.abstract_operation) + " :" + str(self.cnt) if self.is_leaf() else str(self.type) + "(" + ",".join(
            str(son) for son in self.cnt) + ")"


# special nodes (with 0 argument/son)
any_node = Node(SPECIAL, "any")
any_cond = Node(SPECIAL, "anyc")  # any under condition
var = Node(SPECIAL, "var")
val = Node(SPECIAL, "val")
var_or_val = Node(SPECIAL, "var-or-val")
any_add_val = Node(SPECIAL, "any-add-val")
var_add_val = Node(SPECIAL, "var-add-val")
sub = Node(SPECIAL, "sub")
non = Node(SPECIAL, "not")
set_vals = Node(SPECIAL, "set-vals")
min_vars = Node(SPECIAL, "min-vars")
max_vars = Node(SPECIAL, "max-vars")
logic_vars = Node(SPECIAL, "logic-vars")
add_vars = Node(SPECIAL, "add-vars")
mul_vars = Node(SPECIAL, "mul-vars")
add_mul_vals = Node(SPECIAL, "add-mul-vals")
add_mul_vars = Node(SPECIAL, "add-mul-vars")


class Matcher:

    def __init__(self, target: Node, p=None):
        self.target = target
        self.p = p

    def valid_for_special_target_node(self, node: Node, level: int):
        return self.p is None or self.p(node, level)

    def _matching(self, source: Node, target: Node, level: int):
        # print("matching ", str(source), str(target), level)
        if target is any_node:  # any node (i.e., full abstract node) => everything matches
            return True
        if target is any_cond:  # any node under condition (the difference with SPECIAL only, is that sons are not considered recursively)
            return self.valid_for_special_target_node(source, level)
        if target is var:
            return source.type == VAR
        if target is val:
            return source.type == INT
        if target is var_or_val:
            return source.type in (VAR, INT)
        if target is any_add_val:
            return source.type == ADD and len(source.cnt) == 2 and source.cnt[1].type == INT
        if target is var_add_val:
            return source.type == ADD and len(source.cnt) == 2 and source.cnt[0].type == VAR and source.cnt[1].type == INT
        if target is sub:
            return source.type == SUB
        if target is non:
            return source.type == NOT
        if target is set_vals:  # abstract set => we control that source is either an empty set or a set built on only longs
            return source.type == SET and all(son.type == INT for son in source.cnt)
        if target is min_vars:  # abstract min => we control that source is a min built on only variables
            return source.type == MIN and len(source.cnt) >= 2 and all(son.type == VAR for son in source.cnt)
        if target is max_vars:  # abstract max => we control that source is a max built on only variables
            return source.type == MAX and len(source.cnt) >= 2 and all(son.type == VAR for son in source.cnt)
        if target is logic_vars:
            return source.type.is_logical_operator() and len(source.cnt) >= 2 and all(son.type == VAR for son in source.cnt)
        if target is add_vars:
            return source.type == ADD and len(source.cnt) >= 2 and all(son.type == VAR for son in source.cnt)
        if target is mul_vars:
            return source.type == MUL and len(source.cnt) >= 2 and all(son.type == VAR for son in source.cnt)
        if target is add_mul_vals:
            return source.type == ADD and len(source.cnt) >= 2 and all(son.type == VAR or x_mul_k.matches(son) for son in source.cnt)
        if target is add_mul_vars:
            return source.type == ADD and len(source.cnt) >= 2 and all(x_mul_y.matches(son) for son in source.cnt)
        if target.type != SPECIAL:
            if target.is_leaf() != source.is_leaf() or target.type != source.type:
                return False
        else:
            if isinstance(target, NodeAbstract):
                ao = target.abstract_operation
                if ao == ARIOP:
                    if not source.type.is_arithmetic_operator():
                        return False
                if ao == RELOP:
                    if not source.type.is_relational_operator():
                        return False
                if ao == SETOP:
                    if source.type not in (IN, NOTIN):
                        return False
                if ao == UNALOP:
                    if source.type not in (ABS, NEG, TypeNode.SQR, NOT):
                        return False
                if ao == SYMOP:
                    if source.type not in (EQ, NE):
                        return False
            elif not self.valid_for_special_target_node(source, level):
                return False
        if not isinstance(target, NodeAbstract) and target.is_leaf():
            return True  # it seems that we have no more control to do
        return len(target.cnt) == len(source.cnt) and all(self._matching(source.cnt[i], target.cnt[i], level + 1) for i in range(len(target.cnt)))

    def matches(self, tree: Node):
        return self._matching(tree, self.target, 0)

    def __str__(self):
        return str(self.target) + " : " + str(self.p)

    def __repr__(self):
        return self.__str__()


# # # Canonization

x_mul_k = Matcher(Node(MUL, [var, val]))
x_mul_y = Matcher(Node(MUL, [var, var]))
k_mul_x = Matcher(Node(MUL, [val, var]))  # used in some other contexts (when non canonized forms)
abs_sub = Matcher(Node(ABS, Node(SUB, [any_node, any_node])))
not_not = Matcher(Node(NOT, Node(NOT, any_node)))
neg_neg = Matcher(Node(NEG, Node(NEG, any_node)))
any_lt_k = Matcher(Node(LT, [any_node, val]))
k_lt_any = Matcher(Node(LT, [val, any_node]))
not_logop = Matcher(Node(NOT, any_cond), lambda r, p: p == 1 and r.type.is_logically_invertible())
not_symop_any = Matcher(NodeAbstract(SYMOP, [non, any_node]))
any_symop_not = Matcher(NodeAbstract(SYMOP, [any_node, non]))
x_mul_k__eq_l = Matcher(Node(EQ, [Node(MUL, [var, val]), val]))
l__eq_x_mul_k = Matcher(Node(EQ, [val, Node(MUL, [var, val])]))
flattenable = Matcher(any_cond, lambda r, p: p == 0 and r.type.is_flattenable() and any(son.type == r.type for son in r.cnt))
mergeable = Matcher(any_cond, lambda r, p: p == 0 and r.type.is_mergeable() and len(r.cnt) >= 2 and r.cnt[-1].type == r.cnt[- 2].type == INT)
sub_relop_sub = Matcher(NodeAbstract(RELOP, [sub, sub]))
any_relop_sub = Matcher(NodeAbstract(RELOP, [any_node, sub]))
sub_relop_any = Matcher(NodeAbstract(RELOP, [sub, any_node]))
any_add_val__relop__any_add_val = Matcher(NodeAbstract(RELOP, [any_add_val, any_add_val]))
var_add_val__relop__val = Matcher(NodeAbstract(RELOP, [var_add_val, val]))
val__relop__var_add_val = Matcher(NodeAbstract(RELOP, [val, var_add_val]))
imp_logop = Matcher(Node(IMP, [any_cond, any_node]), lambda r, p: p == 1 and r.type.is_logically_invertible())
imp_not = Matcher(Node(IMP, [Node(NOT, any_node), any_node]))

# # # recognizing constraints (primitives)

# unary
x_relop_k = Matcher(NodeAbstract(RELOP, [var, val]))
k_relop_x = Matcher(NodeAbstract(RELOP, [val, var]))
x_ariop_k__relop_l = Matcher(NodeAbstract(RELOP, [NodeAbstract(ARIOP, [var, val]), val]))
l_relop__x_ariop_k = Matcher(NodeAbstract(RELOP, [val, NodeAbstract(ARIOP, [var, val])]))
x_setop_S = Matcher(NodeAbstract(SETOP, [var, set_vals]))
x_in_intvl = Matcher(Node(AND, [Node(LE, [var, val]), Node(LE, [val, var])]))
x_notin_intvl = Matcher(Node(OR, [Node(LE, [var, val]), Node(LE, [val, var])]))

# binary
x_relop_y = Matcher(NodeAbstract(RELOP, [var, var]))
x_ariop_y__relop_k = Matcher(NodeAbstract(RELOP, [NodeAbstract(ARIOP, [var, var]), val]))
k_relop__x_ariop_y = Matcher(NodeAbstract(RELOP, [val, NodeAbstract(ARIOP, [var, var])]))
x_relop__y_ariop_k = Matcher(NodeAbstract(RELOP, [var, NodeAbstract(ARIOP, [var, val])]))
y_ariop_k__relop_x = Matcher(NodeAbstract(RELOP, [NodeAbstract(ARIOP, [var, val]), var]))
logic_y_relop_k__eq_x = Matcher(Node(EQ, [NodeAbstract(RELOP, [var, val]), var]))
logic_k_relop_y__eq_x = Matcher(Node(EQ, [NodeAbstract(RELOP, [val, var]), var]))
unalop_x__eq_y = Matcher(Node(EQ, [NodeAbstract(UNALOP, var), var]))

# ternary
x_ariop_y__relop_z = Matcher(NodeAbstract(RELOP, [NodeAbstract(ARIOP, [var, var]), var]))
z_relop__x_ariop_y = Matcher(NodeAbstract(RELOP, [var, NodeAbstract(ARIOP, [var, var])]))
logic_y_relop_z__eq_x = Matcher(Node(EQ, [NodeAbstract(RELOP, [var, var]), var]))

# logic
logic_X = Matcher(logic_vars)
logic_X__eq_x = Matcher(Node(EQ, [logic_vars, var]))
logic_X__ne_x = Matcher(Node(NE, [logic_vars, var]))

# extremum
min_relop = Matcher(NodeAbstract(RELOP, [min_vars, var_or_val]))
max_relop = Matcher(NodeAbstract(RELOP, [max_vars, var_or_val]))

# sum
add_vars__relop = Matcher(NodeAbstract(RELOP, [add_vars, var_or_val]))
add_mul_vals__relop = Matcher(NodeAbstract(RELOP, [add_mul_vals, var_or_val]))
add_mul_vars__relop = Matcher(NodeAbstract(RELOP, [add_mul_vars, var_or_val]))
