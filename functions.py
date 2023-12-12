import inspect
import math
import types

from pycsp3.classes.auxiliary.conditions import Condition, eq, le
from pycsp3.classes.auxiliary.ptypes import TypeOrderedOperator, TypeConditionOperator, TypeVar, TypeCtr, TypeCtrArg, TypeRank
from pycsp3.classes.auxiliary.structures import Automaton, MDD
from pycsp3.classes.entities import (
    EVar, EVarArray, ECtr, EMetaCtr, ECtrs, EToGather, EToSatisfy, EBlock, ESlide, EAnd, EOr, ENot, EXor, EIfThen, EIfThenElse, EIff, EObjective, EAnnotation,
    AnnEntities, TypeNode, Node, CtrEntities, ObjEntities)
from pycsp3.classes.main.annotations import (
    AnnotationDecision, AnnotationOutput, AnnotationVarHeuristic, AnnotationValHeuristic, AnnotationFiltering, AnnotationPrepro, AnnotationSearch,
    AnnotationRestarts)
from pycsp3.classes.main.constraints import (
    ConstraintIntension, ConstraintExtension, ConstraintRegular, ConstraintMdd, ConstraintAllDifferent,
    ConstraintAllDifferentList, ConstraintAllDifferentMatrix, ConstraintAllEqual, ConstraintAllEqualList, ConstraintOrdered, ConstraintLex, ConstraintLexMatrix,
    ConstraintPrecedence, ConstraintSum, ConstraintCount, ConstraintNValues, ConstraintCardinality, ConstraintMaximum,
    ConstraintMinimum, ConstraintMaximumArg, ConstraintMinimumArg, ConstraintElement, ConstraintChannel, ConstraintNoOverlap, ConstraintCumulative,
    ConstraintBinPacking, ConstraintKnapsack, ConstraintFlow, ConstraintCircuit, ConstraintClause, ConstraintRefutation, ConstraintDummyConstant,
    ConstraintSlide, PartialConstraint, ScalarProduct, auxiliary, manage_global_indirection, global_indirection)
from pycsp3.classes.main.domains import Domain
from pycsp3.classes.main.objectives import ObjectiveExpression, ObjectivePartial
from pycsp3.classes.main.variables import Variable, VariableInteger, VariableSymbolic
from pycsp3.dashboard import options
from pycsp3.tools.curser import queue_in, columns, OpOverrider, ListInt, ListVar, ListCtr, cursing
from pycsp3.tools.inspector import checkType, extract_declaration_for, comment_and_tags_of, comments_and_tags_of_parameters_of
from pycsp3.tools.utilities import (
    flatten, is_containing, is_1d_list, is_1d_tuple, is_matrix, ANY, ALL, to_starred_table_for_no_overlap1, to_starred_table_for_no_overlap2, warning,
    warning_if, error_if)

''' Global Variables '''

absPython, maxPython, minPython = abs, max, min

EQ, NE, IN, NOTIN, SET = TypeNode.EQ, TypeNode.NE, TypeNode.IN, TypeNode.NOTIN, TypeNode.SET

started_modeling = False  # It becomes true when the first variable or array of variables is defined (cursing is then activated)


def protect():
    """
    Disables the redefined operators (==, >, >=, etc.) , and returns the object OpOverrider.
    On can then execute some code in protected mode by calling execute().
    Once the code is executed, the redefined operators are reactivated.

    The code typically looks like:
      protect().execute(...)

    :return: the object OpOverrider
    """
    return OpOverrider.disable()


''' Checking Model Variants '''


def variant(name=None):
    """
    Returns the name of the variant given on the command line (option -variant) if the specified argument is None.
    Returns True iff the variant given on the command line is equal to the argument otherwise.
    Note that the variant given on the command line is the substring until the symbol '-' (after this symbol,
    the name of the sub-variant starts), or the end of the string

    :param name: the name of a variant, or None
    :return: the name of the variant specified by the user, or a Boolean
    """
    assert options.variant is None or isinstance(options.variant, str)
    pos = -1 if options.variant is None else options.variant.find("-")  # position of dash ('-') in options.variant
    option_variant = options.variant[0:pos] if pos != -1 else options.variant
    return option_variant if name is None else option_variant == name


def subvariant(name=None):
    """
    Returns the name of the sub-variant given on the command line (option -variant) if the specified argument is None.
    Returns True iff the sub-variant given on the command line is equal to the argument otherwise.
    Note that the sub-variant given on the command line is the substring starting after the symbol '-' (before this symbol,
    this is the name of the variant).

    :param name: the name of a sub-variant, or None
    :return: the name of the sub-variant specified by the user, or a Boolean
    """
    assert options.variant is None or isinstance(options.variant, str)
    pos = -1 if options.variant is None else options.variant.find("-")  # position of dash ('-') in options.variant
    option_subvariant = options.variant[pos + 1:] if pos != -1 else None
    return option_subvariant if name is None else option_subvariant == name


''' Declaring stand-alone variables and arrays '''


def _valid_identifier(s):
    return isinstance(s, str) and all(c.isalnum() or c == '_' for c in s)  # other characters to be allowed?


def Var(term=None, *others, dom=None, id=None):
    """
    Builds a stand-alone variable with the specified domain.
    The domain is either given by the named parameter dom, or given
    by the sequence of terms passed as parameters. For example:
      x = Var(0,1)
      y = Var(range(10))
      z = Var(v for v in range(100) if v%3 == 0)

    :param term: the first term defining the domain, or None
    :param others: the other terms defining the domain, or None
    :param dom: the domain of the variable, or None
    :param id: the id (name) of the variable, or None (usually, None)
    :return: a stand-alone Variable with the specified domain
    """
    global started_modeling
    if not started_modeling and not options.uncurse:
        cursing()
        started_modeling = True
    if term is None and dom is None:
        dom = Domain(math.inf)
    assert not (term and dom)
    if term is not None:
        dom = flatten(term, others)
    if not isinstance(dom, Domain):
        if isinstance(dom, (set, frozenset)):
            dom = list(dom)
        if isinstance(dom, (tuple, list)) and len(dom) > 1 and isinstance(dom[0], int):
            dom = sorted(dom)
            if dom[-1] - dom[0] + 1 == len(dom):
                dom = range(dom[0], dom[-1] + 1)
        dom = Domain(dom)
    error_if(dom.get_type() not in {TypeVar.INTEGER, TypeVar.SYMBOLIC},
             "Currently, only integer and symbolic variables are supported. Problem with " + str(dom))

    var_name = id if id else extract_declaration_for("Var")  # the specified name, if present, has priority
    # if var_name is None:  # TODO: I do not remember the use of that piece of code
    #     if not hasattr(Var, "fly"):
    #         Var.fly = True
    #         warning("at least, one variable created on the fly")
    #     return dom
    error_if(not _valid_identifier(var_name), "The variable identifier " + str(var_name) + " is not valid")
    error_if(var_name in Variable.name2obj, "The identifier " + str(var_name) + " is used twice. This is not possible")

    comment, tags = comment_and_tags_of(function_name="Var")
    assert isinstance(comment, (str, type(None))), "A comment must be a string (or None). Usually, they are given on plain lines preceding the declaration"

    var_object = VariableInteger(var_name, dom) if dom.get_type() == TypeVar.INTEGER else VariableSymbolic(var_name, dom)
    Variable.name2obj[var_name] = var_object
    EVar(var_object, comment, tags)  # object wrapping the variable x
    return var_object


def VarArray(doms=None, *, size=None, dom=None, id=None, comment=None):
    """
    Builds an array of variables.
    The number of dimensions of the array is given by the number of values in size.
    The size of the ith dimension is given by the ith value of size.
    The domain is either the same for all variables, and then directly given by dom,
    or specific to each variable, in which case dom must a function.

    :param size: the size of each dimension of the array
    :param dom: the domain of the variables
    :param id: the id (name) of the array, or None (usually, None)
    :param comment: a string
    :return: an array of variables
    """
    global started_modeling
    if not started_modeling and not options.uncurse:
        cursing()
        started_modeling = True
    if doms is not None:
        assert isinstance(doms, list) and size is None and dom is None and comment is None
        assert all(isinstance(dom, Domain) or dom is None for dom in doms)
        return VarArray(size=len(doms), dom=lambda i: doms[i])

    size = [size] if isinstance(size, int) else size
    if len(size) > 1 and isinstance(size[-1], (tuple, list)):  # it means that the last dimension is of variable length
        assert not isinstance(dom, type(lambda: 0))
        return VarArray(size=size[:-1] + [max(size[-1])], dom=lambda *ids: dom if ids[-1] < size[-1][ids[-2]] else None)

    error_if(any(dimension == 0 for dimension in size), "No dimension must not be equal to 0")
    checkType(size, [int])

    # checkType(dom, (range, Domain, [int, range, str, Domain, type(None)], type(lambda: 0)))  # TODO a problem with large sets
    ext_name = extract_declaration_for("VarArray")
    if isinstance(ext_name, list):
        array_name = ext_name
        error_if(id, "The parameter 'id' is not compatible with the specification of a list of individual names")
        error_if(any(not _valid_identifier(v) for v in ext_name), "Some identifiers in " + str(ext_name) + " are not valid")
        error_if(any(v in Variable.name2obj for v in ext_name), "Some identifiers in " + str(ext_name) + " are used twice.")
    else:
        array_name = id if id else ext_name  # the specified name, if present, has priority
        error_if(not _valid_identifier(array_name), "The variable identifier " + str(array_name) + " is not valid")
        error_if(array_name in Variable.name2obj, "The identifier " + str(array_name) + " is used twice. This is not possible")
    if comment is None and not isinstance(array_name, list):
        comment, tags = comment_and_tags_of(function_name="VarArray")
    else:
        tags = []

    assert isinstance(comment, (str, type(None))), "A comment must be a string (or None). Usually, they are given on plain lines preceding the declaration"
    if isinstance(dom, type(lambda: 0)):
        r = len(inspect.signature(dom).parameters)  # r=1 means that it must be a lambda *args:
        assert len(size) == r or r == 1, "The number of arguments of the lambda must be equal to the number of dimensions of the multidimensional array "
    assert isinstance(comment, (str, type(None))), "A comment must be a string (or None). Usually, they are given on plain lines preceding the declaration"

    if isinstance(dom, (tuple, list, set)):
        domain = flatten(dom)
        assert all(isinstance(v, int) for v in domain) or all(isinstance(v, str) for v in domain)
        dom = Domain(set(domain))
    var_objects = Variable.build_variables_array(array_name, size, dom)

    if isinstance(array_name, list):
        assert (len(array_name) == len(var_objects))
        for i in range(len(array_name)):
            Variable.name2obj[array_name[i]] = var_objects[i]
            EVar(var_objects[i], None, None)  # object wrapping the variables
        return tuple(var_objects)
    else:
        def _to_ListVar(t):
            if t is None:
                return None
            if isinstance(t, Variable):
                return t
            assert isinstance(t, list)
            return ListVar(_to_ListVar(x) for x in t)

        Variable.name2obj[array_name] = var_objects
        lv = _to_ListVar(var_objects)
        EVarArray(lv, array_name, comment, tags)  # object wrapping the array of variables
        Variable.arrays.append(lv)
        return lv


def var(name):
    """
    Returns the variable or variable array whose name is specified
    :param name: the name of the variable or variable array to be returned
    """
    assert isinstance(name, str)
    error_if(name not in Variable.name2obj,
             "the variable, or variable array, specified when calling the function 'var()' with the name " + name + " has not been declared")
    return Variable.name2obj[name]


''' Posting constraints (through satisfy()) '''


def _bool_interpretation_for_in(left_operand, right_operand, bool_value):
    assert type(bool_value) is bool
    if isinstance(left_operand, Variable):
        if isinstance(right_operand, (tuple, list, set, frozenset, range)) and len(right_operand) == 0:
            return None
        if isinstance(right_operand, (tuple, list, set, frozenset)) and is_containing(right_operand, Variable):
            if len(right_operand) < 4:  # TODO hard coding (introducing an option to adjust that?)
                st = Node.build(SET, right_operand)
                return _Intension(Node.build(IN, left_operand, st) if bool_value else Node.build(NOTIN, left_operand, st))
            if bool_value:
                condition = Condition.build_condition((TypeConditionOperator.EQ, left_operand))
                return ECtr(ConstraintElement(flatten(right_operand), index=None, condition=condition))  # member
            else:
                return [_Intension(Node.build(NE, left_operand, y)) for y in right_operand]
                # condition = Condition.build_condition(TypeConditionOperator.NE, left_operand)
                # return ECtr(ConstraintElement(flatten(right_operand), index=None, condition=condition))  # member
        if isinstance(right_operand, range):
            # return (right_operand.start <= left_operand) & (left_operand < right_operand.stop)
            return _Extension(scope=[left_operand], table=list(right_operand), positive=bool_value)
    if isinstance(left_operand, (Variable, int, str)) and isinstance(right_operand, (set, frozenset, range)):
        # it is a unary constraint of the form x in/not in set/range
        return _Intension(Node.build(IN, left_operand, right_operand) if bool_value else Node.build(NOTIN, left_operand, right_operand))
    # elif isinstance(left_operand, Node) and isinstance(right_operand, range):
    #     if bool_value:
    #         ctr = Intension(conjunction(left_operand >= right_operand.start, left_operand <= right_operand.stop - 1))
    #     else:
    #         ctr = Intension(disjunction(left_operand < right_operand.start, left_operand > right_operand.stop - 1))
    elif isinstance(left_operand, PartialConstraint):  # it is a partial form of constraint (sum, count, maximum, ...)
        ctr = ECtr(left_operand.constraint.set_condition(TypeConditionOperator.IN if bool_value else TypeConditionOperator.NOTIN, right_operand))
    elif isinstance(right_operand, Automaton):  # it is a regular constraint
        ctr = _Regular(scope=left_operand, automaton=right_operand)
    elif isinstance(right_operand, MDD):  # it is a MDD constraint
        ctr = _Mdd(scope=left_operand, mdd=right_operand)
    elif isinstance(left_operand, int) and (is_1d_list(right_operand, Variable) or is_1d_tuple(right_operand, Variable)):
        ctr = Count(right_operand, value=left_operand, condition=(TypeConditionOperator.GE, 1))  # atLeast1 TODO to be replaced by a member/element constraint ?
    # elif isinstance(left_operand, Node):
    #
    else:  # It is a table constraint
        if not hasattr(left_operand, '__iter__'):
            left_operand = [left_operand]
        assert isinstance(right_operand, list)
        if not bool_value and len(right_operand) == 0:
            return None
        # TODO what to do if the table is empty and bool_value is true? an error message ?
        # if len(right_operand) == 0:  # it means an empty table, and Python will generate True (not in [] => True)
        if len(left_operand) == 1:
            if not is_1d_list(right_operand, int) and not is_1d_list(right_operand, str):
                assert all(isinstance(v, (tuple, list)) and len(v) == 1 for v in right_operand)
                right_operand = [v[0] for v in right_operand]
        ctr = _Extension(scope=flatten(left_operand), table=right_operand, positive=bool_value)  # TODO ok for using flatten? (before it was list())
    return ctr


def _complete_partial_forms_of_constraints(entities):
    for i, c in enumerate(entities):
        if isinstance(c, bool):
            assert len(queue_in) > 0, "A boolean that does not represent a constraint is in the list of constraints in satisfy(): " + str(entities)
            right_operand, left_operand = queue_in.popleft()
            entities[i] = _bool_interpretation_for_in(left_operand, right_operand, c)
        elif isinstance(c, ESlide):
            for ent in c.entities:
                _complete_partial_forms_of_constraints(ent.entities)
    return entities


def _wrap_intension_constraints(entities):
    for i, c in enumerate(entities):
        if isinstance(c, Node):
            entities[i] = _Intension(c)  # the node is wrapped by a Constraint object (Intension)
    return entities


def And(*args, meta=True):
    """
    Builds a meta-constraint And from the specified arguments.
    For example: And(Sum(x) > 10, AllDifferent(x))

    When the parameter 'meta' is not true,
    reification is employed.

    :param args: a tuple of constraints
    :param meta true if a meta-constraint form must be really posted
    :return: a meta-constraint And, or its reified form
    """
    if options.usemeta or meta:
        return EAnd(_wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(*args))))
    return conjunction(*args)


def Or(*args, meta=True):
    """
    Builds a meta-constraint Or from the specified arguments.
    For example: Or(Sum(x) > 10, AllDifferent(x))

    When the parameter 'meta' is not true,
    reification is employed.

    :param args: a tuple of constraints
    :param meta true if a meta-constraint form must be really posted
    :return: a meta-constraint Or, or its reified form
    """
    if meta:
        return EOr(_wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(*args))))
    return disjunction(*args)


def Not(arg, meta=True):
    """
    Builds a meta-constraint Not from the specified argument.
    For example: Not(AllDifferent(x))

    When the parameter 'meta' is not true,
    reification is employed.

    :param arg: a constraint
    :param meta true if a meta-constraint form must be really posted
    :return: a meta-constraint Not, or its reified form
    """
    if meta:
        return ENot(_wrap_intension_constraints(_complete_partial_forms_of_constraints(arg)))
    res = manage_global_indirection(arg)
    if res is None:
        return ENot(_wrap_intension_constraints(_complete_partial_forms_of_constraints(arg)))
    return ~res  # TODO to be checked


def Xor(*args, meta=True):
    """
    Builds a meta-constraint Xor from the specified arguments.
    For example: Xor(Sum(x) > 10, AllDifferent(x))

    When the parameter 'meta' is not true,
    reification is employed.

    :param args: a tuple of constraints
    :param meta true if a meta-constraint form must be really posted
    :return: a meta-constraint Xor, or its reified form
    """
    if meta:
        return EXor(_wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(*args))))
    return xor(*args)


def If(test, *testOthers, Then, Else=None, meta=False):
    """
    Builds a complex form of constraint(s), based on the general control structure 'if then else'
    that can possibly be decomposed, at compilation time.

    For example:
      - If(Sum(x) > 10, Then=AllDifferent(x))
      - If(Sum(x) > 10, Then=AllDifferent(x), Else=AllEqual(x))
      - If(w > 0, y != z, Then=w == y + z)
      - If(w > 0, y != z, Then=[w == y + z, v != 1])
      - If(Sum(x) > 10, Then=y == z, Else=[AllEqual(x), y < 3])

    When the parameter 'meta' is not true (the usual and default case),
    reification may be employed.

    :param test: the condition expression
    :param testOthers: the other terms (if any) of the condition expression (assuming a conjunction)
    :param Then the Then part
    :param Else the Else part
    :param meta true if a meta-constraint form must be really posted
    :return: a complex form of constraint(s) based on the control structure 'if then else'
    """

    # if len(testOthers) == 0 and isinstance(test, bool):  # We don't allow that because otherwise 'in' no more usable as in If(x[0] in (2,3), Then=...
    #     return Then if test else Else

    tests, thens = flatten(test, testOthers), flatten(Then)
    assert isinstance(tests, list) and len(tests) > 0 and isinstance(thens, list)  # after flatten, we have a list
    if len(thens) == 0:
        return None if Else is None else Or(tests, Else)
    if meta:
        if Else is None:
            return EIfThen(_wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(tests, thens))))
        else:
            return EIfThenElse(_wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(tests, thens, Else))))

    tests, thens = manage_global_indirection(tests, also_pc=True), manage_global_indirection(thens, also_pc=True)  # we get None or a list
    assert tests is not None and thens is not None and len(tests) > 0 and len(thens) > 0

    def __neg(term):
        if isinstance(term, Variable):
            assert term.dom.is_binary()
            return var(term.id) if term.negation else Node.build(EQ, term, 0)
        assert isinstance(term, Node) and term.type.is_predicate_operator()
        sons = term.sons
        if term.type == TypeNode.NOT:
            assert sons[0].type.is_predicate_operator()
            return sons[0]
        if term.type == TypeNode.AND:
            return Node.build(TypeNode.OR, *[__neg(son) for son in sons])
        if term.type == TypeNode.OR:
            return Node.build(TypeNode.AND, *[__neg(son) for son in sons])
        if term.type == TypeNode.IFF:
            return Node.build(TypeNode.NOT, term)
        if term.type == TypeNode.IMP:
            assert len(sons) == 2 and sons[0].type.is_predicate_operator() and sons[1].type.is_predicate_operator()
            return Node.build(TypeNode.AND, sons[0], Node.build(TypeNode.NOT, sons[1]))
        if term.type == TypeNode.EQ and len(sons) == 2 and sons[1].type == TypeNode.INT and sons[1].sons == 0 \
                and sons[0].type == TypeNode.VAR and sons[0].sons.dom.is_binary():  # x=0  => x
            return sons[0].sons
        assert ~term.type is not None
        return Node(~term.type, sons)

    # if options.ev:
    if Else is None and len(tests) == 1:
        if isinstance(tests[0], Variable) and not tests[0].negation:
            return [imply(tests, term) for term in flatten(thens)]
        if len(thens) == 1:
            if (not (isinstance(thens[0], Node) and thens[0].type == TypeNode.OR)
                    and not (isinstance(tests[0], Node) and tests[0].type == TypeNode.NOT)
                    and not (isinstance(tests[0], Variable) and tests[0].negation)):
                return imply(tests, thens)

    neg_test = __neg(tests[0]) if len(tests) == 1 else disjunction(__neg(term) for term in tests)
    t = []
    t.extend(disjunction(neg_test, term) for term in flatten(thens))
    if Else is not None:
        elses = manage_global_indirection(Else, also_pc=True)
        if len(elses) > 0:
            test = conjunction(term for term in tests) if len(tests) > 1 else tests
            t.extend(disjunction(test, v) for v in flatten(elses))
    return t  # [0] if len(t) == 1 else t


def Match(Expr, *, Cases):
    assert isinstance(Cases, dict)
    t = [(k, w) for k, v in Cases.items() for w in (v if isinstance(v, (tuple, list, set, frozenset)) else [v])]
    if isinstance(Expr, (Variable, Node)):
        return [expr(~k.operator, Expr, k.right_operand()) | v if isinstance(k, Condition)
                else (Expr != k if not isinstance(k, (tuple, list, set, frozenset)) else not_belong(Expr, k)) | v for k, v in t]
    else:
        assert False, "Bad construction with Match: the expression must be a variable or an expression involving a variable"
        # return [v for k, v in t if
        #         (not isinstance(k, (tuple, list, set, frozenset)) and Expr == k) or (isinstance(k, (tuple, list, set, frozenset)) and Expr in k)]


def Iff(*args, meta=True):
    """
    Builds a meta-constraint Iff from the specified arguments.
    For example: Iff(Sum(x) > 10, AllDifferent(x))

    When the parameter 'meta' is not true,
    reification is employed.

    :param args: a tuple of constraints
    :param meta true if a meta-constraint form must be really posted
    :return: a meta-constraint Iff, or its reified form
    """
    if meta:
        return EIff(_wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(*args))))
    return iff(*args)


def Slide(*args, expression=None, circular=None, offset=None, collect=None):
    """
    Builds a meta-constraint Slide from the specified arguments.
    Slide((x[i], x[i + 1]) in table for i in range(n - 1))

    According to the specified constraints, the compiler may or may not succeed
    in generating a slide meta-constraint.

    :param args: a tuple of constraints
    :return: a meta-constraint Slide
    """
    if expression is not None:  # the meta-constraint is defined directly by the user
        return ECtr(ConstraintSlide(*args, expression, circular, offset, collect))
    # we cannot directly complete partial forms (because it is executed before the analysis of the parameters of satisfy
    entities = _wrap_intension_constraints(flatten(*args))
    checkType(entities, [ECtr, bool])
    return ESlide([EToGather(entities)])


def _group(*_args, block=False):
    def _remove_dummy_constraints(tab):
        if any(isinstance(v, ConstraintDummyConstant) for v in tab):
            warning_if(any(isinstance(v, ConstraintDummyConstant) and v.val != 1 for v in tab), "It seems that there is a bad expression in the model")
            return [v for v in tab if not isinstance(v, ConstraintDummyConstant)]
        return tab

    def _block_reorder(_entities):
        reordered_entities = []
        g = []
        for c in _entities:
            if isinstance(c, ECtr) and c.blank_basic_attributes():
                g.append(c)
            else:
                if len(g) != 0:
                    reordered_entities.append(_group(g))
                g.clear()
                reordered_entities.append(c)
        if len(g) != 0:
            reordered_entities.append(_group(g))
        return reordered_entities

    tab = _remove_dummy_constraints(flatten(*_args))
    if len(tab) == 0:
        return None
    entities = _wrap_intension_constraints(_complete_partial_forms_of_constraints(tab))
    checkType(entities, [ECtr, ECtrs, EMetaCtr])
    return EBlock(_block_reorder(entities)) if block else EToGather(entities)


def satisfy_from_auxiliary(t=[]):
    to_post = _group(pc == var for (pc, var) in auxiliary().get_collected_and_clear())
    if to_post is not None:
        t.append(to_post)
    to_post = _group(auxiliary().get_collected_raw_and_clear())
    if to_post is not None:
        t.append(to_post)
    to_post = _group((index, aux) in table for (index, aux, table) in auxiliary().get_collected_extension_and_clear())
    if to_post is not None:
        t.append(to_post)
    return EToSatisfy(t)


def satisfy(*args, no_comment_tags_extraction=False):
    """
    Posts all constraints that are specified as arguments

    :param args: the different constraints to be posted
    :return: an object wrapping the posted constraints
    """
    global no_parameter_satisfy, nb_parameter_satisfy

    def _reorder(l):  # if constraints are given in (sub-)lists inside tuples; we flatten and reorder them to hopefully improve compactness
        d = dict()
        for tp in l:
            if isinstance(tp, (tuple, list)):
                for i, v in enumerate(tp):
                    d.setdefault(i, []).append(v)
            else:
                d.setdefault(0, []).append(tp)
        return [v for vs in d.values() for v in vs]

    no_parameter_satisfy = 0
    nb_parameter_satisfy = len(args)
    comments1, comments2, tags1, tags2 = comments_and_tags_of_parameters_of(function_name="satisfy", args=args, no_extraction=no_comment_tags_extraction)

    t = []
    for i, arg in enumerate(args):
        if arg is None:
            continue
        if isinstance(arg, ConstraintDummyConstant):
            warning_if(arg.val != 1, "It seems that there is a bad expression in the model " + str(arg))
            continue
        if isinstance(arg, (tuple, set, frozenset, types.GeneratorType)):
            arg = list(arg)
        if isinstance(arg, list) and any(v is None for v in arg):
            # TODO: what if there is a trailing comma?
            if len(arg) == len(comments2[i]):
                comments2[i] = [c for i, c in enumerate(comments2[i]) if arg[i] is not None]
            if len(arg) == len(tags2[i]):
                tags2[i] = [c for i, c in enumerate(tags2[i]) if arg[i] is not None]
            arg = [v for v in arg if v is not None]

        if isinstance(arg, list) and len(arg) > 0:
            if isinstance(arg[0], tuple):
                arg = _reorder(arg)
            elif isinstance(arg[0], list):  # do not work if the constraints involve the operator 'in'
                # triple_list = all(isinstance(ar, list) and (len(ar) == 0 or isinstance(ar, (tuple, list))) for ar in arg)
                # if triple_list:
                #     arg = _reorder(flatten(arg))
                # else:
                for j, l in enumerate(arg):
                    if isinstance(l, list) and len(l) > 0 and isinstance(l[0], tuple):
                        arg[j] = _reorder(l)
        no_parameter_satisfy = i

        assert isinstance(arg, (ECtr, EMetaCtr, ESlide, Node, bool, list)), "non authorized type " + str(arg) + " " + str(type(arg))
        comment_at_2 = any(comment != '' for comment in comments2[i])
        tag_at_2 = any(tag != '' for tag in tags2[i])
        if isinstance(arg, (ECtr, EMetaCtr, ESlide)):  # case: simple constraint or slide
            if isinstance(arg, ECtr) and isinstance(arg.constraint, ConstraintRefutation):  # refutations must be transformed
                to_post = _group(arg.constraint.to_list())
            else:
                to_post = _complete_partial_forms_of_constraints([arg])[0]
        elif isinstance(arg, Node):  # a predicate to be wrapped by a constraint (intension)
            to_post = _Intension(arg)
        elif isinstance(arg, bool):  # a Boolean representing the case of a partial constraint or a node with operator in {IN, NOT IN}
            assert queue_in, "An argument of satisfy() before position " + str(i) + " is badly formed"
            other, partial = queue_in.popleft()
            to_post = _bool_interpretation_for_in(partial, other, arg)
            if isinstance(to_post, list):
                to_post = _group(to_post)
        else:
            assert isinstance(arg, list)
            if any(isinstance(ele, ESlide) for ele in arg):  # Case: Slide
                to_post = _group(arg, block=True)
            elif comment_at_2 or tag_at_2:  # Case: block
                if len(arg) == len(comments2[i]) - 1 == len(tags2[i]) - 1 and comments2[i][-1] == "" and tags2[i][-1] == "":
                    # this avoids the annoying case where there is a comma at the end of the last line in a block
                    comments2[i] = comments2[i][:-1]
                    tags2[i] = tags2[i][:-1]
                if len(arg) == len(comments2[i]) == len(tags2[i]):  # if comments are not too wildly put
                    for j in range(len(arg)):
                        if isinstance(arg[j], (ECtr, ESlide)):
                            arg[j].note(comments2[i][j]).tag(tags2[i][j])
                        else:  # if comments2[i][j] or tags2[i][j]: PB if we use this as indicated below
                            # BE CAREFUL: if bool present _group must be executed systematically (otherwise, confusion between false and True possible)
                            if isinstance(arg[j], list) and len(arg[j]) == 1:
                                arg[j] = arg[j][0]
                            if isinstance(arg[j], list) and len(arg[j]) > 0 and isinstance(arg[j][0], list):
                                for k in range(len(arg[j])):
                                    arg[j][k] = _group(arg[j][k])
                                arg[j] = _group(arg[j], block=True).note(comments2[i][j]).tag(tags2[i][j])
                            else:
                                g = _group(arg[j])  # , block=True)
                                arg[j] = g.note(comments2[i][j]).tag(tags2[i][j]) if g is not None else None
                to_post = _group(arg, block=True)
            else:  # Group
                to_post = _group(arg)
        if to_post is not None:
            # to_post_aux = satisfy_from_auxiliary()
            # if len(to_post_aux) > 0:
            #     to_post = EBlock(flatten(to_post, to_post_aux))
            t.append(to_post.note(comments1[i]).tag(tags1[i]))
            # if isinstance(to_post, ESlide) and len(to_post.entities) == 1:
            #     to_post.entities[0].note(comments1[i]).tag(tags1[i])
    # return EToSatisfy(t)
    return satisfy_from_auxiliary(t)


''' Generic Constraints (intension, extension) '''


def _Extension(*, scope, table, positive=True):
    scope = flatten(scope)
    checkType(scope, [Variable])
    assert isinstance(table, list)
    assert len(table) > 0, "A table must be a non-empty list of tuples or integers (or symbols)"
    checkType(positive, bool)

    if len(scope) == 1:
        assert all(isinstance(v, int) if isinstance(scope[0], VariableInteger) else isinstance(v, str) for v in table)
    else:  # if all(isinstance(x, VariableInteger) for x in scope):
        for i, t in enumerate(table):
            if isinstance(t, list):
                table[i] = tuple(t)
            else:
                assert isinstance(t, tuple), str(t)
            # we now manage shortcut expressions as in col(i) instead of eq(col(i)), and discard trivial ranges
            if any(isinstance(v, (range, Node)) for v in t):
                table[i] = tuple(eq(v) if isinstance(v, Node) else v.start if isinstance(v, range) and len(v) == 1 else v for v in t)
            if len(t) != len(scope):
                t = tuple(flatten(t))
                assert len(t) == len(scope), ("The length of each tuple must be the same as the arity."
                                              + "Maybe a problem with slicing: you must for example write x#[i:i+3,0] instead of x[i:i+3][0]")
                table[i] = t
    return ECtr(ConstraintExtension(scope, table, positive, options.keephybrid, options.restricttableswrtdomains))


def _Intension(node):
    checkType(node, Node)
    ctr = ECtr(ConstraintIntension(node))
    if ctr.blank_basic_attributes():
        ctr.copy_basic_attributes_of(node)
    node.mark_as_used()
    return ctr


def col(*args):
    assert len(args) == 1 and isinstance(args[0], int)
    return Node(TypeNode.COL, args[0])


def abs(arg):
    """
    If the specified argument is a node or a variable of the model, the function builds
    and returns a node 'abs', root of a tree expression where the specified argument is a child.
    Otherwise, the function returns, as usual, the absolute value of the specified argument

    :return: either a node, root of a tree expression, or the absolute value of the specified argument
    """
    if isinstance(arg, PartialConstraint):
        arg = auxiliary().replace_partial_constraint(arg)
    if isinstance(arg, Node) and arg.type == TypeNode.SUB:
        return Node.build(TypeNode.DIST, arg.sons)
    return Node.build(TypeNode.ABS, arg) if isinstance(arg, (Node, Variable)) else absPython(arg)


def min(*args):
    """
    When one of the specified arguments is a node or a variable of the model, the function builds
    and returns a node 'min', root of a tree expression where specified arguments are children.
    Otherwise, the function returns, as usual, the smallest item of the specified arguments

    :return: either a node, root of a tree expression, or the smallest item of the specified arguments
    """
    return args[0] if len(args) == 1 and isinstance(args[0], (int, str)) else Node.build(TypeNode.MIN, *args) if len(args) > 1 and any(
        isinstance(a, (Node, Variable)) for a in args) else minPython(*args)


def max(*args):
    """
    When one of the specified arguments is a node or a variable of the model, the function builds
    and returns a node 'max', root of a tree expression where specified arguments are children.
    Otherwise, the function returns, as usual, the largest item of the specified arguments

    :return: either a node, root of a tree expression, or the largest item of the specified arguments
    """
    return args[0] if len(args) == 1 and isinstance(args[0], (int, str)) else Node.build(TypeNode.MAX, *args) if len(args) > 1 and any(
        isinstance(a, (Node, Variable)) for a in args) else maxPython(*args)


def xor(*args):
    """
    If there is only one argument, returns it.
    Otherwise, builds and returns a node 'xor', root of a tree expression where specified arguments are children.
    Without any parent, it becomes a constraint.

    :return: a node, root of a tree expression or the argument if there is only one
    """
    if len(args) == 1 and isinstance(args[0], (tuple, list, set, frozenset, types.GeneratorType)):
        args = tuple(args[0])
    args = [v if not isinstance(v, (tuple, list)) else v[0] if len(v) == 1 else conjunction(v) for v in args]
    return args[0] ^ args[1] if len(args) == 2 else Node.build(TypeNode.XOR, *args) if len(args) > 1 else args[0]


def iff(*args):
    """
    Builds and returns a node 'iff', root of a tree expression where specified arguments are children.
    Without any parent, it becomes a constraint.

    :return: a node, root of a tree expression
    """
    if len(args) == 1 and isinstance(args[0], (tuple, list, set, frozenset, types.GeneratorType)):
        args = tuple(args[0])
    assert len(args) >= 2
    res = manage_global_indirection(*args)
    if res is None:
        return Iff(*args, meta=True)
    res = [v if not isinstance(v, (tuple, list)) else v[0] if len(v) == 1 else conjunction(v) for v in res]
    return res[0] == res[1] if len(res) == 2 else Node.build(TypeNode.IFF, *res)


def imply(*args):
    """
    Builds and returns a node 'imply', root of a tree expression where specified arguments are children.
    Without any parent, it becomes a constraint.

    :param args: a tuple of two arguments
    :return: a node, root of a tree expression
    """
    assert len(args) == 2
    cnd, tp = args  # condition and then part
    if isinstance(tp, (tuple, list, set, frozenset)):
        tp = list(tp)  # to transform sets into lists
        assert len(tp) >= 1
        return imply(cnd, tp[0]) if len(tp) == 1 else [imply(cnd, v) for v in tp]
    if isinstance(tp, PartialConstraint):
        tp = Node.build(TypeNode.EQ, auxiliary().replace_partial_constraint(tp), 1)
    res = manage_global_indirection(cnd, tp)
    if res is None:
        return If(cnd, tp)
    # if len(res) == 2 and isinstance(res[1], (tuple, list, set, frozenset)):
    #     return [imply(res[0], v) for v in res[1]]
    res = [v if not isinstance(v, (tuple, list)) else v[0] if len(v) == 1 else conjunction(v) for v in res]
    return Node.build(TypeNode.IMP, *res)


def ift(test, Then, Else):
    """
    Builds and returns a node 'ifthenelse', root of a tree expression where specified arguments are children.
    Without any parent, it becomes a constraint.

    :param test: the condition expression
    :param Then the Then part
    :param Else the Else part

    :return: a node, root of a tree expression
    """
    # assert len(args) == 3
    # test, Then, Else = args  # condition, then part and else part
    if isinstance(test, ConstraintDummyConstant):
        assert test.val in (0, 1)
        return Then if test.val == 1 else Else
    if Else is None:
        return imply(test, Then)
    if isinstance(test, (tuple, list)):
        assert len(test) == 1, str(test)
        test = test[0]
    btp = isinstance(Then, (tuple, list, set, frozenset))
    if btp:
        Then = list(Then)
        assert len(Then) >= 1
        if len(Then) == 1:
            return ift(test, Then[0], Else)
    etp = isinstance(Else, (tuple, list, set, frozenset))
    if etp:
        Else = list(Else)
        assert len(Else) >= 1
        if len(Else) == 1:
            return ift(test, Then, Else[0])
    if btp or etp:
        Then, Else = Then if isinstance(Then, list) else [Then], Else if isinstance(Else, list) else [Else]
        # # we compute the negation of cnd
        # if isinstance(cnd, Node) and ~cnd.type is not None:
        #     rcnd = Node(~cnd.type, cnd.sons)
        # elif isinstance(cnd, Variable):
        #     rcnd = var(cnd.id) if cnd.negation else ~cnd
        # else:
        #     rcnd = ~cnd
        return [imply(test, v) for v in Then] + [test | v for v in Else]
    res = manage_global_indirection(test, Then, Else, also_pc=True)
    if res is None:
        return If(test, Then, Else, meta=True)
    res = [v if not isinstance(v, (tuple, list)) else v[0] if len(v) == 1 else conjunction(v) for v in res]
    assert len(res) == 3
    if isinstance(res[0], int):
        assert res[0] in (0, 1)
        return res[1] if res[0] == 1 else res[2]
    return Node.build(TypeNode.IF, *res)


def belong(x, values):
    if isinstance(x, PartialConstraint):
        x = auxiliary().replace_partial_constraint(x)
    if isinstance(x, int):
        assert is_1d_list(values, Variable)
        return disjunction(y == x for y in values if y)
    assert isinstance(x, Variable)
    if isinstance(values, range):
        if values.step != 1 or len(values) < 10:
            values = list(values)
        else:
            return Node.in_range(x, values)
    elif isinstance(values, int):
        values = [values]
    assert isinstance(values, (tuple, list, set, frozenset)) and all(isinstance(v, int) for v in values)
    if len(values) == 1:
        return Node.build(EQ, x, values[0])
    return Node.build(IN, x, Node.build(SET, values))


def not_belong(x, values):
    if isinstance(x, PartialConstraint):
        x = auxiliary().replace_partial_constraint(x)
    if isinstance(x, int):
        assert is_1d_list(values, Variable)
        return conjunction(y != x for y in values if y)
    assert isinstance(x, Variable)
    if isinstance(values, range):
        if values.step != 1 or len(values) < 10:
            values = list(values)
        else:
            return Node.not_in_range(x, values)
    elif isinstance(values, int):
        values = [values]
    assert isinstance(values, (tuple, list, set, frozenset)) and all(isinstance(v, int) for v in values)
    if len(values) == 1:
        return Node.build(NE, x, values[0])
    return Node.build(NOTIN, x, Node.build(SET, values))


def expr(operator, *args):
    """
    Builds and returns a node, root of a tree expression where specified arguments are children.
    The type of the new node is given by the specified operator.
    When it is a string, it can be among {"<", "lt", "<=", "le", ">=", "ge", ">", "gt", "=", "==", "eq", "!=", "<>", "ne"}
    Without any parent, it becomes a constraint.

    :param operator: a string, or a constant from TypeNode or a constant from TypeConditionOperator or TypeOrderedOperator
    :return: a node, root of a tree expression
    """
    return Node.build(operator, *args)


def conjunction(*args):
    """
    Builds and returns a node 'and', root of a tree expression where specified arguments are children.
    Without any parent, it becomes a constraint.

    :return: a node, root of a tree expression
    """
    # return Count(manage_global_indirection(*args)) == len(args)
    # t = flatten(args)
    # if len(t) > 3:
    #     return Count(t) == len(t)
    return Node.conjunction(manage_global_indirection(*args))


def both(this, And):
    """
    Builds and returns a node 'and', root of a tree expression where the two specified arguments are children.
    Without any parent, it becomes a constraint.

    :return: a node, root of a tree expression
    """
    return conjunction(this, And)


def disjunction(*args):
    """
    Builds and returns a node 'or', root of a tree expression where specified arguments are children.
    Without any parent, it becomes a constraint.

    :return: a node, root of a tree expression
    """
    return Node.disjunction(manage_global_indirection(*args))


def either(this, Or):
    """
    Builds and returns a node 'or', root of a tree expression where the two specified arguments are children.
    Without any parent, it becomes a constraint.

    :return: a node, root of a tree expression
    """
    return disjunction(this, Or)


''' Language-based Constraints '''


def _Regular(*, scope, automaton):
    scope = flatten(scope)
    checkType(scope, [Variable])
    checkType(automaton, Automaton)
    return ECtr(ConstraintRegular(scope, automaton))


def _Mdd(*, scope, mdd):
    scope = flatten(scope)
    checkType(scope, [Variable])
    checkType(mdd, MDD)
    return ECtr(ConstraintMdd(scope, mdd))


''' Comparison-based Constraints '''


def AllDifferent(term, *others, excepting=None, matrix=False):
    """
    Builds and returns a constraint AllDifferent.

    :param term: the first term on which the constraint applies
    :param others: the other terms (if any) on which the constraint applies
    :param excepting: the value(s) that must be ignored (None, most of the time)
    :param matrix: if True, the matrix version must be considered
    :return: a constraint AllDifferent
    """
    excepting = list(excepting) if isinstance(excepting, (tuple, set)) else [excepting] if isinstance(excepting, int) else excepting
    checkType(excepting, ([int], type(None)))
    if matrix:
        assert len(others) == 0
        matrix = [flatten(row) for row in term]
        assert all(len(row) == len(matrix[0]) for row in matrix), "The matrix id badly formed"
        assert all(checkType(l, [Variable]) for l in matrix)
        if not options.mini:
            return ECtr(ConstraintAllDifferentMatrix(matrix, excepting))
        else:
            return [AllDifferent(row) for row in matrix] + [AllDifferent(col) for col in columns(matrix)]
    terms = flatten(term, others)
    if len(terms) == 0 or (len(terms) == 1 and isinstance(terms[0], (int, Variable, Node))):
        return None
    checkType(terms, ([Variable, Node]))
    auxiliary().replace_partial_constraints_and_constraints_with_condition_and_possibly_nodes(terms, nodes_too=options.mini)  # only if mini
    return ECtr(ConstraintAllDifferent(terms, excepting))


def AllDifferentList(term, *others, excepting=None):
    """
    Builds and returns a constraint AllDifferentList.

    :param term: the first term on which the constraint applies
    :param others: the other terms (if any) on which the constraint applies
    :param excepting: the tuple(s) that must be ignored (None, most of the time)
    :return: a constraint AllDifferentList
    """
    if isinstance(term, types.GeneratorType):
        term = [l for l in term]
    elif len(others) > 0:
        term = list((term,) + others)
    lists = [flatten(l) for l in term]
    assert all(checkType(l, [Variable]) for l in lists)
    excepting = list(excepting) if isinstance(excepting, (tuple, range)) else excepting
    checkType(excepting, ([int], type(None)))
    assert all(len(l) == len(lists[0]) for l in lists) and (excepting is None or len(excepting) == len(lists[0]))
    return ECtr(ConstraintAllDifferentList(lists, excepting))


def AllEqual(term, *others, excepting=None):
    """
    Builds and returns a constraint AllEqual.

    :param term: the first term on which the constraint applies
    :param others: the other terms (if any) on which the constraint applies
    :param excepting: the value(s) that must be ignored (None, most of the time)
    :return: a constraint AllEqual
    """
    excepting = list(excepting) if isinstance(excepting, (tuple, set)) else [excepting] if isinstance(excepting, int) else excepting
    checkType(excepting, ([int], type(None)))
    terms = flatten(term, others)
    auxiliary().replace_partial_constraints_and_constraints_with_condition_and_possibly_nodes(terms, nodes_too=options.mini)
    checkType(terms, ([Variable], [Node]))
    return ECtr(ConstraintAllEqual(terms, excepting))


def AllEqualList(term, *others, excepting=None):
    """
    Builds and returns a constraint AllEqualList. In case only two lists are given, and excepting is None,
    a group of intensional constraints of the form x[i] == y[i] is posted

    :param term: the first term on which the constraint applies
    :param others: the other terms (if any) on which the constraint applies
    :param excepting: the tuple(s) that must be ignored (None, most of the time)
    :return: a constraint AllEqualList
    """
    if isinstance(term, types.GeneratorType):
        term = [l for l in term]
    elif len(others) > 0:
        term = list((term,) + others)
    lists = [flatten(l) for l in term]
    assert all(checkType(l, [Variable]) for l in lists)
    excepting = list(excepting) if isinstance(excepting, (tuple, range)) else excepting
    checkType(excepting, ([int], type(None)))
    assert all(len(l) == len(lists[0]) for l in lists) and (excepting is None or len(excepting) == len(lists[0]))
    if len(lists) == 2 and excepting is None:
        return [lists[0][i] == lists[1][i] for i in range(len(lists[0]))]
    return ECtr(ConstraintAllEqualList(lists, excepting))


def _ordered(term, others, operator, lengths):
    terms = flatten(term, others)
    auxiliary().replace_partial_constraints_and_constraints_with_condition_and_possibly_nodes(terms, nodes_too=True)
    checkType(terms, [Variable])
    checkType(operator, TypeOrderedOperator)
    if isinstance(lengths, range):
        lengths = list(lengths)
    if isinstance(lengths, int):
        lengths = [lengths] * (len(terms) - 1)
    checkType(lengths, ([int, Variable], type(None)))
    if lengths is not None:
        if len(terms) == len(lengths):
            lengths = lengths[:-1]  # we assume that the last value is useless
        assert len(terms) == len(lengths) + 1
    if options.mini:
        return [expr(operator, terms[i] if lengths is None else terms[i] + lengths[i], terms[i + 1]) for i in range(len(terms) - 1)]
    return ECtr(ConstraintOrdered(terms, operator, lengths))


def Increasing(term, *others, strict=False, lengths=None):
    """
    Builds and returns a constraint Increasing.

    :param term: the first term on which the constraint applies
    :param others: the other terms (if any) on which the constraint applies
    :param strict: if True, strict ordering must be considered
    :param lengths: the lengths (durations) that must separate the values
    :return: a constraint Increasing
    """
    return _ordered(term, others, TypeOrderedOperator.INCREASING if not strict else TypeOrderedOperator.STRICTLY_INCREASING, lengths)


def Decreasing(term, *others, strict=False, lengths=None):
    """
    Builds and returns a constraint Decreasing.

    :param term: the first term on which the constraint applies
    :param others: the other terms (if any) on which the constraint applies
    :param strict: if True, strict ordering must be considered
    :param lengths: the lengths (durations) that must separate the values
    :return: a constraint Decreasing
    """
    return _ordered(term, others, TypeOrderedOperator.DECREASING if not strict else TypeOrderedOperator.STRICTLY_DECREASING, lengths)


def _lex(term, others, operator, matrix):
    if len(others) == 0:
        lists = [flatten(l) for l in term]
        assert is_matrix(lists, Variable)
    elif not is_1d_list(term, Variable):
        l1, l2 = flatten(term), flatten(others)
        assert len(l1) == len(l2)
        lists = [l1, l2]
    else:
        if len(others) == 1 and is_1d_list(others[0], int):
            assert matrix is False
            lists = [flatten(term)] + [flatten(others[0])]
        else:
            assert all(is_1d_list(l, Variable) for l in others)
            lists = [flatten(term)] + [flatten(l) for l in others]
    assert is_matrix(lists)  # new check because some null cells (variables) may have been discarded
    assert all(len(l) == len(lists[0]) for l in lists)
    assert all(checkType(l, [int, Variable] if i == 1 else [Variable]) for i, l in enumerate(lists))
    checkType(operator, TypeOrderedOperator)
    return ECtr(ConstraintLexMatrix(lists, operator)) if matrix else ECtr(ConstraintLex(lists, operator))


def LexIncreasing(term, *others, strict=False, matrix=False):
    """
    Builds and returns a constraint (increasing) Lexicographic.

    :param term: the first term on which the constraint applies
    :param others: the other terms (if any) on which the constraint applies
    :param strict: if True, strict ordering must be considered
    :param matrix: if True, the matrix version must be considered
    :return: a constraint Lexicographic
    """
    return _lex(term, others, TypeOrderedOperator.INCREASING if not strict else TypeOrderedOperator.STRICTLY_INCREASING, matrix)


def LexDecreasing(term, *others, strict=False, matrix=False):
    """
    Builds and returns a constraint (decreasing) Lexicographic.

    :param term: the first term on which the constraint applies
    :param others: the other terms (if any) on which the constraint applies
    :param strict: if True, strict ordering must be considered
    :param matrix: if True, the matrix version must be considered
    :return: a constraint Lexicographic
    """
    return _lex(term, others, TypeOrderedOperator.DECREASING if not strict else TypeOrderedOperator.STRICTLY_DECREASING, matrix)


def Precedence(scope, *, values=None, covered=False):
    """
    Builds and returns a constraint Precedence.

    :param scope: the scope of the constraint
    :param values: the values such that the ith value must precede the i+1th value in the scope.
    when None, all values in the scope of the first variable are considered
    :param covered: if True, all specified values must be assigned to the variables of the scope
    :return: a constraint Precedence
    """
    assert len(scope) > 2
    if values is None:
        return ECtr(ConstraintPrecedence(flatten(scope)))
        # assert all(scope[i].dom == scope[0].dom for i in range(1, len(scope)))
        # values = scope[0].dom.all_values()
    if isinstance(values, types.GeneratorType):
        values = list(values)
    assert isinstance(values, (range, tuple, list)) and all(isinstance(v, int) for v in values)
    values = list(values)
    if len(values) > 1:
        return ECtr(ConstraintPrecedence(flatten(scope), values=values, covered=covered))
    else:
        warning("A constraint Precedence discarded because defined with " + str(len(values)) + " values")
        return None


''' Method for handling complete/partial constraints '''


def _wrapping_by_complete_or_partial_constraint(ctr):
    condition = ctr.arguments[TypeCtrArg.CONDITION].content
    return ECtr(ctr) if condition is not None else PartialConstraint(ctr)


''' Counting and Summing Constraints '''


def Sum(term, *others, condition=None):
    """
    Builds and returns a component Sum (that becomes a constraint when subject to a condition)

    :param term: the first term on which the sum applies
    :param others: the other terms (if any) on which the sum applies
    :param condition: a condition directly specified for the sum (typically, None)
    :return: a component/constraint Sum
    """

    def _get_terms_coeffs(terms):
        if len(terms) == 1 and isinstance(terms[0], ScalarProduct):
            return flatten(terms[0].variables), flatten(terms[0].coeffs)
        if all(isinstance(x, (Variable, PartialConstraint)) for x in terms):
            return terms, None
        t1, t2 = [], []
        for tree in terms:
            if isinstance(tree, Variable):
                t1.append(tree)
                t2.append(-1 if tree.inverse else 1)
            else:
                assert isinstance(tree, Node)
                if tree.type == TypeNode.NEG and tree.sons[0].type == TypeNode.VAR:
                    pair = (tree.sons[0].sons, -1)
                else:
                    pair = tree.tree_val_if_binary_type(TypeNode.MUL)
                if pair is None:
                    break
                t1.append(pair[0])
                t2.append(pair[1])
        if len(t1) == len(terms):
            for tree in terms:
                if isinstance(tree, Node):
                    tree.mark_as_used()
            return t1, t2
        return terms, None

    def _manage_coeffs(terms, coeffs):
        if coeffs:
            OpOverrider.disable()
            if len(coeffs) == 1 and isinstance(coeffs[0], (tuple, set, range)):
                coeffs = list(coeffs[0])
            elif isinstance(coeffs, (tuple, set, range)):  # TODO is set appropriate?
                coeffs = list(coeffs)
            elif isinstance(coeffs, (int, Variable)):
                coeffs = [coeffs]
            assert len(terms) == len(coeffs), "Lists (vars and coeffs) should have the same length. Here, we have " + str(len(terms)) + "!=" + str(len(coeffs))
            # if 0 in coeffs:
            #    terms = [term for i, term in enumerate(terms) if coeffs[i] != 0]
            #    coeffs = [coeff for coeff in coeffs if coeff != 0]
            # if all(c == 1 for c in coeffs): coeffs = None
            checkType(coeffs, ([Node, Variable, int], type(None)))
            OpOverrider.enable()
        return terms, coeffs

    terms = flatten(list(term)) if isinstance(term, types.GeneratorType) else flatten(term, others)
    if any(v is None or (isinstance(v, int) and v == 0) for v in terms):  # note that False is of type int and equal to 0
        terms = [v for v in terms if v is not None and not (isinstance(v, int) and v == 0)]
    if len(terms) == 0:
        return 0  # TODO ConstraintDummyConstant(0)   # None
    auxiliary().replace_partial_constraints_and_constraints_with_condition_and_possibly_nodes(terms, nodes_too=options.mini)
    checkType(terms, ([Variable], [Node], [Variable, Node], [PartialConstraint], [ScalarProduct], [ECtr]))
    terms, coeffs = _get_terms_coeffs(terms)
    if options.groupsumcoeffs and all(isinstance(v, Variable) for v in terms) and coeffs is None:
        # maybe some variables occurs several times
        d = dict()
        for t in terms:
            d[t] = d.get(t, 0) + 1
        if any(v > 1 for v in d.values()):
            terms, coeffs = [list(v) for v in zip(*d.items())]
    terms, coeffs = _manage_coeffs(terms, coeffs)
    if len(terms) == 1 and (coeffs is None or coeffs[0] == 1):
        if condition is None:
            return terms[0]
        # else  return ...  # TODO returning a unary (or binary) constraint terms[0] <op> k?
    # TODO control here some assumptions (empty list seems to be possible. See RLFAP)
    return _wrapping_by_complete_or_partial_constraint(ConstraintSum(terms, coeffs, Condition.build_condition(condition)))


def Product(term, *others):
    """
    Builds and returns a node 'mul', root of a tree expression where specified arguments are children

    :param term: the first term on which the product applies
    :param others: the other terms (if any) on which the product applies
    :return: a node, root of a tree expression
    """

    terms = flatten(term, others)
    assert len(terms) > 0
    for i, t in enumerate(terms):
        if isinstance(t, PartialConstraint):
            terms[i] = auxiliary().replace_partial_constraint(t)
    checkType(terms, ([Variable], [Node]))
    return Node.build(TypeNode.MUL, *terms)


def Count(term, *others, value=None, values=None, condition=None):
    """
    Builds and returns a component Count (that becomes a constraint when subject to a condition).
    Either the named parameter value or the name parameter values must be used.

    :param term: the first term on which the count applies
    :param others: the other terms (if any) on which the count applies
    :param value: the value to be counted
    :param values: the values to be counted
    :param condition: a condition directly specified for the count (typically, None)
    :return: a component/constraint Count
    """
    terms = flatten(term, others)
    if len(terms) == 0:
        return ConstraintDummyConstant(0)
    # assert len(terms) > 0, "A count with an empty scope"

    terms = manage_global_indirection(terms, also_pc=True)
    assert terms is not None
    checkType(terms, ([Variable], [Node], [Variable, Node]))

    if value is None and values is None:
        value = 1
    assert value is None or values is None, str(value) + " " + str(values)
    values = list(values) if isinstance(values, (tuple, set)) else [value] if isinstance(value, (int, Variable)) else values
    if isinstance(value, PartialConstraint):
        values = [auxiliary().replace_partial_constraint(value)]
    elif isinstance(value, Node):
        values = [auxiliary().replace_node(value)]
    values = sorted(set(values))  # ordered set of values
    checkType(values, ([int], [Variable]))
    # terms = list(terms)
    return _wrapping_by_complete_or_partial_constraint(ConstraintCount(terms, values, Condition.build_condition(condition)))


def Exist(term, *others, value=None):
    """
    Builds and returns a constraint Count that checks if at least one of the term evaluates to the specified value,
    or to 1 (seen as True) when value is None.

    :param term: the first term on which the count applies
    :param others: the other terms (if any) on which the count applies
    :param value the value to be found if not None (None, by default)
    :return: a constraint Count
    """
    terms = flatten(term, others)
    if value is None:
        if len(terms) == 1:
            return terms[0]
        if len(terms) == 2:
            return disjunction(terms)
        # if all(isinstance(t, Node) and t.type.is_predicate_operator() for t in terms):  # TODO is that interesting?
        #     return disjunction(terms)
    res = Count(terms, value=value)
    if isinstance(res, int):
        assert res == 0
        return 0  # for false
    return res >= 1


def AnyHold(term, *others):
    """
    Builds and returns a constraint Count that checks if at least one term evaluates to 1 (seen as True).

    :param term: the first term on which the count applies
    :param others: the other terms (if any) on which the count applies
    :return: a constraint Count
    """
    return Exist(term, others, value=None)


def NotExist(term, *others, value=None):
    """
    Builds and returns a constraint Count that checks that no term evaluates to the specified value,
    or to 1 (seen as True) when value is None.

    :param term: the first term on which the count applies
    :param others: the other terms (if any) on which the count applies
    :param value the value to be tested if not None (None, by default)
    :return: a constraint Count
    """
    terms = flatten(term, others)
    res = Count(terms, value=value)
    if isinstance(res, int):
        assert res == 0
        return 1  # for true
    return res == 0


def NoneHold(term, *others):
    """
    Builds and returns a constraint Count that checks that no term evaluates to 1 (seen as True).

    :param term: the first term on which the count applies
    :param others: the other terms (if any) on which the count applies
    :return: a constraint Count
    """
    return NotExist(term, others, value=None)


def ExactlyOne(term, *others, value=None):
    """
    Builds and returns a constraint Count that checks that exactly one term evaluates to 1 (seen as True) when value is not specified,
    or to the value (when the parameter is specified, and not None)

    :param term: the first term on which the count applies
    :param others: the other terms (if any) on which the count applies
    :param value the value to be found if not None (None, by default)
    :return: a constraint Count
    """
    terms = flatten(term, others)
    res = Count(terms, value=value)
    if isinstance(res, int):
        assert res == 0
        return 0  # for false
    return res == 1
    # return Sum(term, others) == 1


def AtLeastOne(term, *others, value=None):
    """
    Builds and returns a constraint Count that checks that at least one term evaluates to 1 (seen as True) when value is not specified,
    or to the value (when the parameter is specified, and not None).

    :param term: the first term on which the count applies
    :param others: the other terms (if any) on which the count applies
    :param value the value to be found if not None (None, by default)
    :return: a constraint Count
    """
    return Exist(term, others, value)


def AtMostOne(term, *others, value=None):
    """
    Builds and returns a constraint Count that checks that at most one term evaluates to 1 (seen as True) when value is not specified,
    or to the value (when the parameter is specified, and not None).

    :param term: the first term on which the count applies
    :param others: the other terms (if any) on which the count applies
    :param value the value to be found if not None (None, by default)
    :return: a constraint Count
    """
    terms = flatten(term, others)
    res = Count(terms, value=value)
    if isinstance(res, int):
        assert res == 0
        return 1  # for true
    return res <= 1


def AllHold(term, *others):
    """
    Builds and returns a constraint Count that checks that all terms evaluate to 1 (seen as True).

    :param term: the first term on which the count applies
    :param others: the other terms (if any) on which the count applies
    :return: a constraint Count
    """
    terms = flatten(term, others)
    res = Count(terms)  # , value=value)
    if isinstance(res, int):
        assert res == 0
        return 1  # for true
    return res == len(terms)


def Hamming(term, *others):
    """
    Builds and returns a constraint Sum, corresponding to the Hamming distance of the two specified lists.

    :param term: the first term on which the constraint applies
    :param others: the other terms (if any) on which the constraint applies
    :return: a constraint Sum
    """
    if isinstance(term, types.GeneratorType):
        term = [l for l in term]
    elif len(others) > 0:
        term = list((term,) + others)
    lists = [flatten(l) for l in term]
    assert all(checkType(l, [Variable]) for l in lists) and len(lists) == 2 and len(lists[0]) == len(lists[1])
    return Sum(lists[0][j] != lists[1][j] for j in range(len(lists[0])))


def NValues(term, *others, excepting=None, condition=None):
    """
    Builds and returns a component NValues (that becomes a constraint when subject to a condition).

    :param term: the first term on which the NValues applies
    :param others: the other terms (if any) on which the NValues applies
    :param excepting: the value(s) that must be ignored (None, most of the time)
    :param condition: a condition directly specified for the count (typically, None)
    :return: a component/constraint NValues
    """
    terms = flatten(term, others)
    if len(terms) == 0:
        return 0
    for i, t in enumerate(terms):
        if isinstance(t, PartialConstraint):
            terms[i] = auxiliary().replace_partial_constraint(t)
        elif isinstance(t, int):
            terms[i] = auxiliary().replace_int(t)
    checkType(terms, ([Variable], [Node]))
    if excepting is not None:
        excepting = flatten(excepting)
        checkType(excepting, [int])
    return _wrapping_by_complete_or_partial_constraint(ConstraintNValues(terms, excepting, Condition.build_condition(condition)))


def NotAllEqual(term, *others):
    """
      Builds and returns a component NValues (capturing NotAllEqual)

      :param term: the first term on which the constraint applies
      :param others: the other terms (if any) on which the constraint applies
      :return: a constraint NValues (equivalent to NotAllEqual)
      """
    return NValues(term, others) > 1


def Cardinality(term, *others, occurrences, closed=False):
    """
    Builds and returns a constraint Cardinality.

    When occurrences is given under the form of a list or tuple t,
    a dictionary is computed as dict(enumerate(t))

    :param term: the first term on which the constraint applies
    :param others: the other terms (if any) on which the constraint applies
    :param occurrences: a dictionary indicating the restriction (constant, range or variable) of occurrences per value
    :param closed: if True, variables must be assigned to values (keys of the dictionary)
    :return: a Cardinality constraint
    """
    terms = flatten(term, others)
    for i, t in enumerate(terms):
        if isinstance(t, PartialConstraint):
            terms[i] = auxiliary().replace_partial_constraint(t)
        elif isinstance(t, Node):
            terms[i] = [auxiliary().replace_node(t)]
    checkType(terms, [Variable])
    if isinstance(occurrences, (tuple, list)):
        occurrences = dict(enumerate(occurrences))
    assert isinstance(occurrences, dict)
    values = list(occurrences.keys())
    assert all(isinstance(value, (int, Variable)) for value in values)
    occurs = list(occurrences.values())
    checkType(closed, (bool, type(None)))
    for i, occ in enumerate(occurs):
        if isinstance(occ, range):
            occurs[i] = min(occ) if len(occ) == 1 else str(min(occ)) + ".." + str(max(occ))
        if isinstance(occ, list):
            flat = flatten(occ)
            if len(flat) == 1:
                flat = flat[0]
            elif all(isinstance(e, int) for e in flat) and flat == list(range(min(flat), max(flat) + 1)):
                flat = str(min(flat)) + ".." + str(max(flat))
            occurs[i] = flat
    return ECtr(ConstraintCardinality(terms, values, occurs, closed))


''' Connection Constraints '''


def _extremum_terms(term, others):
    terms = list(term) if isinstance(term, types.GeneratorType) else flatten(term, others)
    terms = [Sum(t) if isinstance(t, ScalarProduct) else t for t in terms]  # to have PartialConstraints
    # if len(terms) == 0:
    #     return None
    # if len(terms) == 1:
    #     return terms[0]
    checkType(terms, ([Variable, Node, int], [PartialConstraint]))
    auxiliary().replace_partial_constraints_and_constraints_with_condition_and_possibly_nodes(terms)
    return terms


def Maximum(term, *others, condition=None):
    """
    Builds and returns a component Maximum (that becomes a constraint when subject to a condition).

    :param term: the first term on which the maximum applies
    :param others: the other terms (if any) on which the maximum applies
    :param condition: a condition directly specified for the maximum (typically, None)
    :return: a component/constraint Maximum
    """
    terms = _extremum_terms(term, others)
    c = ConstraintMaximum(terms, condition)
    return _wrapping_by_complete_or_partial_constraint(c) if isinstance(c, ConstraintMaximum) else c


def Minimum(term, *others, condition=None):
    """
    Builds and returns a component Minimum (that becomes a constraint when subject to a condition).

    :param term: the first term on which the minimum applies
    :param others: the other terms (if any) on which the minimum applies
    :param condition: a condition directly specified for the minimum (typically, None)
    :return: a component/constraint Minimum
    """
    terms = _extremum_terms(term, others)
    c = ConstraintMinimum(terms, condition)
    return _wrapping_by_complete_or_partial_constraint(c) if isinstance(c, ConstraintMinimum) else c


def MaximumArg(term, *others, rank=None, condition=None):
    """
    Builds and returns a component MaximumArg (that becomes a constraint when subject to a condition).

    :param term: the first term on which the maximum applies
    :param others: the other terms (if any) on which the maximum applies
    :param rank: ranking condition on the index (ANY, FIRST or LAST); ANY if None
    :param condition: a condition directly specified for the maximum (typically, None)
    :return: a component/constraint MaximumArg
    """
    terms = _extremum_terms(term, others)
    checkType(rank, (type(None), TypeRank))
    c = ConstraintMaximumArg(terms, rank, condition)
    return _wrapping_by_complete_or_partial_constraint(c) if isinstance(c, ConstraintMaximumArg) else c


def MinimumArg(term, *others, rank=None, condition=None):
    """
    Builds and returns a component MinimumArg (that becomes a constraint when subject to a condition).

    :param term: the first term on which the maximum applies
    :param others: the other terms (if any) on which the maximum applies
    :param rank: ranking condition on the index (ANY, FIRST or LAST); ANY if None
    :param condition: a condition directly specified for the maximum (typically, None)
    :return: a component/constraint MinimumArg
    """
    terms = _extremum_terms(term, others)
    checkType(rank, (type(None), TypeRank))
    c = ConstraintMinimumArg(terms, rank, condition)
    return _wrapping_by_complete_or_partial_constraint(c) if isinstance(c, ConstraintMinimumArg) else c


def Channel(list1, list2=None, *, start_index1=0, start_index2=0):
    """
    Builds a constraint Channel between the two specified lists.

    :param list1: the first list to be channeled
    :param list2: the second list to be channeled
    :param start_index1: the number used for indexing the first variable in the first list (0, by default)
    :param start_index2: the number used for indexing the first variable in the second list (0, by default)
    :return: a constraint Channel
    """
    list1 = flatten(list1)
    checkType(list1, [Variable])
    if list2:
        list2 = flatten(list2)
        checkType(list2, [Variable])
    checkType(start_index1, int)
    checkType(start_index2, int)
    assert start_index2 == 0 or list2 is not None, "start_index2 is defined while list2 is not specified"
    return ECtr(ConstraintChannel(list1, start_index1, list2, start_index2))


''' Packing and Scheduling Constraints '''


def _is_mixed_list(t, index=-1):
    present_int, present_var, present_node = False, False, False
    for v in t:
        v = v if index == -1 else v[index]
        if isinstance(v, int):
            present_int = True
        elif isinstance(v, Variable):
            present_var = True
        elif isinstance(v, Node):
            present_node = True
        if (present_int and present_var) or (present_int and present_node) or (present_var and present_node):
            return True
    return False


def NoOverlap(tasks=None, *, origins=None, lengths=None, zero_ignored=False):
    """
    Builds and returns a constraint NoOverlap.
    Either the tasks are specified as pairs, or the tasks are given by the name parameters origins and lengths.

    :param tasks: the tasks given as pairs composed of an origin and a length
    :param origins: the origins of the tasks
    :param lengths: the lengths of the tasks
    :param zero_ignored: if True, the tasks with length 0 must be discarded
    :return: a constraint NoOverlap
    """
    if tasks is not None:
        assert origins is None and lengths is None
        tasks = list(tasks) if isinstance(tasks, (tuple, set, frozenset, types.GeneratorType)) else tasks
        if len(tasks) <= 1:
            warning("A constraint NoOverlap discarded because defined with " + str(len(tasks)) + " task")
            return ConstraintDummyConstant(1)  # return None
        assert isinstance(tasks, list) and len(tasks) > 0
        for i, task in enumerate(tasks):
            assert isinstance(task, (tuple, list)) and len(task) in (2, 3)
            if len(task) == 3:
                assert task[2] is None
                tasks[i] = task[:2]
        origins, lengths = zip(*tasks)
    if isinstance(origins, zip):
        origins = list(origins)
    if isinstance(lengths, zip):
        lengths = list(lengths)
    if len(origins) == 2 and len(lengths) == 2 and all(isinstance(t, (list, tuple)) for t in [origins[0], origins[1], lengths[0], lengths[1]]):
        assert len(origins[0]) == len(origins[1]) == len(lengths[0]) == len(lengths[1])
        origins = [(origins[0][i], origins[1][i]) for i in range(len(origins[0]))]
        lengths = [(lengths[0][i], lengths[1][i]) for i in range(len(lengths[0]))]
    checkType(origins, [int, Variable])
    if not isinstance(origins[0], Variable) and not isinstance(origins[0], tuple):  # if 2D but not tuples
        origins = [tuple(origin) for origin in origins]
    lengths = [lengths for _ in range(len(origins))] if isinstance(lengths, int) else lengths
    if not isinstance(lengths[0], (int, Variable)) and not isinstance(lengths[0], tuple):  # if 2D but not tuples
        lengths = [tuple(length) for length in lengths]
    checkType(lengths, ([int, Variable]))
    if isinstance(origins, list) and len(origins) > 0 and isinstance(origins[0], tuple) and len(origins[0]) == 2:  # if 2D
        # currently, only variables are authorized in origins
        origins = [(auxiliary().replace_int(u) if isinstance(u, int) else u, auxiliary().replace_int(v) if isinstance(v, int) else v)
                   for (u, v) in origins]
    if isinstance(lengths, list) and len(lengths) > 0 and isinstance(lengths[0], tuple) and len(lengths[0]) == 2:  # if 2D
        # currently, either only variables or only integers
        b0 = _is_mixed_list(lengths, 0)
        b1 = _is_mixed_list(lengths, 1)
        if b0 or b1:
            lengths = [(auxiliary().replace_int(u) if b0 and isinstance(u, int) else u, auxiliary().replace_int(v) if b1 and isinstance(v, int) else v)
                       for (u, v) in lengths]
    if options.mini:
        assert zero_ignored is False  # for the moment
        t = []
        if isinstance(origins[0], Variable):  # 1D
            for i in range(len(origins)):
                for j in range(i + 1, len(origins)):
                    xi, xj = origins[i], origins[j]
                    li, lj = lengths[i], lengths[j]
                    if xi.dom.greatest_value() + li <= xj.dom.smallest_value() or xj.dom.greatest_value() + lj <= xi.dom.smallest_value():
                        continue
                    t.append((xi, xj) in to_starred_table_for_no_overlap1(xi, xj, li, lj))
        else:  # 2D
            for i in range(len(origins)):
                for j in range(i + 1, len(origins)):
                    xi, xj, yi, yj = origins[i][0], origins[j][0], origins[i][1], origins[j][1]
                    wi, wj, hi, hj = lengths[i][0], lengths[j][0], lengths[i][1], lengths[j][1]
                    if xi.dom.greatest_value() + wi <= xj.dom.smallest_value or xj.dom.greatest_value() + wj <= xi.dom.smallest_value():
                        continue
                    if yi.dom.greatest_value + hi <= yj.dom.smallest_value or yj.dom.greatest_value() + hj <= yi.dom.smallest_value():
                        continue
                    t.append((xi, xj, yi, yj) in to_starred_table_for_no_overlap2(xi, xj, yi, yj, wi, wj, hi, hj))
        return t
    return ECtr(ConstraintNoOverlap(origins, lengths, zero_ignored))


def Cumulative(tasks=None, *, origins=None, lengths=None, ends=None, heights=None, condition=None):
    """
    Builds and returns a component Cumulative (that becomes a constraint when subject to a condition).
    Either the tasks are specified as tuples of size 3 or 4, or the tasks are given by the name parameters
    origins, lengths and heights (and possibly ends).

    :param tasks:
    :param origins: the origins of the tasks
    :param lengths: the lengths of the tasks
    :param ends: the ends of the tasks (typically, None)
    :param heights: the heights (amounts of resource consumption) of the tasks
    :param condition: a condition directly specified for the Cumulative (typically, None)
    :return: a component/constraint Cumulative
    """
    if tasks is not None:
        assert origins is None and lengths is None and ends is None and heights is None
        tasks = list(tasks) if isinstance(tasks, (tuple, set, frozenset, types.GeneratorType)) else tasks
        if len(tasks) == 0:
            warning("A constraint Cumulative transformed because defined with 0 task")
            return ConstraintDummyConstant(0)  # auxiliary().replace_int(0)
        if len(tasks) == 1:
            warning("A constraint Cumulative transformed because defined with 1 task only")
            h = tasks[0][2 if len(tasks[0]) == 3 else 3]  # the height for the task
            return h if isinstance(h, Variable) else ConstraintDummyConstant(h)  # auxiliary().replace_int(h)

        assert len(tasks) > 0, "a cumulative constraint without no tasks"
        assert isinstance(tasks, list) and len(tasks) > 0
        v = len(tasks[0])
        assert v in (3, 4) and any(isinstance(task, (tuple, list)) and len(task) == v for task in tasks)
        if v == 3:
            origins, lengths, heights = zip(*tasks)
        else:
            origins, lengths, ends, heights = zip(*tasks)
    origins = flatten(origins)
    auxiliary().replace_partial_constraints_and_constraints_with_condition_and_possibly_nodes(origins, nodes_too=True)
    if _is_mixed_list(origins):
        origins = auxiliary().replace_ints(origins)
    checkType(origins, [Variable])
    lengths = [lengths for _ in range(len(origins))] if isinstance(lengths, int) else flatten(lengths)
    if _is_mixed_list(lengths):
        lengths = auxiliary().replace_ints(lengths)
    checkType(lengths, ([Variable], [int]))
    heights = [heights for _ in range(len(origins))] if isinstance(heights, int) else flatten(heights)
    if _is_mixed_list(heights):
        heights = auxiliary().replace_ints(heights)
    for i, h in enumerate(heights):
        if isinstance(h, PartialConstraint):
            heights[i] = auxiliary().replace_partial_constraint(h)
        elif isinstance(h, Node):
            heights[i] = auxiliary().replace_node(h)
    checkType(heights, ([Variable], [int]))
    ends = flatten(ends) if ends is not None else ends  # ends is optional
    checkType(ends, ([Variable], type(None)))
    return _wrapping_by_complete_or_partial_constraint(ConstraintCumulative(origins, lengths, ends, heights, Condition.build_condition(condition)))


def BinPacking(term, *others, sizes, limits=None, loads=None, condition=None):
    """
    Builds and returns a component BinPacking that:
      - either is directly a constraint when capacities (limits or loads) are given
      - or becomes a constraint when subject to a condition (specified outside the function)
    Capacities can be given by integers or variables, by specifying either limits or loads.
    When capacities are absent (both limits and loads being None), BinPacking is a component
    that must be subject to a condition, typically '<= k' where k is a value used as the same limit for all bins.

    :param term: the first term on which the component applies
    :param others: the other terms (if any) on which the component applies
    :param sizes: the sizes of the available items
    :param limits: the limits of bins (if loads is None)
    :param loads: the loads of bins (if limits is None)
    :param condition: a condition directly specified for the BinPacking (typically, None)
    :return: a component/constraint BinPacking
    """
    terms = flatten(term, others)
    assert len(terms) > 0, "A binPacking with an empty scope"
    checkType(terms, [Variable])
    if isinstance(sizes, int):
        sizes = [sizes for _ in range(len(terms))]
    sizes = flatten(sizes)
    checkType(sizes, [int])
    assert len(terms) == len(sizes)
    assert limits is None or loads is None
    if limits is not None:
        assert condition is None
        checkType(limits, ([Variable], [int]))
        return ECtr(ConstraintBinPacking(terms, sizes, limits=limits))
    if loads is not None:
        assert condition is None
        checkType(loads, ([Variable], [int]))
        return ECtr(ConstraintBinPacking(terms, sizes, loads=loads))
    return _wrapping_by_complete_or_partial_constraint(ConstraintBinPacking(terms, sizes, condition=Condition.build_condition(condition)))


def Knapsack(term, *others, weights, wlimit=None, wcondition=None, profits, pcondition=None):
    """
    Builds and returns a component Knapsack that must guarantee that a condition holds wrt the capacity of the knapsack
    (when considering accumulated weights of selected items) and another condition holds wrt the profits.
    The second condition is typically specified outside the function which then represents ("returns")
    the accumulated profits of selected items.
    One has to specify either wlimit or wcondition.

    :param term: the first term on which the component applies
    :param others: the other terms (if any) on which the component applies
    :param weights: the weights associated with the items
    :param wlimit: the limit of the knapsack (if wcondition is None)
    :param wcondition: the condition on the knapsack (if wlimit is None)
    :param profits: the benefits associated with the items
    :param pcondition: a condition on the profits directly specified for the Knapsack (typically, None)
    :return: a component/constraint Knapsack
    """

    terms = flatten(term, others)
    assert len(terms) > 0, "A Knapsack with an empty scope"
    assert len(terms) == len(weights) == len(profits)
    assert (wlimit is None) != (wcondition is None)
    if wlimit:
        checkType(wlimit, (int, Variable))
        wcondition = le(wlimit)
    checkType(wcondition, Condition)
    return _wrapping_by_complete_or_partial_constraint(ConstraintKnapsack(terms, weights, wcondition, profits, Condition.build_condition(pcondition)))


def Flow(term, *others, balance, arcs, weights=None, condition=None):
    terms = flatten(term, others)
    assert len(terms) > 0, "A Flow with an empty scope"
    if isinstance(weights, int):
        weights = [weights for _ in range(len(terms))]
    assert len(terms) == len(arcs) and (weights is None or len(terms) == len(weights))
    assert isinstance(arcs, list)
    for i, arc in enumerate(arcs):
        if isinstance(arc, list):
            arcs[i] = tuple(arc)
    assert all(isinstance(arc, tuple) and len(arc) == 2 and isinstance(arc[0], int) and isinstance(arc[1], int) for arc in arcs)
    all_nodes = {node for arc in arcs for node in arc}
    mina, maxa = min(all_nodes), max(all_nodes)
    if isinstance(balance, int):
        balance = [balance for _ in range(maxa - mina + 1)]
    assert maxa - mina + 1 == len(balance) and all(v in all_nodes for v in range(mina, maxa + 1))
    return _wrapping_by_complete_or_partial_constraint(ConstraintFlow(terms, balance, arcs, weights, Condition.build_condition(condition)))


''' Constraints on Graphs'''


def Circuit(term, *others, start_index=0, size=None):
    """
    Builds and returns a constraint Circuit.

    :param term: the first term on which the constraint applies
    :param others: the other terms (if any) on which the constraint applies
    :param start_index: the number used for indexing the first variable/node in the list of terms
    :param size: the size of the circuit (a constant, a variable or None)
    :return: a constraint Circuit
    """
    terms = flatten(term, others)
    checkType(terms, [Variable])
    checkType(start_index, int)
    checkType(size, (int, Variable, type(None)))
    return ECtr(ConstraintCircuit(terms, start_index, size))


''' Elementary Constraints '''


def Clause(term, *others, phases=None):
    literals = flatten(term, others)
    phases = [False] * len(literals) if phases is None else flatten(phases)
    assert len(literals) == len(phases)
    checkType(literals, [Variable])
    checkType(phases, [bool])
    for i, literal in enumerate(literals):
        if literal.negation:
            phases[i] = True
    return ECtr(ConstraintClause(literals, phases))


''' Objectives '''


def _optimize(term, minimization):
    if options.tocsp:
        if options.tocsp[0] in ('(', '['):
            assert len(options.tocsp) > 5 and options.tocsp[-1] in (')', ']') and options.tocsp[3] == ','
            op, k = options.tocsp[1:3], int(options.tocsp[4:-1])
        else:
            op, k = "eq", int(options.tocsp)
        if isinstance(term, Node):
            #  term.mark_as_used() # TODO do we need to do that?
            return satisfy(expr(op, term, k), no_comment_tags_extraction=True)
        op = TypeConditionOperator.value_of(op)
        if op == TypeConditionOperator.LT:
            return satisfy(term < k)
        if op == TypeConditionOperator.LE:
            return satisfy(term <= k)
        if op == TypeConditionOperator.GE:
            return satisfy(term >= k)
        if op == TypeConditionOperator.GT:
            return satisfy(term > k)
        if op == TypeConditionOperator.EQ:
            return satisfy(term == k)
        assert op == TypeConditionOperator.NE
        return satisfy(term != k)

    ObjEntities.items = []  # TODO currently, we overwrite the objective if one was posted
    if isinstance(term, PartialConstraint) and isinstance(term.constraint, (ConstraintSum, ConstraintMaximum, ConstraintMinimum)):
        l = term.constraint.arguments[TypeCtrArg.LIST]
        if len(l.content) == 1 and TypeCtrArg.COEFFS not in term.constraint.arguments:
            term = l.content[0]  # this was a sum/maximum/minimum with only one term, so we just consider this term as an expression to be optimized
    if isinstance(term, ScalarProduct):
        term = Sum(term)  # to have a PartialConstraint
    checkType(term, (Variable, Node, PartialConstraint)), "Did you forget to use Sum, e.g., as in Sum(x[i]*3 for i in range(10))"
    satisfy(pc == var for (pc, var) in auxiliary().get_collected_and_clear())

    comment, _, tag, _ = comments_and_tags_of_parameters_of(function_name="minimize" if minimization else "maximize", args=[term])
    way = TypeCtr.MINIMIZE if minimization else TypeCtr.MAXIMIZE
    if isinstance(term, (Variable, Node)):
        if isinstance(term, Node):
            term.mark_as_used()
        return EObjective(ObjectiveExpression(way, term)).note(comment[0]).tag(tag[0])  # TODO why only one tag?
    else:
        return EObjective(ObjectivePartial(way, term)).note(comment[0]).tag(tag[0])


def minimize(term):
    """
    Builds and returns an objective that corresponds to minimizing the specified term.
    This term can be a variable, an expression, a component Sum, Count, NValues, Maximum, Minimum, etc.

    :param term: the term to be minimized
    :return: the objective to be minimized
    """
    return _optimize(term, True)


def maximize(term):
    """
    Builds and returns an objective that corresponds to maximizing the specified term.
    This term can be a variable, an expression, a component Sum, Count, NValues, Maximum, Minimum, etc.

    :param term: the term to be maximized
    :return: the objective to be maximized
    """
    return _optimize(term, False)


''' Annotations '''


def annotate(*, decision=None, output=None, varHeuristic=None, valHeuristic=None, filtering=None, prepro=None, search=None, restarts=None):
    def add_annotation(obj, Ann):
        if obj:
            ann = Ann(obj)
            assert type(ann) not in AnnEntities.items_types, "This type of annotation can be specified only one time"
            annotations.append(EAnnotation(ann))

    annotations = []
    add_annotation(decision, AnnotationDecision)
    add_annotation(output, AnnotationOutput)
    add_annotation(varHeuristic, AnnotationVarHeuristic)
    add_annotation(valHeuristic, AnnotationValHeuristic)
    add_annotation(filtering, AnnotationFiltering)
    add_annotation(prepro, AnnotationPrepro)
    add_annotation(search, AnnotationSearch)
    add_annotation(restarts, AnnotationRestarts)
    return annotations


''' Helpers '''


def posted(i=None, j=None):
    """
    Returns the list of posted constraints when no parameter is specified.
    Returns the constraints of the ith posted operation, otherwise; possibly
    a subset is returned if teh second parameter j is specified.

    :param i: the number/index of the posting operation (i.e., call to satisfy())
    :param j: the number (or slice) of the constraint wrt the ith posting operation
    """
    t = []
    if i is None or i is ALL:  # all posted constraints are returned
        assert j is None
        for item in CtrEntities.items:
            assert isinstance(item, EToSatisfy)
            t.extend(c for c in item.flat_constraints())
    else:
        assert isinstance(i, (int, slice))
        if j is None:
            for item in [CtrEntities.items[i]] if isinstance(i, int) else CtrEntities.items[i]:
                assert isinstance(item, EToSatisfy)
                t.extend(c for c in item.flat_constraints())
        else:
            assert isinstance(i, int) and isinstance(j, (int, slice))
            item = CtrEntities.items[i]
            if isinstance(j, int):
                t.append(item.flat_constraints()[j])
            else:
                t.extend(c for c in item.flat_constraints()[j])
    return t if len(t) == 0 else ListCtr(t)


def objective():
    """
    Returns the objective of the model, or None if no one has been defined by calling either the function minimize() or the function maximize()
    """
    assert len(ObjEntities.items) <= 1
    return ObjEntities.items[0].constraint if len(ObjEntities.items) == 1 else None


def unpost(i=None, j=None):
    """
    If no parameter is specified, discards the last posting operation (call to satisfy).
    If two parameters are specified, discards the constraint(s) whose index(es) is specified
    by the second argument j (possibly a slice) inside the posting operation whose index is specified by the first parameter.
    If one parameter is specified, discards the posting operation whose index is specified,
    except if the constant ALL is used, in which case all posted constraints are discarded.

    :param i: the index of the posting operation (call to satisfy) to be discarded (if j is None)
    :param j: the index (or slice) of the constraint(s) to be removed inside the group of constraints
              corresponding to the specified posting operation
    """
    if i is None:
        i = -1
    if j is None:
        if i is ALL:
            CtrEntities.items = []
        else:
            assert isinstance(i, (int, slice))
            del CtrEntities.items[i]
    else:
        assert isinstance(i, int)
        CtrEntities.items[i].delete(j)


def value(x, *, sol=-1):
    """
    Returns the value assigned to the specified variable when the solution at the specified index has been found

    :param x: a variable
    :param sol: the index of a found solution
    """
    assert isinstance(x, Variable) and len(x.values) > 0
    return x.values[sol]


def values(m, *, sol=-1):
    """
    Returns a list similar to the specified structure with the values assigned to the involved variables
    when the solution at the specified index has been found

    :param m: a structure (typically list) of any dimension involving variables
    :param sol: the index of a found solution
    """
    if isinstance(m, Variable):
        return value(m, sol=sol)
    if isinstance(m, (list, tuple, set, frozenset, types.GeneratorType)):
        g = [values(v, sol=sol) for v in m]
        return ListInt(g) if len(g) > 0 and (isinstance(g[0], (int, ListInt)) or g[0] == ANY) else g
