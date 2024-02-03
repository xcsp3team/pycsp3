import re

from pycsp3 import tools
from pycsp3.classes import main
from pycsp3.classes.auxiliary.enums import TypeCtr, TypeCtrArg
from pycsp3.classes.main.variables import Variable
from pycsp3.tools.inspector import checkType
from pycsp3.tools.utilities import flatten, is_containing, warning, ANY, combinations


class Entity:
    def __init__(self, name, comment=None, tags=None):
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
            self.tags.extend(tok for tok in toks if tok != "" and tok not in self.tags)
        return self

    def same_type_and_basic_attributes(self, other):
        return type(self) is type(other) and self.comment == other.comment and self.tags == other.tags

    def mergeable_with(self, other):
        return (type(self) is type(other) and (self.comment == other.comment or None in {self.comment, other.comment})
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
    def __init__(self, x, comment=None, tags=None):
        super().__init__(x.id, comment, tags)
        self.variable = x
        VarEntities.items.append(self)
        VarEntities.varToEVar[x] = self

    def get_type(self):
        return self.variable.dom.get_type()

    def __call__(self):
        return self.variable


class EVarArray(Entity):
    def __init__(self, X, name, comment=None, tags=None):
        super().__init__(name, comment, tags)
        self.name = name
        self.variables = X
        self.flatVars = flatten(X)
        if len(self.flatVars) == 0:
            return
        # assert len(self.flatVars) != 0, "Array of variable empty !"
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

    def __bool__(self):
        warning("A constraint is evaluated as a Boolean (technically, __bool__ is called)"
                + "\n\tIt is likely a problem with the use of logical operators."
                + "\n\tFor example, you must write Or(AllDifferent(x), (x[0] == x[2])) instead of AllDifferent(x) or (x[0] == x[2])"
                + "\n\t  or you must post separately the two constraints."
                + "\n\tSee also the end of section about constraint Intension in chapter 'Twenty popular constraints' of the guide.\n")
        return True

    def to_table(self):  # experimental
        c = self.constraint
        if c.name == TypeCtr.ALL_DIFFERENT and c.arguments[TypeCtrArg.LIST].lifted and TypeCtrArg.EXCEPT not in c.arguments:
            lists = c.arguments[TypeCtrArg.LIST].content
            if all(x.dom.is_binary() for x in flatten(lists)):
                r = len(lists[0])
                T = [tuple(v if j == i else ANY for j in range(r)) + tuple((v + 1) % 2 if j == i else ANY for j in range(r)) for i in range(r) for v in (0, 1)]
                return [(l1, l2) in T for l1, l2 in combinations(lists, 2)]
        return self


class ECtrs(Entity):
    """ Class for representing sets of constraints """

    def __init__(self, constraints=None):
        super().__init__(None)  # no need to have an id here
        assert isinstance(constraints, list)
        self.entities = [c for c in constraints if c is not None]
        if all(isinstance(c, ECtr) for c in self.entities):
            t = []
            for c in self.entities:
                # if any(c.constraint == cc.constraint for cc in t):
                if any(tools.curser.OpOverrider.disable().execute(c.constraint == cc.constraint) for cc in t):
                    continue
                t.append(c)
                if len(t) > 1:
                    break
            else:
                self.entities = t

    def _flat_constraints(self, t):
        for e in self.entities:
            if isinstance(e, ECtr):
                t.append(e.constraint)
            elif isinstance(e, ECtrs):
                e._flat_constraints(t)
            elif isinstance(e, EMetaCtr):
                t.append(e)
        return t

    def flat_constraints(self):
        return self._flat_constraints([])

    def __repr__(self):
        return "\n".join(str(e) for e in self.flat_constraints())


class EToGather(ECtrs):
    #  Constraints possibly stored in a group (the user asked to gather these constraints)

    def __init__(self, constraints):
        super().__init__(constraints)


class EToSatisfy(ECtrs):
    # Constraints possibly stored in several groups or several blocks (block built when a group is not possible) or stand-alone constraints

    def __init__(self, constraints):
        assert constraints is not None
        constraints = [c for c in constraints if c is not None]
        if len(constraints) > 0:
            CtrEntities.items.append(self)
            super().__init__(constraints)

    def delete(self, i=None):
        if i is None:
            self.entities = []
        elif len(self.entities) == 1 and isinstance(self.entities[0], ECtrs):
            del self.entities[0].entities[i]
        else:
            del self.entities[i]


class EGroup(ECtrs):
    # Constraints in a group

    def __init__(self):
        super().__init__([])
        self.abstraction = ""
        self.all_args = []


class EBlock(ECtrs):
    def __init__(self, constraints):
        super().__init__(constraints)


class ESlide(ECtrs):
    # Constraints possibly stored as a slide meta-constraint (the user asked to slide the constraints)

    def __init__(self, constraints):
        super().__init__(constraints)
        self.scope = []
        self.offset = False
        self.circular = False


class EMetaCtr(Entity):
    def __init__(self, name, constraints, min_arity, max_arity=None):
        super().__init__(name)  # no need to have an id here
        assert isinstance(constraints, list)
        self.entities = [c for c in constraints if c is not None]
        checkType(self.entities, [ECtr, EMetaCtr])
        assert len(self.entities) >= min_arity, "At least " + str(min_arity) + " components must be specified in the meta-constraint"
        assert max_arity is None or len(self.entities) <= max_arity, "At most " + str(max_arity) + " components must be specified in the meta-constraint"

    def __repr__(self):
        return str(self.id) + "(" + ",".join(str(e.constraint) for e in self.entities) + ")"


class EAnd(EMetaCtr):
    def __init__(self, constraints):
        super().__init__(TypeCtr.AND, constraints, 2)


class EOr(EMetaCtr):
    def __init__(self, constraints):
        super().__init__(TypeCtr.OR, constraints, 2)


class ENot(EMetaCtr):
    def __init__(self, constraints):
        super().__init__(TypeCtr.NOT, constraints, 1, 1)


class EXor(EMetaCtr):
    def __init__(self, constraints):
        super().__init__(TypeCtr.XOR, constraints, 2)


class EIfThen(EMetaCtr):
    def __init__(self, constraints):
        super().__init__(TypeCtr.IF_THEN, constraints, 2, 2)


class EIfThenElse(EMetaCtr):
    def __init__(self, constraints):
        super().__init__(TypeCtr.IF_THEN_ELSE, constraints, 3, 3)


class EIff(EMetaCtr):
    def __init__(self, constraints):
        super().__init__(TypeCtr.IFF, constraints, 2, 2)


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
                if isinstance(item, EVar) and item.id == s:
                    return item
        return None


class CtrEntities:
    items = []  # contains EToSatisfy objects


class ObjEntities:
    items = []


class AnnEntities:
    items = []
    items_types = []


def clear():
    """
    Removes everything that was declared (variables) or posted (constraints, objective)
    """
    VarEntities.items = []
    VarEntities.varToEVar = dict()
    VarEntities.varToEVarArray = dict()
    VarEntities.prefixToEVarArray = dict()
    CtrEntities.items = []
    ObjEntities.items = []
    AnnEntities.items = []
    AnnEntities.items_types = []
    Variable.name2obj = dict()
    main.constraints.auxiliary.obj = None
    # Diffs.reset()
