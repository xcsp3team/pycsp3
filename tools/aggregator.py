import re
from collections import OrderedDict

from pycsp3.classes.auxiliary.ptypes import TypeCtrArg
from pycsp3.classes.auxiliary.conditions import Condition
from pycsp3.classes.entities import CtrEntities, ECtr, ECtrs, EMetaCtr, EGroup, EBlock, EToGather, ESlide, EToSatisfy, TypeNode
from pycsp3.classes.main.constraints import ConstraintIntension, Diffs, ConstraintInstantiation
from pycsp3.classes.main.variables import Variable
from pycsp3.tools.utilities import error
from pycsp3.dashboard import options

LIMIT_FOR_VAR_ARGS = 3

_in_slide = False


def switch_limit_for_var_args():
    global _in_slide

    _in_slide = not _in_slide


def _limit_for_var_args(from_slide):
    if from_slide:
        return float('inf')
    return LIMIT_FOR_VAR_ARGS


def build_similar_constraints():
    detecting_groups_recursively(CtrEntities.items)
    building_groups_recursively(CtrEntities.items)
    canonizing_groups_and_blocks(CtrEntities.items)
    if not options.mini:
        recognizing_instantiations(CtrEntities.items)


# Phase 1: Detecting groups of similar constraints

def detecting_groups_recursively(ctr_entities):
    def _detecting_groups(entities):
        flags = [False] * len(entities)  # indicate (indexes of) constraints that are similar at a given moment (see intern loop)
        removal = False
        groups = []
        for i, e1 in enumerate(entities):
            if flags[i] or e1 is None or isinstance(e1, EGroup):
                continue
            Diffs.reset()
            group = EGroup()  # group of similar constraints tried to be built
            group.entities.append(e1)  # first constraint of the new group
            for j in range(i + 1, len(entities)):
                e2 = entities[j]
                if flags[j] is False and e2 is not None and not isinstance(e2, EGroup):
                    diffs = e2.constraint.close_to(e1.constraint)
                    # if diffs is None:
                    #     flags[j] = True
                    #     entities[j] = None
                    #     removal = True
                    if diffs is not False:
                        diffs.merge()  # merging flags of two lists, indicating if the length of argument contents is different
                        group.entities.append(e2)  # adding the constraint to the new group
                        flags[j] = True  # to avoid processing it again
                        entities[j] = None  # to discard this constraint (since it is now in a group)
                        removal = True
            if len(group.entities) > 1:
                group.diff_argument_names = Diffs.fusion.argument_names
                group.diff_argument_flags = Diffs.fusion.argument_flags
                entities[i] = group  # constraint replaced by the new group (and other constraints of the group will be now ignored since flagged to False)
            groups.append(group)
            if len(entities) > 100 and len(groups) == 2 and len(groups[0].entities) + len(groups[1].entities) < 5:  #len(entities) // 5:
                print("\tStopping to detect groups")  # because it may be very expensive (and not very efficient)
                break
        return [e for e in entities if e is not None] if removal else entities

    for e in ctr_entities:
        if isinstance(e, (EBlock, ESlide, EToSatisfy)):
            detecting_groups_recursively(e.entities)
        if isinstance(e, EToGather) and len(e.entities) > 0 and not isinstance(e.entities[0], EMetaCtr):
            e.entities = _detecting_groups(e.entities)


# Phase 2: Building groups (constraint templates and args)

def _compute_group_abstraction_intension(group):
    def _replace_parameter(s, k, v):
        return (s.replace("(" + k + ")", "(" + v + ")").replace("," + k + ",", "," + v + ",").replace("(" + k + ",", "(" + v + ",")
                .replace("," + k + ")", "," + v + ")").replace("(" + k + ")", "(" + v + ")"))

    def _same(v1, v2):
        if isinstance(v1, Variable):
            return v1.eq__safe(v2)
        if isinstance(v2, Variable):
            return v2.eq__safe(v1)
        return v1 == v2

    def _is_same_value_at_column(i, all_args):
        """ comparison from both ends so as to find opportunistically that the parameter is not the same everywhere"""
        left, right = 1, len(all_args) - 1
        value = all_args[0][i]
        while True:
            if not _same(value, all_args[left][i]):
                return False
            left += 1
            if not _same(value, all_args[right][i]):
                return False
            right -= 1
            if left > right:
                break
        return True

    def _is_same_value_in_columns(i, j, all_args):
        left, right = 0, len(all_args) - 1
        while True:
            if not _same(all_args[left][i], all_args[left][j]):
                return False
            left += 1
            if not _same(all_args[right][i], all_args[right][j]):
                return False
            right -= 1
            if left > right:
                break
        return True

    if group.abstraction:
        # TODO not perfect because if we remove a constraint from the list in incremental mode
        # the group is no more coherent
        return group.abstraction, group.all_args

    all_args = [ce.constraint.abstract_values() for ce in group.entities]
    abstract_tree = group.entities[0].constraint.abstract_tree()
    n_parameters = len(group.entities[0].constraint.abstract_values())
    marked = [False] * n_parameters

    # discarding a parameter if the same value appears all along the column
    for i in range(n_parameters):
        if _is_same_value_at_column(i, all_args):
            marked[i] = True
            abstract_tree = _replace_parameter(abstract_tree, "%" + str(i), str(all_args[0][i]))

    # merging two columns if they are identical
    for i in range(n_parameters):
        for j in range(i + 1, n_parameters):
            if _is_same_value_in_columns(i, j, all_args):
                marked[j] = True
                abstract_tree = _replace_parameter(abstract_tree, "%" + str(j), "%" + str(i))

    # removing marked arguments (in a symbolic way with a special value)
    for i in range(n_parameters - 1, -1, -1):
        if marked[i]:
            for args in all_args:
                del args[i]  # args[i] = DELETED

    # reordering %i in the abstract tree
    for i in range(n_parameters):
        par = "%" + str(i)
        if par not in re.findall('(%\d+)', abstract_tree):
            t = {int(m[1:]) for m in re.findall('(%\d+)', abstract_tree) if int(m[1:]) > i}
            if len(t) > 0:
                old = "%" + str(min(t))
                # while old in abstract_tree:
                abstract_tree = _replace_parameter(abstract_tree, old, par)
    if any(len(args) == 0 for args in all_args):
        error("A group with at least an empty argument list")
    return abstract_tree, all_args


def _compute_group_abstraction_other(group, *, from_slide=False):
    c = group.entities[0].constraint
    abstraction = OrderedDict()
    var_args_argument = None

    # building the abstract constraint template
    abstract_condition = len(group.diff_argument_names) == 2 and group.diff_argument_names[-1] == TypeCtrArg.CONDITION
    c.n_parameters = 0
    for arg in c.arguments.values():
        if arg.name in group.diff_argument_names:
            index = group.diff_argument_names.index(arg.name)
            if group.diff_argument_flags[index]:
                assert len(set(len(ce.constraint.arguments[arg.name].content) for ce in group.entities)) > 1
                abstraction[arg.name] = "%..."
                var_args_argument = arg.name
            elif abstract_condition and index == 0 and isinstance(group.entities[0].constraint.arguments[arg.name].content, list) and len(
                    group.entities[0].constraint.arguments[arg.name].content) > LIMIT_FOR_VAR_ARGS:
                abstraction[arg.name] = "%..."
                var_args_argument = arg.name
            elif var_args_argument is None and group.diff_argument_names[-1] == arg.name and isinstance(arg.content, list) and len(
                    arg.content) > _limit_for_var_args(from_slide):  # LIMIT_FOR_VAR_ARGS:
                abstraction[arg.name] = "%..."
            else:
                if arg.name == TypeCtrArg.CONDITION:
                    abstraction[arg.name] = "(" + str(arg.content.operator) + "," + c.parameter_form(arg.content) + ")"  # TODO is it correct?
                else:
                    abstraction[arg.name] = c.parameter_form(arg.content)
        else:
            abstraction[arg.name] = arg.content

    def add_content(content):
        if isinstance(content, list):
            tmp.extend(content)
        elif isinstance(content, Condition):
            tmp.append(str(content.right_operand()))
        else:
            tmp.append(content)

    # collecting arguments
    all_args = []
    arguments_names = list(c.arguments.keys())
    for ce in group.entities:
        tmp = []
        if var_args_argument is None or group.diff_argument_flags[-1]:
            for name in arguments_names:
                if name in group.diff_argument_names:
                    add_content(ce.constraint.arguments[name].content)
        else:
            for name in arguments_names:
                if name in group.diff_argument_names and name != var_args_argument:
                    add_content(ce.constraint.arguments[name].content)
            add_content(ce.constraint.arguments[var_args_argument].content)
        all_args.append(tmp)
    return abstraction, all_args


def building_groups_recursively(entities, previous=None, from_slide=False):
    def _build_group(group, from_slide):
        if isinstance(group.entities[0].constraint, ConstraintIntension):
            group.abstraction, group.all_args = _compute_group_abstraction_intension(group)
        else:
            group.abstraction, group.all_args = _compute_group_abstraction_other(group, from_slide=from_slide)

    for e in entities:
        if isinstance(e, EGroup):
            _build_group(e, from_slide)
            e.copy_basic_attributes_of(previous)
            # previous.clearBasicAttributes()
        if isinstance(e, (ESlide, EToGather, EBlock, EToSatisfy)):
            building_groups_recursively(e.entities, e, from_slide or isinstance(e, ESlide))


# Phase 3: adding/removing some blocks

def canonizing_groups_and_blocks(entities, previous=None):
    def _building_block(entity):
        if len(entity.entities) == 0:
            return entity
        if len(entity.entities) == 1:  # no need to create a block in this case
            entity.entities[0].copy_basic_attributes_of(entity)
            return entity.entities[0]
        block = EBlock([entity])  # creating a new block and copying the appropriate comments and tags
        block.copy_basic_attributes_of(entity if not entity.blank_basic_attributes() else entity.entities[0])
        for c in entity.entities:  # clearing comments and tags of the constraints embedded in the block
            c.clear_basic_attributes()
        return block

    for i, e in enumerate(entities):
        if not isinstance(e, ECtrs) or len(e.entities) == 0:
            continue
        first = e.entities[0]
        if isinstance(e, EBlock) and isinstance(first, (ECtr, EToGather, EGroup)):
            # removing a block when we have only one element inside
            if len(e.entities) == 1 and None in {e.comment, first.comment} and 0 in {len(e.tags), len(first.tags)}:
                if e.comment:
                    first.note(e.comment)
                if len(e.tags) > 0:
                    first.tag(e.tags)
                entities[i] = first
        if isinstance(e, EToGather):
            # Creating a new block when there are several sub-groups (or stand-alone constraints); it was impossible to do a single group
            if any(not c.blank_basic_attributes() for c in e.entities):
                if not isinstance(previous, EBlock):
                    entities[i] = _building_block(e)
            elif not e.blank_basic_attributes():
                entities[i] = _building_block(e)
        if isinstance(e, (ESlide, EBlock, EToSatisfy)):
            canonizing_groups_and_blocks(e.entities, e)


# Phase 4: detecting forms corresponding to instantiations

def recognizing_instantiations(entities):
    def _elements_for_building_instantiation(trees):
        t1, t2 = [], []
        for tree in trees:
            pair = tree.var_val_if_binary_type(TypeNode.EQ)
            if pair is None:
                return None
            t1.append(pair[0])
            t2.append(pair[1])
        return t1, t2

    for i, e in enumerate(entities):
        # since a group, we can test only the first constraint (to see if it is a group of intension constraints)
        if isinstance(e, EGroup) and isinstance(e.entities[0].constraint, ConstraintIntension):
            elements = _elements_for_building_instantiation(c.constraint.arguments[TypeCtrArg.FUNCTION].content for c in e.entities)
            if elements:
                entities[i] = ECtr(ConstraintInstantiation(elements[0], elements[1])).copy_basic_attributes_of(e)
        elif isinstance(e, (ESlide, EToGather, EBlock, EToSatisfy)):
            recognizing_instantiations(e.entities)
