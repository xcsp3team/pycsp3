from pycsp3.problems.data.parsing import *

next_line()
data["height"] = next_int()
data["width"] = next_int()

next_line()
nBugTypes = next_int()

next_line()
bugTypesLength = [next_int() for i in range(nBugTypes)];

next_line()
nBugs = next_int()

next_line()
data["bugs"] = []
data["bugTypes"] = []
lst = [False] * nBugs
for index in range(nBugs):
    bug = {"row": next_int(), "col": next_int(), "type": next_int()}
    data["bugs"].append(bug)
    if lst[bug["type"]] is False: lst[bug["type"]] = []
    lst[bug["type"]].append(index)

for index, length in enumerate(bugTypesLength):
    data["bugTypes"].append({"length": length, "cells": lst[index]})
