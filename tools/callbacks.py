from pycsp3.classes.auxiliary.ptypes import TypeFramework, TypeConditionOperator, TypeXML, TypeVar, TypeCtr, TypeCtrArg
from pycsp3.classes.entities import (Entity, EVar, EVarArray, ECtr, EMetaCtr, EObjective, EAnnotation, EGroup, EBlock, ESlide, EIfThenElse, EToGather,
                                     EToSatisfy, CtrEntities, VarEntities, ObjEntities, AnnEntities)
from pycsp3.classes.main.constraints import ConstraintIntension, ConstraintRefutation
from pycsp3.classes.main.annotations import TypeAnnArg
from pycsp3.dashboard import options
from pycsp3.tools.compactor import compact
from pycsp3.tools.slider import _identify_slide
from pycsp3.classes.auxiliary.conditions import Condition
from pycsp3.tools.utilities import warning, table_to_string

SIZE_LIMIT_FOR_USING_AS = 12  # when building domains of variables of arrays of variables (and using the attribute 'as')


class Callbacks:
    def __init__(self):
        pass

    def loadInstance(self, discardedClasses=None):
        self.beginInstance(TypeFramework.COP if len(ObjEntities.items) else TypeFramework.CSP)

        # beginVariables(parser.vEntries);
        # loadVariables(parser);
        # endVariables();
        # beginConstraints(parser.cEntries);
        # loadConstraints(parser);
        # endConstraints();
        # beginObjectives(parser.oEntries, parser.typeCombination);
        # loadObjectives(parser);
        # endObjectives();
        # beginAnnotations(parser.aEntries);
        # loadAnnotations(parser);
        # endAnnotations();
        
        self.endInstance()

    def loadVariables(self, vEntries):
        pass

    def loadVar(v):
        pass

    def loadArray(va):
        pass

    def loadConstraints(cEntries):
        pass

    def loadBlock(b):
        pass

    def loadGroup(g):
        pass

    def loadSlide(s):
        pass

    def loadLogic(l):
        pass

    def loadCtrs(template, argss, entry):
        pass

    def loadCtr(c):
        pass

    def loadObjectives(parser):
        pass

    def loadObj(o):
        pass

    def loadAnn(aEntry):
        pass

    def loadAnnotations(parser):
        pass

    # -----------------

    def beginInstance(self, type_framework):
        pass

    def endInstance(self):
        pass
