import re
from collections import OrderedDict

from pycsp3.classes.auxiliary.types import TypeCtrArg
from pycsp3.classes.entities import CtrEntities, ECtr, ECtrs, EGroup, EBlock, EToGather, ESlide, EToSatisfy, TypeNode
from pycsp3.classes.main.constraints import ConstraintIntension, Diffs, ConstraintInstantiation

LIMIT_FOR_VAR_ARGS = 3


def build_similar_constraints():
    detecting_groups_recursively(CtrEntities.items)
    building_groups_recursively(CtrEntities.items)
    canonizing_groups_and_blocks(CtrEntities.items)
    recognizing_instantiations(CtrEntities.items)


# Phase 1 : Detecting groups of similar constraints

def _detecting_groups(ctr_entities):
    flags = [False] * len(ctr_entities)  # indicate (indexes of) constraints that are similar at a given moment (see intern loop)
    removal = False
    for i, ce1 in enumerate(ctr_entities):
        if flags[i] or ce1 is None or isinstance(ce1, EGroup):
            continue
        Diffs.reset()
        group = EGroup()  # group of similar constraints tried to be built
        group.entities.append(ce1)  # first constraint of the new group
        for j in range(i + 1, len(ctr_entities)):
            ce2 = ctr_entities[j]
            if flags[j] is False and not isinstance(ce2, EGroup):
                diffs = ce2.constraint.close_to(ce1.constraint)
                if diffs is not False:
                    diffs.merge()  # merging flags of two lists, indicating if the length of argument contents is different
                    group.entities.append(ce2)  # adding the constraint to the new group
                    flags[j] = True  # to avoid processing it again
                    ctr_entities[j] = None  # to discard this constraint (since it is now in a group)
                    removal = True
        if len(group.entities) > 1:
            group.diff_argument_names = Diffs.fusion.argument_names
            group.diff_argument_flags = Diffs.fusion.argument_flags
            ctr_entities[i] = group  # constraint replaced by the new group (and other constraints of the group will be now ignored since flagged to False)

    return [ce for ce in ctr_entities if ce is not None] if removal else ctr_entities


def detecting_groups_recursively(ctr_entities):
    for ce in ctr_entities:
        if isinstance(ce, (EBlock, ESlide, EToSatisfy)):
            detecting_groups_recursively(ce.entities)
        if isinstance(ce, EToGather):
            ce.entities = _detecting_groups(ce.entities)


# Phase 2 : Building groups (constraint templates and args)

def _replace_parameter(s, k, v):
    return (s.replace("(" + k + ")", "(" + v + ")").replace("," + k + ",", "," + v + ",").replace("(" + k + ",", "(" + v + ",")
            .replace("," + k + ")", "," + v + ")").replace("(" + k + ")", "(" + v + ")"))


def _is_same_value_at_column(i, all_args):
    """ comparison from both ends so as to find opportunistically that the parameter is not the same everywhere"""
    left, right = 1, len(all_args) - 1
    value = all_args[0][i]
    while True:
        if value != all_args[left][i]:
            return False
        left += 1
        if value != all_args[right][i]:
            return False
        right -= 1
        if left > right:
            break
    return True


def _is_same_value_in_columns(i, j, all_args):
    left, right = 0, len(all_args) - 1
    while True:
        if all_args[left][i] != all_args[left][j]:
            return False
        left += 1
        if all_args[right][i] != all_args[right][j]:
            return False
        right -= 1
        if left > right:
            break
    return True


def _compute_group_abstraction_intension(group):
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
        if par not in abstract_tree:
            t = {int(m[1:]) for m in re.findall('(%\d+)', abstract_tree) if int(m[1:]) > i}
            if len(t) > 0:
                old = "%" + str(min(t))
                # while old in abstract_tree:
                abstract_tree = _replace_parameter(abstract_tree, old, par)

    return abstract_tree, all_args


def _compute_group_abstraction_other(group):
    c = group.entities[0].constraint
    abstraction = OrderedDict()
    var_args_argument = None

    # building the abstract constraint template
    for arg in c.arguments.values():
        if arg.name in group.diff_argument_names:
            if group.diff_argument_flags[group.diff_argument_names.index(arg.name)]:
                assert len(set(len(ce.constraint.arguments[arg.name].content) for ce in group.entities)) > 1
                abstraction[arg.name] = "%..."
                var_args_argument = arg.name
            elif var_args_argument is None and group.diff_argument_names[- 1] == arg.name and isinstance(arg.content, list) and len(
                    arg.content) > LIMIT_FOR_VAR_ARGS:
                abstraction[arg.name] = "%..."
            else:
                abstraction[arg.name] = c.parameter_form(arg.content)
        else:
            abstraction[arg.name] = arg.content

    def add_content(content):
        if isinstance(content, list):
            tmp.extend(content)
        else:
            tmp.append(content)

    # collecting arguments
    all_args = []
    arguments_names = list(c.arguments.keys())
    for ce in group.entities:
        tmp = []
        if var_args_argument is None or group.diff_argument_flags[- 1]:
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


def _build_group(group):
    if isinstance(group.entities[0].constraint, ConstraintIntension):
        group.abstraction, group.all_args = _compute_group_abstraction_intension(group)
    else:
        group.abstraction, group.all_args = _compute_group_abstraction_other(group)


def building_groups_recursively(ctr_entities, previous=None):
    for ce in ctr_entities:
        if isinstance(ce, EGroup):
            _build_group(ce)
            ce.copy_basic_attributes_of(previous)
            # previous.clearBasicAttributes()
        if isinstance(ce, (ESlide, EToGather, EBlock, EToSatisfy)):
            building_groups_recursively(ce.entities, ce)


# Phase 3 : adding/removing some blocks

def _building_block(ce):
    if len(ce.entities) == 0:
        return ce
    if len(ce.entities) == 1:  # no need to create a block in this case
        ce.entities[0].copy_basic_attributes_of(ce)
        return ce.entities[0]
    block = EBlock([ce])  # creating a new block and copying the appropriate comments and tags
    block.copy_basic_attributes_of(ce if not ce.blank_basic_attributes() else ce.entities[0])
    for c in ce.entities:  # clearing comments and tags of the constraints embedded in the block
        c.clear_basic_attributes()
    return block


def canonizing_groups_and_blocks(ctr_entities, previous=None):
    for i, ce in enumerate(ctr_entities):
        if not isinstance(ce, ECtrs) or len(ce.entities) == 0:
            continue
        first = ce.entities[0]

        if isinstance(ce, EBlock) and isinstance(first, (ECtr, EToGather, EGroup)):
            # removing a block when we have only one element inside
            if len(ce.entities) == 1 and None in {ce.comment, first.comment} and 0 in {len(ce.tags), len(first.tags)}:
                if ce.comment:
                    first.note(ce.comment)
                if len(ce.tags) > 0:
                    first.tag(ce.tags)
                ctr_entities[i] = first

        if isinstance(ce, EToGather):
            # Creating a new block when there are several sub-groups (or stand-alone constraints); it was impossible to do a single group
            if any(not c.blank_basic_attributes() for c in ce.entities):
                if not isinstance(previous, EBlock):
                    ctr_entities[i] = _building_block(ce)
            elif not ce.blank_basic_attributes():
                ctr_entities[i] = _building_block(ce)

        if isinstance(ce, (ESlide, EBlock, EToSatisfy)):
            canonizing_groups_and_blocks(ce.entities, ce)


# Phase 4 : detecting forms corresponding to instantiations

def _elements_for_building_instantiation(trees):
    t1, t2 = [], []
    for tree in trees:
        pair = tree.var_val_if_binary_type(TypeNode.EQ)
        if pair is None:
            return None
        t1.append(pair[0])
        t2.append(pair[1])
    return t1, t2


def recognizing_instantiations(ctr_entities):
    for i, ce in enumerate(ctr_entities):
        # since a group, we can test only the first constraint (to see if it is a group of intension constraints)
        if isinstance(ce, EGroup) and isinstance(ce.entities[0].constraint, ConstraintIntension):
            elements = _elements_for_building_instantiation(c.constraint.arguments[TypeCtrArg.FUNCTION].content for c in ce.entities)
            if elements:
                ctr_entities[i] = ECtr(ConstraintInstantiation(elements[0], elements[1])).copy_basic_attributes_of(ce)
        elif isinstance(ce, (ESlide, EToGather, EBlock, EToSatisfy)):
            recognizing_instantiations(ce.entities)
