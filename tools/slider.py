from pycsp3.classes.entities import CtrEntities, EBlock, EGroup, ESlide, EToGather, EToSatisfy
from pycsp3.classes.main.variables import Variable


def handle_slides():
    detect_slides_recursively(CtrEntities.items)
    # canonize_blocks_of_slides(CtrEntities.items)  # TODO desactivated because very limited interest and problem with holes (see at bottom)


def detect_slides_recursively(ctr_entities):
    for ce in ctr_entities:
        if isinstance(ce, (EBlock, EToGather, EToSatisfy)):
            detect_slides_recursively(ce.entities)
        elif isinstance(ce, ESlide) and len(ce.entities) == 1:
            son = ce.entities[0]
            if isinstance(son, EToGather) and len(son.entities) == 1:
                grand_son = son.entities[0]
                if isinstance(grand_son, EGroup) and len(grand_son.entities) > 0:
                    res = _identify_slide(ce.entities[0].entities[0])
                    if res:
                        ce.scope, ce.offset, ce.circular = res  # the slide is validated: information for it is recorded
                    else:
                        print("Warning: The slide is not really a slide but a group")


def _identify_slide(group):
    def _possible_offset(all_args):  # attempt to find a simple offset
        for arg1 in all_args[1]:
            for i, arg0 in enumerate(all_args[0]):
                if arg0 == arg1:
                    return i
        return None

    if isinstance(group.abstraction, dict) and len([v for v in group.abstraction.values() if "%" in str(v)]) != 1:
        return None  # if more than one difference, we currently don't know how to slide (compute it automatically)

    all_args = group.original_all_args if hasattr(group, "original_all_args") else group.all_args

    # we compute the global scope
    t = [x for args in all_args for x in args]
    if any(not isinstance(x, Variable) for x in t):
        return None
    scope = [x for i, x in enumerate(t) if x not in t[0:i]]  # in O(n^2) but should not be a big deal here

    ''' trying to recognize a normal slide '''
    arity = len(all_args[0])
    sliding_scope = [[x for x in scope[i:i + arity]] for i in range(0, len(scope) - arity + 1, 1)]  # OFFSET 1
    if sliding_scope == all_args:
        return scope, 1, False

    ''' trying to recognize a circular Slide '''
    sliding_scope = [[x for x in [scope[(i + k) % len(scope)] for k in range(arity)]] for i in range(len(scope))]
    if sliding_scope == all_args:
        return scope, 1, True

    ''' trying to recognize a slide with an offset not equal to 1'''
    offset = _possible_offset(all_args)
    if offset is None or offset <= 1:
        return None
    sliding_scope = [[x for x in scope[i:i + arity]] for i in range(0, len(scope) - arity + 1, offset)]
    if sliding_scope == all_args:
        return scope, offset, False
    if sliding_scope + [[scope[i] for i in range(len(scope) - arity + 1, len(scope))] + [scope[0]]] == all_args:
        return scope, offset, True
    return None


# gathering slides : currently, it is not activated

def canonize_blocks_of_slides(ctr_entities, parent=None):
    for i, ce in enumerate(ctr_entities):
        if isinstance(ce, (EBlock, EToGather, EToSatisfy)):
            canonize_blocks_of_slides(ce.entities, ce)
    if not isinstance(parent, (EBlock, EToSatisfy)):
        indexes = [i for i, ce in enumerate(ctr_entities) if isinstance(ce, ESlide)]
        if len(indexes) > 1 and all(ctr_entities[indexes[0]].same_type_and_basic_attributes(ctr_entities[i]) for i in indexes):
            _build_block_of_slides(ctr_entities, indexes)


def _build_block_of_slides(ctr_entities, indexes):
    block = EBlock([ctr_entities[i] for i in indexes])
    block.copy_basic_attributes_of(ctr_entities[indexes[0]])
    for i in indexes:
        ctr_entities[i].clear_basic_attributes()
        ctr_entities[i] = None
    # CtrEntities.remove(block)  # todo can we do that?
    ctr_entities[indexes[0]] = block
    # TODO we should not keep holes (None) in arrays as above
