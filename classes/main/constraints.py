import os
from collections import OrderedDict

from pycsp3 import functions
from pycsp3.classes.auxiliary.conditions import Condition, ConditionInterval, ConditionSet, ConditionNode
from pycsp3.classes.auxiliary.ptypes import TypeVar, TypeCtr, TypeCtrArg, TypeXML, TypeConditionOperator, TypeRank
from pycsp3.classes.auxiliary.values import IntegerEntity
from pycsp3.classes.entities import EVarArray, ECtr, EMetaCtr, TypeNode, Node, possible_range
from pycsp3.classes import main
from pycsp3.classes.main.domains import Domain
from pycsp3.classes.main.variables import Variable, VariableInteger
from pycsp3.dashboard import options
from pycsp3.tools import curser
from pycsp3.tools.utilities import ANY, is_1d_list, matrix_to_string, integers_to_string, table_to_string, flatten, is_matrix, error, error_if, \
    to_ordinary_table, warning, is_windows


class Diffs:
    """"
      Objects of this class are used to record the differences between two (or more) close constraints.
      This allows us to build groups in an automatic way.
    """

    fusion = None  # the current Diffs object memorizing the arguments that differ between two (or more) constraints

    @staticmethod
    def reset():
        Diffs.fusion = None

    def __init__(self, records=[]):
        self.argument_names = [name for (name, flag) in records]
        self.argument_flags = [flag for (name, flag) in records]

    def merge(self):
        if Diffs.fusion is None:
            Diffs.fusion = self  # this is the first time such an object is built (since the last reset); we simply record it
        else:  # the recorded object (fusion) and the last built one are compatible (we know that at time of calling); so, we simply update flags
            for i, name in enumerate(self.argument_names):
                index = Diffs.fusion.argument_names.index(name)  # note that self.argument_names must be be included in Diffs.fusion.argument_names
                Diffs.fusion.argument_flags[index] |= self.argument_flags[i]
                # for i in range(len(Diffs.fusion.argument_flags)): Diffs.fusion.argument_flags[i] |= self.argument_flags[i]


class ConstraintArgument:
    def __init__(self, name, content, attributes=[], content_compressible=True, content_ordered=False, lifted=False):
        assert isinstance(name, (TypeCtrArg, TypeXML, main.annotations.TypeAnnArg)), str(name) + " " + str(type(name))
        self.name = name  # name of the argument
        self.attributes = attributes  # list of pairs (key, value) representing the attributes
        self.content = content  # content of the argument
        self.content_compressible = content_compressible  # indicates if we can try to make the content more compact
        self.content_ordered = content_ordered  # indicates if the content must be kept as it is (order is important)
        self.lifted = lifted  # indicates if the constraint is lifted to several lists (or sets); see specifications

    def __eq__(self, other):  # must be called in protection mode (see in functions.py the function protect())
        if not isinstance(other, ConstraintArgument) or self.name != other.name or len(self.attributes) > 0 or len(other.attributes) > 0:
            return False  # attributes not currently completely taken into account
        if self.name != TypeCtrArg.MATRIX and self.content_compressible != other.content_compressible:  # because for matrix, the argument may be a list
            return False
        if self.content_ordered != other.content_ordered or self.lifted != other.lifted:
            return False
        return curser.OpOverrider.eq_protected(self.content, other.content)

        # #print(type(self.content),type(other.content))
        # if isinstance(self.content, list):  #
        #     return list.__eq__(self.content, other.content)
        # #if isinstance(self.content, (EMetaCtr, Variable, Node)):
        # #    return object.__eq__(self.content, other.content)
        # return object.__eq__(self.content, other.content)
        # return self.content == other.content

    def __str__(self):
        content = "[" + ", ".join(str(v) for v in self.content) + "]" if isinstance(self.content, list) else self.content
        return str(self.name) + ":" + str(content)


class Constraint:
    def __init__(self, name):
        self.name = name
        self.attributes = []
        self.arguments = OrderedDict()  # arguments of the constraint (such as list, supports, condition, ...)
        self.n_parameters = 0  # used when building abstract forms of constraints (e.g., in groups for %0 %1 %2 ...)

    def __eq__(self, other):  # must be called in protection mode (see in functions.py the function protect())
        if not isinstance(other, Constraint) or self.name != other.name or len(self.attributes) > 0 or len(other.attributes) > 0:
            return False  # attributes not currently completely taken into account
        if self.n_parameters > 0 or other.n_parameters > 0:
            return False
        return self.arguments == other.arguments

    def equal_except_condition(self, other):
        if not isinstance(other, Constraint) or self.name != other.name or len(self.attributes) > 0 or len(other.attributes) > 0:
            return False  # attributes not currently completely taken into account
        if self.n_parameters > 0 or other.n_parameters > 0:
            return False
        return [v for v in self.arguments.items() if str(v[0]) != "condition"] == [v for v in other.arguments.items() if str(v[0]) != "condition"]

    def arg(self, name, content, *, attributes=[], content_compressible=True, content_ordered=False, lifted=False):
        self.arguments[name] = ConstraintArgument(name, content, attributes, content_compressible, content_ordered, lifted)
        return self

    def set_condition(self, operator, right_operand):
        return self.arg(TypeCtrArg.CONDITION, Condition.build_condition((operator, right_operand)))

    def set_value(self, new_value):
        return self.arg(TypeCtrArg.VALUE, new_value)

    def similar_structure(self, other):
        if type(self) != type(other) or self.attributes != other.attributes:
            return False
        args1, args2 = list(self.arguments.values()), list(other.arguments.values())
        if len(args1) != len(args2):
            return False
        if any(args1[i].name != args2[i].name or args1[i].attributes != args2[i].attributes or args1[i].lifted != args2[i].lifted for i in range(len(args1))):
            return False
        return any(type(args1[i].content) == type(args2[i].content) for i in range(len(args1)))

    def close_to(self, other):
        if not self.similar_structure(other):
            return False
        args1, args2 = list(self.arguments.values()), list(other.arguments.values())
        records = []
        for i in range(len(args1)):
            if str(args1[i].content) != str(args2[i].content):
                if args1[i].name == TypeCtrArg.MATRIX:  # TODO making a more specific test?
                    return False
                if args1[i].name == TypeCtrArg.CONDITION and args1[i].content.operator != args2[i].content.operator:
                    return False  # the operators are different in the two conditions
                b = hasattr(args1[i].content, '__len__') and hasattr(args2[i].content, '__len__') and len(args1[i].content) != len(args2[i].content)
                records.append((args1[i].name, b))
        if len(records) > 2:
            return False  # too many differences
        if len(records) == 0:
            return False  # or None
        diffs = Diffs(records)
        if Diffs.fusion and not all(
                name in Diffs.fusion.argument_names for name in diffs.argument_names):  # diffs.argument_names != Diffs.fusion.argument_names:
            return False  # because arguments are not the same (so it is not possible to make a unique abstraction)
        if len([flag for flag in diffs.argument_flags if flag]) > 1:
            return False  # two arguments of different size cannot be currently abstracted
        return diffs

    def parameter_form(self, p):
        length = len(p) if isinstance(p, list) else 1
        self.n_parameters += length
        return " ".join("%" + str(v + self.n_parameters - length) for v in range(length))

    def __str__(self):
        items = list(self.arguments.items())
        condition = None  # items[-1][1].content.infix_string() if items[-1][0] == TypeCtrArg.CONDITION else None
        s_attributes = " ".join(str(t.name) + ": " + str(v) for (t, v) in self.attributes if t is not TypeCtrArg.TYPE)
        s_arguments = ", ".join(str(v) for k, v in (items if condition is None else items[:-1]) if v and v.content is not None)
        body = ("[" + s_attributes + "]" if len(s_attributes) > 0 else "") + "(" + s_arguments + ")"
        if len(self.attributes) > 0 and self.attributes[0][0] is TypeCtrArg.TYPE:  # objective
            s = str(self.name) + "(" + str(self.attributes[0][1]) + body + ")"
        else:
            s = str(self.name) + body
        return s if condition is None else s + " " + condition


class ConstraintUnmergeable(Constraint):
    def __init__(self, name):
        super().__init__(name)

    def close_to(self, other):
        return False


class ConstraintWithCondition(Constraint):
    def __init__(self, name):
        super().__init__(name)

    def min_possible_value(self):
        pass

    def max_possible_value(self):
        pass


''' Generic Constraints '''


class ConstraintIntension(Constraint):
    def __init__(self, tree):
        super().__init__(TypeCtr.INTENSION)
        self.arg(TypeCtrArg.FUNCTION, tree)

    def abstract_tree(self):
        return self.arguments[TypeCtrArg.FUNCTION].content.abstract_tree()

    def abstract_values(self):
        return self.arguments[TypeCtrArg.FUNCTION].content.abstract_values()

    def close_to(self, other):
        if not self.similar_structure(other):
            return False
        return Diffs() if self.abstract_tree() == other.abstract_tree() else False


class ConstraintExtension(Constraint):
    cache = dict()
    cache_for_knowing_if_hybrid = dict()

    @staticmethod
    def convert_hybrid_to_ordinary(scope, table):
        for i, t in enumerate(table):
            tpl = None
            for j, v in enumerate(t):
                if isinstance(v, int) or v == ANY:
                    if tpl:
                        tpl.append(v)
                else:
                    if isinstance(v, range):
                        if not tpl:
                            tpl = list(t[:j])
                        tpl.append(ConditionInterval(TypeConditionOperator.IN, v.start, v.stop - 1))
                    elif isinstance(v, (tuple, list, set, frozenset)):
                        assert all(isinstance(w, (int, range)) for w in v)
                        if not tpl:
                            tpl = list(t[:j])
                        values = {u for w in v for u in ([w] if isinstance(w, int) else list(w))}
                        tpl.append(ConditionSet(TypeConditionOperator.IN, values))  # set(v)))
                    else:
                        assert isinstance(v, Condition), "An element of this table should not be of type: " + str(type(v))
                        if tpl:
                            tpl.append(v)
            if tpl:
                table[i] = tuple(tpl)
        return sorted(list(to_ordinary_table(table, [x.dom for x in scope], starred=True)))

    @staticmethod
    def remove_redundant_tuples(table):
        tbl = None
        for i in range(len(table) - 1):
            if table[i] != table[i + 1]:
                if tbl:
                    tbl.append(table[i])
            else:
                if not tbl:
                    tbl = table[:i]
        if tbl:
            tbl.append(table[-1])
            table = tbl
        return table

    def process_table(self, scope, table):
        if len(table) == 0:
            return None
        # we compute the hash code of the table
        try:
            h = hash(tuple(table) + (self.keep_hybrid,))  # if ever we change the value of keep_hybrid
        except TypeError:
            for i, t in enumerate(table):
                if any(isinstance(v, (list, set, frozenset)) for v in t):
                    table[i] = tuple(tuple(v) if isinstance(v, (list, set, frozenset)) else v for v in t)
            h = hash(tuple(table))

        if len(scope) == 1:  # if arity 1
            if h not in ConstraintExtension.cache:
                ConstraintExtension.cache[h] = integers_to_string(table) if isinstance(table[0], int) else " ".join(v for v in sorted(table))
            return ConstraintExtension.cache[h]

        possible_parallelism = not options.safe and not is_windows()
        if h in ConstraintExtension.cache_for_knowing_if_hybrid:
            hybrid = ConstraintExtension.cache_for_knowing_if_hybrid[h]
        else:
            check_hybrid2 = True
            hybrid = 0
            for t in table:
                for v in t:
                    error_if(isinstance(v, Node), "Bad form")
                    if isinstance(v, ConditionNode):
                        hybrid = 2
                        if not check_hybrid2:
                            break
                        else:
                            assert True  # TODO test to be written
                    elif hybrid == 0 and not (isinstance(v, (int, str)) or v is ANY):
                        hybrid = 1
                if hybrid == 2:
                    if not check_hybrid2:
                        break
            # hybrid = any(not (isinstance(v, (int, str)) or v == ANY) for t in table for v in t)  # A parallelisation attempt showed no gain.
            ConstraintExtension.cache_for_knowing_if_hybrid[h] = hybrid

        if hybrid == 0:  # if not hybrid
            if not self.restrict_table_wrt_domains:
                if h not in ConstraintExtension.cache:  # we can directly use caching here (without paying attention to domains)
                    table.sort()
                    table = ConstraintExtension.remove_redundant_tuples(table)
                    ConstraintExtension.cache[h] = table_to_string(table, parallel=possible_parallelism)
                return ConstraintExtension.cache[h]
            else:
                domains = [x.dom for x in scope]
                if h in ConstraintExtension.cache:  # we need to be careful about domains when caching here
                    domains_cache, table_cache = ConstraintExtension.cache[h]
                    if domains == domains_cache:
                        return table_cache
                table.sort()
                table_s = table_to_string(table, restricting_domains=domains, parallel=possible_parallelism)
                ConstraintExtension.cache[h] = (domains, table_s)
                return table_s
        else:  # it is hybrid (level 1 or 2)
            if self.keep_hybrid:  # currently, no restriction of tables (wrt domains) in that case
                self.attributes.append((TypeXML.TYPE, "hybrid-" + str(hybrid)))
                if h not in ConstraintExtension.cache:
                    table = ConstraintExtension.remove_redundant_tuples(table)
                    ConstraintExtension.cache[h] = table_to_string(table, parallel=possible_parallelism)
                return ConstraintExtension.cache[h]
            else:
                domains = [x.dom for x in scope]
                if h in ConstraintExtension.cache:  # we need to be careful about domains when caching here
                    domains_cache, table_cache = ConstraintExtension.cache[h]
                    if domains == domains_cache:
                        return table_cache
                table = ConstraintExtension.convert_hybrid_to_ordinary(scope, table)
                table = ConstraintExtension.remove_redundant_tuples(table)
                table_s = table_to_string(table, restricting_domains=domains if self.restrict_table_wrt_domains else None, parallel=possible_parallelism)
                ConstraintExtension.cache[h] = (domains, table_s)
                return table_s

    def __init__(self, scope, table, positive=True, keep_hybrid=False, restrict_table_wrt_domains=False):
        super().__init__(TypeCtr.EXTENSION)
        self.keep_hybrid = keep_hybrid
        self.restrict_table_wrt_domains = restrict_table_wrt_domains
        assert is_1d_list(scope, Variable)
        assert len(table) == 0 or (len(scope) == 1 and (is_1d_list(table, int) or is_1d_list(table, str))) or (len(scope) > 1 and len(scope) == len(table[0]))
        self.arg(TypeCtrArg.LIST, scope, content_ordered=True)
        self.arg(TypeCtrArg.SUPPORTS if positive else TypeCtrArg.CONFLICTS, self.process_table(scope, table), content_compressible=False)

    def close_to(self, other):
        if not self.similar_structure(other):
            return False
        if len(self.arguments[TypeCtrArg.LIST].content) != len(other.arguments[TypeCtrArg.LIST].content):
            return False
        if TypeCtrArg.SUPPORTS in self.arguments and self.arguments[TypeCtrArg.SUPPORTS].content != other.arguments[TypeCtrArg.SUPPORTS].content:
            return False
        if TypeCtrArg.CONFLICTS in self.arguments and self.arguments[TypeCtrArg.CONFLICTS].content != other.arguments[TypeCtrArg.CONFLICTS].content:
            return False
        return Diffs([(TypeCtrArg.LIST, False)])


''' Constraints defined from languages'''


class ConstraintRegular(Constraint):
    def __init__(self, lst, automaton):
        super().__init__(TypeCtr.REGULAR)
        self.arg(TypeCtrArg.LIST, lst, content_ordered=True)
        self.arg(TypeCtrArg.TRANSITIONS, automaton.transitions_to_string(lst))
        self.arg(TypeCtrArg.START, automaton.start)
        self.arg(TypeCtrArg.FINAL, automaton.final)

    def close_to(self, other):
        diffs = super().close_to(other)
        return False if not diffs or TypeCtrArg.TRANSITIONS in diffs.argument_names else diffs


class ConstraintMdd(Constraint):
    def __init__(self, lst, mdd):
        super().__init__(TypeCtr.MDD)
        self.arg(TypeCtrArg.LIST, lst, content_ordered=True)
        # TODO reordering transitions in order to guarantee to have:
        # - the root as the src of the first transition
        # - the terminal as the dst of the last transition
        # - no transition with a src occurring before it was reached
        self.arg(TypeCtrArg.TRANSITIONS, mdd.transitions_to_string(lst))


''' Comparison-based Constraints '''


class ConstraintAllDifferent(Constraint):
    def __init__(self, lst, excepting):
        super().__init__(TypeCtr.ALL_DIFFERENT)
        self.arg(TypeCtrArg.LIST, lst)
        self.arg(TypeCtrArg.EXCEPT, excepting)


class ConstraintAllDifferentList(ConstraintUnmergeable):
    def __init__(self, lst, excepting):
        super().__init__(TypeCtr.ALL_DIFFERENT)
        self.arg(TypeCtrArg.LIST, lst, content_ordered=True, lifted=True)
        if excepting is not None:
            self.arg(TypeCtrArg.EXCEPT, "(" + ",".join(str(v) for v in excepting) + ")")  # if excepting else excepting)


class ConstraintAllDifferentMatrix(ConstraintUnmergeable):
    def __init__(self, lst, excepting):
        super().__init__(TypeCtr.ALL_DIFFERENT)
        self.arg(TypeCtrArg.MATRIX, matrix_to_string(lst), content_compressible=lst)
        self.arg(TypeCtrArg.EXCEPT, excepting)


class ConstraintAllEqual(Constraint):
    def __init__(self, lst, excepting):
        super().__init__(TypeCtr.ALL_EQUAL)
        self.arg(TypeCtrArg.LIST, lst)
        self.arg(TypeCtrArg.EXCEPT, excepting)


class ConstraintAllEqualList(ConstraintUnmergeable):
    def __init__(self, lst, excepting):
        super().__init__(TypeCtr.ALL_EQUAL)
        self.arg(TypeCtrArg.LIST, lst, content_ordered=True, lifted=True)
        self.arg(TypeCtrArg.EXCEPT, "(" + ",".join(str(v) for v in excepting) + ")" if excepting else excepting)


class ConstraintOrdered(Constraint):
    def __init__(self, lst, operator, lengths):
        super().__init__(TypeCtr.ORDERED)
        self.arg(TypeCtrArg.LIST, lst, content_ordered=True)
        self.arg(TypeCtrArg.LENGTHS, lengths, content_ordered=True)
        self.arg(TypeCtrArg.OPERATOR, operator)


class ConstraintLex(ConstraintUnmergeable):
    def __init__(self, lst, operator):
        super().__init__(TypeCtr.LEX)
        self.arg(TypeCtrArg.LIST, lst, content_ordered=True, lifted=True)
        self.arg(TypeCtrArg.OPERATOR, operator)


class ConstraintLexMatrix(ConstraintUnmergeable):
    def __init__(self, lst, operator):
        super().__init__(TypeCtr.LEX)
        self.arg(TypeCtrArg.MATRIX, matrix_to_string(lst), content_compressible=lst)
        self.arg(TypeCtrArg.OPERATOR, operator)


class ConstraintPrecedence(Constraint):
    def __init__(self, lst, *, values=None, covered=False):
        super().__init__(TypeCtr.PRECEDENCE)
        self.arg(TypeCtrArg.LIST, lst, content_ordered=True)
        assert covered is False or values is not None
        if values is not None:
            self.arg(TypeCtrArg.VALUES, values, attributes=[(TypeCtrArg.COVERED, "true")] if covered else [], content_ordered=True)


# class ConstraintSubsetAllDifferent(ConstraintUnmergeable):
#     def __init__(self, subsets):
#         super().__init__(TypeCtr.SUBSET_ALL_DIFFERENT)
#         self.arg(TypeCtrArg.SUBSETS, subsets, lifted=True)


''' Counting and Summing Constraints '''


class ConstraintSum(ConstraintWithCondition):
    def __init__(self, lst, coefficients, condition):
        super().__init__(TypeCtr.SUM)
        self.arg(TypeCtrArg.LIST, lst, content_ordered=True)
        if coefficients is not None and any(not isinstance(v, int) or v != 1 for v in coefficients):
            self.arg(TypeCtrArg.COEFFS, coefficients, content_ordered=True)
        self.arg(TypeCtrArg.CONDITION, condition)

    def _min_or_max_term_value(self, x, c, is_min):
        if isinstance(x, Variable):
            xmin, xmax = x.dom.smallest_value(), x.dom.greatest_value()
        else:
            assert isinstance(x, Node)
            values = x.possible_values()
            xmin, xmax = values[0], values[-1]
        if isinstance(c, int):
            return min(xmin * c, xmax * c) if is_min else max(xmin * c, xmax * c)
        if isinstance(c, Variable):
            cmin, cmax = c.dom.smallest_value(), c.dom.greatest_value()
        else:
            assert isinstance(c, Node)
            values = c.possible_values()
            cmin, cmax = values[0], values[-1]
        return min(xmin * cmin, xmin * cmax, xmax * cmin, xmax * cmax) if is_min else max(xmin * cmin, xmin * cmax, xmax * cmin, xmax * cmax)

    def min_possible_value(self):
        vs = self.arguments[TypeCtrArg.LIST].content
        cs = self.arguments[TypeCtrArg.COEFFS].content if TypeCtrArg.COEFFS in self.arguments else None
        if cs is None:
            return sum(x.dom.smallest_value() if isinstance(x, Variable) else x.possible_values()[0] for x in vs)
        assert len(vs) == len(cs)
        return sum(self._min_or_max_term_value(x, cs[i], True) for i, x in enumerate(vs))

    def max_possible_value(self):
        vs = self.arguments[TypeCtrArg.LIST].content
        cs = self.arguments[TypeCtrArg.COEFFS].content if TypeCtrArg.COEFFS in self.arguments else None
        if cs is None:
            return sum(x.dom.greatest_value() if isinstance(x, Variable) else x.possible_values()[-1] for x in vs)
        assert len(vs) == len(cs)
        return sum(self._min_or_max_term_value(x, cs[i], False) for i, x in enumerate(vs))

    def revert_coeffs(self):
        if TypeCtrArg.COEFFS in self.arguments:
            self.arguments[TypeCtrArg.COEFFS].content = [-v for v in self.arguments[TypeCtrArg.COEFFS].content]
        else:
            self.arg(TypeCtrArg.COEFFS, [-1 for _ in range(len(self.arguments[TypeCtrArg.LIST]))])
        return self


class ConstraintCount(ConstraintWithCondition):
    def __init__(self, lst, values, condition):
        super().__init__(TypeCtr.COUNT)
        self.arg(TypeCtrArg.LIST, lst, content_ordered=False)
        self.arg(TypeCtrArg.VALUES, values)
        self.arg(TypeCtrArg.CONDITION, condition)

    def min_possible_value(self):
        return 0

    def max_possible_value(self):
        return len(self.arguments[TypeCtrArg.LIST].content)


class ConstraintNValues(ConstraintWithCondition):
    def __init__(self, lst, excepting, condition):
        super().__init__(TypeCtr.N_VALUES)
        self.arg(TypeCtrArg.LIST, lst)
        self.arg(TypeCtrArg.EXCEPT, excepting)
        self.arg(TypeCtrArg.CONDITION, condition)

    def min_possible_value(self):
        return 1

    def max_possible_value(self):
        return len(self.arguments[TypeCtrArg.LIST].content)


class ConstraintCardinality(Constraint):
    def __init__(self, lst, values, occurs, closed=False):
        super().__init__(TypeCtr.CARDINALITY)
        self.arg(TypeCtrArg.LIST, lst)
        assert len(values) == len(occurs)
        #  values = integers_to_string(values)  TODO (and compact form for occurs)
        self.arg(TypeCtrArg.VALUES, values, content_ordered=True, attributes=[(TypeXML.CLOSED, "true")] if closed else [])
        self.arg(TypeCtrArg.OCCURS, occurs, content_ordered=True)


''' Connection Constraints '''


def _index_att(v):
    return []  # [(TypeCtrArg.START_INDEX, v)] if v is not None and v != 0 else []


class ConstraintMaximum(ConstraintWithCondition):
    def __init__(self, lst, condition=None):
        super().__init__(TypeCtr.MAXIMUM)
        self.arg(TypeCtrArg.LIST, auxiliary().replace_ints(lst))
        self.arg(TypeCtrArg.CONDITION, condition)

    def min_possible_value(self):
        return max(x.dom.smallest_value() if isinstance(x, Variable) else x.possible_values()[0] for x in self.arguments[TypeCtrArg.LIST].content)

    def max_possible_value(self):
        return max(x.dom.greatest_value() if isinstance(x, Variable) else x.possible_values()[-1] for x in self.arguments[TypeCtrArg.LIST].content)

    def all_possible_values(self):  # be careful: may be costly
        max_min = self.min_possible_value()
        s = set()
        for x in self.arguments[TypeCtrArg.LIST].content:
            s.update(v for v in (x.dom.all_values() if isinstance(x, Variable) else x.possible_values()) if v >= max_min)
        return s


class ConstraintMinimum(ConstraintWithCondition):
    def __init__(self, lst, condition=None):
        super().__init__(TypeCtr.MINIMUM)
        self.arg(TypeCtrArg.LIST, auxiliary().replace_ints(lst))
        self.arg(TypeCtrArg.CONDITION, condition)

    def min_possible_value(self):
        return min(x.dom.smallest_value() if isinstance(x, Variable) else x.possible_values()[0] for x in self.arguments[TypeCtrArg.LIST].content)

    def max_possible_value(self):
        return min(x.dom.greatest_value() if isinstance(x, Variable) else x.possible_values()[-1] for x in self.arguments[TypeCtrArg.LIST].content)

    def all_possible_values(self):  # be careful: may be costly
        min_max = self.max_possible_value()
        s = set()
        for x in self.arguments[TypeCtrArg.LIST].content:
            s.update(v for v in (x.dom.all_values() if isinstance(x, Variable) else x.possible_values()) if v <= min_max)
        return s


class ConstraintMaximumArg(ConstraintWithCondition):
    def __init__(self, lst, type_rank=None, condition=None):
        super().__init__(TypeCtr.MAXIMUM_ARG)
        self.attributes = [(TypeCtrArg.RANK, type_rank)] if type_rank and type_rank != TypeRank.ANY else []
        self.arg(TypeCtrArg.LIST, lst, content_ordered=True)
        self.arg(TypeCtrArg.CONDITION, condition)

    def min_possible_value(self):
        return 0

    def max_possible_value(self):
        return len(self.arguments[TypeCtrArg.LIST].content) - 1


class ConstraintMinimumArg(ConstraintWithCondition):
    def __init__(self, lst, type_rank=None, condition=None):
        super().__init__(TypeCtr.MINIMUM_ARG)
        self.attributes = [(TypeCtrArg.RANK, type_rank)] if type_rank and type_rank != TypeRank.ANY else []
        self.arg(TypeCtrArg.LIST, lst, content_ordered=True)
        self.arg(TypeCtrArg.CONDITION, condition)

    def min_possible_value(self):
        return 0

    def max_possible_value(self):
        return len(self.arguments[TypeCtrArg.LIST].content) - 1


class ConstraintElement(ConstraintWithCondition):  # currently, not exactly with a general condition
    def __init__(self, lst, *, index, type_rank=None, condition=None):
        super().__init__(TypeCtr.ELEMENT)
        if len(lst) == 0:
            error("A constraint Element on an empty list of variables is encountered. Did you write something like x[:j] instead of x[:,j]?")
        smallest = [] if index is None else index.dom[0].smallest() if isinstance(index.dom[0], IntegerEntity) else index.dom[0]
        self.arg(TypeCtrArg.LIST, lst, content_ordered=index is not None, attributes=_index_att(smallest))
        if index is not None:
            lst_flatten = flatten(lst)
            aux = auxiliary().replace_element_index(len(lst_flatten), index)
            if aux:  # this is the case if we need another variable to have a correct indexing
                self.arg(TypeCtrArg.INDEX, aux, attributes=[(TypeCtrArg.RANK, type_rank)] if type_rank else [])
                # below, should we replace ANY by a specific value (for avoiding interchangeable values)?
                auxiliary().extension_for_element(index, aux, {(v, v if 0 <= v < len(lst_flatten) else ANY) for v in index.dom})
                # functions.satisfy((index, aux) in {(v, v if 0 <= v < len(lst_flatten) else ANY) for v in index.dom}, no_comment_tags_extraction=True)
            else:
                self.arg(TypeCtrArg.INDEX, index, attributes=[(TypeCtrArg.RANK, type_rank)] if type_rank else [])
        if condition:
            self.arg(TypeCtrArg.CONDITION, condition)  # Condition.build_condition((TypeConditionOperator.EQ, value)))
        # self.arg(TypeCtrArg.VALUE, value)

    def min_possible_value(self):
        if isinstance(self.arguments[TypeCtrArg.LIST].content[0], int):
            return min(v for v in self.arguments[TypeCtrArg.LIST].content)
        return min(x.dom.smallest_value() for x in self.arguments[TypeCtrArg.LIST].content)

    def max_possible_value(self):
        if isinstance(self.arguments[TypeCtrArg.LIST].content[0], int):
            return max(v for v in self.arguments[TypeCtrArg.LIST].content)
        return max(x.dom.greatest_value() for x in self.arguments[TypeCtrArg.LIST].content)


class ConstraintElementMatrix(ConstraintWithCondition):
    def __init__(self, lst, index1, index2, value=None, start_row_index=0, start_col_index=0):
        super().__init__(TypeCtr.ELEMENT)
        self.matrix = lst
        self.arg(TypeCtrArg.MATRIX, matrix_to_string(lst), content_compressible=lst,  # side-effect use of content_compressible for matrix
                 attributes=([(TypeCtrArg.ST.START_ROW_INDEX, start_row_index)] if start_row_index else []) + (
                     [(TypeCtrArg.START_COL_INDEX, start_col_index)] if start_col_index else []))
        self.arg(TypeCtrArg.INDEX, [index1, index2], content_ordered=True)
        if value:
            self.arg(TypeCtrArg.CONDITION, Condition.build_condition((TypeConditionOperator.EQ, value)))
        # self.arg(TypeCtrArg.VALUE, value)

    def min_possible_value(self):
        if isinstance(self.matrix[0][0], int):
            return min(v for row in self.matrix for v in row)
        return min(x.dom.smallest_value() for row in self.matrix for x in row)

    def max_possible_value(self):
        if isinstance(self.matrix[0][0], int):
            return max(v for row in self.matrix for v in row)
        return max(x.dom.greatest_value() for row in self.matrix for x in row)


class ConstraintChannel(ConstraintUnmergeable):
    def __init__(self, list1, start_index1, list2, start_index2):
        super().__init__(TypeCtr.CHANNEL)
        assert list1 is not None
        if list2 is None:  # first variant of channel
            assert start_index2 == 0
            self.arg(TypeCtrArg.LIST, list1, content_ordered=True, attributes=_index_att(start_index1))
        elif len(list2) > 1:  # second variant of channel
            assert 1 < len(list1) <= len(list2)
            self.arg(TypeCtrArg.LIST, [list1, list2], content_ordered=True, lifted=True, attributes=_index_att(start_index1) + _index_att(start_index2))
        else:  # third variant of channel
            assert all(var.dom.is_binary() for var in list1) and len(list2) == 1
            self.arg(TypeCtrArg.LIST, list1, content_ordered=True, attributes=_index_att(start_index1))
            self.arg(TypeCtrArg.VALUE, list2)


''' Packing and Scheduling Constraints '''


class ConstraintNoOverlap(ConstraintUnmergeable):
    def __init__(self, origins, lengths, zero_ignored):
        super().__init__(TypeCtr.NO_OVERLAP)
        self.arg(TypeCtrArg.ORIGINS, "".join(["(" + ",".join(str(v) for v in t) + ")" for t in origins]) if isinstance(origins[0], tuple) else origins,
                 content_ordered=True)
        self.arg(TypeCtrArg.LENGTHS, "".join(["(" + ",".join(str(v) for v in t) + ")" for t in lengths]) if isinstance(lengths[0], tuple) else lengths,
                 content_ordered=True)
        if zero_ignored:
            self.attributes.append((TypeCtrArg.ZERO_IGNORED, zero_ignored))


class ConstraintCumulative(Constraint):  # TODO inheriting from ConstraintWithCondition instead? is this a pb?
    def __init__(self, origins, lengths, ends, heights, condition):
        super().__init__(TypeCtr.CUMULATIVE)
        self.arg(TypeCtrArg.ORIGINS, origins, content_ordered=True)
        self.arg(TypeCtrArg.LENGTHS, lengths, content_ordered=True)
        self.arg(TypeCtrArg.ENDS, ends, content_ordered=True)
        self.arg(TypeCtrArg.HEIGHTS, heights, content_ordered=True)
        self.arg(TypeCtrArg.CONDITION, condition)


class ConstraintBinPacking(ConstraintUnmergeable):
    def __init__(self, lst, sizes, *, limits=None, loads=None, condition=None):
        super().__init__(TypeCtr.BIN_PACKING)
        self.arg(TypeCtrArg.LIST, lst, content_ordered=True)
        self.arg(TypeCtrArg.SIZES, sizes, content_ordered=True)
        if limits is not None:
            assert isinstance(limits, list) and loads is None and condition is None
            self.arg(TypeCtrArg.LIMITS, limits, content_ordered=True)
        elif loads is not None:
            assert isinstance(loads, list) and limits is None and condition is None
            self.arg(TypeCtrArg.LOADS, loads, content_ordered=True)
        else:
            self.arg(TypeCtrArg.CONDITION, condition)


class ConstraintKnapsack(ConstraintWithCondition):
    def __init__(self, lst, weights, wcondition, profits, pcondition):
        super().__init__(TypeCtr.KNAPSACK)
        self.vars = lst
        self.profits = profits
        self.arg(TypeCtrArg.LIST, lst, content_ordered=True)
        self.arg(TypeCtrArg.WEIGHTS, weights, content_ordered=True)
        self.arg(TypeCtrArg.LIMIT, wcondition)  # temporarily, we use LIMIT (but will be replaced by CONDITION later)
        self.arg(TypeCtrArg.PROFITS, profits, content_ordered=True)
        self.arg(TypeCtrArg.CONDITION, pcondition)

    def min_possible_value(self):
        return sum(self.vars[i].dom.smallest_value() * self.profits[i] for i in len(self.vars))

    def max_possible_value(self):
        return sum(self.vars[i].dom.greatest_value() * self.profits[i] for i in len(self.vars))

    def close_to(self, other):
        return False


class ConstraintFlow(Constraint):  # TODO inheriting from ConstraintWithCondition instead?
    def __init__(self, lst, balance, arcs, weights, condition):
        super().__init__(TypeCtr.FLOW)
        self.arg(TypeCtrArg.LIST, lst, content_ordered=True)
        self.arg(TypeCtrArg.BALANCE, balance, content_ordered=True)
        self.arg(TypeCtrArg.ARCS, matrix_to_string(arcs), content_ordered=True)
        if weights is not None:
            self.arg(TypeCtrArg.WEIGHTS, weights, content_ordered=True)
            self.arg(TypeCtrArg.CONDITION, condition)


''' Constraints on Graphs'''


class ConstraintCircuit(Constraint):
    def __init__(self, variables, start_index, size):
        super().__init__(TypeCtr.CIRCUIT)
        if start_index != 0:
            self.attributes.append((TypeCtrArg.START_INDEX, start_index))
        self.arg(TypeCtrArg.LIST, variables, content_ordered=True)
        self.arg(TypeCtrArg.SIZE, size)


''' Elementary Constraints '''


class ConstraintClause(Constraint):
    def __init__(self, variables, phases):
        super().__init__(TypeCtr.CLAUSE)
        self.arg(TypeCtrArg.LIST, [str(v) if phases[i] else "not(" + str(v) + ")" for i, v in enumerate(variables)], content_ordered=True)


class ConstraintInstantiation(Constraint):
    def __init__(self, variables, values):
        super().__init__(TypeCtr.INSTANTIATION)
        assert len(variables) == len(values)
        self.arg(TypeCtrArg.LIST, variables, content_ordered=True)
        self.arg(TypeCtrArg.VALUES, values, content_ordered=True)


''' Slide Constraints (when posted directly) '''


class ConstraintSlide(ConstraintUnmergeable):
    def __init__(self, variables, slide_expression, circular=None, offset=None, collect=None):
        super().__init__(TypeCtr.SLIDE)
        assert slide_expression is not None  # the meta-constraint is defined directly by the user
        variables = list(variables) if isinstance(variables, tuple) else variables
        if circular is True:
            self.attributes.append((TypeXML.CIRCULAR, "true"))
        n_offsets = 0 if offset is None else 1 if isinstance(offset, int) else len(offset)
        n_collects = 0 if collect is None else 1 if isinstance(collect, int) else len(collect)
        assert n_offsets == 0 or n_collects == 0 or n_offsets == n_collects
        k = max(1, n_offsets, n_collects)
        if k == 1:  # only one list
            atts = ([(TypeXML.OFFSET, offset)] if offset is not None and offset != 1 else []) + \
                   ([(TypeXML.COLLECT, collect)] if collect is not None and collect != 1 else [])
            self.arg(TypeCtrArg.LIST, flatten(variables), content_ordered=True, attributes=atts)
        else:
            assert isinstance(variables, list) and len(variables) == k and all(isinstance(l, (list, tuple)) for l in variables)
            atts = [
                ([(TypeXML.OFFSET, offset[i])] if offset and offset[i] != 1 else [])
                + ([(TypeXML.COLLECT, collect[i])] if collect and collect[i] != 1 else [])
                for i in range(k)]
            self.arg(TypeCtrArg.LIST, variables, lifted=True, content_ordered=True, attributes=atts)
        self.arg(TypeCtrArg.INTENTION, slide_expression)  # possibly transformed into extension later in xcsp


''' PartialConstraints and ScalarProduct '''


class PartialConstraint:  # constraint whose condition has not been given such as 'Sum', 'Count', 'Element', 'maximum', etc.
    def __init__(self, constraint):
        self.constraint = constraint

    def add_condition(self, operator, right_operand):
        if isinstance(right_operand, (int, Variable)):
            return ECtr(self.constraint.set_condition(operator, right_operand))
        # TODO : which kind of right operand is authorized? just a partial sum?
        assert isinstance(self.constraint, ConstraintSum)
        pc = PartialConstraint.combine_partial_objects(self, TypeNode.SUB, right_operand)  # the 'complex' right operand is moved to the left
        return ECtr(pc.constraint.set_condition(operator, 0))

    def _simplify_with_auxiliary_variables(self, other):
        if isinstance(other, (int, Variable)):
            return other
        if isinstance(other, Node):
            return auxiliary().replace_node(other)
        assert isinstance(other, (ScalarProduct, PartialConstraint)), "Wrong type for " + str(other)
        if isinstance(self.constraint, ConstraintSum) and (isinstance(other, ScalarProduct) or isinstance(other.constraint, ConstraintSum)):
            return other
        assert isinstance(self.constraint, ConstraintWithCondition) and isinstance(other.constraint, ConstraintWithCondition), "Wrong type for " + str(
            other.constraint) + " or/and " + str(self.constraint)
        return auxiliary().replace_partial_constraint(other)

    def _simplify_operation(self, other):
        assert isinstance(self.constraint, ConstraintWithCondition)
        if isinstance(other, int):
            return auxiliary().replace_partial_constraint(self), other
        if isinstance(self.constraint, ConstraintSum) and (not isinstance(other, PartialConstraint) or isinstance(other.constraint, ConstraintSum)):
            return None  # we can combine partial sums and terms
        if not isinstance(self.constraint, ConstraintSum) and not isinstance(other, PartialConstraint):
            return auxiliary().replace_partial_constraint(self), other
        assert isinstance(other.constraint, ConstraintWithCondition)
        return auxiliary().replace_partial_constraint(self), auxiliary().replace_partial_constraint(other)

    def __eq__(self, other):
        if isinstance(self.constraint, ConstraintElement) and is_1d_list(other, int):
            tab = self.constraint.arguments[TypeCtrArg.LIST].content
            idx = self.constraint.arguments[TypeCtrArg.INDEX].content
            assert is_matrix(tab, Variable) and len(tab[0]) == len(other)
            return [tab[idx][i] == other[i] for i in range(len(other))]
        other = self._simplify_with_auxiliary_variables(other)
        if isinstance(self.constraint, (ConstraintElement, ConstraintElementMatrix)) and isinstance(other, (int, Variable)):
            if isinstance(self.constraint, ConstraintElement):
                arg = self.constraint.arguments[TypeCtrArg.LIST]
                arg.content = flatten(arg.content)  # we need to flatten now because it has not been done before
            # return ECtr(self.constraint.set_value(other))  # only value must be replaced for these constraints
            return ECtr(self.constraint.set_condition(TypeConditionOperator.EQ, other))  # the condition must be replaced
        return self.add_condition(TypeConditionOperator.EQ, other)
        # pair = self._simplify_with_auxiliary_variables(other)
        # return Node.build(TypeNode.EQ, pair) if pair else self.add_condition(TypeConditionOperator.EQ, other)

    def __ne__(self, other):
        return self.add_condition(TypeConditionOperator.NE, self._simplify_with_auxiliary_variables(other))

    def __lt__(self, other):
        return self.add_condition(TypeConditionOperator.LT, self._simplify_with_auxiliary_variables(other))

    def __le__(self, other):
        return self.add_condition(TypeConditionOperator.LE, self._simplify_with_auxiliary_variables(other))

    def __ge__(self, other):
        return self.add_condition(TypeConditionOperator.GE, self._simplify_with_auxiliary_variables(other))

    def __gt__(self, other):
        return self.add_condition(TypeConditionOperator.GT, self._simplify_with_auxiliary_variables(other))

    def __add__(self, other):
        pair = self._simplify_operation(other)
        return Node.build(TypeNode.ADD, pair) if pair else PartialConstraint.combine_partial_objects(self, TypeNode.ADD, other)

    def __sub__(self, other):
        pair = self._simplify_operation(other)
        return Node.build(TypeNode.SUB, pair) if pair else PartialConstraint.combine_partial_objects(self, TypeNode.SUB, other)

    def __mul__(self, other):
        if not isinstance(other, int):
            pair = self._simplify_operation(other)
            return Node.build(TypeNode.MUL, pair) if pair else PartialConstraint.combine_partial_objects(self, TypeNode.MUL, other)
        if not isinstance(self.constraint, ConstraintSum):
            return Node.build(TypeNode.MUL, self._simplify_operation(other))
        # we have a ConstraintSum (self) and an integer (other)

        args = self.constraint.arguments
        if TypeCtrArg.COEFFS not in args:  # or only 1 as coeffs? TODO
            return auxiliary().replace_partial_constraint(self) * other
        cs = args[TypeCtrArg.COEFFS].content if TypeCtrArg.COEFFS in args else [1] * len(args[TypeCtrArg.LIST].content)
        value = args[TypeCtrArg.CONDITION]
        del args[TypeCtrArg.CONDITION]  # we delete and put back below this argument so as to have arguments in the right order
        self.constraint.arg(TypeCtrArg.COEFFS, [c * other for c in cs])
        args[TypeCtrArg.CONDITION] = value
        return self

    def __rmul__(self, other):
        return PartialConstraint.__mul__(self, other)

    def __floordiv__(self, other):
        if isinstance(other, PartialConstraint):
            other = auxiliary().replace_partial_constraint(other)
        return Node.build(TypeNode.DIV, auxiliary().replace_partial_constraint(self), other)

    def __mod__(self, other):
        if isinstance(other, PartialConstraint):
            other = auxiliary().replace_partial_constraint(other)
        return Node.build(TypeNode.MOD, auxiliary().replace_partial_constraint(self), other)

    def __getitem__(self, i):
        assert isinstance(self.constraint, ConstraintElement), "\nBad form. Did you forget to use parentheses? " + \
                                                               "For example, you must write (x[0] == x[1])  | (x[0] == x[2]) instead of (x[0] == x[1])  or (x[0] == x[2])"
        lst = self.constraint.arguments[TypeCtrArg.LIST].content
        assert is_matrix(lst), "Variables in element constraint must be in the form of matrix"
        index = self.constraint.arguments[TypeCtrArg.INDEX].content
        if isinstance(i, Variable):
            assert is_matrix(lst), "Variables in element constraint must be in the form of matrix"
            self.constraint = ConstraintElementMatrix(lst, index, i)
        elif isinstance(i, int):
            self.constraint = ConstraintElement(lst[:, i], index=index)
        elif isinstance(i, Node):
            self.constraint = ConstraintElementMatrix(lst, index, auxiliary().replace_node(i, values=range(max(len(row) for row in lst))))
        return self

    def __str__(self):
        c = self.constraint
        # assert len(c.arguments) == 2
        s = str(c.name) + "("
        for k, v in c.arguments.items():
            s = s + str(v) + ","
        return s[:-1] + ")"
        # return s + str(compact(c.arguments[TypeCtrArg.LIST].content)) + ")"

    @staticmethod
    def combine_partial_objects(obj1, operator, obj2):  # currently, only partial sums can be combined
        assert operator in {TypeNode.ADD, TypeNode.SUB}
        if isinstance(obj1, ScalarProduct):
            obj1 = PartialConstraint(ConstraintSum(obj1.variables, obj1.coeffs, None))  # to be sure to have at least one PartialConstraint
        assert isinstance(obj1, PartialConstraint) or isinstance(obj2, PartialConstraint)
        if obj2 is None:
            return obj1
        inverted, obj1, obj2 = (False, obj1, obj2) if isinstance(obj1, PartialConstraint) else (True, obj2, obj1)
        pair = obj2.var_val_if_binary_type(TypeNode.MUL) if isinstance(obj2, Node) else None
        if pair:
            obj2 = PartialConstraint(ConstraintSum([pair[0]], [pair[1]], None))
        elif isinstance(obj2, (Variable, Node)):
            obj2 = PartialConstraint(ConstraintSum([obj2], [1], None))
        elif isinstance(obj2, ScalarProduct):
            obj2 = PartialConstraint(ConstraintSum(obj2.variables, obj2.coeffs, None))
        elif isinstance(obj2, int):
            aux = auxiliary().replace_partial_constraint(obj1)
            return aux + obj2 if operator is TypeNode.ADD else aux - obj2
        elif not isinstance(obj2, PartialConstraint):
            error("The type of the operand of the partial constraint is wrong as it is " + str(type(obj2)))
        obj1, obj2 = (obj1, obj2) if not inverted else (obj2, obj1)  # we invert back
        assert isinstance(obj1, PartialConstraint) and isinstance(obj2, PartialConstraint)
        assert isinstance(obj1.constraint, ConstraintSum) and isinstance(obj2.constraint, ConstraintSum), str(type(obj1.constraint)) + " " + str(
            type(obj2.constraint))
        args1, args2 = obj1.constraint.arguments, obj2.constraint.arguments
        vs1, vs2 = args1[TypeCtrArg.LIST].content, args2[TypeCtrArg.LIST].content
        cs1 = args1[TypeCtrArg.COEFFS].content if TypeCtrArg.COEFFS in args1 else [1] * len(vs1)
        cs2 = args2[TypeCtrArg.COEFFS].content if TypeCtrArg.COEFFS in args2 else [1] * len(vs2)
        cs2 = [-c for c in cs2] if operator == TypeNode.SUB else cs2
        return PartialConstraint(ConstraintSum(vs1 + vs2, cs1 + cs2, None))


class ScalarProduct:
    def __init__(self, variables, coefficients):
        variables = list(variables) if isinstance(variables, tuple) else variables
        coefficients = list(coefficients) if isinstance(coefficients, tuple) else coefficients
        assert isinstance(variables, list) and isinstance(coefficients, (int, list, range)), str(variables) + " " + str(coefficients)
        self.variables = flatten(variables)  # for example, in order to remove None occurrences
        self.coeffs = flatten([coefficients] * len(variables) if isinstance(coefficients, int) else coefficients)
        assert len(self.variables) == len(self.coeffs), str(self.variables) + " " + str(self.coeffs)

    def _combine_with(self, operator, right_operand):
        pc = PartialConstraint(ConstraintSum(self.variables, self.coeffs, None))
        if isinstance(right_operand, Node) and right_operand.var_val_if_binary_type(TypeNode.MUL):
            return pc.add_condition(operator, right_operand)
        if operator == TypeConditionOperator.LT:
            return pc < right_operand
        if operator == TypeConditionOperator.LE:
            return pc <= right_operand
        if operator == TypeConditionOperator.GE:
            return pc >= right_operand
        if operator == TypeConditionOperator.GT:
            return pc > right_operand
        if operator == TypeConditionOperator.EQ:
            return pc == right_operand
        if operator == TypeConditionOperator.NE:
            return pc != right_operand
        assert False

    def __lt__(self, other):
        return self._combine_with(TypeConditionOperator.LT, other)

    def __le__(self, other):
        return self._combine_with(TypeConditionOperator.LE, other)

    def __ge__(self, other):
        return self._combine_with(TypeConditionOperator.GE, other)

    def __gt__(self, other):
        return self._combine_with(TypeConditionOperator.GT, other)

    def __eq__(self, other):
        return self._combine_with(TypeConditionOperator.EQ, other)

    def __ne__(self, other):
        return self._combine_with(TypeConditionOperator.NE, other)

    def __add__(self, other):
        return PartialConstraint.combine_partial_objects(self, TypeNode.ADD, other)

    def __sub__(self, other):
        return PartialConstraint.combine_partial_objects(self, TypeNode.SUB, other)

    def __floordiv__(self, other):
        pc = PartialConstraint(ConstraintSum(self.variables, self.coeffs, None))
        if isinstance(other, PartialConstraint):
            other = auxiliary().replace_partial_constraint(other)
        return Node.build(TypeNode.DIV, auxiliary().replace_partial_constraint(pc), other)

    def __mod__(self, other):
        pc = PartialConstraint(ConstraintSum(self.variables, self.coeffs, None))
        if isinstance(other, PartialConstraint):
            other = auxiliary().replace_partial_constraint(other)
        return Node.build(TypeNode.MOD, auxiliary().replace_partial_constraint(pc), other)


class _Auxiliary:
    cache_ints = dict()
    cache_nodes = dict()

    def __init__(self):
        self._introduced_variables = []
        self._collected_constraints = []
        self._collected_raw_constraints = []
        self._collected_extension_for_element_constraints = []
        self.prefix = "aux_gb"
        self.cache = []

    def __clear(self):
        self._introduced_variables = []
        self._collected_constraints = []
        self.cache = []

    def __replace(self, obj, dom, *, systematically_append_obj=True):
        assert dom.get_type() == TypeVar.INTEGER
        index = len(self._introduced_variables)
        name = self.prefix + "[" + str(index) + "]"
        var = VariableInteger(name, dom)
        Variable.name2obj[name] = var
        if index == 0:
            self._introduced_variables = EVarArray([var], self.prefix, self.prefix + "[i] is the ith auxiliary variable having been automatically introduced")
        else:
            self._introduced_variables.extend_with(var)
        if systematically_append_obj or obj:
            self._collected_constraints.append((obj, var))
        return var

    def n_introduced_variables(self):
        return len(self._introduced_variables)

    def replace_partial_constraint(self, pc):
        assert isinstance(pc, PartialConstraint)
        if not options.dontuseauxcache:
            for c, x in self.cache:
                if pc.constraint.equal_except_condition(c):
                    # if functions.protect().execute(pc.constraint.equal_except_condition(c)):
                    # if functions.protect().execute(pc.constraint == c):
                    return x
        else:  # partial use
            if len(self.cache) > 0:
                c, x = self.cache[0]
                if pc.constraint.equal_except_condition(c):
                    return x
            if len(self.cache) > 1:
                c, x = self.cache[-1]
                if pc.constraint.equal_except_condition(c):
                    return x

        if isinstance(pc.constraint, (ConstraintMinimum, ConstraintMaximum)):
            values = possible_range(pc.constraint.all_possible_values())
        else:
            values = range(pc.constraint.min_possible_value(), pc.constraint.max_possible_value() + 1)
        aux = self.__replace(pc, Domain(values))  # range(pc.constraint.min_possible_value(), pc.constraint.max_possible_value() + 1)))
        self.cache.append((pc.constraint, aux))
        return aux

    def replace_constraint_with_condition(self, cc):
        assert isinstance(cc, ECtr) and isinstance(cc.constraint, ConstraintWithCondition)
        cond = cc.constraint.arguments[TypeCtrArg.CONDITION].content
        op, k = cond.operator, cond.right_operand()
        aux = self.__replace(None, Domain(range(cc.constraint.min_possible_value(), cc.constraint.max_possible_value() + 1)),
                             systematically_append_obj=False)
        cc.constraint.set_condition(TypeConditionOperator.EQ, aux)
        self._collected_raw_constraints.append(cc)
        return functions.expr(op, aux, k)

    def replace_constant(self, cst):
        assert isinstance(cst, int)
        return self.__replace(cst, Domain({cst}), systematically_append_obj=False)

    def replace_node(self, node, *, values=None):
        assert isinstance(node, Node)
        if values is None:  # otherwise, for the moment, this parameter is used when this is a range for an Element constraint
            values = node.possible_values()
            values = {v for v in values} if len(values) <= 2 else values  # in order to avoid having a range for just 1 or 2 values
        return self.__replace(node, Domain(values))

    def replace_partial_constraint_and_constraint_with_condition_and_possibly_node(self, term, *, node_too=False, values=None):
        # TODO: for the moment, values is only used for a node
        if isinstance(term, PartialConstraint):
            return self.replace_partial_constraint(term)
        if isinstance(term, ECtr):
            return self.replace_constraint_with_condition(term)
        if node_too and isinstance(term, Node):
            return self.replace_node(term, values=values)
        return term

    def replace_partial_constraints_and_constraints_with_condition_and_possibly_nodes(self, terms, *, nodes_too=False, values=None):
        assert isinstance(terms, list)
        for i, term in enumerate(terms):
            terms[i] = self.replace_partial_constraint_and_constraint_with_condition_and_possibly_node(term, node_too=nodes_too, values=values)
        return terms

    def replace_element_index(self, length, index):
        if all(0 <= v < length for v in index.dom):
            return None
        values = possible_range({v for v in index.dom if 0 <= v < length})
        return self.__replace(None, Domain(values), systematically_append_obj=False)

    def replace_int(self, v):
        assert isinstance(v, int)
        # if v in _Auxiliary.cache_ints:  # for the moment, we do not use it because it may cause some problems with some constraints (similar variables)
        #     return _Auxiliary.cache_ints[v]
        aux = self.__replace(None, Domain(v), systematically_append_obj=False)
        # _Auxiliary.cache_ints[v] = aux
        return aux

    def replace_ints(self, lst):
        return curser.cp_array(self.replace_int(v) if isinstance(v, int) else v for v in lst)

    def normalize_list(self, lst):
        return curser.ListVar([v if isinstance(v, Variable) else self.replace_int(v) if isinstance(v, int) else self.replace_node(v) for v in lst])

    def extension_for_element(self, index, aux, table):
        self._collected_extension_for_element_constraints.append((index, aux, table))

    def collected(self):
        t = self._collected_constraints
        self._collected_constraints = []
        return t

    def raw_collected(self):
        t = self._collected_raw_constraints
        self._collected_raw_constraints = []
        return t

    def collected_extension_for_element(self):
        t = self._collected_extension_for_element_constraints
        self._collected_extension_for_element_constraints = []
        return t


def auxiliary():
    if not hasattr(auxiliary, "obj") or auxiliary.obj is None:
        auxiliary.obj = _Auxiliary()
    return auxiliary.obj


def global_indirection(c):
    pc = None
    if options.usemeta:
        return None  # to force using meta-constraints
    if isinstance(c, ConstraintInstantiation):  # we transform instantiation into a conjunction (Node)
        lst = c.arguments[TypeCtrArg.LIST].content
        values = c.arguments[TypeCtrArg.VALUES].content
        assert len(lst) == len(values)
        return functions.conjunction(lst[i] == values[i] for i in range(len(lst)))
    if isinstance(c, ConstraintWithCondition):
        condition = c.arguments[TypeCtrArg.CONDITION].content
        c.arguments[TypeCtrArg.CONDITION] = None
        pc = PartialConstraint(c)
    if isinstance(c, ConstraintElement):
        index = c.arguments[TypeCtrArg.INDEX].content
        length = len(c.arguments[TypeCtrArg.LIST].content)
        aux = auxiliary().replace_element_index(length, index)
        if aux:  # this is the case if we need another variable to have a correct indexing
            c.arguments[TypeCtrArg.INDEX].content = aux
            # below, should we replace ANY by a specific value (for avoid interchangeable values)?
            auxiliary().extension_for_element(index, aux, {(v, v if 0 <= v < length else ANY) for v in index.dom})
            # functions.satisfy((index, aux) in {(v, v if 0 <= v < length else ANY) for v in index.dom})
    if isinstance(c, ConstraintAllDifferent):
        lst = c.arguments[TypeCtrArg.LIST].content
        pc = PartialConstraint(ConstraintNValues(lst, c.arguments[TypeCtrArg.EXCEPT].content, None))
        condition = Condition.build_condition((TypeConditionOperator.EQ, len(lst)))
    if isinstance(c, ConstraintAllEqual):
        pc = PartialConstraint(ConstraintNValues(c.arguments[TypeCtrArg.LIST].content, None, None))
        condition = Condition.build_condition((TypeConditionOperator.EQ, 1))
    if pc is None:
        warning("You use a global constraint in a complex expression.\n" +
                "\tHowever, this constraint cannot be externalized by introducing an auxiliary variable.\n" +
                "\tHence a meta-constraint function (Or, And, Not, IfThen, IfThenElse, Iff) is automatically called.\n" +
                "\tCheck that it is relevant, or modify your model.\n")
        return None
    return Node.build(condition.operator, auxiliary().replace_partial_constraint(pc), condition.right_operand())


def manage_global_indirection(*args):
    assert len(args) > 1
    if any(isinstance(arg, EMetaCtr) for arg in args):
        return None

    msg = "A subexpression node is evaluated as a Boolean (False or True)" + \
          "\n\tIt is likely a problem with the use of logical operators" + \
          "\n\tFor example, you must write (x[0] == x[1])  | (x[0] == x[2]) instead of (x[0] == x[1])  or (x[0] == x[2])" + \
          "\n\tSee also the end of section about constraint Intension in chapter 'Twenty popular constraints' of the guide\n"

    t = []
    for arg in args:
        if arg is True:  # means that we must have a unary subexpression of the form 'x in S' in a more general expression
            error_if(len(curser.queue_in) == 0, msg)
            (values, x) = curser.queue_in.pop()
            arg = functions.belong(x, values)
        elif arg is False:  # means that we must have in a more general expression:
            # either a unary subexpression of the form 'x not in S'
            # or a nogood of the form x != t where x a list of variables and t a list of values
            error_if(len(curser.queue_in) == 0, msg)
            (values, x) = curser.queue_in.pop()
            if isinstance(x, list) and len(x) > 1 and isinstance(values, list) and len(values) == 1:
                assert len(x) == len(values[0])
                arg = functions.disjunction(x[i] != values[0][i] for i in range(len(x)))
            else:
                arg = functions.not_belong(x, values)
        elif isinstance(arg, ECtr):
            gi = global_indirection(arg.constraint)
            if gi is None:
                return None
            arg = gi
        t.append(arg)
    return tuple(t)
