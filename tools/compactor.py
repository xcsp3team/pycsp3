import re
from collections import defaultdict

from pycsp3.classes.auxiliary.ptypes import TypeCtrArg
from pycsp3.classes.entities import CtrEntities, ObjEntities, AnnEntities, ESlide, EGroup, VarEntities
from pycsp3.classes.main.variables import Variable
from pycsp3.tools.utilities import flatten, is_containing, is_1d_list
from pycsp3.dashboard import options


class SequenceOfSuccessiveVariables:
    def __init__(self, x):
        self.firstVar, self.posMod, self.stopMod, self.arrayVar = x, -1, 0, VarEntities.varToEVarArray[x]
        if '[' in x.id:
            pos = x.id.index("[")
            self.prefix, self.suffix = x.id[:pos], x.id[pos:]
            self.starts = [int(v) for v in re.split("\]\[", self.suffix[1:-1])]  # the indexes of the first variable (in case of an array)

    def differ_just_at(self, t):
        pos = -1
        for i in range(len(self.starts)):
            if self.starts[i] != t[i]:
                if pos == -1:
                    pos = i
                else:
                    return -1  # at least two differences
        return pos

    def can_be_extended_with(self, id):
        x = Variable.name2obj[id]
        if not x.indexes or x.prefix != self.prefix:  # meaning x is not from an array
            return None
        t = x.indexes
        pos = self.differ_just_at(t)
        if pos == -1:
            return False
        if self.posMod == -1:
            if t[pos] != self.starts[pos] + 1:
                return False
            self.posMod, self.stopMod = pos, t[pos]
        else:
            if pos != self.posMod or t[pos] != self.stopMod + 1:
                return False
            self.stopMod = t[pos]
        return True

    def __repr__(self):
        s = self.prefix
        for i, value in enumerate(self.starts):
            if self.posMod != i:
                s += "[" + str(value) + "]"
            elif self.starts[self.posMod] == 0 and self.stopMod == self.arrayVar.size[self.posMod] - 1:
                s += "[]"
            else:
                s += "[" + str(value) + ".." + str(self.stopMod) + "]"
        return s


def build_partition(variables, preserve_order):
    def _simple_partition(vars):
        # if isinstance(vars, list) and len(vars) == 1 and isinstance(vars[0], list): vars = vars[0]  # TODO never reached. We can remove that ?
        harvest = []  # variables (and other objects) are collected to compute the complete expanded form (string) with their names (values)
        arrays = []  # arrays encountered and recorded all along the process
        others = []  # list collecting any stand-alone variables or any kind of objects that are not variables from arrays
        arrays_partition = defaultdict(list)  # a dict for partitioning variables according to arrays

        def update(z):
            harvest.append(z)
            if isinstance(z, Variable) and z.indexes:  # if z from an array
                va = VarEntities.varToEVarArray[z]
                arrays_partition[va].append(z)
                if va not in arrays:
                    arrays.append(va)
                elif arrays[-1][0] is not va:
                    return False
            else:  # if z is not DELETED:  # it can be a Variable, but also an integer, a Node, a state (for an automaton).
                others.append(z)
            return True

        for x in vars:
            if isinstance(x, list):
                for y in x:
                    assert isinstance(y, Variable), "a variable is expected in the inner list. Problem with " + str(
                        y)  # relaxing this by a test 'not isinstance(y,list)' ?
                    if not update(y):
                        return None  # because variables from different arrays are mixed
            else:
                if not update(x):
                    return None  # because variables from different arrays are mixed
        # arrays = sorted(arrays, key=attrgetter('id'))  # TODO useless. No impact at all. We can remove that, right?
        return arrays, others, arrays_partition, " ".join(str(x) for x in harvest)

    def _complex_partition(vars):
        harvest = []  # variables (and other objects) are collected to compute the complete expanded form (string) with their names (values)
        partition = []  # the partition built from successive identified parts
        part = []  # the current part being built (before being added to the partition)
        no_arrays = False

        def update(z):
            nonlocal part, no_arrays
            harvest.append(z)
            if isinstance(z, Variable) and z.indexes and not z.inverse and not z.negation:
                no_arrays = False
                if len(part) == 0 or VarEntities.varToEVarArray[z].id == VarEntities.varToEVarArray[part[-1]].id:
                    part.append(z)
                else:
                    partition.append(part)
                    part = [z]
            else:  # z is not DELETED:
                partition.append(part)
                partition.append(z)
                part = []

        for x in vars:
            if isinstance(x, list):
                for y in x:
                    update(y)
            else:
                update(x)
        if len(part) > 0:
            partition.append(part)
        if no_arrays:
            return None, None
        return partition, " ".join(str(x) for x in harvest)

    if not preserve_order:
        simple_partition = _simple_partition(variables)  # we make an attempt to build a simple partition
    else:
        simple_partition = None
    if simple_partition:
        arrays, others, arrays_partition, complete_expanded_form = simple_partition
        if len(arrays) == 0:
            return None, None
        # Here, as the order is not a problem, we can below build the partition by means of the returned structure
        return [arrays_partition[a] for a in arrays] + [others], complete_expanded_form
    else:
        return _complex_partition(variables)


def _complex_compact(variables):
    compact_form = ""
    sequence = None
    for x in variables:
        if sequence is None:
            sequence = SequenceOfSuccessiveVariables(x)
        elif not sequence.can_be_extended_with(x.id):
            compact_form += str(sequence) if compact_form == "" else " " + str(sequence)
            sequence = SequenceOfSuccessiveVariables(x)
    compact_form += str(sequence) if compact_form == "" else " " + str(sequence)
    return compact_form


''' We try to identify a compact form corresponding to a unique token (note that variables are from the same array, by construction) '''


def _simple_compact(variables):
    var_array = VarEntities.varToEVarArray[variables[0]]
    mins, maxs = [float('inf')] * len(var_array.size), [float('-inf')] * len(var_array.size)
    for x in variables:
        for i, v in enumerate(x.indexes):
            mins[i] = min(mins[i], v)
            maxs[i] = max(maxs[i], v)
    # Check the size
    size = 1
    for i in range(len(mins)):
        size *= maxs[i] - mins[i] + 1
    if size != len(variables):
        return None  # because it means that we didn't succeed in having a simple compact form (i.e., a unique token)

    compact_form = var_array.id
    for i in range(len(mins)):
        compact_form += "["
        if (mins[i], maxs[i]) != (0, var_array.size[i] - 1):
            compact_form += str(mins[i]) if mins[i] == maxs[i] else str(mins[i]) + ".." + str(maxs[i])
        compact_form += "]"
    return compact_form


def _expand(compact_form):
    assert " " not in compact_form, "The specified string must correspond to a single token; bad form : " + compact_form
    if compact_form[-1] == ")":
        return compact_form  # // this means that we have an expression (predicate) here
    if "[" not in compact_form:
        return compact_form
    pos = compact_form.index("[")
    prefix, suffix = compact_form[:pos], compact_form[pos:]
    tokens = [int(v) if v.isdigit() else v for v in re.split("\]\[", suffix[1:-1])]
    var_array = VarEntities.prefixToEVarArray[prefix]
    assert var_array, "Pb with " + compact_form
    assert len(var_array.size) == len(tokens)
    mins, maxs, sizes = [0] * len(tokens), [0] * len(tokens), [0] * len(tokens)
    for i, value in enumerate(tokens):
        if isinstance(value, int):
            mins[i] = maxs[i] = value
        elif value == "":
            mins[i] = 0
            maxs[i] = var_array.size[i] - 1
        else:
            spl = value.split("..")
            mins[i], maxs[i] = int(spl[0]), int(spl[1])
        sizes[i] = maxs[i] - mins[i] + 1

    var_names = flatten(Variable.build_names_array(prefix, sizes, mins))
    return " ".join(s for s in var_names)


def compact(variables, *, preserve_order=False, group_args=False):
    if not isinstance(variables, list):
        return variables
    if group_args is False and len(variables) < 3:
        return variables
    partition, complete_expanded_form = build_partition(variables, preserve_order)
    if partition is None:
        return variables
    t = []
    for part in partition:
        if isinstance(part, list):
            if not is_1d_list(part, Variable):
                t.extend(part)
            else:
                if not preserve_order:
                    part = sorted(part, key=lambda x: [int(v) for v in re.split("\]\[", x.id[x.id.index("[") + 1:-1])])
                if len(part) > 2:
                    compact = _simple_compact(part)
                    if compact is None:
                        t.append(_complex_compact(part))
                    else:
                        if preserve_order:
                            expand = " ".join([_expand(e) for e in compact.split()])
                            if expand not in complete_expanded_form:
                                t.append(_complex_compact(part))
                            else:
                                t.append(compact)
                        else:
                            t.append(compact)
                else:
                    t.extend(part)
        else:
            t.append(part)
    return " ".join(str(s) for s in t)


def _compact_values(values, limit):
    if options.dontcompactvalues:
        return values
    assert isinstance(values, list) and len(values) > 0, type(values)
    l = []
    i = 0
    last = values[0]
    while True:
        before = i
        while i < len(values) and values[i] == last:
            i += 1
        nb = i - before
        if nb >= limit:
            l.append(str(last) + "x" + str(nb))
        else:
            for _ in range(nb):
                l.append(last)
        if i == len(values):
            break
        last = values[i]
    return l


def _compact_constraint_arguments(arguments):
    for arg in list(arguments.values()):
        if isinstance(arg.content, list) and len(arg.content) > 0 and arg.content_compressible:
            if not isinstance(arg.content[0], list):  # It is only one list
                if isinstance(arg.content[0], int) and str(arg.name) in ["coeffs", "values", "sizes", "lengths", "heights", "weights", "profits", "balance"]:
                    # TODO still other arguments to be added?
                    arg.content = _compact_values(arg.content, 3)
                else:
                    arg.content = compact(arg.content, preserve_order=arg.content_ordered)
            elif arg.lifted is True:
                arg.content = [compact(l, preserve_order=arg.content_ordered) for l in arg.content]
        elif arg.name == TypeCtrArg.MATRIX:  # Special case for matrix
            # sc = None if is_containing(arg.content, int) else _simple_compact(flatten(arg.content))
            sc = None if is_containing(arg.content_compressible, int) else _simple_compact(flatten(arg.content_compressible))
            arg.content = sc if sc is not None else arg.content


def _compact_constraint_group(group):
    preserve_order = False
    cnt = 0
    if isinstance(group.abstraction, dict):
        for key, value in group.abstraction.items():
            if "%" in str(value):
                cnt += 1
            argument = group.entities[0].constraint.arguments[key]
            if argument.content_compressible:
                if "%" not in str(value):
                    if key == TypeCtrArg.MATRIX:  # Special case for matrix
                        sc = None if is_containing(argument.content_compressible, int) else _simple_compact(flatten(argument.content_compressible))
                        group.abstraction[key] = sc if sc is not None else group.abstraction[key]
                    else:
                        group.abstraction[key] = compact(value, preserve_order=argument.content_ordered)
                elif argument.content_ordered is True:
                    preserve_order = True
    else:
        preserve_order = True
    if cnt > 1:
        preserve_order = True
    group.original_all_args = [aa for aa in group.all_args]  # useful when reasoning to build the meta-constraint 'slide'
    for i in range(len(group.all_args)):
        group.all_args[i] = compact(group.all_args[i], preserve_order=preserve_order, group_args=True)


def _compact_forms_recursive(entities):
    for e in entities:
        if e is not None:
            if hasattr(e, "entities"):
                if isinstance(e, EGroup):
                    _compact_constraint_group(e)
                elif isinstance(e, ESlide):
                    if len(e.scope) > 0:
                        e.scope = compact(e.scope)
                    _compact_forms_recursive(e.entities)
                else:
                    _compact_forms_recursive(e.entities)
            elif e.constraint is not None:
                _compact_constraint_arguments(e.constraint.arguments)


def build_compact_forms():
    _compact_forms_recursive(CtrEntities.items)
    _compact_forms_recursive(ObjEntities.items)
    _compact_forms_recursive(AnnEntities.items)
