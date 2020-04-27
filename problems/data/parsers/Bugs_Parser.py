from pycsp3.problems.data.parsing import *

next_line()
data["height"] = next_int()
data["width"] = next_int()
next_line()
nBugTypes = next_int()
next_line()
data["bugTypeLengths"] = [next_int() for _ in range(nBugTypes)]
next_line()
nBugs = next_int()
next_line()
data["bugs"] = [OrderedDict([("row", next_int()), ("col", next_int()), ("type", next_int())]) for _ in range(nBugs)]
# data.bugTypeLengths = bugTypesLength  # [DataDict({"length": bugTypesLength[i], "cells": [j for j in range(nBugs) if data.bugs[j].type == i]}) for i in range(nBugTypes)]
