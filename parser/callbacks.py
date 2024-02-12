from pycsp3.classes.auxiliary.conditions import Condition
from pycsp3.classes.auxiliary.enums import (TypeConditionOperator, TypeArithmeticOperator, TypeUnaryArithmeticOperator, TypeLogicalOperator,
                                            TypeOrderedOperator, TypeRank, TypeObj)
from pycsp3.classes.main.variables import Variable
from pycsp3.classes.nodes import (Node)


class Callbacks:

    def __init__(self):
        self.print_general_methods = True
        self.print_specific_methods = True
        self.force_exit = False

        self.recognize_unary_primitives = True
        self.recognize_binary_primitives = True
        self.recognize_ternary_primitives = True
        self.recognize_logic_intension = True
        self.recognize_sum_intension = True
        self.recognize_extremum_intension = True
        self.recognize_specific_count_cases = True
        self.recognize_specific_nvalues_cases = True

    def _unimplemented(self, *args, general_method=False):
        if (general_method and self.print_general_methods) or (not general_method and self.print_specific_methods):
            import inspect

            print("  " + inspect.currentframe().f_back.f_code.co_name)
            for arg in args:
                if arg is not None:
                    print("\t", str(arg))
        if not general_method and self.force_exit:
            print("  EXIT because not implemented method:")
            exit(1)

    # # # # # # # # # #
    # Methods called at Specific Moments (not necessarily useful)
    # # # # # # # # # #

    def load_instance(self, discarded_classes=None):
        self._unimplemented(discarded_classes, general_method=True)

    def begin_instance(self, type_framework):
        self._unimplemented(type_framework, general_method=True)

    def load_variables(self, entries):
        self._unimplemented(entries, general_method=True)

    def load_var_array(self, va):
        self._unimplemented(va, general_method=True)

    def load_var(self, v):
        pass  # not sure that overriding this method it can be useful

    def load_constraints(self, entries):
        self._unimplemented(entries, general_method=True)

    def load_block(self, block):
        self._unimplemented(block, general_method=True)

    def load_group(self, group):
        self._unimplemented(group, general_method=True)

    def load_slide(self, slide):
        self._unimplemented(slide, general_method=True)

    def load_templated_constraints(self, template, all_args):
        self._unimplemented(template, all_args, general_method=True)

    def load_ctr(self, c):
        pass  # not sure that overriding this method can be useful

    def load_objectives(self, objectives):
        self._unimplemented(objectives, general_method=True)

    def load_objective(self, objective):
        self._unimplemented(objective, general_method=True)

    def load_annotations(self, annotations):
        self._unimplemented(annotations, general_method=True)

    def load_annotation(self, annotation):
        self._unimplemented(annotation, general_method=True)

    def end_instance(self):
        self._unimplemented(general_method=True)

    # # # # # # # # # #
    # All methods about variables to be implemented
    # # # # # # # # # #

    def var_integer_range(self, x: Variable, min_value: int, max_value: int):
        self._unimplemented(x.id, min_value, max_value)

    def var_integer(self, x: Variable, values: list[int]):
        self._unimplemented(x.id, values)

    def var_symbolic(self, x: Variable, values: list[str]):
        self._unimplemented(x.id, values)

        # # # # # # # # # #

    # All methods about constraints to be implemented
    # # # # # # # # # #

    def ctr_true(self, scope: list[Variable]):
        print("Warning: ctr true", str(scope))

    def ctr_false(self, scope: list[Variable]):
        assert False, "Problem as a constraint with 0 supports: " + str(scope)

    def ctr_intension(self, scope: list[Variable], tree: Node):
        self._unimplemented(scope, tree)

    def ctr_primitive1a(self, x: Variable, op: TypeConditionOperator, k: int):
        assert op.is_rel()
        self._unimplemented(x, op, k)

    def ctr_primitive1b(self, x: Variable, op: TypeConditionOperator, term: list[int] | range):
        assert op.is_set()
        self._unimplemented(x, op, term)

    def ctr_primitive1c(self, x: Variable, aop: TypeArithmeticOperator, p: int, op: TypeConditionOperator, k: int):
        assert op.is_rel()
        self._unimplemented(x, aop, p, op, k)

    def ctr_primitive2a(self, x: Variable, aop: TypeUnaryArithmeticOperator, y: Variable):
        self._unimplemented(x, aop, y)

    def ctr_primitive2b(self, x: Variable, aop: TypeArithmeticOperator, y: Variable, op: TypeConditionOperator, k: int):
        assert op.is_rel()
        self._unimplemented(x, aop, y, op, k)

    def ctr_primitive2c(self, x: Variable, aop: TypeArithmeticOperator, p: int, op: TypeConditionOperator, y: Variable):
        assert op.is_rel()
        self._unimplemented(x, aop, p, op, y)

    def ctr_primitive3(self, x: Variable, aop: TypeArithmeticOperator, y: Variable, op: TypeConditionOperator, z: Variable):
        assert op.is_rel()
        self._unimplemented(x, aop, y, op, z)

    def ctr_logic(self, lop: TypeLogicalOperator, scope: list[Variable]):  # lop(scope)
        self._unimplemented(lop, scope)

    def ctr_logic_reif(self, x: Variable, y: Variable, op: TypeConditionOperator, k: int | Variable):  # x = y <op> k
        assert op.is_rel()
        self._unimplemented(x, y, op, k)

    def ctr_logic_eqne(self, x: Variable, op: TypeConditionOperator, lop: TypeLogicalOperator, scope: list[Variable]):  # x = lop(scope) or x != lop(scope)
        assert op in (TypeConditionOperator.EQ, TypeConditionOperator.NE)
        self._unimplemented(x, op, lop, scope)

    def ctr_extension_unary(self, x: Variable, values: list[int], positive: bool, flags: set[str]):
        self._unimplemented(x, values, positive, flags)

    def ctr_extension(self, scope: list[Variable], tuples: list, positive: bool, flags: set[str]):
        self._unimplemented(scope, tuples, positive, flags)

    def ctr_regular(self, scope: list[Variable], transitions: list, start_state: str, final_states: list[str]):
        self._unimplemented(scope, transitions, start_state, final_states)

    def ctr_mdd(self, scope: list[Variable], transitions: list):
        self._unimplemented(scope, transitions)

    def ctr_all_different(self, scope: list[Variable] | list[Node], excepting: None | list[int]):
        self._unimplemented(scope, excepting)

    def ctr_all_different_lists(self, lists: list[list[Variable]], excepting: None | list[list[int]]):
        self._unimplemented(lists, excepting)

    def ctr_all_different_matrix(self, matrix: list[list[Variable]], excepting: None | list[int]):
        self._unimplemented(matrix, excepting)

    def ctr_all_equal(self, scope: list[Variable] | list[Node], excepting: None | list[int]):
        self._unimplemented(scope, excepting)

    def ctr_ordered(self, lst: list[Variable], operator: TypeOrderedOperator, lengths: None | list[int] | list[Variable]):
        self._unimplemented(lst, operator, lengths)

    def ctr_lex_limit(self, lst: list[Variable], limit: list[int], operator: TypeOrderedOperator):  # should soon enter XCSP3-core
        self._unimplemented(lst, limit, operator)

    def ctr_lex(self, lists: list[list[Variable]], operator: TypeOrderedOperator):
        self._unimplemented(lists, operator)

    def ctr_lex_matrix(self, matrix: list[list[Variable]], operator: TypeOrderedOperator):
        self._unimplemented(matrix, operator)

    def ctr_precedence(self, lst: list[Variable], values: None | list[int], covered: bool):
        self._unimplemented(lst, values, covered)

    def ctr_sum(self, lst: list[Variable] | list[Node], coefficients: None | list[int] | list[Variable], condition: Condition):
        self._unimplemented(lst, coefficients, condition)

    def ctr_count(self, lst: list[Variable] | list[Node], values: list[int] | list[Variable], condition: Condition):
        self._unimplemented(lst, values, condition)

    def ctr_atleast(self, lst: list[Variable], value: int, k: int):
        self._unimplemented(lst, value, k)

    def ctr_atmost(self, lst: list[Variable], value: int, k: int):
        self._unimplemented(lst, value, k)

    def ctr_exactly(self, lst: list[Variable], value: int, k: int | Variable):
        self._unimplemented(lst, value, k)

    def ctr_among(self, lst: list[Variable], values: list[int], k: int | Variable):
        self._unimplemented(lst, values, k)

    def ctr_nvalues(self, lst: list[Variable] | list[Node], excepting: None | list[int], condition: Condition):
        self._unimplemented(lst, excepting, condition)

    def ctr_not_all_qual(self, lst: list[Variable]):
        self._unimplemented(lst)

    def ctr_cardinality(self, lst: list[Variable], values: list[int] | list[Variable], occurs: list[int] | list[Variable] | list[range], closed: bool):
        self._unimplemented(lst, values, occurs, closed)

    def ctr_minimum(self, lst: list[Variable] | list[Node], condition: Condition):
        self._unimplemented(lst, condition)

    def ctr_maximum(self, lst: list[Variable] | list[Node], condition: Condition):
        self._unimplemented(lst, condition)

    def ctr_minimum_arg(self, lst: list[Variable] | list[Node], condition: Condition, rank: TypeRank):  # should enter XCSP3-core
        self._unimplemented(lst, condition, rank)

    def ctr_maximum_arg(self, lst: list[Variable] | list[Node], condition: Condition, rank: TypeRank):  # should enter XCSP3-core
        self._unimplemented(lst, condition, rank)

    def ctr_element(self, lst: list[Variable] | list[int], i: Variable, condition: Condition):
        self._unimplemented(lst, i, condition)

    def ctr_element_matrix(self, matrix: list[list[Variable]] | list[list[int]], i: Variable, j: Variable, condition: Condition):
        self._unimplemented(matrix, i, j, condition)

    def ctr_channel(self, lst1: list[Variable], lst2: None | list[Variable]):
        self._unimplemented(lst1, lst2)

    def ctr_channel_value(self, lst: list[Variable], value: Variable):
        self._unimplemented(lst, value)

    def ctr_nooverlap(self, origins: list[Variable], lengths: list[int] | list[Variable],
                      zero_ignored: bool):  # in XCSP3 competitions, no 0 permitted in lengths
        self._unimplemented(origins, lengths, zero_ignored)

    def ctr_nooverlap_multi(self, origins: list[list[Variable]], lengths: list[list[int]] | list[list[Variable]], zero_ignored: bool):
        self._unimplemented(origins, lengths, zero_ignored)

    def ctr_nooverlap_mixed(self, xs: list[Variable], ys: list[Variable], lx: list[Variable], ly: list[int], zero_ignored: bool):
        self._unimplemented(xs, ys, lx, ly, zero_ignored)

    def ctr_cumulative(self, origins: list[Variable], lengths: list[int] | list[Variable], heights: list[int] | list[Variable], condition: Condition):
        self._unimplemented(origins, lengths, heights, condition)

    def ctr_binpacking(self, lst: list[Variable], sizes: list[int], condition: Condition):
        self._unimplemented(lst, sizes, condition)

    def ctr_binpacking_limits(self, lst: list[Variable], sizes: list[int], limits: list[int] | list[Variable]):
        self._unimplemented(lst, sizes, limits)

    def ctr_binpacking_loads(self, lst: list[Variable], sizes: list[int], loads: list[int] | list[Variable]):
        self._unimplemented(lst, sizes, loads)

    def ctr_binpacking_conditions(self, lst: list[Variable], sizes: list[int], conditions: list[Condition]):  # not in XCSP3-core
        self._unimplemented(lst, sizes, conditions)

    def ctr_knapsack(self, lst: list[Variable], weights: list[int], wcondition: Condition, profits: list[int], pcondition: Condition):
        self._unimplemented(lst, weights, wcondition, profits, pcondition)

    def ctr_flow(self, lst: list[Variable], balance: list[int] | list[Variable], arcs: list, capacities: None | list[range]):  # not in XCSP3-core
        self._unimplemented(lst, balance, arcs, capacities)

    def ctr_flow_weighted(self, lst: list[Variable], balance: list[int] | list[Variable], arcs: list, capacities: None | list[range],
                          weights: list[int] | list[Variable],
                          condition: Condition):  # not in XCSP3-core
        self._unimplemented(lst, balance, arcs, capacities, weights, condition)

    def ctr_instantiation(self, lst: list[Variable], values: list[int]):
        self._unimplemented(lst, values)

    def ctr_clause(self, pos: list[Variable], neg: list[Variable]):  # not in XCSP3-core
        self._unimplemented(pos, neg)

    def ctr_circuit(self, lst: list[Variable], size: None | int | Variable):  # size is None in XCSP3 competitions
        self._unimplemented(lst, size)

    # # # # # # # # # #
    # All methods about objectives to be implemented
    # # # # # # # # # #

    def obj_minimize(self, term: Variable | Node):
        self._unimplemented(term)

    def obj_maximize(self, term: Variable | Node):
        self._unimplemented(term)

    def obj_minimize_special(self, obj_type: TypeObj, terms: list[Variable] | list[Node], coefficients: None | list[int]):
        self._unimplemented(obj_type, terms, coefficients)

    def obj_maximize_special(self, obj_type: TypeObj, terms: list[Variable] | list[Node], coefficients: None | list[int]):
        self._unimplemented(obj_type, terms, coefficients)

    # # # # # # # # # #
    # All methods about annotations to be implemented
    # # # # # # # # # #

    def ann_decision(self, lst: list[Variable]):
        self._unimplemented(lst)

    def ann_val_heuristic_static(self, lst: list[Variable], order: list[int]):
        self._unimplemented(lst, order)
