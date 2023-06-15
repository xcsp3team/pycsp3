from collections import OrderedDict

from lxml import etree

from pycsp3.classes.auxiliary.ptypes import TypeFramework, TypeConditionOperator, TypeXML, TypeVar, TypeCtr, TypeCtrArg
from pycsp3.classes.entities import (Entity, EVar, EVarArray, ECtr, EMetaCtr, EObjective, EAnnotation, EGroup, EBlock, ESlide, EIfThenElse, EToGather,
                                     EToSatisfy, CtrEntities, VarEntities, ObjEntities, AnnEntities)
from pycsp3.classes.main.constraints import ConstraintIntension
from pycsp3.classes.main.annotations import TypeAnnArg
from pycsp3.dashboard import options
from pycsp3.tools.compactor import compact
from pycsp3.tools.slider import _identify_slide
from pycsp3.classes.auxiliary.conditions import Condition
from pycsp3.tools.utilities import warning, table_to_string

SIZE_LIMIT_FOR_USING_AS = 12  # when building domains of variables of arrays of variables (and using the attribute 'as')


class DefaultListOrderedDict(OrderedDict):
    def __missing__(self, k):
        self[k] = []
        return self[k]


def _text(elt, s):
    test = str(s)
    if "False" in test or "True" in test:
        warning(
            "False or True is present in " + test
            + "\n\tIt is likely a problem with the use of logical operators"
            + "\n\tFor example, you must write (x == 0) | (x ==1) instead of (x == 0) or (x == 1)"
            + "\n\tSee also the end of section about constraint Intension in chapter 'Twenty popular constraints' of the guide\n")
    elt.text = " " + (" ".join(str(v) for v in s) if isinstance(s, (list, tuple)) else str(s)) + " "


def _element(name, entity=None, *, id=None, attributes=[], text=None):
    elt = etree.Element(str(name))
    if id is not None:
        assert isinstance(id, str)
        elt.set(str(TypeXML.ID), id)
    if entity is not None:
        assert isinstance(entity, Entity)
        if len(entity.tags) > 0:
            elt.set(str(TypeXML.CLASS), ' '.join(tag for tag in entity.tags))
        if entity.comment and options.sober is False:
            elt.set(str(TypeXML.NOTE), entity.comment)
    attributes = attributes if isinstance(attributes, list) else [attributes]
    for (k, v) in attributes:
        elt.set(str(k), str(v))
    if text is not None:
        _text(elt, text)
    return elt


def _complex_var(va, dom_or_dom2vars):
    elt = _element(TypeXML.VAR if isinstance(va, EVar) else TypeXML.ARRAY, va, id=va.id)
    if isinstance(va, EVarArray):
        elt.set(str(TypeXML.SIZE), va.size_to_string())
    if not isinstance(dom_or_dom2vars, DefaultListOrderedDict):
        if isinstance(dom_or_dom2vars, (EVar, EVarArray)):  # meaning an alias
            elt.set(str(TypeXML.AS), dom_or_dom2vars.id)
        else:
            _text(elt, dom_or_dom2vars)
    else:
        for dom, vars in dom_or_dom2vars.items():
            s = compact(vars)
            elt.append(_element(TypeXML.DOMAIN, attributes=(TypeXML.FOR, " ".join(str(x) for x in s) if isinstance(s, list) else s), text=dom))
    if va.get_type() == TypeVar.SYMBOLIC:
        elt.set(str(TypeXML.TYPE), str(TypeVar.SYMBOLIC))
    return elt


def _simple_var(va, dom, dom2var):
    if dom in dom2var:
        return _complex_var(va, dom if len(dom) < SIZE_LIMIT_FOR_USING_AS else dom2var[dom])
    else:
        dom2var[dom] = va
        return _complex_var(va, dom)


def _variables():
    elt = _element(TypeXML.VARIABLES)
    dom2var = dict()
    for va in VarEntities.items:
        if isinstance(va, EVar):
            elt.append(_simple_var(va, str(va.variable.dom), dom2var))
        else:
            dom2vars = DefaultListOrderedDict(())
            for x in va.flatVars:
                if x is not None:
                    dom2vars[str(x.dom)].append(x)
            dom2vars = DefaultListOrderedDict(sorted(dom2vars.items(), key=lambda item: [y.indexes for y in item[1]]))
            if len(dom2vars) == 1:  # and not va.is_containing_hole():  # TODO do we keep the second part of the condition?
                elt.append(_simple_var(va, str(va.flatVars[0].dom), dom2var))
            else:
                elt.append(_complex_var(va, dom2vars))
    return elt


def _argument(elt, arg, key, value, change_element_value=False):
    assert value is not None
    if key == TypeAnnArg.STATICS:
        for k, v in value:
            elt.append(_element(TypeAnnArg.STATIC, attributes=[(TypeAnnArg.ORDER, " ".join(str(ele) for ele in v))], text=compact(k)))
        return
    if key == TypeCtrArg.LIMIT:  # we modify the name of the argument for constraint knapsack
        key = TypeCtrArg.CONDITION
    if key == TypeCtrArg.INTENTION and isinstance(value, (list, tuple, set, frozenset)):
        value = list(value)
        subelt = _element(TypeCtr.EXTENSION)
        subelt.append(_element(TypeCtrArg.LIST, text=" ".join("%" + str(i) for i in range(len(value[0])))))
        subelt.append(_element(TypeCtrArg.SUPPORTS, text=table_to_string(value)))
        elt.append(subelt)
    elif arg.lifted is True:
        for i, l in enumerate(value):
            no_attributes = arg.attributes is None or len(arg.attributes) == 0
            assert no_attributes or len(arg.attributes) == len(value)
            subelt = _element(key, text=l, attributes=[] if no_attributes else arg.attributes[i])
            # for att in arg.attributes[i]:  #(att for att in arg.attributes if att[1] == key and att[0] == i):
            #     subelt.set(str(att[2]), str(att[3]))
            elt.append(subelt)
    else:
        # the first part (if) will be removed in the medium term (we will systematically use the XML <condition>)
        if change_element_value and key == TypeCtrArg.CONDITION and ((isinstance(value, Condition) and value.operator == TypeConditionOperator.EQ)
                                                                     or (isinstance(value, str) and value.startswith("(eq,"))):
            v = str(value)
            elt.append(_element(TypeCtrArg.VALUE, attributes=arg.attributes, text=v[v.index(',') + 1:-1]))
        else:
            v = None if isinstance(value, list) and len(value) == 1 and value[0] is None else value
            elt.append(_element(key, attributes=arg.attributes, text=v))


def _constraint(entity, *, possible_simplified_form=False):
    assert isinstance(entity, (ECtr, EObjective, EAnnotation))
    c = entity.constraint
    if c is None:
        return None
    if isinstance(c, ConstraintIntension):
        return _element(TypeCtr.INTENSION, entity, text=c.arguments[TypeCtrArg.FUNCTION].content)
    elt = _element(c.name, entity, attributes=c.attributes)
    arguments = [arg for arg in c.arguments.values() if arg.content is not None]  # we keep only valid (non null) arguments
    if len(arguments) == 1 and not arguments[0].lifted and (possible_simplified_form or arguments[0].name == TypeCtrArg.LIST):
        _text(elt, arguments[0].content)
    else:
        b = c.name == TypeCtr.ELEMENT
        for arg in arguments:
            _argument(elt, arg, arg.name, arg.content, change_element_value=b)
    return elt


def _constraint_template(group):
    if isinstance(group.entities[0].constraint, ConstraintIntension):
        return _element(TypeCtr.INTENSION, text=group.abstraction)
    else:
        first = group.entities[0]
        arguments = [(k, v) for k, v in group.abstraction.items() if v is not None]  # we keep only valid (non null) arguments
        elt = _element(first.constraint.name, first, attributes=first.constraint.attributes)
        if len(arguments) == 1 and TypeCtrArg.LIST in group.abstraction:
            _text(elt, group.abstraction[TypeCtrArg.LIST])
        else:
            b = str(first.constraint.name) == "element"
            for k, v in arguments:
                _argument(elt, first.constraint.arguments[k], k, v, change_element_value=b)
        return elt


def _slide(entity, scope, offset, circular, group):
    elt = _element(TypeCtr.SLIDE, entity, attributes=(TypeXML.CIRCULAR, "true") if circular else [])
    elt.append(_element(TypeCtrArg.LIST, text=scope, attributes=(TypeXML.OFFSET, offset) if offset > 1 else []))
    elt.append(_constraint_template(group))
    return elt


def _group(entity):
    if options.recognizeslides:
        all_args = entity.original_all_args if hasattr(entity, "original_all_args") else entity.all_args
        if len(all_args) > 3 and len(all_args[0]) > 1:
            res = _identify_slide(entity)
            if res:
                scope, offset, circular = res
                return _slide(entity, compact(scope, preserve_order=True), offset, circular, entity)
    elt = _element(TypeXML.GROUP, entity)
    elt.append(_constraint_template(entity))
    for arg in entity.all_args:
        elt.append(_element(TypeXML.ARGS, text=arg))
    return elt


def _constraints_recursive(elt, entity):
    if entity is None:
        return None
    son = None
    if isinstance(entity, ECtr):
        son = _constraint(entity)
    elif isinstance(entity, EToGather):
        _constraints_iterative(elt, entity.entities)
    elif isinstance(entity, ESlide):
        if len(entity.scope) == 0:
            _constraints_iterative(elt, entity.entities)
        else:
            son = _slide(entity, entity.scope, entity.offset, entity.circular, entity.entities[0].entities[0])
    elif isinstance(entity, EGroup):
        son = _group(entity)
    elif isinstance(entity, EBlock):
        if len(entity.entities) != 0:
            son = _constraints_iterative(_element(TypeXML.BLOCK, entity), entity.entities)
    elif isinstance(entity, EMetaCtr):
        son = _constraints_iterative(_element(str(entity.id), entity), entity.entities)
    elif isinstance(entity, EToSatisfy):
        _constraints_iterative(elt, entity.entities)
    else:
        raise TypeError("Problem with " + str(type(entity)))
    if son is not None:
        elt.append(son)


def _constraints_iterative(elt, entities):
    for ce in entities:
        _constraints_recursive(elt, ce)
    return elt


def _constraints():
    return _constraints_iterative(_element(TypeXML.CONSTRAINTS), CtrEntities.items)


def _objectives():
    elt = _element(TypeXML.OBJECTIVES)
    for ce in ObjEntities.items:
        elt.append(_constraint(ce, possible_simplified_form=True))
    return elt


def _annotations():
    elt = _element(TypeXML.ANNOTATIONS)
    for ce in AnnEntities.items:
        elt.append(_constraint(ce, possible_simplified_form=False))
    return elt


def build_document():
    root = _element(TypeXML.INSTANCE, attributes=(TypeXML.FORMAT, "XCSP3"))

    variables = _variables()
    if len(variables) > 0:
        root.append(variables)
    else:
        print("Warning: no variables in this model (and so, no generated file)!")
        return None

    constraints = _constraints()
    if len(constraints) > 0:
        root.append(constraints)
    else:
        print("Warning: no constraints for this model!")

    objectives = _objectives()
    if len(objectives) > 0:
        root.append(objectives)
        root.set(str(TypeXML.TYPE), str(TypeFramework.COP))
    else:
        root.set(str(TypeXML.TYPE), str(TypeFramework.CSP))

    annotations = _annotations()
    if len(annotations) > 0:
        root.append(annotations)

    return root
