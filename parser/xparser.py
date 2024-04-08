import os
import re
import sys
from xml.etree import ElementTree

from pycsp3.classes.auxiliary.conditions import Condition, ConditionValue, ConditionVariable
from pycsp3.classes.auxiliary.enums import (TypeFramework, TypeVar, TypeCtr, TypeCtrArg, TypeAnn, TypeConditionOperator, TypeArithmeticOperator,
                                            TypeUnaryArithmeticOperator, TypeOrderedOperator, TypeRank, TypeObj)
from pycsp3.classes.main.variables import Variable
from pycsp3.classes.nodes import (TypeNode, Node, x_relop_k, k_relop_x, x_ariop_k__relop_l, l_relop__x_ariop_k, x_setop_S, x_in_intvl, x_notin_intvl, min_relop,
                                  max_relop, x_ariop_y__relop_z, z_relop__x_ariop_y, logic_X, logic_X__eq_x, logic_X__ne_x, logic_y_relop_z__eq_x, x_relop_y,
                                  x_ariop_y__relop_k, add_mul_vars__relop, add_vars__relop, k_relop__x_ariop_y, x_relop__y_ariop_k, y_ariop_k__relop_x,
                                  logic_y_relop_k__eq_x, logic_k_relop_y__eq_x, unalop_x__eq_y, add_mul_vals__relop)
from pycsp3.parser.callbacks import Callbacks
from pycsp3.parser.constants import (COVERED, CLOSED, RANK, START_INDEX, START_ROW_INDEX, START_COL_INDEX, ZERO_IGNORED, STATIC,
                                     DELIMITER_LISTS, DELIMITER_COMMA, DELIMITER_WHITESPACE, ID, CLASS, VAR, ARRAY, DOMAIN, SIZE, AS, FOR, TYPE, GROUP, BLOCK,
                                     INTENSION, MATRIX, INDEX, OFFSET, COLLECT, CIRCULAR, STARRED, UNCLEANED, MINIMIZE, ORDER)
from pycsp3.parser.methods import (parse_domain, parse_expression, parse_sequence, parse_double_sequence, parse_double_sequence_of_vars, parse_condition,
                                   parse_conditions, parse_data, parse_tuples, replace_intern_commas)
from pycsp3.parser.xentries import XCtr, XBlock, XGroup, XSlide, XObjExpr, XVar, XVarArray, domains_for, XCtrArg, XObjSpecial, XAnn
from pycsp3.tools.curser import OpOverrider
from pycsp3.tools.utilities import flatten

OpOverrider.disable()  # because activated due to the imports (and this causes problem with XVar inheriting from Variable)


class ParserXCSP3:

    def must_discard_element(self, elt):
        return CLASS in elt.attrib and len(set(re.split(DELIMITER_WHITESPACE, elt.attrib[CLASS])).intersection(self.discarded_classes)) > 0

    def parse_variables(self, elements):
        def actual_element(elt):
            return elt if AS not in elt.attrib else self.tree.find(".//*[@id='" + elt.attrib[AS] + "']")

        cache_id_to_domain = {}  # a map for managing pairs(id, domain); remember that aliases can be encountered
        for elt in elements:
            id = elt.attrib[ID]
            tp = None if TYPE not in elt.attrib else elt.attrib[TYPE]
            tp = TypeVar.INTEGER if tp is None else TypeVar[tp.upper()]
            actual_elt = actual_element(elt)  # managing aliases, i.e., 'as' indirection
            assert actual_elt is not None
            dom = cache_id_to_domain.get(actual_elt.attrib[ID], None)  # may be not None when 'as' indirection
            if elt.tag == VAR:
                if dom is None:
                    dom = parse_domain(actual_elt.text.strip(), tp)
                    cache_id_to_domain[id] = dom
                entry = XVar(id, tp, dom)
            else:
                assert elt.tag == ARRAY
                sizes = [int(v[1:-1]) for v in re.findall("\[[0-9]*\]", elt.attrib[SIZE])]
                if dom is None:  # meaning no 'as' indirection
                    domains = elt.findall(DOMAIN)
                    if len(domains) > 0:
                        va = XVarArray(id, tp, sizes)
                        for child in domains:
                            actual_child = actual_element(child)
                            dom_child = None if ID not in actual_child.attrib else cache_id_to_domain.get(actual_child.attrib[ID], None)
                            if dom_child is None:
                                dom_child = parse_domain(actual_child.text.strip(), tp)
                                if ID in child.attrib:
                                    cache_id_to_domain[child.attrib[ID]] = dom_child
                            va.set_dom(child.attrib[FOR].strip(), dom_child)
                        entry = va
                    else:
                        dom = parse_domain(actual_elt.text.strip(), tp)
                        cache_id_to_domain[id] = dom
                        entry = XVarArray(id, tp, sizes, dom)
                else:
                    entry = XVarArray(id, tp, sizes, dom)

            if not self.must_discard_element(elt):
                self.vEntries.append(entry)

        for entry in self.vEntries:
            if isinstance(entry, XVar):
                self.map_for_vars[entry.id] = entry
            else:
                for x in entry.variables:
                    if x is not None:
                        self.map_for_vars[x.id] = x
                self.map_for_arrays[entry.id] = entry

    def parse_ctr_arguments(self, elt):
        if len(elt) == 0:
            tc = TypeCtrArg.FUNCTION if elt.tag == INTENSION else TypeCtrArg.LIST
            return [XCtrArg(tc, self.parsing(tc, elt))]
        else:
            return [XCtrArg(tc, self.parsing(tc, e)) for e in elt if (tc := TypeCtrArg[e.tag.upper()],)]

    def parsing(self, tc, elt, args=None):
        if tc == TypeCtrArg.FUNCTION:
            return parse_expression(self, elt.text.strip())
        if tc == TypeCtrArg.LIST:
            return parse_sequence(self, elt)
        if tc == TypeCtrArg.MATRIX:
            if elt.text.strip()[0] == "(":
                return parse_double_sequence(self, elt)
            return parse_double_sequence_of_vars(self, elt)
        if tc in (TypeCtrArg.ROW_OCCURS, TypeCtrArg.COL_OCCURS):
            return parse_double_sequence_of_vars(self, elt)
        if tc == TypeCtrArg.CONDITION:
            return parse_condition(self, elt)
        # if tc in (TypeCtrArg.SUPPORTS, TypeCtrArg.CONFLICTS):
        #     assert len(self.leafs) == 1 and self.leafs[0].type == TypeCtrArg.LIST
        #     variables = self.leafs[0].value if all(isinstance(v, XVar) for v in self.leafs[0].value) else None  # may be null if a constraint template
        #     domains = domains_for(args) if args is not None else domains_for(variables) if variables is not None else None
        #     tuples, starred, cleaned = parse_tuples(elt[1], domains is not None and isinstance(domains[0][0], str))
        #     ctr_arg = self.add_leaf(tc, tuples)
        #     if starred:
        #         ctr_arg.flags.add(STARRED)
        #     if not cleaned:
        #         ctr_arg.flags.add(UNCLEANED)
        if tc == TypeCtrArg.CONDITIONS:
            return parse_conditions(self, elt)
        if tc == TypeCtrArg.OPERATOR:
            return TypeOrderedOperator.value_of(elt.text.strip())
        if tc in (TypeCtrArg.INDEX, TypeCtrArg.VALUE, TypeCtrArg.SIZE, TypeCtrArg.TOTAL, TypeCtrArg.IMAGE, TypeCtrArg.ROOT, TypeCtrArg.GRAPH):
            return parse_data(self, elt)
        if tc == TypeCtrArg.EXCEPT:
            return parse_double_sequence(self, elt, DELIMITER_LISTS) if elt.text.strip()[0] == "(" else parse_sequence(self, elt)
        if tc in (TypeCtrArg.ARCS, TypeCtrArg.PATTERNS):
            return parse_double_sequence(self, elt, DELIMITER_LISTS)
        if tc == TypeCtrArg.START:
            return elt.text.strip()
        if tc == TypeCtrArg.FINAL:
            return re.split(DELIMITER_WHITESPACE, elt.text.strip())
        if tc == TypeCtrArg.TRANSITIONS:  # TODO to be extended as val can be more complex than a simple int
            return [(src, int(val), tgt) for (src, val, tgt) in
                    [re.split(DELIMITER_COMMA, replace_intern_commas(s)) for s in re.split(DELIMITER_LISTS, elt.text.strip())[1:-1]]]
        # below, this is for cases: coeffs values occurs mapping widths sizes limits loads weights heights profits balance origins lengths ends machines
        return parse_sequence(self, elt)

    def parsing_of_constraints_inner(self, elt, args):
        if elt.tag == GROUP:
            all_args = [parse_sequence(self, elt[i]) for i in range(1, len(elt))]  # from 1 because template at 0
            return XGroup(self.parsing_of_constraints_outer(elt[0], all_args), all_args)
        tc = TypeCtr.value_of(elt.tag.upper())

        if tc == TypeCtr.SLIDE:
            lists = [XCtrArg(TypeCtrArg.LIST, parse_sequence(self, e)) for e in elt[:-1]]
            offsets = [e.attrib.get(OFFSET, 1) for e in elt[:-1]]
            collects = [e.attrib.get(COLLECT, 1) for e in elt[:-1]]
            if len(lists) == 1:
                ctr = self.parsing_of_constraints_outer(elt[-1], None)
                assert len(ctr.abstraction.abstract_ctr_args) == 1, "Other cases must be implemented"
                if ctr.type == TypeCtr.INTENSION:
                    collects[0] = ctr.ctr_args[0].value.max_parameter_number() + 1
                else:
                    pars = ctr.abstraction.abstract_ctr_args[0].value
                    assert len(pars) > 0 and all(p.number != -1 for p in pars), "One parameter is %..., which is forbidden in slide"
                    collects[0] = max(p.number for p in pars) + 1
            scopes = XSlide.build_scopes([t.value for t in lists], offsets, collects, CIRCULAR in elt.attrib and elt.attrib[CIRCULAR] == "true")
            return XSlide(lists, offsets, collects, self.parsing_of_constraints_outer(elt[-1], scopes), scopes)

        assert tc != TypeCtr.SEQBIN  # for the moment

        leafs = []

        if tc is TypeCtr.EXTENSION:
            hybrid = TYPE in elt.attrib and elt.attrib[TYPE] in ("hybrid-1", "hybrid-2")
            leafs.append(XCtrArg(TypeCtrArg.LIST, self.parsing(TypeCtrArg.LIST, elt[0])))
            type_tuples = TypeCtrArg[elt[1].tag.upper()]
            if not hybrid:
                assert len(leafs) == 1 and leafs[0].type == TypeCtrArg.LIST
                variables = leafs[0].value if all(isinstance(v, XVar) for v in leafs[0].value) else None  # may be null if a constraint template
                domains = domains_for(args) if args is not None else domains_for(variables) if variables is not None else None
                tuples, starred, cleaned = parse_tuples(elt[1], domains is not None and isinstance(domains[0][0], str))
                leafs.append(XCtrArg(type_tuples, tuples))
                if starred:
                    leafs[-1].flags.add(STARRED)
                if not cleaned:
                    leafs[-1].flags.add(UNCLEANED)
            else:
                assert False, "For the moment, hybrid tuples are not handled"

        elif tc is TypeCtr.ELEMENT and elt[0].tag == MATRIX and elt[1].tag == INDEX:
            leafs.append(XCtrArg(TypeCtrArg.MATRIX, self.parsing(TypeCtrArg.MATRIX, elt[0])))
            leafs.append(XCtrArg(TypeCtrArg.INDEX, parse_sequence(self, elt[1])))  # not default case for index
            leafs.extend(self.parse_ctr_arguments(elt[2:]))

        elif tc is TypeCtr.NO_OVERLAP:
            multi_dimensional = elt[1].text.strip()[0] == '('
            leafs.append(XCtrArg(TypeCtrArg.ORIGINS, parse_double_sequence_of_vars(self, elt[0]) if multi_dimensional else parse_sequence(self, elt[0])))
            leafs.append(
                XCtrArg(TypeCtrArg.LENGTHS, parse_double_sequence(self, elt[1], DELIMITER_LISTS) if multi_dimensional else parse_sequence(self, elt[1])))

        else:
            if tc is TypeCtr.EXTENSION:
                hybrid = TYPE in elt.attrib and elt.attrib[TYPE] in ("hybrid-1", "hybrid-2")
                assert not hybrid, "for the moment"
            leafs.extend(self.parse_ctr_arguments(elt))

        return XCtr(tc, leafs)

    # called to parse any constraint entry in <constraints> , that can be a group, a constraint, or a meta-constraint. This method calls parseCEntry.
    def parsing_of_constraints_outer(self, elt, args):
        entry = self.parsing_of_constraints_inner(elt, args)
        entry.copy_attributes_of(elt)
        if isinstance(entry, XCtr):
            if entry.type != TypeCtr.ADHOC:
                for i, e in enumerate(elt):
                    entry.ctr_args[i].copy_attributes_of(e)  # we copy the attributes for each parameter of the constraint
        elif isinstance(entry, XSlide):
            for i, e in enumerate(elt[:-1]):
                entry.lists[i].copy_attributes_of(e)
        return entry

    #  Recursive parsing, traversing possibly multiple blocks
    def recursive_parsing_of_constraints(self, elt, t):
        if self.must_discard_element(elt):
            return
        if elt.tag == BLOCK:
            block_entries = []
            for e in elt:
                self.recursive_parsing_of_constraints(e, block_entries)
            block = XBlock(block_entries)
            block.copy_attributes_of(elt)
            t.append(block)
        else:
            t.append(self.parsing_of_constraints_outer(elt, None))

    def parse_constraints(self, elements):
        for elt in elements:
            self.recursive_parsing_of_constraints(elt, self.cEntries)

    def parse_objectives(self, elements):
        assert len(elements) <= 1, "For the moment, only mono-objective handled"
        for elt in elements:
            minimize = elt.tag == MINIMIZE
            obj_type = TypeObj.EXPRESSION if TYPE not in elt.attrib else TypeObj[elt.attrib[TYPE].upper()]
            if obj_type == TypeObj.EXPRESSION:
                entry = XObjExpr(minimize, parse_expression(self, elt.text.strip()))
            else:
                terms = parse_sequence(self, elt if len(elt) == 0 else elt[0])
                coefficients = None if len(elt) == 0 else parse_sequence(self, elt[1])
                entry = XObjSpecial(minimize, obj_type, terms, coefficients)
            self.oEntries.append(entry)

    def parse_annotations(self, elements):
        for elt in elements:
            ta = TypeAnn.value_of(elt.tag.upper())
            if ta == TypeAnn.DECISION:
                entry = XAnn(ta, parse_sequence(self, elt))
            elif ta == TypeAnn.VAL_HEURISTIC:
                # for the moment, only static ordering
                d = {STATIC: [(parse_sequence(self, son), parse_sequence(self, son.attrib[ORDER])) for son in elt if son.tag == STATIC]}
                entry = XAnn(ta, d)
            self.aEntries.append(entry)

    def compute_var_degrees(self):

        def update_degrees_wrt(t):  # NB: it is not possible to directly call collect_vars()
            for e in t:
                if isinstance(e, XBlock):
                    update_degrees_wrt(e.subentries)
                elif isinstance(e, XGroup):
                    for i in range(len(e.all_args)):
                        for x in e.get_scope(i):
                            x.increment_degree()
                else:
                    assert isinstance(e, (XCtr, XSlide))
                    for x in e.involved_vars():
                        x.increment_degree()

        update_degrees_wrt(self.cEntries)
        for entry in self.oEntries:
            for x in entry.involved_vars():
                x.increment_degree()

    def __init__(self, filename, discarded_classes=None):
        self.map_for_vars = {}  # The map that stores pairs (id, variable).
        self.map_for_arrays = {}  # The map that stores pairs (id, array of variables).

        self.vEntries = []
        self.cEntries = []
        self.oEntries = []
        self.aEntries = []

        self.tree = ElementTree.parse(filename)
        self.discarded_classes = set() if discarded_classes is None else set(discarded_classes)

        self.parse_variables(self.tree.findall("./variables/"))
        self.parse_constraints(self.tree.findall("./constraints/"))
        self.parse_objectives(self.tree.findall("./objectives/"))
        self.parse_annotations(self.tree.findall("./annotations/"))

        self.compute_var_degrees()


class Recognizer:
    def __init__(self, callbacks):
        self.cb = callbacks

        def basic_condition(r: Node):
            assert r.type.is_relational_operator() and r.arity == 2 and r[1].type in (TypeNode.VAR, TypeNode.INT)
            return Condition.build_condition((r.relop(0), r[1].cnt))

        self.unary_rules = {
            x_relop_k: lambda r: callbacks.ctr_primitive1a(r.var(0), r.relop(0), r.val(0)),
            k_relop_x: lambda r: callbacks.ctr_primitive1a(r.var(0), r.relop(0).arithmetic_inversion(), r.val(0)),
            x_ariop_k__relop_l: lambda r: callbacks.ctr_primitive1c(r.var(0), r.ariop(0), r.val(0), r.relop(0), r.val(1)),
            l_relop__x_ariop_k: lambda r: callbacks.ctr_primitive1c(r.var(0), r.ariop(0), r.val(1), r.relop(0).arithmetic_inversion(), r.val(0)),
            x_setop_S: lambda r: callbacks.ctr_primitive1b(r.var(0), TypeConditionOperator[str(r.type).upper()], r.list_of_ints()),
            x_in_intvl: lambda r: callbacks.ctr_primitive1b(r.var(0), TypeConditionOperator.IN, range(r.val(1), r.val(0) + 1)),
            x_notin_intvl: lambda r: callbacks.ctr_primitive1b(r.var(0), TypeConditionOperator.NOTIN, range(r.val(0) + 1, r.val(1)))
        }

        self.binary_rules = {
            x_relop_y: lambda r: callbacks.ctr_primitive2b(r.var(0), TypeArithmeticOperator.SUB, r.var(1), r.relop(0), 0),
            x_ariop_y__relop_k: lambda r: callbacks.ctr_primitive2b(r.var(0), r.ariop(0), r.var(1), r.relop(0), r.val(0)),
            k_relop__x_ariop_y: lambda r: callbacks.ctr_primitive2b(r.var(0), r.ariop(0), r.var(1), r.relop(0).arithmetic_inversion(), r.val(0)),
            x_relop__y_ariop_k: lambda r: callbacks.ctr_primitive2c(r.var(1), r.ariop(0), r.val(0), r.relop(0).arithmetic_inversion(), r.var(0)),
            y_ariop_k__relop_x: lambda r: callbacks.ctr_primitive2c(r.var(0), r.ariop(0), r.val(0), r.relop(0), r.var(1)),
            logic_y_relop_k__eq_x: lambda r: callbacks.ctr_logic_reif(r.var(1), r.var(0), r.relop(1), r.val(0)),
            logic_k_relop_y__eq_x: lambda r: callbacks.ctr_logic_reif(r.var(1), r.var(0), r.relop(1).arithmetic_inversion(), r.val(0)),
            unalop_x__eq_y: lambda r: callbacks.ctr_primitive2a(r.var(1), TypeUnaryArithmeticOperator[str(r[0].type).upper()], r.var(0))
        }

        self.ternary_rules = {
            x_ariop_y__relop_z: lambda r: callbacks.ctr_primitive3(r.var(0), r.ariop(0), r.var(1), r.relop(0), r.var(2)),
            z_relop__x_ariop_y: lambda r: callbacks.ctr_primitive3(r.var(1), r.ariop(0), r.var(2), r.relop(0).arithmetic_inversion(), r.var(0))
        }

        self.logic_rules = {
            logic_X: lambda r: callbacks.ctr_logic(r.logop(0), r.list_of_vars()),
            logic_X__eq_x: lambda r: callbacks.ctr_logic_neq(r[1].var(0), TypeConditionOperator.EQ, r.logop(0), r[0].list_of_vars()),
            logic_X__ne_x: lambda r: callbacks.ctr_logic_neeq(r[1].var(0), TypeConditionOperator.NE, r.logop(0), r[0].lisst_of_vars()),
            logic_y_relop_z__eq_x: lambda r: callbacks.ctr_logic_reif(r.var(2), r.var(0), r.relop(1), r.var(1))
        }

        self.sum_rules = {
            add_mul_vals__relop: lambda r: callbacks.ctr_sum(r[0].list_of_vars(), [1 if s.type == TypeNode.VAR else s.val(0) for s in r[0].cnt],
                                                             basic_condition(r)),
            add_vars__relop: lambda r: callbacks.ctr_sum(r[0].list_of_vars(), None, basic_condition(r)),
            add_mul_vars__relop: lambda r: callbacks.ctr_sum([s.var(0) for s in r[0].cnt], [s.var(1) for s in r[0].cnt], basic_condition(r))
        }

        self.extremum_rules = {
            min_relop: lambda r: callbacks.buildCtrMinimum(r[0].vars(), basic_condition(r)),
            max_relop: lambda r: callbacks.ctr_maximum(r[0].vars(), basic_condition(r))
        }

    def _recognize(self, tree: Node, d: dict, flag: bool):
        if flag:
            for k, v in d.items():
                if k.matches(tree):
                    return v(tree)
        return False

    def recognize_primitive1(self, tree: Node, arity: int):
        return self._recognize(tree, self.unary_rules, self.cb.recognize_unary_primitives and arity == 1)

    def recognize_primitive2(self, tree: Node, arity: int):
        return self._recognize(tree, self.binary_rules, self.cb.recognize_binary_primitives and arity == 2)

    def recognize_primitive3(self, tree: Node, arity: int):
        return self._recognize(tree, self.ternary_rules, self.cb.recognize_ternary_primitives and arity == 3)

    def recognize_logic(self, tree: Node, arity: int):
        return self._recognize(tree, self.logic_rules, self.cb.recognize_logic_intension)

    def recognize_sum(self, tree: Node, arity: int):
        return self._recognize(tree, self.sum_rules, self.cb.recognize_sum_intension)

    def recognize_extremum(self, tree: Node, arity: int):
        return self._recognize(tree, self.extremum_rules, self.cb.recognize_extremum_intension)

    def recognize_count(self, lst: list[Variable], values: list[int] | list[Variable], condition: Condition):
        if not self.cb.recognize_specific_count_cases:
            return False
        if not isinstance(values[0], int):
            return False
        op = condition.operator
        if len(values) == 1:
            if isinstance(condition, ConditionValue):
                k = condition.value
                if op == TypeConditionOperator.LT:
                    return self.cb.ctr_atmost(lst, values[0], k - 1)
                if op == TypeConditionOperator.LE:
                    return self.cb.ctr_atmost(lst, values[0], k)
                if op == TypeConditionOperator.GE:
                    return self.cb.ctr_atleast(lst, values[0], k)
                if op == TypeConditionOperator.GT:
                    return self.cb.ctr_atleast(lst, values[0], k + 1)
                if op == TypeConditionOperator.EQ:
                    return self.cb.ctr_exactly(lst, values[0], k)
            elif isinstance(condition, ConditionVariable):
                if op == TypeConditionOperator.EQ:
                    return self.cb.ctr_exactly(lst, values[0], condition.variable)
        elif op == TypeConditionOperator.EQ:
            if isinstance(condition, ConditionValue):
                return self.cb.ctr_among(lst, values, condition.value)
            elif isinstance(condition, ConditionVariable):
                return self.cb.ctr_among(lst, values, condition.variable)
        return False

    def recognize_nvalues(self, lst: list[Variable], condition: Condition):
        if not self.cb.recognize_specific_nvalues_cases:
            return False
        if not isinstance(condition, ConditionValue):
            return False
        op, k = condition.operator, condition.value
        if op == TypeConditionOperator.EQ and k == len(lst):
            return self.cb.ctr_all_different(lst, excepting=None)
        if op == TypeConditionOperator.EQ and k == 1:
            return self.cb.ctr_all_equal(lst, excepting=None)
        if (op == TypeConditionOperator.GE and k == 2) or (op == TypeConditionOperator.GT and k == 1):
            return self.cb.ctr_not_all_qual(lst)
        return False


class CallbackerXCSP3:

    def __init__(self, parser, callbacks):
        self.parser = parser
        self.cb = callbacks
        self.recognizer = Recognizer(callbacks)

        self.curr_ctr = None

    def load_instance(self, discarded_classes=None):
        self.cb.load_instance(discarded_classes)
        self.cb.begin_instance(TypeFramework.COP if len(self.parser.oEntries) > 0 else TypeFramework.CSP)
        self.load_variables(self.parser.vEntries)
        self.load_constraints(self.parser.cEntries)
        self.load_objectives(self.parser.oEntries)
        self.load_annotations(self.parser.aEntries)
        self.cb.end_instance()

    def load_variables(self, entries):
        self.cb.load_variables(entries)
        for entry in entries:
            if isinstance(entry, Variable):
                self.load_var(entry)
            else:
                self.load_var_array(entry)

    def load_var(self, x):
        self.cb.load_var(x)
        if not self.cb.discard_variables_of_degree_0 or x.degree is not None:
            assert len(x.domain) > 0
            if x.type == TypeVar.SYMBOLIC:
                assert all(isinstance(v, str) for v in x.domain)
                self.cb.var_symbolic(x, x.domain)
            elif len(x.domain) == 1 and isinstance(x.domain[0], range):
                self.cb.var_integer_range(x, x.domain[0].start, x.domain[0].stop - 1)
            else:
                self.cb.var_integer(x, flatten(v if isinstance(v, int) else list(v) for v in x.domain))

    def load_var_array(self, va):
        self.cb.load_var_array(va)
        for x in va.variables:
            if x is not None:
                self.load_var(x)

    def load_constraints(self, entries):
        self.cb.load_constraints(entries)
        for entry in entries:
            if isinstance(entry, XBlock):
                self.load_block(entry)
            elif isinstance(entry, XGroup):
                self.load_group(entry)
            elif isinstance(entry, XSlide):
                self.load_slide(entry)
            elif isinstance(entry, XCtr):
                self.load_ctr(entry)
            else:
                assert False

    def load_block(self, block):
        self.cb.load_block(block)
        self.load_constraints(block.subentries)  # recursive call

    def load_group(self, group):
        self.cb.load_group(group)
        assert isinstance(group.template, XCtr)
        self.load_templated_constraints(group.template, group.all_args)

    def load_slide(self, slide):
        self.cb.load_slide(slide)
        self.load_templated_constraints(slide.template, slide.scopes)

    def load_ctr(self, c):
        self.cb.load_ctr(c)

        def check_args(args, types):
            types = [t if isinstance(t, tuple) else (t,) for t in types]
            i, j = 0, 0
            while i < len(args) and j < len(types):
                if args[i].type in types[j]:
                    if args[i].type == TypeCtrArg.CONDITION and not isinstance(args[i].value, Condition):
                        return False
                    if args[i].type == TypeCtrArg.OPERATOR and not isinstance(args[i].value, TypeOrderedOperator):
                        return False
                    i += 1
                    if not (len(types[j]) == 2 and types[j][1] == '*'):
                        j += 1
                elif None in types[j] or (len(types[j]) == 2 and types[j][1] == '*'):
                    j += 1
                else:
                    return False
            while j < len(types):
                if None in types[j] or (len(types[j]) == 2 and types[j][1] == '*'):
                    j += 1
                else:
                    break
            return i == len(args) and j == len(types)

        def homogeneous_list(t):
            assert isinstance(t, list) and len(t) > 0
            present_node, present_var = False, False
            for v in t:
                if isinstance(v, Node):
                    present_node = True
                else:
                    assert isinstance(v, Variable)
                    present_var = True
            if present_node and present_var:
                return [Node(TypeNode.VAR, v) if isinstance(v, Variable) else v for v in t]
            return t

        self.curr_ctr = c
        args, n_args = c.ctr_args, len(c.ctr_args)
        if all(x.type == TypeVar.INTEGER for x in c.involved_vars()):
            match c.type:

                case TypeCtr.INTENSION:
                    assert check_args(args, [TypeCtrArg.FUNCTION])
                    # print("befooore", args[0].value)
                    tree = args[0].value.canonization()
                    # print("afteer", tree)
                    scope = tree.scope()

                    if (rc := self.recognizer.recognize_primitive1(tree, len(scope))) is not False:
                        return rc
                    if (rc := self.recognizer.recognize_primitive2(tree, len(scope))) is not False:
                        return rc
                    if (rc := self.recognizer.recognize_primitive3(tree, len(scope))) is not False:
                        return rc
                    if (rc := self.recognizer.recognize_logic(tree, len(scope))) is not False:
                        return rc
                    if (rc := self.recognizer.recognize_sum(tree, len(scope))) is not False:
                        return rc
                    if (rc := self.recognizer.recognize_extremum(tree, len(scope))) is not False:
                        return rc

                    return self.cb.ctr_intension(list(c.involved_vars()), tree)

                case TypeCtr.EXTENSION:
                    assert check_args(args, [TypeCtrArg.LIST, (TypeCtrArg.SUPPORTS, TypeCtrArg.CONFLICTS)])
                    scope, table = args[0].value, args[1].value
                    positive, flags = args[1].type == TypeCtrArg.SUPPORTS, args[1].flags
                    if table is None or len(table) == 0:  # special case because empty table (0 tuple)
                        return self.cb.ctr_false(scope) if positive else self.cb.ctr_true(scope)
                    return self.cb.ctr_extension_unary(scope[0], table, positive, flags) if len(scope) == 1 else self.cb.ctr_extension(scope, table,
                                                                                                                                       positive, flags)

                case TypeCtr.REGULAR:
                    assert check_args(args, [TypeCtrArg.LIST, TypeCtrArg.TRANSITIONS, TypeCtrArg.START, TypeCtrArg.FINAL])
                    return self.cb.ctr_regular(args[0].value, args[1].value, args[2].value, args[3].value)

                case TypeCtr.MDD:
                    assert check_args(args, [TypeCtrArg.LIST, TypeCtrArg.TRANSITIONS])
                    return self.cb.ctr_mdd(args[0].value, args[1].value)

                case TypeCtr.ALL_DIFFERENT:
                    assert n_args > 0 and (check_args(args, [(TypeCtrArg.LIST, '*'), (None, TypeCtrArg.EXCEPT)]) or check_args(args, [TypeCtrArg.MATRIX]))
                    excepting = args[-1].value if args[-1].type == TypeCtrArg.EXCEPT else None
                    if args[0].type == TypeCtrArg.MATRIX:
                        return self.cb.ctr_all_different_matrix(args[0].value, excepting)
                    if n_args > 1 and args[1].type == TypeCtrArg.LIST:
                        return self.cb.ctr_all_different_lists([arg.value for arg in args if arg.type == TypeCtrArg.LIST], excepting)
                    return self.cb.ctr_all_different(homogeneous_list(args[0].value), excepting)

                case TypeCtr.ALL_EQUAL:
                    assert check_args(args, [TypeCtrArg.LIST, (None, TypeCtrArg.EXCEPT)])
                    return self.cb.ctr_all_equal(homogeneous_list(args[0].value), args[1].value if n_args == 2 else None)

                case TypeCtr.ORDERED:
                    assert check_args(args, [TypeCtrArg.LIST, (None, TypeCtrArg.LENGTHS), TypeCtrArg.OPERATOR])
                    return self.cb.ctr_ordered(args[0].value, args[-1].value, args[1].value if n_args == 3 else None)

                case TypeCtr.LEX:
                    assert check_args(args, [(TypeCtrArg.LIST, '*'), TypeCtrArg.OPERATOR]) or check_args(args, [TypeCtrArg.MATRIX, TypeCtrArg.OPERATOR])
                    if args[0].type == TypeCtrArg.MATRIX:
                        return self.cb.ctr_lex_matrix(args[0].value, args[1].value)
                    if isinstance(args[1].value[0], int):  # special case (soon in XCSP3-core)
                        assert n_args == 3 and all(isinstance(v, int) for v in args[1].value) and len(args[0].value) == len(args[1].value)
                        return self.cb.ctr_lex_limit(args[0].value, args[1].value, args[2].value)
                    return self.cb.ctr_lex([arg.value for arg in args if arg.type == TypeCtrArg.LIST], args[-1].value)

                case TypeCtr.PRECEDENCE:
                    assert check_args(args, [TypeCtrArg.LIST, (None, TypeCtrArg.VALUES)])
                    return self.cb.ctr_precedence(args[0].value, args[1].value if n_args == 2 else None, n_args == 2 and args[1].attributes.get(COVERED, False))

                case TypeCtr.SUM:
                    assert check_args(args, [TypeCtrArg.LIST, (None, TypeCtrArg.COEFFS), TypeCtrArg.CONDITION])
                    return self.cb.ctr_sum(homogeneous_list(args[0].value), args[1].value if n_args == 3 else None, args[-1].value)

                case TypeCtr.COUNT:
                    assert check_args(args, [TypeCtrArg.LIST, TypeCtrArg.VALUES, TypeCtrArg.CONDITION])
                    lst, values, condition = homogeneous_list(args[0].value), args[1].value, args[2].value
                    if (rc := self.recognizer.recognize_count(lst, values, condition)) is not False:
                        return rc
                    return self.cb.ctr_count(lst, values, condition)

                case TypeCtr.N_VALUES:
                    assert check_args(args, [TypeCtrArg.LIST, (None, TypeCtrArg.EXCEPT), TypeCtrArg.CONDITION])
                    lst, excepting, condition = homogeneous_list(args[0].value), args[1].value if n_args == 3 else None, args[-1].value
                    if excepting is None and (rc := self.recognizer.recognize_nvalues(lst, condition)) is not False:
                        return rc
                    return self.cb.ctr_nvalues(lst, excepting, condition)

                case TypeCtr.CARDINALITY:
                    assert check_args(args, [TypeCtrArg.LIST, TypeCtrArg.VALUES, TypeCtrArg.OCCURS])
                    return self.cb.ctr_cardinality(homogeneous_list(args[0].value), args[1].value, args[2].value, args[1].attributes.get(CLOSED, False))

                case TypeCtr.MINIMUM:
                    assert check_args(args, [TypeCtrArg.LIST, TypeCtrArg.CONDITION])
                    return self.cb.ctr_minimum(homogeneous_list(args[0].value), args[1].value)

                case TypeCtr.MAXIMUM:
                    assert check_args(args, [TypeCtrArg.LIST, TypeCtrArg.CONDITION])
                    return self.cb.ctr_maximum(homogeneous_list(args[0].value), args[1].value)

                case TypeCtr.MINIMUM_ARG:
                    assert check_args(args, [TypeCtrArg.LIST, TypeCtrArg.CONDITION])
                    return self.cb.ctr_minimum_arg(homogeneous_list(args[0].value), args[1].value, c.attributes.get(RANK, TypeRank.ANY))

                case TypeCtr.MAXIMUM_ARG:
                    assert check_args(args, [TypeCtrArg.LIST, TypeCtrArg.CONDITION])
                    return self.cb.ctr_maximum_arg(homogeneous_list(args[0].value), args[1].value, c.attributes.get(RANK, TypeRank.ANY))

                case TypeCtr.ELEMENT:
                    assert n_args == 3, "element seen as a member constraint is not in XCSP3-core, as it can be written differently"
                    assert (check_args(args, [TypeCtrArg.LIST, TypeCtrArg.INDEX, (TypeCtrArg.VALUE, TypeCtrArg.CONDITION)])
                            or check_args(args, [TypeCtrArg.MATRIX, TypeCtrArg.INDEX, (TypeCtrArg.VALUE, TypeCtrArg.CONDITION)]))
                    condition = Condition.build_condition((TypeConditionOperator.EQ, args[-1].value)) if args[-1].type == TypeCtrArg.VALUE else args[-1].value
                    if args[0].type == TypeCtrArg.MATRIX:
                        assert args[0].attributes.get(START_ROW_INDEX, 0) == args[0].attributes.get(START_COL_INDEX, 0) == 0, "indexes must be 0 for XCSP3-core"
                        assert isinstance(args[1].value, list) and len(args[1].value) == 2 and all(isinstance(x, Variable) for x in args[1].value)
                        row_index, col_index = args[1].value
                        return self.cb.ctr_element_matrix(args[0].value, row_index, col_index, condition)
                    assert args[0].attributes.get(START_INDEX, 0) == 0, "indexes must always be 0 for XCSP3-core"
                    return self.cb.ctr_element(args[0].value, args[1].value, condition)

                case TypeCtr.CHANNEL:
                    assert check_args(args, [TypeCtrArg.LIST, (None, TypeCtrArg.LIST, TypeCtrArg.VALUE)])
                    assert args[0].attributes.get(START_INDEX, 0) == 0, "indexes must always be 0 for XCSP3-core"
                    if n_args == 1:
                        return self.cb.ctr_channel(args[0].value, None)
                    if args[1].type == TypeCtrArg.LIST:
                        assert args[1].attributes.get(START_INDEX, 0) == 0, "indexes must always be 0 for XCSP3-core"
                        return self.cb.ctr_channel(args[0].value, args[1].value)
                    return self.cb.ctr_channel_value(args[0].value, args[1].value)

                case TypeCtr.STRETCH:  # no more in XCSP3-core
                    assert check_args(args, [TypeCtrArg.LIST, TypeCtrArg.VALUES, TypeCtrArg.WIDTHS, (None, TypeCtrArg.PATTERNS)])
                    assert False, "not implemented for the moment (and not in XCSP3-core)"

                case TypeCtr.NO_OVERLAP:
                    assert check_args(args, [TypeCtrArg.ORIGINS, TypeCtrArg.LENGTHS])
                    origins, lengths = args[0].value, args[1].value
                    b = c.attributes.get(ZERO_IGNORED, True)  # must be True for XCSP3-core
                    assert isinstance(origins, list) and isinstance(lengths, list) and len(origins) == len(lengths) > 0
                    if isinstance(origins[0], Variable):
                        assert all(isinstance(x, Variable) for x in origins) and (all(isinstance(y, Variable) for y in lengths) or all(
                            isinstance(y, int) for y in lengths))
                        return self.cb.ctr_nooverlap(origins, lengths, b)
                    if len(lengths[0]) == 2 and isinstance(lengths[0][1], int):  # special mixed case
                        return self.cb.ctr_nooverlap_mixed([t[0] for t in origins], [t[1] for t in origins], [t[0] for t in lengths],
                                                           [t[1] for t in lengths], b)
                    return self.cb.ctr_nooverlap_multi(origins, lengths, b)

                case TypeCtr.CUMULATIVE:
                    assert check_args(args, [TypeCtrArg.ORIGINS, TypeCtrArg.LENGTHS, (None, TypeCtrArg.ENDS), TypeCtrArg.HEIGHTS, TypeCtrArg.CONDITION])
                    if n_args == 4:
                        return self.cb.ctr_cumulative(args[0].value, args[1].value, args[2].value, args[3].value)
                    else:
                        assert False, "cumulative variant not implemented (and not in XCSP3-core)"

                case TypeCtr.BIN_PACKING:
                    assert check_args(args,
                                      [TypeCtrArg.LIST, TypeCtrArg.SIZES, (TypeCtrArg.CONDITION, TypeCtrArg.LIMITS, TypeCtrArg.LOADS, TypeCtrArg.CONDITIONS)])
                    bins, sizes = args[0].value, args[1].value
                    if args[2].type == TypeCtrArg.CONDITION:
                        return self.cb.ctr_binpacking(bins, sizes, args[2].value)
                    if args[2].type == TypeCtrArg.LIMITS:
                        return self.cb.ctr_binpacking_limits(bins, sizes, args[2].value)
                    if args[2].type == TypeCtrArg.LOADS:
                        return self.cb.ctr_binpacking_loads(bins, sizes, args[2].value)
                    return self.cb.ctr_binpacking_conditions(bins, sizes, args[2].value)  # not in XCSP3-core

                case TypeCtr.KNAPSACK:
                    assert check_args(args, [TypeCtrArg.LIST, TypeCtrArg.WEIGHTS, TypeCtrArg.CONDITION, TypeCtrArg.PROFITS, TypeCtrArg.CONDITION])
                    return self.cb.ctr_knapsack(args[0].value, args[1].value, args[2].value, args[3].value, args[4].value)

                case TypeCtr.FLOW:  # not in XCSP3-core
                    assert args[0].type == TypeCtrArg.LIST and args[1].type == TypeCtrArg.BALANCE and args[2].type == TypeCtrArg.ARCS
                    if n_args in (3, 4):
                        return self.cb.ctr_flow(args[0].value, args[1].value, args[2].value, None if n_args == 3 else args[3].value)
                    assert n_args in (5, 6) and args[-2].type == TypeCtrArg.WEIGHTS and args[-1].type == TypeCtrArg.CONDITION
                    return self.cb.ctr_flow_weighted(args[0].value, args[1].value, args[2].value, None if n_args == 5 else args[3].value, args[-2].value,
                                                     args[-1].value)

                case TypeCtr.INSTANTIATION:
                    assert check_args(args, [TypeCtrArg.LIST, TypeCtrArg.VALUES])
                    return self.cb.ctr_instantiation(args[0].value, args[1].value)

                case TypeCtr.CLAUSE:
                    assert check_args(args, [TypeCtrArg.LIST])
                    literals = args[0].value
                    assert all(isinstance(v, Node) and v.is_literal() for v in literals)
                    return self.cb.ctr_clause([v.cnt for v in literals if v.type == TypeNode.VAR],
                                              [v.cnt[0].cnt for v in literals if v.type == TypeNode.NOT])

                case TypeCtr.CIRCUIT:
                    assert check_args(args, [TypeCtrArg.LIST, (None, TypeCtrArg.SIZE)])
                    assert args[0].attributes.get(START_INDEX, 0) == 0, "indexes must always be 0 for XCSP3-core"
                    return self.cb.ctr_circuit(args[0].value, None if n_args == 1 else args[1].value)

                case TypeCtr.ADHOC:  # not in XCSP3-core
                    assert False, "not implemented for the moment (and not in XCSP3-core)"

                case _:
                    assert False, "not implemented"

        else:
            assert all(x.type == TypeVar.SYMBOLIC for x in c.involved_vars())
            match c.type:
                case TypeCtr.INTENSION:
                    assert check_args(args, [TypeCtrArg.FUNCTION])
                    tree = args[0].value.canonization()
                    return self.cb.ctr_intension_symbolic(list(c.involved_vars()), tree)

                case TypeCtr.EXTENSION:
                    assert check_args(args, [TypeCtrArg.LIST, (TypeCtrArg.SUPPORTS, TypeCtrArg.CONFLICTS)])
                    scope, table = args[0].value, args[1].value
                    positive, flags = args[1].type == TypeCtrArg.SUPPORTS, args[1].flags
                    if table is None or len(table) == 0:  # special case because empty table (0 tuple)
                        return self.cb.ctr_false(scope) if positive else self.cb.ctr_true(scope)
                    return self.cb.ctr_extension_unary_symbolic(scope[0], table, positive, flags) if len(scope) == 1 \
                        else self.cb.ctr_extension_symbolic(scope, table, positive, flags)

                case TypeCtr.ALL_DIFFERENT:
                    assert n_args > 0 and (check_args(args, [(TypeCtrArg.LIST, '*'), (None, TypeCtrArg.EXCEPT)]) or check_args(args, [TypeCtrArg.MATRIX]))
                    excepting = args[-1].value if args[-1].type == TypeCtrArg.EXCEPT else None
                    return self.cb.ctr_all_different_symbolic(homogeneous_list(args[0].value), excepting)

                case TypeCtr.INSTANTIATION:
                    assert check_args(args, [TypeCtrArg.LIST, TypeCtrArg.VALUES])
                    return self.cb.ctr_instantiation_symbolic(args[0].value, args[1].value)

                case _:
                    assert False, "not implemented"

    def load_templated_constraints(self, template, all_args):
        self.cb.load_templated_constraints(template, all_args)
        for args in all_args:
            template.id = None  # because the template object is shared
            template.abstraction.concretize(args)
            self.load_ctr(template)

    def load_objectives(self, objectives):
        self.cb.load_objectives(objectives)
        for objective in objectives:
            self.load_objective(objective)

    def load_objective(self, objective):
        self.cb.load_objective(objective)
        if isinstance(objective, XObjExpr):
            if objective.minimize:
                self.cb.obj_minimize(objective.root)
            else:
                self.cb.obj_maximize(objective.root)
        else:
            if objective.minimize:
                self.cb.obj_minimize_special(objective.type, objective.terms, objective.coefficients)
            else:
                self.cb.obj_maximize_special(objective.type, objective.terms, objective.coefficients)

    def load_annotations(self, annotations):
        self.cb.load_annotations(annotations)
        for annotation in annotations:
            self.load_annotation(annotation)

    def load_annotation(self, annotation):
        if annotation.type == TypeAnn.DECISION:
            self.cb.ann_decision(annotation.value)
        elif annotation.type == TypeAnn.VAL_HEURISTIC:
            d = annotation.value
            assert isinstance(d, dict) and len(d) == 1 and STATIC in d, "for the moment, only this is taken into account"
            for (lst, order) in d[STATIC]:
                self.cb.ann_val_heuristic_static(lst, order)


if __name__ == "__main__":
    assert len(sys.argv) >= 2
    parser = ParserXCSP3(os.path.join("./", sys.argv[1]))
    callbacks = Callbacks()
    # e.g., callbacks.force_exit = True
    # e.g., callbacks.recognize_unary_primitives = False
    callbacker = CallbackerXCSP3(parser, callbacks)
    callbacker.load_instance()

    # obj = build_dynamic_object(sys.argv[2], sys.argv[3])
