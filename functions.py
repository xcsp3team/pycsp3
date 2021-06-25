import inspect
import math
import types
from collections import namedtuple
from itertools import combinations, product, permutations

from pycsp3.classes.auxiliary.conditions import Condition, ConditionInterval, ConditionSet, lt, le, ge, gt, ne, complement
from pycsp3.classes.auxiliary.ptypes import TypeOrderedOperator, TypeConditionOperator, TypeVar, TypeCtr, TypeCtrArg, TypeRank
from pycsp3.classes.auxiliary.structures import Automaton, MDD
from pycsp3.classes.entities import (
    EVar, EVarArray, ECtr, EMetaCtr, ECtrs, EToGather, EToSatisfy, EBlock, ESlide, EAnd, EOr, ENot, EXor, EIfThen, EIfThenElse, EIff, EObjective, EAnnotation,
    AnnEntities,
    TypeNode, Node)
from pycsp3.classes.main.annotations import (
    AnnotationDecision, AnnotationOutput, AnnotationVarHeuristic, AnnotationValHeuristic, AnnotationFiltering, AnnotationPrepro, AnnotationSearch,
    AnnotationRestarts)
from pycsp3.classes.main.constraints import (
    ConstraintIntension, ConstraintExtension, ConstraintRegular, ConstraintMdd, ConstraintAllDifferent,
    ConstraintAllDifferentList, ConstraintAllDifferentMatrix, ConstraintAllEqual, ConstraintOrdered, ConstraintLex, ConstraintLexMatrix, ConstraintSum,
    ConstraintCount, ConstraintNValues, ConstraintCardinality, ConstraintMaximum, ConstraintMinimum, ConstraintChannel, ConstraintNoOverlap,
    ConstraintCumulative, ConstraintBinPacking, ConstraintCircuit, ConstraintClause, PartialConstraint, ScalarProduct, auxiliary, global_indirection,
    manage_global_indirection)
from pycsp3.classes.main.domains import Domain
from pycsp3.classes.main.objectives import ObjectiveExpression, ObjectivePartial
from pycsp3.classes.main.variables import Variable, VariableInteger, VariableSymbolic
from pycsp3.compiler import default_data
from pycsp3.dashboard import options
from pycsp3.tools import curser
from pycsp3.tools.curser import OpOverrider, ListInt, ListVar
from pycsp3.tools.inspector import checkType, extract_declaration_for, comment_and_tags_of, comments_and_tags_of_parameters_of
from pycsp3.tools.utilities import ANY, flatten, is_1d_list, is_1d_tuple, is_matrix, is_square_matrix, transpose, alphabet_positions, all_primes, \
    integer_scaling, to_ordinary_table

''' Global Variables '''

absPython, maxPython, minPython, combinationsPython = abs, max, min, combinations


def combinations(n, size):
    return combinationsPython(n, size) if not isinstance(n, int) else combinationsPython(range(n), size)


def protect():
    return OpOverrider.disable()


''' Checking Model Variants '''


def variant(name=None):
    """"
       test
    """
    pos = -1 if not options.variant else options.variant.find("-")  # position of dash ('-') in options.variant
    if not name:
        return options.variant[0:pos] if pos != -1 else options.variant
    return options.variant[0:pos] == name if pos != -1 else options.variant == name


def subvariant(name=None):
    pos = -1 if not options.variant else options.variant.find("-")  # position of dash ('-') in options.variant
    if not name:
        return None if pos == -1 else options.variant[pos + 1:]
    return pos != -1 and options.variant[pos + 1:] == name


''' Declaring stand-alone variables and arrays '''


def Var(term=None, *others, dom=None):
    if term is None and dom is None:
        dom = Domain(math.inf)
    assert not (term and dom)
    if term is not None:
        dom = flatten(term, others)
    if not isinstance(dom, Domain):
        dom = Domain(dom)
    name = extract_declaration_for("Var")
    comment, tags = comment_and_tags_of(function_name="Var")

    assert isinstance(comment, (str, type(None))), "A comment must be a string (or None). Usually, they are given on plain lines preceding the declaration"
    assert name not in Variable.name2obj, "The identifier " + name + " is used twice. This is not possible"
    assert dom.get_type() in {TypeVar.INTEGER, TypeVar.SYMBOLIC}, "Currently, only integer and symbolic variables are supported. Problem with " + str(dom)
    assert str(name) not in Variable.name2obj, "The identifier " + name + " is used twice. This is not possible"

    var_object = VariableInteger(name, dom) if dom.get_type() == TypeVar.INTEGER else VariableSymbolic(name, dom)
    Variable.name2obj[name] = var_object
    EVar(var_object, comment, tags)  # object wrapping the variable x
    return var_object


def VarArray(*, size, dom, comment=None):
    size = [size] if isinstance(size, int) else size
    assert all(dimension != 0 for dimension in size), "No dimension must not be equal to 0"
    checkType(size, [int])
    # checkType(dom, (range, Domain, [int, range, str, Domain, type(None)], type(lambda: 0)))  # TODO a problem with large sets
    name = extract_declaration_for("VarArray")
    if comment is None and not isinstance(name, list):
        comment, tags = comment_and_tags_of(function_name="VarArray")
    else:
        tags = []

    assert isinstance(comment, (str, type(None))), "A comment must be a string (or None). Usually, they are given on plain lines preceding the declaration"
    assert not isinstance(dom, type(lambda: 0)) or len(size) == len(inspect.signature(dom).parameters), \
        "The number of arguments of the lambda must be equal to the number of dimensions of the multidimensional array"
    assert isinstance(comment, (str, type(None))), "A comment must be a string (or None). Usually, they are given on plain lines preceding the declaration"
    assert str(name) not in Variable.name2obj, "The identifier " + name + " is used twice. This is not possible"

    if isinstance(dom, (tuple, list, set)):
        domain = flatten(dom)
        assert all(isinstance(v, int) for v in domain) or all(isinstance(v, str) for v in domain)
        dom = Domain(set(domain))

    var_objects = Variable.build_variables_array(name, size, dom)
    if isinstance(name, list):
        for variable in var_objects:
            EVar(variable, None, None)  # object wrapping the variables
        return tuple(var_objects)
    else:
        EVarArray(var_objects, name, comment, tags)  # object wrapping the array of variables
        return ListVar(var_objects)


''' Posting constraints (through satisfy()) '''


def _bool_interpretation_for_in(left_operand, right_operand, bool_value):
    assert type(bool_value) is bool

    if isinstance(left_operand, Variable) and isinstance(right_operand, (tuple, list, set, frozenset, range)) and len(right_operand) == 0:
        return None
    if isinstance(left_operand, Variable) and isinstance(right_operand, range):
        ctr = Extension(scope=[left_operand], table=list(right_operand), positive=bool_value)
    elif isinstance(left_operand, (Variable, int, str)) and isinstance(right_operand, (set, frozenset, range)):
        # it is a unary constraint of the form x in/not in set/range
        ctr = Intension(Node.build(TypeNode.IN, left_operand, right_operand) if bool_value else Node.build(TypeNode.NOTIN, left_operand, right_operand))
    # elif isinstance(left_operand, Node) and isinstance(right_operand, range):
    #     if bool_value:
    #         ctr = Intension(conjunction(left_operand >= right_operand.start, left_operand <= right_operand.stop - 1))
    #     else:
    #         ctr = Intension(disjunction(left_operand < right_operand.start, left_operand > right_operand.stop - 1))
    elif isinstance(left_operand, PartialConstraint):  # it is a partial form of constraint (sum, count, maximum, ...)
        ctr = ECtr(left_operand.constraint.set_condition(TypeConditionOperator.IN if bool_value else TypeConditionOperator.NOTIN, right_operand))
    elif isinstance(right_operand, Automaton):  # it is a regular constraint
        ctr = Regular(scope=left_operand, automaton=right_operand)
    elif isinstance(right_operand, MDD):  # it is a MDD constraint
        ctr = Mdd(scope=left_operand, mdd=right_operand)
    elif isinstance(left_operand, int) and (is_1d_list(right_operand, Variable) or is_1d_tuple(right_operand, Variable)):
        ctr = Count(right_operand, value=left_operand, condition=(TypeConditionOperator.GE, 1))  # atLeast1 TODO to be replaced by a member/element constraint ?
    # elif isinstance(left_operand, Node):
    #
    else:  # It is a table constraint
        if not hasattr(left_operand, '__iter__'):
            left_operand = [left_operand]
        if not bool_value and len(right_operand) == 0:
            return None
        # TODO what to do if the table is empty and bool_value is true? an error message ?
        ctr = Extension(scope=flatten(left_operand), table=right_operand, positive=bool_value)  # TODO ok for using flatten? (before it was list())
    return ctr


def _complete_partial_forms_of_constraints(entities):
    for i, c in enumerate(entities):
        if isinstance(c, bool):
            assert len(curser.queue_in) > 0, "A boolean that does not represent a constraint is in the list of constraints in satisfy(): " + str(entities)
            right_operand, left_operand = curser.queue_in.popleft()
            entities[i] = _bool_interpretation_for_in(left_operand, right_operand, c)
        elif isinstance(c, ESlide):
            for ent in c.entities:
                _complete_partial_forms_of_constraints(ent.entities)
    return entities


def _wrap_intension_constraints(entities):
    for i, c in enumerate(entities):
        if isinstance(c, Node):
            entities[i] = Intension(c)  # the node is wrapped by a Constraint object (Intension)
    return entities


def And(*args):
    return EAnd(_wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(*args))))


def Or(*args):
    return EOr(_wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(*args))))


def Not(*args):
    return ENot(_wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(*args))))


def Xor(*args):
    return EXor(_wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(*args))))


def IfThen(*args):
    return EIfThen(_wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(*args))))


def IfThenElse(*args):
    return EIfThenElse(_wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(*args))))


def Iff(*args):
    return EIff(_wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(*args))))


def Slide(*args):
    entities = _wrap_intension_constraints(
        flatten(*args))  # we cannot directly complete partial forms (because it is executed before the analysis of the parameters of satisfy
    checkType(entities, [ECtr, bool])
    return ESlide([EToGather(entities)])


def satisfy(*args):
    global no_parameter_satisfy, nb_parameter_satisfy

    def _group(*_args):
        entities = _wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(*_args)))
        checkType(entities, [ECtr, ECtrs, EMetaCtr])
        return EToGather(entities)

    def _block(*_args):
        def _reorder(_entities):
            reordered_entities = []
            g = []
            for c in _entities:
                if isinstance(c, ECtr):
                    g.append(c)
                else:
                    if len(g) != 0:
                        reordered_entities.append(_group(g))
                    g.clear()
                    reordered_entities.append(c)
            if len(g) != 0:
                reordered_entities.append(_group(g))
            return reordered_entities

        entities = _wrap_intension_constraints(_complete_partial_forms_of_constraints(flatten(*_args)))
        checkType(entities, [ECtr, ECtrs])
        return EBlock(_reorder(entities))

    def _reorder(l):  # if constraints are given in (sub-)lists inside tuples; we flatten and reorder them to hopefully improve compactness
        d = dict()
        for tp in l:
            if isinstance(tp, tuple):
                for i, v in enumerate(tp):
                    d.setdefault(i, []).append(v)
            else:
                d.setdefault(0, []).append(tp)
        r = []
        for i in range(len(d)):
            r.extend(d[i])
        return r

    no_parameter_satisfy = 0
    nb_parameter_satisfy = len(args)
    comments1, comments2, tags1, tags2 = comments_and_tags_of_parameters_of(function_name="satisfy", args=args)

    t = []
    for i, arg in enumerate(args):
        if isinstance(arg, list) and len(arg) > 0:
            if isinstance(arg[0], tuple):
                arg = _reorder(arg)
            elif isinstance(arg[0], list):  # do not work if the constraints involve the operator 'in'
                for j, l in enumerate(arg):
                    if isinstance(l, list) and len(l) > 0 and isinstance(l[0], tuple):
                        arg[j] = _reorder(l)
        no_parameter_satisfy = i
        if isinstance(arg, (set,frozenset)):
            arg= list(arg)
        assert isinstance(arg, (ECtr, EMetaCtr, ESlide, Node, bool, list, tuple, type(None), types.GeneratorType)), \
            "non authorized type " + str(arg) + " " + str(type(arg))
        if arg is None:
            continue
        arg = list(arg) if isinstance(arg, types.GeneratorType) else arg
        comment_at_2 = any(comment != '' for comment in comments2[i])
        if isinstance(arg, (ECtr, EMetaCtr, ESlide)):  # case: simple constraint or slide
            to_post = _complete_partial_forms_of_constraints([arg])[0]
        elif isinstance(arg, Node):  # a predicate to be wrapped by a constraint (intension)
            to_post = Intension(arg)
        elif isinstance(arg, bool):  # a Boolean representing the case of a partial constraint or a node with operator in {IN, NOT IN}
            assert curser.queue_in, "An argument of satisfy() before position " + str(i) + " is badly formed"
            # assert queue_in, "A boolean that do not represents a constraint is in the list of constraints in satisfy(): " \
            #                 + str(args) + " " + str(i) + ".\nA constraint is certainly badly formed"
            other, partial = curser.queue_in.popleft()
            to_post = _bool_interpretation_for_in(partial, other, arg)
        elif any(isinstance(ele, ESlide) for ele in arg):  # Case: Slide
            to_post = _block(arg)
        elif comment_at_2:  # Case: block
            for j, ele in enumerate(arg):
                if isinstance(arg[j], (ECtr, ESlide)):
                    arg[j].note(comments2[i][j]).tag(tags2[i][j])
                elif comments2[i][j] or tags2[i][j]:
                    arg[j] = _group(arg[j]).note(comments2[i][j]).tag(tags2[i][j])
            to_post = _block(arg)
        else:  # Group
            to_post = _group(arg)
        if to_post:
            t.append(to_post.note(comments1[i]).tag(tags1[i]))
            # if isinstance(to_post, ESlide) and len(to_post.entities) == 1:
            #     to_post.entities[0].note(comments1[i]).tag(tags1[i])
    t.append(_group(pc == var for (pc, var) in auxiliary().collected()))
    return EToSatisfy(t)


''' Generic Constraints (intension, extension) '''


def Extension(*, scope, table, positive=True):
    scope = flatten(scope)
    checkType(scope, [Variable])
    assert isinstance(table, list)
    assert len(table) > 0, "A table must be a non-empty list of tuples or integers (or symbols)"
    checkType(positive, bool)

    if len(scope) == 1:
        assert all(isinstance(v, int) if isinstance(scope[0], VariableInteger) else isinstance(v, str) for v in table)
    else:  # if all(isinstance(x, VariableInteger) for x in scope):
        for i, t in enumerate(table):
            assert isinstance(t, tuple), str(t)
            assert len(t) == len(scope), ("The length of each tuple must be the same as the arity."
                                          + "Maybe a problem with slicing: you must for example write x#[i:i+3,0] instead of x[i:i+3][0]")
    return ECtr(ConstraintExtension(scope, table, positive, options.keepsmartconditions, options.restricttableswrtdomains))


def Intension(node):
    checkType(node, Node)
    ctr = ECtr(ConstraintIntension(node))
    if ctr.blank_basic_attributes():
        ctr.copy_basic_attributes_of(node)
    node.mark_as_used()
    return ctr


def abs(*args):
    if len(args) == 1 and isinstance(args[0], Node) and args[0].type == TypeNode.SUB:
        return Node.build(TypeNode.DIST, *args[0].sons)
    return Node.build(TypeNode.ABS, *args) if len(args) == 1 and isinstance(args[0], (Node, Variable)) else absPython(*args)


def min(*args):
    return Node.build(TypeNode.MIN, *args) if len(args) > 0 and any(isinstance(a, (Node, Variable)) for a in args) else minPython(*args)


def max(*args):
    return Node.build(TypeNode.MAX, *args) if len(args) > 0 and any(isinstance(a, (Node, Variable)) for a in args) else maxPython(*args)


def xor(*args):
    return args[0] ^ args[1] if len(args) == 2 else Node.build(TypeNode.XOR, *args) if len(args) > 1 else args[0]


def iff(*args):
    assert len(args) >= 2
    res = manage_global_indirection(*args)
    if res is None:
        return Iff(args)
    args = res
    return args[0] == args[1] if len(args) == 2 else Node.build(TypeNode.IFF, *args)


def imply(*args):
    assert len(args) == 2
    res = manage_global_indirection(*args)
    if res is None:
        return IfThen(args)
    return Node.build(TypeNode.IMP, *res)


def ift(*args):
    assert len(args) == 3
    res = manage_global_indirection(*args)
    if res is None:
        return IfThenElse(args)
    return Node.build(TypeNode.IF, *res)


def expr(operator, *args):
    return Node.build(operator, *args)


def conjunction(*args):
    return Node.conjunction(*args)


def disjunction(*args):
    return Node.disjunction(*args)


''' Language-based Constraints '''


def Regular(*, scope, automaton):
    scope = flatten(scope)
    checkType(scope, [Variable])
    checkType(automaton, Automaton)
    return ECtr(ConstraintRegular(scope, automaton))


def Mdd(*, scope, mdd):
    scope = flatten(scope)
    checkType(scope, [Variable])
    checkType(mdd, MDD)
    return ECtr(ConstraintMdd(scope, mdd))


''' Comparison-based Constraints '''


def AllDifferent(term, *others, excepting=None, matrix=None):
    terms = flatten(term, others)
    if len(terms) == 0 or (len(terms) == 1 and isinstance(terms[0], (int, Variable, Node))):
        return None
    if matrix is not None:
        assert excepting is None, "excepting values are currently not supported for AllDifferentMatrix"
        matrix = [flatten(row) for row in terms]
        assert all(len(row) == len(matrix[0]) for row in matrix), "The matrix id badly formed"
        assert all(checkType(l, [Variable]) for l in matrix)
        return ECtr(ConstraintAllDifferentMatrix(matrix))
    excepting = list(excepting) if isinstance(excepting, (tuple, set)) else [excepting] if isinstance(excepting, int) else excepting
    checkType(terms, ([Variable, Node]))
    checkType(excepting, ([int], type(None)))
    return ECtr(ConstraintAllDifferent(terms, excepting))


def AllDifferentList(term, *others, excepting=None):
    if isinstance(term, types.GeneratorType):
        term = [l for l in term]
    elif len(others) > 0:
        term = list((term,) + others)
    lists = [flatten(l) for l in term]
    assert all(checkType(l, [Variable]) for l in lists)
    excepting = list(excepting) if isinstance(excepting, (tuple, set)) else excepting
    checkType(excepting, ([int], type(None)))
    assert all(len(l) == len(lists[0]) for l in lists) and (excepting is None or len(excepting) == len(list[0]))
    return ECtr(ConstraintAllDifferentList(lists, excepting))


def AllEqual(term, *others):
    terms = flatten(term, others)
    checkType(terms, ([Variable], [Node]))
    return ECtr(ConstraintAllEqual(terms))


def _ordered(term, others, operator, lengths):
    terms = flatten(term, others)
    checkType(terms, [Variable])
    checkType(operator, TypeOrderedOperator)
    checkType(lengths, ([int, Variable], type(None)))
    if lengths is not None:
        if len(terms) == len(lengths):
            lengths = lengths[:-1]  # we assume that the last value is useless
        assert len(terms) == len(lengths) + 1
    return ECtr(ConstraintOrdered(terms, operator, lengths))


def Increasing(term, *others, strict=False, lengths=None):
    return _ordered(term, others, TypeOrderedOperator.INCREASING if not strict else TypeOrderedOperator.STRICTLY_INCREASING, lengths)


def Decreasing(term, *others, strict=False, lengths=None):
    return _ordered(term, others, TypeOrderedOperator.DECREASING if not strict else TypeOrderedOperator.STRICTLY_DECREASING, lengths)


def _lex(term, others, operator, matrix):
    if len(others) == 0:
        assert is_matrix(term, Variable)
        lists = [flatten(l) for l in term]
    else:
        assert is_1d_list(term, Variable) and all(is_1d_list(l, Variable) for l in others)
        lists = [flatten(term)] + [flatten(l) for l in others]
    assert is_matrix(lists, Variable)  # new check because some null cells (variables) may have been discarded
    assert all(len(l) == len(lists[0]) for l in lists)
    checkType(lists, [Variable])
    checkType(operator, TypeOrderedOperator)
    return ECtr(ConstraintLexMatrix(lists, operator)) if matrix else ECtr(ConstraintLex(lists, operator))


def LexIncreasing(term, *others, strict=False, matrix=False):
    return _lex(term, others, TypeOrderedOperator.INCREASING if not strict else TypeOrderedOperator.STRICTLY_INCREASING, matrix)


def LexDecreasing(term, *others, strict=False, matrix=False):
    return _lex(term, others, TypeOrderedOperator.DECREASING if not strict else TypeOrderedOperator.STRICTLY_DECREASING, matrix)


''' Method for handling complete/partial constraints '''


def _wrapping_by_complete_or_partial_constraint(ctr):
    condition = ctr.arguments[TypeCtrArg.CONDITION].content
    return ECtr(ctr) if condition is not None else PartialConstraint(ctr)


''' Counting and Summing Constraints '''


def Sum(term, *others, condition=None):
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
            checkType(coeffs, ([Variable, int], type(None)))
            OpOverrider.enable()
        return terms, coeffs

    terms = list(term) if isinstance(term, types.GeneratorType) else flatten(term, others)
    checkType(terms, ([Variable], [Node], [PartialConstraint], [ScalarProduct]))
    auxiliary().replace_nodes_and_partial_constraints(terms)

    terms, coeffs = _get_terms_coeffs(terms)
    terms, coeffs = _manage_coeffs(terms, coeffs)
    # if len(terms) == 1 and coeffs is None: return terms

    # TODO control here some assumptions (empty list seems to be possible. See RLFAP)
    return _wrapping_by_complete_or_partial_constraint(ConstraintSum(terms, coeffs, Condition.build_condition(condition)))


def Count(term, *others, value=None, values=None, condition=None):
    terms = flatten(term, others)
    assert len(terms) > 0, "A count with an empty scope"
    checkType(terms, ([Variable], [Node]))
    if value is None and values is None:
        value = 1
    assert value is None or values is None, str(value) + " " + str(values)
    values = list(values) if isinstance(values, (tuple, set)) else [value] if isinstance(value, (int, Variable)) else values
    checkType(values, ([int], [Variable]))
    return _wrapping_by_complete_or_partial_constraint(ConstraintCount(terms, values, Condition.build_condition(condition)))


def NValues(term, *others, excepting=None, condition=None):
    terms = flatten(term, others)
    checkType(terms, [Variable])
    if excepting is not None:
        excepting = flatten(excepting)
        checkType(excepting, [int])
    return _wrapping_by_complete_or_partial_constraint(ConstraintNValues(terms, excepting, Condition.build_condition(condition)))


# def NotAllEqual(term, *others):
#    return NValues(term, others) > 1


def Cardinality(term, *others, occurrences, closed=False):
    terms = flatten(term, others)
    checkType(terms, [Variable])
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


def _extremum(term, others, index, start_index, type_rank, condition, maximum):
    terms = list(term) if isinstance(term, types.GeneratorType) else flatten(term, others)
    terms = [Sum(t) if isinstance(t, ScalarProduct) else t for t in terms]  # to have PartialConstraints
    checkType(terms, ([Variable, Node], [PartialConstraint]))
    auxiliary().replace_nodes_and_partial_constraints(terms)
    checkType(index, (Variable, type(None)))
    checkType(start_index, int)
    checkType(type_rank, TypeRank)
    assert index is not None or (start_index == 0 and type_rank is TypeRank.ANY)
    return ConstraintMaximum(terms, index, start_index, type_rank, condition) if maximum else ConstraintMinimum(terms, index, start_index, type_rank, condition)


def Maximum(term, *others, index=None, start_index=0, type_rank=TypeRank.ANY, condition=None):
    return _wrapping_by_complete_or_partial_constraint(_extremum(term, others, index, start_index, type_rank, condition, True))


def Minimum(term, *others, index=None, start_index=0, type_rank=TypeRank.ANY, condition=None):
    return _wrapping_by_complete_or_partial_constraint(_extremum(term, others, index, start_index, type_rank, condition, False))


# def Element(*, vector, index=None, value, rank=TypeRank.ANY):
#    vector = flatten(vector)
#    checkType(vector, ([Variable], [int]))
#    checkType(index, (Variable, type(None)))
#    checkType(value, (Variable, int))
#    checkType(rank, TypeRank)
#    assert index is not None or rank is None, "rank is defined while index is not specified"
#    return ECtr(ConstraintElement(vector, value, index, rank if rank != TypeRank.ANY else None))


def Channel(list1, list2=None, *, start_index1=0, start_index2=0):
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


def NoOverlap(tasks=None, *, origins=None, lengths=None, zero_ignored=False):
    if tasks:
        assert origins is None and lengths is None
        tasks = list(tasks) if isinstance(tasks, (tuple, set, frozenset, types.GeneratorType)) else tasks
        assert isinstance(tasks, list) and len(tasks) > 0
        assert any(isinstance(task, (tuple, list)) and len(task) == 2 for task in tasks)
        origins, lengths = zip(*tasks)
    checkType(origins, [Variable])
    lengths = [lengths for _ in range(len(origins))] if isinstance(lengths, int) else lengths
    checkType(lengths, ([Variable], [int]))
    return ECtr(ConstraintNoOverlap(origins, lengths, zero_ignored))


def Cumulative(tasks=None, *, origins=None, lengths=None, ends=None, heights=None, condition=None):
    if tasks:
        assert origins is None and lengths is None and ends is None and heights is None
        tasks = list(tasks) if isinstance(tasks, (tuple, set, frozenset, types.GeneratorType)) else tasks
        assert isinstance(tasks, list) and len(tasks) > 0
        v = len(tasks[0])
        assert v in (3, 4) and any(isinstance(task, (tuple, list)) and len(task) == v for task in tasks)
        if v == 3:
            origins, lengths, heights = zip(*tasks)
        else:
            origins, lengths, ends, heights = zip(*tasks)
    origins = flatten(origins)
    checkType(origins, [Variable])
    lengths = flatten(lengths)
    checkType(lengths, ([Variable], [int]))
    heights = [heights for _ in range(len(origins))] if isinstance(heights, int) else flatten(heights)
    checkType(heights, ([Variable], [int]))
    ends = flatten(ends) if ends is not None else ends  # ends is optional
    checkType(ends, ([Variable], type(None)))
    return _wrapping_by_complete_or_partial_constraint(ConstraintCumulative(origins, lengths, ends, heights, Condition.build_condition(condition)))


def BinPacking(term, *others, sizes, condition=None):
    terms = flatten(term, others)
    assert len(terms) > 0, "A binPacking with an empty scope"
    checkType(terms, [Variable])
    sizes = flatten(sizes)
    checkType(sizes, [int])
    assert len(terms) == len(sizes)
    return _wrapping_by_complete_or_partial_constraint(ConstraintBinPacking(terms, sizes, Condition.build_condition(condition)))


''' Constraints on Graphs'''


def Circuit(term, *others, start_index=0, size=None):
    terms = flatten(term, others)
    checkType(terms, [Variable])
    checkType(start_index, int)
    checkType(size, (int, type(None)))
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
    if isinstance(term, PartialConstraint) and isinstance(term.constraint, (ConstraintSum, ConstraintMaximum, ConstraintMinimum)):
        l = term.constraint.arguments[TypeCtrArg.LIST]
        if len(l.content) == 1 and TypeCtrArg.COEFFS not in term.constraint.arguments:
            term = l.content[0]  # this was a sum/maximum/minimum with only one term, so we just consider this term as an expression to be optimized
    if isinstance(term, ScalarProduct):
        term = Sum(term)  # to have a PartialConstraint
    checkType(term, (Variable, Node, PartialConstraint)), "Did you forget to use Sum, e.g., as in Sum(x[i]*3 for i in range(10))"
    satisfy(pc == var for (pc, var) in auxiliary().collected())
    comment, _, tag, _ = comments_and_tags_of_parameters_of(function_name="minimize" if minimization else "maximize", args=[term])
    otype = TypeCtr.MINIMIZE if minimization else TypeCtr.MAXIMIZE
    if isinstance(term, (Variable, Node)):
        if isinstance(term, Node):
            term.mark_as_used()
        return EObjective(ObjectiveExpression(otype, term)).note(comment[0]).tag(tag[0])  # TODO why only one tag?
    else:
        return EObjective(ObjectivePartial(otype, term)).note(comment[0]).tag(tag[0])


def minimize(term):
    return _optimize(term, True)


def maximize(term):
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


def columns(m):
    return curser.columns(m)


def diagonal_down(m, i=-1, j=-1, check=True):
    if check is True:
        assert is_square_matrix(m), "The specified first parameter must be a square matrix."
    if i == -1 and j == -1:
        return diagonal_down(m, 0, 0, False)
    if j == -1:
        return ListVar(m[k][len(m) - (i - k) if k < i else k - i] for k in range(len(m)))
    return ListVar(m[i + k][j + k] for k in range(len(m) - max(i, j)))


def diagonals_down(m, *, broken=False):
    assert is_square_matrix(m), "The specified first parameter must be a square matrix."
    if broken:
        return ListVar(diagonal_down(m, i, -1, False) for i in range(len(m)))
    return ListVar(diagonal_down(m, i, 0, False) for i in reversed(range(len(m) - 1))) + ListVar(diagonal_down(m, 0, j, False) for j in range(1, len(m) - 1))


def diagonal_up(m, i=-1, j=-1, check=True):
    if check is True:
        assert is_square_matrix(m), "The specified first parameter must be a square matrix."
    if i == -1 and j == -1:
        return diagonal_up(m, len(m) - 1, 0, False)
    if j == -1:
        return ListVar(m[k][len(m) - i - k - 1 if k < len(m) - i else 2 * len(m) - i - k - 1] for k in range(len(m)))
    return ListVar(m[i - k][j + k] for k in range(min(i + 1, len(m) - j)))


def diagonals_up(m, *, broken=False):
    assert is_square_matrix(m), "The specified first parameter must be a square matrix."
    if broken:
        return ListVar(diagonal_up(m, i, -1, False) for i in range(len(m)))
    return ListVar(diagonal_up(m, i, 0, False) for i in range(1, len(m))) + ListVar(diagonal_up(m, len(m) - 1, j, False) for j in range(1, len(m) - 1))


def different_values(*args):
    assert all(isinstance(arg, int) for arg in args)
    return all(a != b for (a, b) in combinations(args, 2))


def cp_array(*l):
    if len(l) == 1:
        l = l[0]
    if isinstance(l, (tuple, set, types.GeneratorType)):
        l = list(l)
    assert isinstance(l, list) and len(l) > 0
    if isinstance(l[0], (list, types.GeneratorType)):
        assert all(isinstance(t, (list, types.GeneratorType)) for t in l)
        res = [cp_array(t) for t in l]
        return ListInt(res) if isinstance(res[0], ListInt) else ListVar(res)
    if all(isinstance(v, int) for v in l):
        return ListInt(l)
    elif all(isinstance(v, Variable) for v in l):
        return ListVar(l)
    else:
        raise NotImplemented


def _pycharm_security():  # for avoiding that imports are removed when reformatting code
    _ = (permutations, transpose, alphabet_positions, all_primes, integer_scaling, namedtuple, default_data, lt, le, ge, gt, ne, complement)
