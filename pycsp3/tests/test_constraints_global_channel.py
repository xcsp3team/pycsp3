"""
Tests of the constraint Channel of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#Channel): the function Channel(), with one list, two lists or a list and a value,
with the parameters start_index1 and start_index2, with the option -mini, in groups of constraints and in logical expressions.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
According to XCSP3 (the start indexes s1 and s2 being 0 by default, and the only ones accepted by XCSP3-core):
 - channel(X) holds iff, for each i, X[i] = j + s1 implies X[j] = i + s1;
 - channel(X, Y) holds iff, for each i, X[i] = j + s2 iff Y[j] = i + s1 when |X| = |Y|, and X[i] = j + s2 implies Y[j] = i + s1 when |X| < |Y|;
 - channel(X, v) holds iff X is a list of 0/1 variables with a unique 1, at the index v - s1.
A value that is not an index of the channeled list (j outside the list) cannot be assigned, as for an index of Element.
"""

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

# Known bugs of the solvers (each bug is reported in the issue given at the start of its reason)
ACE_RANGE = ("xcsp3team/ACE#37: ACE: wrong solutions (the ith value of a domain is taken as the index i), or ERROR without message (control "
             "list.length == idom.initSize() in ElementList), when the values of a variable of a list are not exactly the indexes of the channeled list")
ACE_REPEATED = "xcsp3team/ACE#38: ACE: ERROR without message (control areAllDistinct in ElementList) when a variable is repeated in a list"
ACE_VALUE = ("xcsp3team/ACE#39: ACE: ERROR without message (control in Problem.channel) when the domain of the value is not exactly the "
             "range of the indexes of the list")
COSOCO_RANGE = "xcsp3team/cosoco#115: COSOCO: segmentation fault when the values of a variable of a list are not indexes of the channeled list"
COSOCO_REPEATED_WRONG = ("xcsp3team/cosoco#118: COSOCO: wrong solutions when a variable is repeated in the second list, longer than the first "
                         "one (element constraints posted on a list with a repeated variable)")
ACE_VALUE_DOMAIN_0 = ("xcsp3team/ACE#39: ACE: ERROR without message (control areAllInitiallyBoolean in Problem.channel) when a variable "
                      "of the list has the domain {0}")
COSOCO_START_INDEX = ("xcsp3team/cosoco#117: COSOCO: startIndex ignored (two lists, list with a value): wrong solutions, or no solution found (status UNKNOWN)")
CHOCO_START_INDEXES = "chocoteam/choco-solver#1270: CHOCO: two lists of the same size with start indexes: the two start indexes are swapped"
COSOCO_VALUE = ("xcsp3team/cosoco#116: COSOCO: wrong solutions with a value outside the indexes of the list (no variable of the list "
                "is required to be 1)")

# The cases that a solver says it does not handle, and the symbolic variables (not reported)
COSOCO_REPEATED = "COSOCO: a variable repeated in a list is not handled (allDifferent: scope contains variable many times)"
ACE_START_INDEX = "ACE: explicit refusal of startIndex with lists (unimplemented case for channel)"
COSOCO_START_INDEX_ONE_LIST = "COSOCO: explicit refusal of startIndex with one list (Channel is not implemented with index != 0)"
SYMBOLIC = "channel on symbolic variables is not part of XCSP3-core"


def channel1(t, s=0):
    """Returns True if the tuple t satisfies channel(t) with start index s."""
    return all(0 <= v - s < len(t) and t[v - s] == i + s for i, v in enumerate(t))


def channel2(x, y, s1=0, s2=0):
    """Returns True if the tuples x and y satisfy channel(x, y) with start indexes s1 and s2 (equivalence only when |x| = |y|)."""
    if any(not (0 <= v - s2 < len(y) and y[v - s2] == i + s1) for i, v in enumerate(x)):
        return False
    return len(x) < len(y) or all(0 <= v - s1 < len(x) and x[v - s1] == j + s2 for j, v in enumerate(y))


def channel3(b, z, s=0):
    """Returns True if the tuple b of 0/1 values and the value z satisfy channel(b, z) with start index s."""
    return sum(b) == 1 and 0 <= z - s < len(b) and b[z - s] == 1


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


def arrays(*specs):
    """Returns the code declaring the specified arrays, given as (name, size, dom)."""
    return "".join(f"{name} = VarArray(size={n}, dom={dom})\n" for name, n, dom in specs)


X4 = arrays(("x", 4, "range(4)"))
D4 = [range(4)] * 4
XY4 = arrays(("x", 4, "range(4)"), ("y", 4, "range(4)"))
BZ = arrays(("b", 4, "{0, 1}")) + "z = Var(dom=range(4))\n"
DBZ = [range(2)] * 4 + [range(4)]


# ------------------------------------------------------------------------------------------------------- one list

@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_channel_one_list(run, solver, n):
    check(run, solver, arrays(("x", n, f"range({n})")) + "satisfy(Channel(x))", [range(n)] * n, lambda *t: channel1(t))


@pytest.mark.parametrize("within", ["x", "x[:]", "tuple(x)", "[x[0], x[1], x[2], x[3]]", "(x[i] for i in range(4))", "[x[:2], x[2:]]"])
def test_channel_one_list_forms(run, solver, within):
    check(run, solver, X4 + f"satisfy(Channel({within}))", D4, lambda *t: channel1(t))


def test_channel_one_list_on_a_matrix(run, solver):
    # the matrix is flattened
    check(run, solver, "m = VarArray(size=[2, 2], dom=range(4))\nsatisfy(Channel(m))", D4, lambda *t: channel1(t))


def test_channel_one_list_in_another_order(run, solver):
    check(run, solver, X4 + "satisfy(Channel([x[2], x[0], x[3], x[1]]))", D4, lambda a, b, c, d: channel1((c, a, d, b)))


# ------------------------------------------------------------------------------------------------------ two lists

@pytest.mark.parametrize("n", [2, 3, 4])
def test_channel_two_lists(run, solver, n):
    code = arrays(("x", n, f"range({n})"), ("y", n, f"range({n})")) + "satisfy(Channel(x, y))"
    check(run, solver, code, [range(n)] * (2 * n), lambda *t: channel2(t[:n], t[n:]))


@pytest.mark.parametrize("lists", ["x, y", "x[:], y[:]", "tuple(x), list(y)", "[x[:2], x[2:]], [y[:2], y[2:]]", "(v for v in x), (v for v in y)",
                                   "list1=x, list2=y"])
def test_channel_two_lists_forms(run, solver, lists):
    check(run, solver, XY4 + f"satisfy(Channel({lists}))", [range(4)] * 8, lambda *t: channel2(t[:4], t[4:]))


def test_channel_two_lists_swapped(run, solver):
    check(run, solver, XY4 + "satisfy(Channel(y, x))", [range(4)] * 8, lambda *t: channel2(t[4:], t[:4]))


def test_channel_two_lists_in_both_directions(run, solver):
    check(run, solver, XY4 + "satisfy(Channel(x, y), Channel(y, x))", [range(4)] * 8, lambda *t: channel2(t[:4], t[4:]))


def test_channel_two_lists_being_the_same_list(run, solver):
    # x[i] = j iff x[j] = i: an involution
    check(run, solver, X4 + "satisfy(Channel(x, x))", D4, lambda *t: channel2(t, t))


@pytest.mark.parametrize("n1, n2", [(2, 3), (2, 4), (3, 4)])
def test_channel_two_lists_of_different_sizes(run, solver, n1, n2):
    # with |X| < |Y|, an implication only: the variables of Y not targeted by X are free
    code = arrays(("x", n1, f"range({n2})"), ("y", n2, f"range({n1})")) + "satisfy(Channel(x, y))"
    check(run, solver, code, [range(n2)] * n1 + [range(n1)] * n2, lambda *t: channel2(t[:n1], t[n1:]))


def test_channel_two_lists_of_different_sizes_with_the_values_of_y_out_of_the_indexes_of_x(run, solver):
    code = arrays(("x", 2, "range(3)"), ("y", 3, "range(3)")) + "satisfy(Channel(x, y))"
    check(run, solver, code, [range(3)] * 5, lambda *t: channel2(t[:2], t[2:]))


# --------------------------------------------------------------------------------------------- a list and a value

@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_channel_with_a_value(run, solver, n):
    code = arrays(("b", n, "{0, 1}")) + f"z = Var(dom=range({n}))\nsatisfy(Channel(b, z))"
    check(run, solver, code, [range(2)] * n + [range(n)], lambda *t: channel3(t[:-1], t[-1]))


@pytest.mark.parametrize("args", ["b, z", "b, [z]", "b[:], z", "[b[:2], b[2:]], z", "list1=b, list2=z"])
def test_channel_with_a_value_forms(run, solver, args):
    check(run, solver, BZ + f"satisfy(Channel({args}))", DBZ, lambda *t: channel3(t[:4], t[4]))


def test_channel_with_a_value_being_a_variable_of_an_array(run, solver):
    code = arrays(("b", 4, "{0, 1}"), ("x", 2, "range(4)")) + "satisfy(Channel(b, x[1]))"
    check(run, solver, code, [range(2)] * 4 + [range(4)] * 2, lambda *t: channel3(t[:4], t[5]))


def test_channel_with_a_value_being_in_the_list(run, solver, request):
    bug_for(request, "ACE", ACE_VALUE)  # the domain of b[1] is not 0..2
    check(run, solver, arrays(("b", 3, "{0, 1}")) + "satisfy(Channel(b, b[1]))", [range(2)] * 3, lambda *t: channel3(t, t[1]))


@pytest.mark.parametrize("dom, values", [("range(6)", range(6)), ("range(-2, 4)", range(-2, 4)), ("range(1, 4)", range(1, 4)), ("{0, 2}", [0, 2])],
                         ids=["larger", "negative values", "without 0", "with holes"])
def test_channel_with_a_value_whose_domain_is_not_the_indexes(run, solver, request, dom, values):
    bug_for(request, "ACE", ACE_VALUE)
    if any(not 0 <= v < 4 for v in values):
        bug_for(request, "COSOCO", COSOCO_VALUE)
    code = arrays(("b", 4, "{0, 1}")) + f"z = Var(dom={dom})\nsatisfy(Channel(b, z))"
    check(run, solver, code, [range(2)] * 4 + [values], lambda *t: channel3(t[:4], t[4]))


# ------------------------------------------------------------------------------------------ values out of the indexes

@pytest.mark.parametrize("dom, values", [("range(6)", range(6)), ("range(-1, 4)", range(-1, 4)), ("range(1, 5)", range(1, 5))],
                         ids=["larger", "negative values", "shifted"])
def test_channel_one_list_with_values_out_of_the_indexes(run, solver, request, dom, values):
    if dom != "range(1, 5)":  # with as many values as indexes, ACE does not fail (and there is no solution)
        bug_for(request, "ACE", ACE_RANGE)
    bug_for(request, "COSOCO", COSOCO_RANGE)
    check(run, solver, arrays(("x", 4, dom)) + "satisfy(Channel(x))", [values] * 4, lambda *t: channel1(t))


def test_channel_one_list_with_domains_with_holes(run, solver, request):
    # the domains do not contain all the indexes
    bug_for(request, "ACE", ACE_RANGE)
    check(run, solver, arrays(("x", 4, "{0, 2, 3}")) + "satisfy(Channel(x))", [[0, 2, 3]] * 4, lambda *t: channel1(t))


@pytest.mark.parametrize("domx, valx", [("range(1, 4)", range(1, 4)), ("{0, 1, 3}", [0, 1, 3])], ids=["shifted", "with a hole"])
def test_channel_two_lists_with_as_many_values_as_indexes(run, solver, request, domx, valx):
    # the values of x are not the indexes of y, although there are as many: there is no solution (ACE finds 6 solutions)
    bug_for(request, "ACE", ACE_RANGE)
    code = arrays(("x", 3, domx), ("y", 3, "range(3)")) + "satisfy(Channel(x, y))"
    check(run, solver, code, [valx] * 3 + [range(3)] * 3, lambda *t: channel2(t[:3], t[3:]))


def test_channel_two_lists_of_different_sizes_with_shifted_values(run, solver, request):
    bug_for(request, "ACE", ACE_RANGE)  # ACE finds 12 wrong solutions, and none of the 4 expected ones
    code = arrays(("x", 2, "range(1, 4)"), ("y", 3, "range(2)")) + "satisfy(Channel(x, y))"
    check(run, solver, code, [range(1, 4)] * 2 + [range(2)] * 3, lambda *t: channel2(t[:2], t[2:]))


@pytest.mark.parametrize("domx, valx, domy, valy", [
    ("range(5)", range(5), "range(4)", range(4)),
    ("range(4)", range(4), "range(-1, 4)", range(-1, 4)),
    ("range(5)", range(5), "range(-1, 4)", range(-1, 4)),
], ids=["x larger", "y negative", "both"])
def test_channel_two_lists_with_values_out_of_the_indexes(run, solver, request, domx, valx, domy, valy):
    bug_for(request, "ACE", ACE_RANGE)
    if domx == "range(5)":  # COSOCO crashes when a value of x is 2 (or more) above the last index of y
        bug_for(request, "COSOCO", COSOCO_RANGE)
    code = arrays(("x", 3, domx), ("y", 3, domy)) + "satisfy(Channel(x, y))"
    check(run, solver, code, [valx] * 3 + [valy] * 3, lambda *t: channel2(t[:3], t[3:]))


def test_channel_two_lists_of_different_sizes_with_values_out_of_the_indexes(run, solver, request):
    bug_for(request, "ACE", ACE_RANGE)
    bug_for(request, "COSOCO", COSOCO_RANGE)
    code = arrays(("x", 2, "range(5)"), ("y", 3, "range(-1, 3)")) + "satisfy(Channel(x, y))"
    check(run, solver, code, [range(5)] * 2 + [range(-1, 3)] * 3, lambda *t: channel2(t[:2], t[2:]))


# --------------------------------------------------------------------------------------------------- start indexes

@pytest.mark.parametrize("s", [1, 2, -1])
def test_channel_one_list_with_a_start_index(run, solver, s):
    if solver in ("ACE", "COSOCO"):
        pytest.skip(ACE_START_INDEX if solver == "ACE" else COSOCO_START_INDEX_ONE_LIST)
    code = arrays(("x", 3, f"range({s}, {s + 3})")) + f"satisfy(Channel(x, start_index1={s}))"
    check(run, solver, code, [range(s, s + 3)] * 3, lambda *t: channel1(t, s))


@pytest.mark.parametrize("s1, s2", [(1, 0), (0, 1), (1, 2), (2, 1), (1, 1)])
def test_channel_two_lists_with_start_indexes(run, solver, request, s1, s2):
    # the values of x are indexes of y (starting at s2), and the values of y are indexes of x (starting at s1)
    if solver == "ACE":
        pytest.skip(ACE_START_INDEX)
    bug_for(request, "COSOCO", COSOCO_START_INDEX)
    if s1 != s2:
        bug_for(request, "CHOCO", CHOCO_START_INDEXES)
    code = arrays(("x", 3, "range(5)"), ("y", 3, "range(5)"))
    check(run, solver, code + f"satisfy(Channel(x, y, start_index1={s1}, start_index2={s2}))", [range(5)] * 6,
          lambda *t: channel2(t[:3], t[3:], s1, s2))


def test_channel_two_lists_of_different_sizes_with_start_indexes(run, solver, request):
    if solver == "ACE":
        pytest.skip(ACE_START_INDEX)
    bug_for(request, "COSOCO", COSOCO_START_INDEX)
    code = arrays(("x", 2, "range(1, 4)"), ("y", 3, "range(2, 4)"))
    check(run, solver, code + "satisfy(Channel(x, y, start_index1=2, start_index2=1))", [range(1, 4)] * 2 + [range(2, 4)] * 3,
          lambda *t: channel2(t[:2], t[2:], 2, 1))


@pytest.mark.parametrize("s", [1, -1])
def test_channel_with_a_value_and_a_start_index(run, solver, request, s):
    bug_for(request, "ACE", ACE_VALUE)
    bug_for(request, "COSOCO", COSOCO_START_INDEX)
    code = arrays(("b", 4, "{0, 1}")) + f"z = Var(dom=range({s}, {s + 4}))\nsatisfy(Channel(b, z, start_index1={s}))"
    check(run, solver, code, [range(2)] * 4 + [range(s, s + 4)], lambda *t: channel3(t[:4], t[4], s))


def test_channel_with_start_indexes_being_0(run, solver):
    check(run, solver, XY4 + "satisfy(Channel(x, y, start_index1=0, start_index2=0))", [range(4)] * 8, lambda *t: channel2(t[:4], t[4:]))


# ----------------------------------------------------------------------------------------------- arrays with holes

def test_channel_one_list_with_holes(run):
    # the index of a variable in the list would not be its index in the array: an explicit error is expected (as for Element, #283)
    r = run("x = VarArray(size=4, dom=lambda i: None if i == 1 else range(4))\nsatisfy(Channel(x))")
    assert_fails(r)
    assert "has holes (None)" in r.stdout + r.stderr, r.report()


@pytest.mark.parametrize("constraint", ["Channel(x, h)", "Channel(h, y)", "Channel(c, z)"])
def test_channel_lists_with_holes(run, constraint):
    code = arrays(("x", 3, "range(5)"), ("y", 5, "range(4)"), ("h", 5, "lambda i: None if i == 1 else range(5)"),
                  ("c", 4, "lambda i: None if i == 1 else {0, 1}")) + "z = Var(dom=range(4))\n"
    r = run(code + f"satisfy({constraint})")
    assert_fails(r)
    assert "has holes (None)" in r.stdout + r.stderr, r.report()


# ---------------------------------------------------------------------------------------------- repeated variables

@pytest.mark.parametrize("code, domains, predicate", [
    (X4 + "satisfy(Channel([x[0], x[0], x[2], x[3]]))", [range(4)] * 3, lambda a, c, d: channel1((a, a, c, d))),
    (arrays(("x", 3, "range(3)"), ("y", 3, "range(3)")) + "satisfy(Channel(x, [y[0], y[0], y[2]]))", [range(3)] * 5,
     lambda a, b, c, d, e: channel2((a, b, c), (d, d, e))),
    (arrays(("x", 3, "range(3)"), ("y", 3, "range(3)")) + "satisfy(Channel([x[0], x[0], x[2]], y))", [range(3)] * 5,
     lambda a, c, d, e, f: channel2((a, a, c), (d, e, f))),
    (arrays(("b", 2, "{0, 1}")) + "z = Var(dom=range(3))\nsatisfy(Channel([b[0], b[0], b[1]], z))", [range(2)] * 2 + [range(3)],
     lambda a, b, z: channel3((a, a, b), z)),
    (arrays(("x", 2, "range(3)"), ("y", 3, "range(2)")) + "satisfy(Channel(x, [y[0], y[0], y[2]]))", [range(3)] * 2 + [range(2)] * 3,
     lambda a, b, d, free, e: channel2((a, b), (d, d, e))),  # y[1] is in no constraint
], ids=["one list", "second list", "first list", "list with a value", "second list longer"])
def test_channel_with_a_repeated_variable(run, solver, request, code, domains, predicate):
    # a repeated variable has the same value at two indexes (with lists, there is then no solution)
    if "y[0], y[0]" in code or "x[0], x[0], x[2], x[3]" in code:  # repeated in the list given to element by ACE
        bug_for(request, "ACE", ACE_REPEATED)
    if "x = VarArray(size=2" in code:  # the second list is longer: no allDifferent posted by COSOCO
        bug_for(request, "COSOCO", COSOCO_REPEATED_WRONG)
    elif solver == "COSOCO" and "z = Var" not in code:  # allDifferent posted by COSOCO (lists of the same size)
        pytest.skip(COSOCO_REPEATED)
    check(run, solver, code, domains, predicate)


# ----------------------------------------------------------------------------------------------- degenerated cases

@pytest.mark.parametrize("code, domains, predicate", [
    (X4 + "satisfy(Channel([x[0]]), x[3] != 1)", D4, lambda *t: t[0] == 0 and t[3] != 1),  # x[0] = j implies x[j] = 0, with j = 0
    (X4 + "satisfy(Channel(x[0]), x[3] != 1)", D4, lambda *t: t[0] == 0 and t[3] != 1),
    (X4 + "satisfy(Channel([x[0]], start_index1=2), x[3] != 1)", D4, lambda *t: t[0] == 2 and t[3] != 1),
    (XY4 + "satisfy(Channel([x[0]], [y[0]]), x[3] != 1)", [range(4)] * 8, lambda *t: t[0] == 0 and t[4] == 0 and t[3] != 1),
    (XY4 + "satisfy(Channel([x[0]], [y[0]], start_index1=1, start_index2=2))", [range(4)] * 8, lambda *t: t[0] == 2 and t[4] == 1),
    (XY4 + "satisfy(Channel([x[0]], y[:3]), x[3] != 1)", [range(4)] * 8, lambda *t: 0 <= t[0] < 3 and t[4 + t[0]] == 0 and t[3] != 1),
    (XY4 + "satisfy(Channel([x[0]], y[:3], start_index1=1, start_index2=1))", [range(4)] * 8, lambda *t: 1 <= t[0] <= 3 and t[3 + t[0]] == 1),
    (BZ + "satisfy(Channel([b[0]], z), b[3] != 1)", DBZ, lambda *t: t[0] == 1 and t[4] == 0 and t[3] != 1),
    (BZ + "satisfy(Channel([b[0]], z, start_index1=3))", DBZ, lambda *t: t[0] == 1 and t[4] == 3),
    (X4 + "satisfy(Channel([]), x[3] != 1)", D4, lambda *t: t[3] != 1),  # no constraint
    (X4 + "satisfy(Channel([], x), x[3] != 1)", D4, lambda *t: t[3] != 1),  # no constraint (nothing imposed on the second list)
], ids=["one variable", "one variable (not in a list)", "one variable and a start index", "two lists of one variable",
        "two lists of one variable and start indexes", "first list of one variable", "first list of one variable and start indexes",
        "a list of one variable and a value", "a list of one variable, a value and a start index", "no variable", "first list empty"])
def test_channel_degenerated(run, solver, code, domains, predicate):
    r = check(run, solver, code, domains, predicate)
    assert r.xml is None or r.xml.find("constraints//channel") is None, r.report()


@pytest.mark.parametrize("constraint", ["Channel([])", "Channel([], x)"])
def test_channel_discarded_with_a_warning(run, constraint):
    r = run(X4 + f"satisfy({constraint}, x[0] == 1)")
    assert r.ok, r.report()
    assert "A constraint Channel discarded because defined with 0 variables" in r.stdout + r.stderr, r.report()


# ------------------------------------------------------------------------------------------------ examples of the doc

def test_channel_example_dual_model_of_queens(run, solver):
    # the first example of the documentation (4 queens instead of 8, with the constraints on diagonals)
    code = (XY4 + "satisfy(Channel(x, y), AllDifferent(x[i] + i for i in range(4)), AllDifferent(x[i] - i for i in range(4)))")
    check(run, solver, code, [range(4)] * 8,
          lambda *t: channel2(t[:4], t[4:]) and len({t[i] + i for i in range(4)}) == 4 and len({t[i] - i for i in range(4)}) == 4)


def test_channel_example_with_a_value(run, solver):
    # the second example of the documentation
    code = arrays(("b", 8, "{0, 1}")) + "z = Var(dom=range(8))\nsatisfy(Channel(b, z))"
    check(run, solver, code, [range(2)] * 8 + [range(8)], lambda *t: channel3(t[:8], t[8]))


# ---------------------------------------------------------------------------------------------------------- groups

def test_channel_on_the_rows_of_a_matrix(run, solver):
    check(run, solver, "m = VarArray(size=[2, 3], dom=range(3))\nsatisfy(Channel(m[i]) for i in range(2))", [range(3)] * 6,
          lambda *t: channel1(t[:3]) and channel1(t[3:]))


def test_channel_with_other_constraints(run, solver):
    code = XY4 + "satisfy(Channel(x, y), x[0] == 2, y[1] != 0)"
    check(run, solver, code, [range(4)] * 8, lambda *t: channel2(t[:4], t[4:]) and t[0] == 2 and t[5] != 0)


def test_channels_sharing_a_list(run, solver):
    code = arrays(("x", 3, "range(3)"), ("y", 3, "range(3)"), ("w", 3, "range(3)")) + "satisfy(Channel(x, y), Channel(y, w))"
    check(run, solver, code, [range(3)] * 9, lambda *t: channel2(t[:3], t[3:6]) and channel2(t[3:6], t[6:]))


# ------------------------------------------------------------------------------------------------ logical contexts

@pytest.mark.parametrize("constraint", ["~Channel(x)", "Channel(x, y) | (x[0] == 1)", "Channel(x, y) & (x[0] == 1)", "imply(x[0] == 1, Channel(x))",
                                        "Channel(b, x[0]) | (x[1] == 1)", "either(Channel(x), x[0] == 1)", "Channel(x, y) == 1"])
def test_channel_in_logical_expressions(run, constraint):
    # a constraint channel cannot be reified: an explicit error is raised
    r = run(XY4 + arrays(("b", 4, "{0, 1}")) + f"satisfy({constraint})")
    assert_fails(r)
    assert "A constraint channel cannot be in a logical expression" in r.stderr + r.stdout, r.report()


# ------------------------------------------------------------------------------------------------------- option -mini

def test_channel_two_lists_mini(run, solver):
    # with -mini, element constraints are posted
    r = check(run, solver, XY4 + "satisfy(Channel(x, y))", [range(4)] * 8, lambda *t: channel2(t[:4], t[4:]), args=["-mini"])
    assert r.xml.find("constraints//channel") is None, r.report()


def test_channel_one_list_mini(run, solver):
    # with -mini, the constraint channel on one list is kept (decision taken for #317)
    r = check(run, solver, X4 + "satisfy(Channel(x))", D4, lambda *t: channel1(t), args=["-mini"])
    assert r.xml.find("constraints/channel") is not None, r.report()


@pytest.mark.parametrize("code, message", [
    (arrays(("x", 2, "range(3)"), ("y", 3, "range(2)")) + "satisfy(Channel(x, y))", "two lists of different sizes"),
    (BZ + "satisfy(Channel(b, z))", "a list of 0/1 variables and a variable (value)"),
    (arrays(("x", 3, "range(1, 4)"), ("y", 3, "range(3)")) + "satisfy(Channel(x, y, start_index2=1))", "start indexes"),
    (X4 + "satisfy(Channel(x, start_index1=1))", "start indexes"),
], ids=["lists of different sizes", "a list and a value", "start index", "one list and a start index"])
def test_channel_mini_refused(run, code, message):
    # with -mini, the forms that cannot be posted with the constraints of the mini-tracks are refused explicitly (#317)
    r = run(code, args=["-mini"])
    assert_fails(r)
    assert message + " is not accepted with the option -mini" in r.stdout + r.stderr, r.report()


# ----------------------------------------------------------------------------------------------------- XCSP3 files

def _children(c):
    return [(e.tag, " ".join(e.text.split())) for e in c] if len(c) > 0 else [("list", " ".join(c.text.split()))]


@pytest.mark.parametrize("constraint, expected", [
    ("Channel(x)", [("list", "x[]")]),
    ("Channel(x[1:] + x[:1])", [("list", "x[1..3] x[0]")]),
    ("Channel(x, y)", [("list", "x[]"), ("list", "y[]")]),
    ("Channel(y, x)", [("list", "y[]"), ("list", "x[]")]),
    ("Channel(x[:2], y[:3])", [("list", "x[0] x[1]"), ("list", "y[0..2]")]),
    ("Channel(b, z)", [("list", "b[]"), ("value", "z")]),
    ("Channel(b, [z])", [("list", "b[]"), ("value", "z")]),
    ("Channel(b[:2], x[0])", [("list", "b[0] b[1]"), ("value", "x[0]")]),
    ("Channel(b, x)", [("list", "b[]"), ("list", "x[]")]),  # two lists, even if the first one has 0/1 variables
])
def test_xcsp3_channel(run, constraint, expected):
    r = run(XY4 + arrays(("b", 4, "{0, 1}")) + f"z = Var(dom=range(4))\nsatisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/channel")
    assert c is not None, r.report()
    assert _children(c) == expected, r.report()


@pytest.mark.parametrize("constraint, expected", [
    ("Channel(x, start_index1=1)", [("list", "x[]", {"startIndex": "1"})]),
    ("Channel(x, y, start_index1=1, start_index2=2)", [("list", "x[]", {"startIndex": "1"}), ("list", "y[]", {"startIndex": "2"})]),
    ("Channel(x, y, start_index2=-1)", [("list", "x[]", {}), ("list", "y[]", {"startIndex": "-1"})]),
    ("Channel(x[:2], y, start_index1=3)", [("list", "x[0] x[1]", {"startIndex": "3"}), ("list", "y[]", {})]),
    ("Channel(b, z, start_index1=1)", [("list", "b[]", {"startIndex": "1"}), ("value", "z", {})]),
    ("Channel(x, y, start_index1=0, start_index2=0)", [("list", "x[]", {}), ("list", "y[]", {})]),
])
def test_xcsp3_channel_with_start_indexes(run, constraint, expected):
    # the start indexes are written in the XCSP3 file (attribute startIndex of the lists): the solvers handle them, or say that they cannot (#313)
    r = run(XY4 + arrays(("b", 4, "{0, 1}")) + f"z = Var(dom=range(4))\nsatisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/channel")
    assert c is not None and len(c) > 0, r.report()
    assert [(e.tag, " ".join(e.text.split()), dict(e.attrib)) for e in c] == expected, r.report()


def test_xcsp3_channel_with_start_indexes_in_a_group(run):
    r = run("m = VarArray(size=[2, 3], dom=range(1, 4))\nsatisfy(Channel(m[i], start_index1=1) for i in range(2))")
    assert r.ok, r.report()
    lists = r.xml.findall("constraints//channel/list")
    assert [(" ".join(e.text.split()), dict(e.attrib)) for e in lists] == [("m[0][]", {"startIndex": "1"}), ("m[1][]", {"startIndex": "1"})], r.report()


# ------------------------------------------------------------------------------- 0/1 variables of fixed value (#316)

def test_channel_with_a_value_and_a_variable_of_domain_0(run, solver, request):
    # a variable of domain {0} is accepted in the list of 0/1 variables
    bug_for(request, "ACE", ACE_VALUE_DOMAIN_0)
    code = "b = VarArray(size=4, dom=lambda i: {0} if i == 1 else {0, 1})\nz = Var(dom=range(4))\nsatisfy(Channel(b, z))"
    check(run, solver, code, [range(2), range(1), range(2), range(2), range(4)], lambda *t: channel3(t[:4], t[4]))


@pytest.mark.parametrize("s", [0, 1])
def test_channel_with_a_value_and_a_variable_of_domain_1(run, solver, s):
    # a variable of domain {1} gives the index of the unique 1: the constraint is simplified, with a warning
    code = (f"b = VarArray(size=4, dom=lambda i: {{1}} if i == 2 else {{0}} if i == 0 else {{0, 1}})\nz = Var(dom=range({s}, {s + 4}))\n"
            f"satisfy(Channel(b, z, start_index1={s}))")
    r = check(run, solver, code, [range(1), range(2), range(1, 2), range(2), range(s, s + 4)], lambda *t: channel3(t[:4], t[4], s))
    assert r.xml.find("constraints//channel") is None, r.report()
    assert "A constraint Channel simplified because b[2] has the domain {1}" in r.stdout + r.stderr, r.report()


def test_channel_with_a_value_and_two_variables_of_domain_1(run):
    r = run("b = VarArray(size=4, dom=lambda i: {1} if i < 2 else {0, 1})\nz = Var(dom=range(4))\nsatisfy(Channel(b, z))")
    assert_fails(r)
    assert "several variables of the list have the domain {1}, which is the case of b[0] and b[1]" in r.stdout + r.stderr, r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("arguments", [
    "x, 'a'",
    "x, y, 1",
    "b, 2",
    "x, start_index1='a'",
    "x, y, start_index2=1.5",
    "x, start_index2=1",  # start_index2 without a second list
    "[x[0] + 1, x[1], x[2], x[3]]",  # expressions are not accepted
    "[x[0], 1, x[2], x[3]]",
    "x, [y[0] + 1, y[1], y[2], y[3]]",
    "b, z + 1",
    "None",
    "x, []",
    "w, x",  # the first list is longer than the second one
    "x, z",  # a list and a value, the list not being of 0/1 variables
    "x, [y[0]]",
    "b, z, start_index2=1",  # start_index2 without a second list (silently discarded)
])
def test_invalid_channel(run, arguments):
    code = XY4 + arrays(("w", 6, "range(6)"), ("b", 4, "{0, 1}")) + "z = Var(dom=range(4))\n"
    assert_fails(run(code + f"satisfy(Channel({arguments}))"))


@pytest.mark.parametrize("arguments, message", [
    ("None", "requires a list of variables as first argument"),
    ("x, []", "must not be longer than the second one"),
    ("w, x", "must not be longer than the second one"),
    ("x, z", "requires a list of 0/1 variables, which is not the case of x[0]"),
    ("x, [y[0]]", "requires a list of 0/1 variables, which is not the case of x[0]"),
    ("b, z, start_index2=1", "start_index2 is defined while the second argument of Channel() is a variable (value)"),
    ("[], z", "requires a non-empty list of 0/1 variables"),
    ("[x[0] + 1, x[1], x[2], x[3]]", "(expressions are not accepted)"),
    ("x, [y[0] + 1, y[1], y[2], y[3]]", "(expressions are not accepted)"),
    ("b, z + 1", "(expressions are not accepted)"),
])
def test_invalid_channel_message(run, arguments, message):
    code = XY4 + arrays(("w", 6, "range(6)"), ("b", 4, "{0, 1}")) + "z = Var(dom=range(4))\n"
    r = run(code + f"satisfy(Channel({arguments}))")
    assert_fails(r)
    assert message in r.stdout + r.stderr, r.report()
    assert "A node is evaluated as a Boolean" not in r.stdout + r.stderr, r.report()


def test_channel_on_symbolic_variables(run, solver):
    pytest.skip(SYMBOLIC)
