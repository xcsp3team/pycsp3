from enum import Enum, unique
from functools import reduce

from pycsp3.classes.auxiliary.types import auto
from pycsp3.classes.main import variables
from pycsp3.dashboard import options
from pycsp3.tools import utilities


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
        if options.debug:
            print("New stand-alone variable (entity): ", self)

    def get_type(self):
        return self.variable.dom.get_type()

    def __call__(self):
        return self.variable


class EVarArray(Entity):
    def __init__(self, X, name, comment=None, tags=[]):
        super().__init__(name, comment, tags)
        self.name = name
        self.variables = X
        self.flatVars = utilities.flatten(X)
        assert len(self.flatVars) != 0, "Array of variable empty !"
        self.size = []
        curr = self.variables
        while isinstance(curr, list):
            self.size.append(len(curr))
            curr = curr[0]
        VarEntities.items.append(self)
        for x in self.flatVars:
            VarEntities.varToEVarArray[x] = self
        VarEntities.prefixToEVarArray[name] = self
        if options.debug:
            print("New VarArray entity: ", self)

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

    # class CtrEntity(ModelingEntity):
    """ Class to represent stand-alone constraints """


class ECtr(Entity):
    def __init__(self, c):
        super().__init__(None)  # no need to have an id for CtrEntity objects
        if c is None:
            self.constraint = None
            print("Warning: a constraint is None")
        else:
            self.constraint = c
            # CtrEntities.allEntities.append(self)
            if options.debug is True:
                print("New CtrEntity ", type(self), " ", str(c))


class ECtrs(Entity):
    """ Class to represent sets of constraints """

    def __init__(self, constraints=None):
        super().__init__(None)  # no need to have an id for CtrArray objects
        assert constraints is not None and isinstance(constraints, list)
        self.entities = [c for c in constraints if c is not None]
        if options.debug is True:
            print("New CtrArray entity: ", type(self), " ", self)


class EToGather(ECtrs):
    ''' Constraints possibly in a group (user ask to gather these constraints)'''

    def __init__(self, constraints):
        super().__init__(constraints)


class EToSatisfy(ECtrs):
    ''' Constraints possibly in several groups or several blocks (automatic block when a group is not possible) or alones'''

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
    ''' Constraints possibly in a slide (user ask to slide these constraints)'''

    def __init__(self, constraints):
        super().__init__(constraints)
        self.scope = []
        self.offset = False
        self.circular = False


class EIfThenElse(ECtrs):
    def __init__(self, constraints):
        super().__init__(constraints)


class EObjective(Entity):
    def __init__(self, c):
        if c is None:
            return
        super().__init__(None)  # no need to have an id for CtrEntity objects
        self.constraint = c
        ObjEntities.items.append(self)
        if options.debug is True:
            print("New CtrObjective ", type(self), " ", str(c))


class EAnnotation(Entity):
    def __init__(self, c):
        if c is None:
            return
        super().__init__(None)  # no need to have an id for CtrEntity objects
        self.constraint = c
        AnnEntities.items.append(self)
        AnnEntities.items_types.append(type(c))
        if options.debug is True:
            print("New CtrAnnotation ", type(self), " ", str(c))


class VarEntities:
    items = []
    varToEVar = dict()
    varToEVarArray = dict()
    prefixToEVarArray = dict()


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

    ''' Unary'''
    NEG, ABS, SQR, NOT, CARD, HULL, CONVEX, SQRT, EXP, LN, SIN, COS, TAN, ASIN, ACOS, ATAN, SINH, COSH, TANH = ((id, 1, 1) for id in auto(19))

    ''' Binary '''
    SUB, DIV, MOD, POW, DIST, LT, LE, GE, GT, IN, NOTIN, IMP, DIFF, DJOINT, SUBSET, SUBSEQ, SUPSEQ, SUPSET, FDIV, FMOD, = ((id, 2, 2) for id in auto(20))

    ''' Ternary '''
    IF = (auto(), 3, 3)

    ''' N-ary (2 to infinity)'''
    ADD, MUL, MIN, MAX, NE, EQ, AND, OR, XOR, IFF, UNION, INTER, SDIFF = ((id, 2, float("inf")) for id in auto(13))

    SET = (auto(), 0, float("inf"))

    ''' 0-ary '''
    VAR, PAR, INT, RATIONAL, DECIMAL, SYMBOL = ((id, 0, 0) for id in auto(6))

    SPECIAL = (auto(), 0, float("inf"))

    def is_leaf(self):
        return self in {TypeNode.VAR, TypeNode.PAR, TypeNode.INT, TypeNode.RATIONAL, TypeNode.DECIMAL, TypeNode.SYMBOL, TypeNode.SPECIAL}

    def is_valid_arity(self, k):
        return self.min_arity <= k <= self.max_arity


class Node(Entity):
    all_nodes = []

    def __init__(self, type, args):
        super().__init__(None)
        Node.all_nodes.append(self)
        self.used = False
        self.type = type
        self.leaf = type.is_leaf()
        self.sons = args  # TODO sons is used whatever this is a parent or a leaf node; change the name of this field ??? to content ??
        self.abstractTree = None
        self.abstractValues = None

    # def __eq__(self, other):
    #     return False

    def __str__(self):
        return str(self.sons) if self.type.is_leaf() else str(self.type) + "(" + ",".join(str(son) for son in self.sons) + ")"

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
            return self.sons[0].sons, self.sons[1].sons
        elif self.sons[0].type == TypeNode.INT and self.sons[1].type != TypeNode.INT:
            return self.sons[1].sons, self.sons[0].sons
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
            elif isinstance(arg, variables.NotVariable):
                t.append(Node(TypeNode.NOT, [Node(TypeNode.VAR, arg.variable)]))
            elif isinstance(arg, variables.NegVariable):
                t.append(Node(TypeNode.NEG, [Node(TypeNode.VAR, arg.variable)]))
            elif isinstance(arg, variables.Variable):
                t.append(Node(TypeNode.VAR, arg))
            elif isinstance(arg, int):
                t.append(Node(TypeNode.INT, arg))
            elif isinstance(arg, str):
                t.append(Node(TypeNode.SYMBOL, arg))
            else:
                raise ValueError("Problem: bad form of predicate " + arg)
        return t

    @staticmethod
    def build(type, *args):
        if type is TypeNode.SET:
            assert len(args) == 1
            return Node(type, Node._create_sons(*sorted(args[0])))
        args = utilities.flatten(Node.build(TypeNode.SET, arg) if isinstance(arg, (set, range, frozenset)) else arg for arg in args)
        assert type.is_valid_arity(len(args)), "Problem: Bad arity for node " + type.name + ". It is " + str(
            len(args)) + " but it should be between " + str(type.arityMin) + " and " + str(type.arityMax)
        node = Node(type, Node._create_sons(*args))
        # Reducing the node
        for t in {TypeNode.ADD, TypeNode.MUL, TypeNode.OR, TypeNode.AND, TypeNode.EQ}:
            node.flatten_by_associativity(t)
        node.reduce_integers()
        if options.debug:
            print("New node:", node)
        return node

    @staticmethod
    def set(*args):
        return Node.build(TypeNode.SET, *args)
