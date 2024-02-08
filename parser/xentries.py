import re
from functools import reduce

from ppycsp3.parser import methods
from ppycsp3.parser.constants import DELIMITER_WHITESPACE, VALID_IDENTIFIER, ID, CLASS, RANK, OTHERS
from pycsp3.classes.auxiliary.conditions import ConditionVariable, ConditionParameter
from pycsp3.classes.auxiliary.enums import TypeVar, TypeCtr, TypeCtrArg, TypeObj, TypeAnn, TypeRank
from pycsp3.classes.main.constraints import Parameter
from pycsp3.classes.main.variables import Domain, Variable
from pycsp3.classes.nodes import TypeNode, Node
from pycsp3.tools.utilities import check_int


# The class root of any entry in variables, constraints and objectives. The basic attributes id, class and note are managed here.
class XEntry:

    def __init__(self, entry_id=None, entry_type=None):
        self.id = entry_id
        self.check_id()
        self.type = entry_type
        self.classes = []
        self.attributes = {}
        self.flags = set()

    def check_id(self):
        if self.id is not None:
            assert re.match(VALID_IDENTIFIER, self.id), "Badly formed id : " + self.id

    def copy_attributes_of(self, elt):
        for k, v in elt.attrib.items():
            v = v.strip()
            if v.lower() == "true":
                v = True
            elif v.lower() == "false":
                v = False
            elif check_int(v):
                v = int(v)
            elif k == RANK:
                v = TypeRank[v.upper()]
            self.attributes[k] = v
        if ID in self.attributes:
            assert self.id is None
            self.id = self.attributes[ID]
            self.check_id()
        if CLASS in self.attributes:
            assert len(self.classes) == 0
            self.classes = re.split(DELIMITER_WHITESPACE, self.attributes[CLASS])


"""
------------------------------------
Section about variables being parsed
------------------------------------
"""


class XVarAbstract(XEntry):

    def __init__(self, entry_id, var_type):
        assert entry_id is not None and isinstance(var_type, TypeVar)
        super().__init__(entry_id, var_type)


class XVar(XVarAbstract, Variable):

    def __init__(self, var_id, var_type, domain, indexes=None):
        name = var_id + ("" if indexes is None else ("[" + "][".join(map(str, indexes)) + "]"))
        XVarAbstract.__init__(self, name, var_type)
        Variable.__init__(self, name, Domain(domain))
        self.domain = domain
        self.degree = None  # the degree will be computed later

    def __str__(self):
        return self.id  # + " in " + str(self.domain)

    def __repr__(self):
        return self.__str__()

    def increment_degree(self, v=1):
        self.degree = v if self.degree is None else (self.degree + v)


class XVarArray(XVarAbstract):

    def __init__(self, var_array_id, var_type, size, dom=None):
        super().__init__(var_array_id, var_type)
        self.size = size
        # The flat (one-dimensional) array, below, composed of all variables contained in the (multidimensional) array.
        # This way, we can easily deal with arrays of any dimensions.
        self.variables = [None] * reduce(lambda x, y: x * y, size)
        if dom is not None:
            self.build_vars_with(dom)

    # Builds a variable with the specified domain for each unoccupied cell of the flat array.
    def build_vars_with(self, dom):
        indexes = [0] * len(self.size)
        for i in range(len(self.variables)):
            if self.variables[i] is None:
                self.variables[i] = XVar(self.id, self.type, dom, indexes)
            for j in range(len(self.size) - 1, -1, -1):
                indexes[j] += 1
                if indexes[j] == self.size[j]:
                    indexes[j] = 0
                else:
                    break

    # Computes the next multidimensional index with respect to specified ranges. Returns false if non exists.
    @staticmethod
    def increment_indexes(indexes, ranges):
        for j in range(len(indexes) - 1, -1, -1):
            if not isinstance(ranges[j], int):
                indexes[j] += 1
                if indexes[j] >= ranges[j].stop:
                    indexes[j] = ranges[j].start
                else:
                    return True
        return False  # as it was not possible to increment the specified array of indexes

    # Transforms a multi-dimensional index into a flat index.
    def flat_index_for(self, indexes):
        idx, nb = 0, 1
        for i in range(len(indexes) - 1, -1, -1):
            idx += indexes[i] * nb
            nb *= self.size[i]
        return idx

    # Any variable that matches one compact form present in the specified string is built with the specified domain.
    def set_dom(self, target, dom):  # target is the value of the attribute "for" of arrays
        if target == OTHERS:
            return self.build_vars_with(dom)
        tokens = re.split(DELIMITER_WHITESPACE, target)
        for token in tokens:
            pos = token.index("[")  # we necessarily have this character (since we have an array)
            prefix, suffix = token[:pos], token[pos:]
            assert self.id == prefix, "one value of attribute 'for' incorrect in array " + str(id)
            index_expressions = methods.parse_indexes(self.size, suffix)  # we get either int or range values
            indexes = [index if isinstance(index, int) else index.start for index in index_expressions]
            while True:
                i = self.flat_index_for(indexes)
                assert self.variables[i] is None, "Problem with two domain definitions for the same variable"
                self.variables[i] = XVar(self.id, self.type, dom, indexes)
                if not XVarArray.increment_indexes(indexes, index_expressions):
                    break

    # Returns the list of variables that match the specified compact form. For example, for x[1..3], the list will contain x[1] x[2] and x[3].
    def vars_for(self, compact_form):
        t = []
        index_expressions = methods.parse_indexes(self.size, compact_form)  # we get either int or range values
        indexes = [index if isinstance(index, int) else index.start for index in index_expressions]  # first index
        while True:
            i = self.flat_index_for(indexes)
            assert self.variables[i] is not None
            t.append(self.variables[i])
            if not XVarArray.increment_indexes(indexes, index_expressions):
                break
        return t

    def var_at(self, indexes):
        return self.variables[self.flat_index_for(indexes)]

    def __str__(self):
        return self.id + " of size " + str(self.size) + " : " + " ".join(str(x) for x in self.variables)


# Returns the sequence of domains for the variables in the specified list if one-dimensional,
# or in the first row of the specified two-dimensional list, provided that variables of the other rows have similar domains.
def domains_for(variables):
    assert len(variables) > 0
    one_dimension = isinstance(variables[0], XVar)
    tmp = variables if one_dimension else variables[0]
    assert all(isinstance(x, XVar) for x in tmp)
    domains = [x.domain for x in tmp]
    if not one_dimension:
        if any(x.domain != domains[i] for row in variables for i, x in enumerate(row)):
            return None
    return domains


def collect_vars_in(obj, harvest):
    assert isinstance(harvest, set)
    if isinstance(obj, list):
        for v in obj:
            collect_vars_in(v, harvest)
    elif isinstance(obj, Node):  # possible if view
        harvest.update(obj.scope())
    elif isinstance(obj, XVar):
        harvest.add(obj)
    elif isinstance(obj, ConditionVariable):
        assert isinstance(obj.variable, XVar)
        harvest.add(obj.variable)
    return harvest


"""
------------------------------------
Section about constraints being parsed
------------------------------------
"""


class XCtrAbstract(XEntry):

    def __init__(self, entry_id=None, entry_type=None):
        super().__init__(entry_id, entry_type)
        self.variables = None  # used as a cache (lazy initialization)

    # Returns the set of variables involved in this element
    def involved_vars(self):
        if isinstance(self, XCtr) and self.abstraction is not None:  # so as not to use a cache when abstraction
            return self.collect_vars(set())
        if self.variables is None:
            self.variables = self.collect_vars(set())
        return self.variables

    # Collect the set of variables involved in this element, and add them to the specified set
    def collect_vars(self, harvest):
        pass

    # Returns true iff this element is subject to abstraction, i.e., contains parameters (tokens of the form %i or %...).
    def subject_to_abstraction(self):
        pass

    def __str__(self):
        return str(self.attributes)


# The class for representing a child element of a constraint (or constraint template).
# For example, it is used to represent an element <list> or an element <supports>
class XCtrArg(XCtrAbstract):

    def __init__(self, ctr_arg_type, value, ctr_arg_id=None):
        assert isinstance(ctr_arg_type, TypeCtrArg)
        super().__init__(ctr_arg_id, ctr_arg_type)
        self.value = value

    @staticmethod
    def _check(obj, predicate):
        if isinstance(obj, (list, tuple)):
            return any(XCtrArg._check(v, predicate) for v in obj)
        if isinstance(obj, Node):
            return obj.first_node_satisfying(lambda n: n.is_leaf() and predicate(n.cnt)) is not None
        return predicate(obj)

    def collect_vars(self, harvest):
        if self.type in (TypeCtrArg.SUPPORTS, TypeCtrArg.CONFLICTS):
            return harvest
        if self.type == TypeCtrArg.MAP:  # for adhoc constraints
            for k, v in self.value.items():
                collect_vars_in(v, harvest)
            return harvest
        return collect_vars_in(self.value, harvest)

    def subject_to_abstraction(self):
        if self.type == TypeCtrArg.FUNCTION and self.value.first_node_satisfying(lambda n: n.type == TypeNode.PAR) is not None:
            return True
        if self.type == TypeCtrArg.CONDITION and isinstance(self.value, ConditionParameter):
            return True
        return XCtrArg._check(self.value, lambda obj: isinstance(obj, Parameter))  # check if a parameter somewhere inside the value

    def is_totally_abstract(self):
        if not isinstance(self.value, list):
            return isinstance(self.value, Parameter)
        return len(self.value) > 0 and all(isinstance(v, Parameter) for v in self.value)

    def __str__(self):
        return str(self.type) + ": " + ((" ".join(str(v) for v in self.value)) if isinstance(self.value, list) else str(self.value))


class XCtr(XCtrAbstract):

    def __init__(self, ctr_type, ctr_args=None, ctr_id=None):
        if ctr_args is None:
            ctr_args = []
        assert isinstance(ctr_type, TypeCtr) and all(isinstance(ca.type, TypeCtrArg) for ca in ctr_args)
        super().__init__(ctr_id, ctr_type)
        self.ctr_args = ctr_args
        self.abstraction = None
        abstract_positions = [i for i in range(len(ctr_args)) if ctr_args[i].subject_to_abstraction()]
        if len(abstract_positions) > 0:
            args = [self.ctr_args[i] for i in abstract_positions]
            assert all(arg.type == TypeCtrArg.FUNCTION or arg.is_totally_abstract() or isinstance(arg.value, ConditionParameter) for arg in args)
            self.abstraction = XAbstraction(args)

    def collect_vars(self, harvest):
        for crt_arg in self.ctr_args:
            crt_arg.collect_vars(harvest)
        return harvest

    def subject_to_abstraction(self):
        return self.abstraction is not None

    def __str__(self):
        return str(self.type) + "\n\t" + "\n\t".join(str(ca) for ca in self.ctr_args)


# The class used for elements <block>
class XBlock(XCtrAbstract):

    def __init__(self, subentries, block_id=None):
        super().__init__(block_id, None)
        self.subentries = subentries  # The list of elements contained in this block

    def collect_vars(self, harvest):
        for e in self.subentries:
            e.collect_vars(harvest)
        return harvest

    def subject_to_abstraction(self):
        return any(e.subject_to_abstraction() for e in self.subentries)

    def __str__(self):
        return "Block " + super.__str__(self) + "\n\t" + "\n\t".join(str(e) for e in self.subentries)


class XGroup(XCtrAbstract):

    def __init__(self, template, all_args, group_id=None):
        assert isinstance(template, XCtr)
        super().__init__(group_id, None)
        self.template = template
        self.all_args = all_args
        self._template_scope = self.template.involved_vars()
        self._scopes = [None] * len(all_args)  # cache

    def get_scope(self, i):
        if self._scopes[i] is None:
            self._scopes[i] = self._template_scope.union(collect_vars_in(self.all_args[i], set()))
        return self._scopes[i]

    def collect_vars(self, harvest):
        self.template.collect_vars(harvest)
        for e in self.all_args:
            collect_vars_in(e, harvest)
        return harvest

    def subject_to_abstraction(self):
        return True

    def __str__(self):
        return "Group " + super.__str__(self) + "\n\t" + str(self.template) + "\n\t" + "\n\t".join(str(a) for a in self.all_args)


# The class for representing the meta-constraint <slide>.
class XSlide(XCtrAbstract):

    def __init__(self, lists, offsets, collects, template, scopes, slide_id=None):
        assert all(isinstance(t, XCtrArg) for t in lists) and isinstance(template, XCtr)
        super().__init__(slide_id, None)
        self.lists = lists
        self.offsets = offsets
        self.collects = collects
        self.template = template
        self.scopes = scopes

    # Builds the scopes of the constraints involved in the meta-constraint.
    @staticmethod
    def build_scopes(lists, offsets, collects, circular):
        indexes = [0] * len(collects)
        m = []
        while True:
            if not circular and indexes[0] + collects[0] > len(lists[0]):
                break
            last_turn = indexes[0] + offsets[0] >= len(lists[0])
            tmp = []
            for i in range(len(collects)):
                for j in range(collects[i]):
                    tmp.append(lists[i][(indexes[i] + j) % len(lists[i])])
                indexes[i] += offsets[i]
            m.append(tmp)
            if last_turn:
                break
        return m

    def collect_vars(self, harvest):
        for t in self.lists:
            t.collect_vars(harvest)
        self.template.collect_vars(harvest)
        return harvest

    def subject_to_abstraction(self):
        return True

    def __str__(self):
        return "Slide " + "\n\t" + "\n\t".join(str(e) for e in self.lists) + "\n\t" + str(self.offsets) + "\n\t" + str(
            self.collects) + "\n\t" + str(self.template)


class XAbstraction:
    def __init__(self, abstract_ctr_args):
        assert all(isinstance(ca.type, TypeCtrArg) for ca in abstract_ctr_args)
        self.abstract_ctr_args = abstract_ctr_args
        self.abstract_ctr_vals = [ca.value for ca in self.abstract_ctr_args]
        self.mappings = [XAbstraction.mapping_for(ca) for ca in abstract_ctr_args]
        self.highestParameterNumber = max(
            ca.value.max_parameter_number() if ca.type == TypeCtrArg.FUNCTION else self.mappings[i] if isinstance(self.mappings[i], int) else max(
                self.mappings[i]) for i, ca in enumerate(self.abstract_ctr_args))

    @staticmethod
    def mapping_for(ca):
        if ca.type == TypeCtrArg.FUNCTION:
            return None
        if ca.type == TypeCtrArg.CONDITION:
            assert isinstance(ca.value, ConditionParameter)
            return ca.value.parameter.number
        if isinstance(ca.value, list):
            assert all(isinstance(p, Parameter) for p in ca.value)
            return [p.number for p in ca.value]
        assert isinstance(ca.value, Parameter)
        return ca.value.number

    def concrete_value_for(self, child, abstract_child_value, args, mapping):
        if child.type == TypeCtrArg.FUNCTION:
            return abstract_child_value.concretization(args)
        if child.type == TypeCtrArg.CONDITION:
            assert isinstance(abstract_child_value, ConditionParameter)
            x = args[mapping].cnt if isinstance(args[mapping], Node) and args[mapping].type == TypeNode.VAR else args[mapping]
            assert isinstance(x, XVar), "pb with " + str(args[mapping]) + " " + str(type(args[mapping]))
            return ConditionVariable(abstract_child_value.operator, x)

        if isinstance(child.value, list):
            t = []
            for i in range(len(mapping)):
                if mapping[i] != -1:
                    t.append(args[mapping[i]])
                else:
                    for j in range(self.highestParameterNumber + 1, len(args)):
                        t.append(args[j])
            return t
        assert isinstance(mapping, int)
        return args[mapping]

    def concretize(self, args):
        for i in range(len(self.abstract_ctr_args)):
            self.abstract_ctr_args[i].value = self.concrete_value_for(self.abstract_ctr_args[i], self.abstract_ctr_vals[i], args, self.mappings[i])


"""
------------------------------------
Section about objectives being parsed
------------------------------------
"""


class XObjAbstract(XEntry):

    def __init__(self, minimize: bool, obj_type, obj_id=None):
        assert isinstance(obj_type, TypeObj)
        super().__init__(obj_id, obj_type)
        self.minimize = minimize

    # Returns the set of variables involved in this element
    def involved_vars(self):
        pass

    def __str__(self):
        return "minimize" if self.minimize else "maximize"


class XObjExpr(XObjAbstract):
    def __init__(self, minimize: bool, root, obj_id=None):
        assert isinstance(root, Node), str(root)
        super().__init__(minimize, TypeObj.EXPRESSION, obj_id)
        self.root = root

    def involved_vars(self):
        return self.root.scope()

    def __str__(self):
        return super().__str__() + "\n\t" + str(self.root)


class XObjSpecial(XObjAbstract):
    def __init__(self, minimize: bool, obj_type, terms, coefficients=None, obj_id=None):
        assert obj_type != TypeObj.EXPRESSION
        super().__init__(minimize, obj_type, obj_id)
        self.terms = terms
        self.coefficients = coefficients

    def involved_vars(self):
        t = set()
        for term in self.terms:
            if isinstance(term, XVar):
                t.add(term)
            else:
                assert isinstance(term, Node)
                t.update(term.scope())
        if self.coefficients is not None:
            for cft in self.coefficients:
                if isinstance(cft, XVar):
                    t.add(cft)
                elif isinstance(cft, Node):
                    t.update(cft.scope())
                else:
                    assert isinstance(cft, int)
        return t

    def __str__(self):
        return super().__str__() + "\n\t list: [" + ", ".join(str(v) for v in self.terms) + "]" + (
            "" if self.coefficients is None else ("\n\t coeffs: [" + ", ".join(str(v) for v in self.coefficients)) + "]")


"""
------------------------------------
Section about annotations
------------------------------------
"""


class XAnn(XEntry):
    def __init__(self, ann_type, value, ann_id=None):
        assert isinstance(ann_type, TypeAnn)
        super().__init__(ann_id, ann_type)
        self.value = value

    def __str__(self):
        return super().__str__() + " " + str(self.value)
