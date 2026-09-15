"""
Tests of the constraint AllDifferentList of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#AllDifferentList): the function AllDifferentList(), with the parameter excepting.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
"""

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
ALL = ("ACE", "CHOCO", "COSOCO")
INVALID = "#122: invalid arguments of AllDifferentList() are accepted, or reported without explicit message"
COSOCO_EXCEPT = "xcsp3team/cosoco#78: cosoco loses solutions or fails with except (here, allDifferent-list with except)"
COSOCO_NEGATIVE = "xcsp3team/cosoco#79: cosoco says that allDifferent-list with negative values is unsatisfiable"

# The cases that a solver says it does not handle, and the symbolic lists (not reported)
CHOCO_EXCEPT = "CHOCO does not handle allDifferent-list with except (RuntimeException: UNSUPPORTED)"
SYMBOLIC = "allDifferent-list on symbolic variables is not part of XCSP3-core (ACE and CHOCO fail, cosoco has no symbolic variables)"


def different_lists(lists, excepting=()):
    """Returns True if the lists (tuples) are all different, the tuples in excepting being ignored."""
    kept = [tuple(t) for t in lists if tuple(t) not in excepting]
    return len(set(kept)) == len(kept)


def rows(t, m):
    return [t[i:i + m] for i in range(0, len(t), m)]


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


X32 = "x = VarArray(size=[3, 2], dom=range(3))\n"
D32 = [range(3)] * 6


# ------------------------------------------------------------------------------------------------------------ forms

@pytest.mark.parametrize("constraint", [
    "AllDifferentList(x)",
    "AllDifferentList(x[0], x[1], x[2])",
    "AllDifferentList([x[0], x[1], x[2]])",
    "AllDifferentList(x[i] for i in range(3))",
    "AllDifferentList([x[0][0], x[0][1]], [x[1][0], x[1][1]], [x[2][0], x[2][1]])",
    "AllDifferentList((x[0][0], x[0][1]), (x[1][0], x[1][1]), (x[2][0], x[2][1]))",
    "AllDifferentList(tuple(x[i]) for i in range(3))",
    "AllDifferentList(x[::-1])",
])
def test_alldifferentlist_forms(run, solver, constraint):
    check(run, solver, X32 + f"satisfy({constraint})", D32, lambda *t: different_lists(rows(t, 2)))


@pytest.mark.parametrize("n, m, d", [(2, 2, 2), (3, 2, 2), (4, 2, 2), (5, 2, 2), (2, 3, 2), (3, 1, 3), (4, 1, 3)],
                         ids=["2 lists", "3 lists", "4 lists (all the pairs)", "5 lists (pigeonhole)", "lists of 3 variables", "lists of 1 variable", "lists of 1 variable (pigeonhole)"])
def test_alldifferentlist_sizes(run, solver, n, m, d):
    check(run, solver, f"x = VarArray(size=[{n}, {m}], dom=range({d}))\nsatisfy(AllDifferentList(x))", [range(d)] * (n * m), lambda *t: different_lists(rows(t, m)))


@pytest.mark.parametrize("constraint, text", [("AllDifferentList(x)", "x[][]"), ("AllDifferentList(x, excepting=(0,))", "x[][] except 0")])
def test_xcsp3_alldifferentlist_on_lists_of_one_variable(run, constraint, text):
    # allDifferent-list requires lists of at least two variables: allDifferent is posted on the variables
    r = run(f"x = VarArray(size=[3, 1], dom=range(3))\nsatisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/allDifferent")
    assert c is not None, r.report()
    lst, exc = c.find("list"), c.find("except")
    assert (lst.text if lst is not None else c.text).strip() + ("" if exc is None else " except " + exc.text.strip()) == text, r.report()


def test_alldifferentlist_on_columns(run, solver):
    check(run, solver, X32 + "satisfy(AllDifferentList(columns(x)))", D32, lambda *t: different_lists(list(zip(*rows(t, 2)))))


def test_alldifferentlist_on_different_domains(run, solver):
    check(run, solver, "x = VarArray(size=[3, 2], dom=lambda i, j: range(i + j + 1))\nsatisfy(AllDifferentList(x))",
          [range(i + j + 1) for i in range(3) for j in range(2)], lambda *t: different_lists(rows(t, 2)))


def test_alldifferentlist_on_negative_values(run, solver, request):
    bug_for(request, "COSOCO", COSOCO_NEGATIVE)
    check(run, solver, "x = VarArray(size=[3, 2], dom=range(-1, 1))\nsatisfy(AllDifferentList(x))", [range(-1, 1)] * 6, lambda *t: different_lists(rows(t, 2)))


def test_alldifferentlist_with_shared_variables(run, solver):
    # a variable can occur in several lists: (x0, x1) and (x1, x0) are different iff x0 != x1
    check(run, solver, "x = VarArray(size=3, dom=range(3))\nsatisfy(AllDifferentList([x[0], x[1]], [x[1], x[0]], [x[2], x[2]]))", [range(3)] * 3,
          lambda a, b, c: different_lists([(a, b), (b, a), (c, c)]))


def test_alldifferentlist_on_symbolic_variables(run, solver):
    pytest.skip(SYMBOLIC)
    check(run, solver, "x = VarArray(size=[3, 2], dom={'a', 'b'})\nsatisfy(AllDifferentList(x))", [["a", "b"]] * 6, lambda *t: different_lists(rows(t, 2)))


def test_alldifferentlist_with_other_constraints(run, solver):
    # the example of the documentation (with fewer meetings)
    check(run, solver, X32 + "satisfy(AllDifferentList(x), x[0][0] == x[1][0], Sum(x[2]) == 1)", D32,
          lambda *t: different_lists(rows(t, 2)) and t[0] == t[2] and t[4] + t[5] == 1)


def test_alldifferentlist_in_a_group(run, solver):
    check(run, solver, "x = VarArray(size=[4, 2], dom=range(2))\nsatisfy([AllDifferentList(x[i], x[i + 1]) for i in range(3)])", [range(2)] * 8,
          lambda *t: all(different_lists(rows(t, 2)[i:i + 2]) for i in range(3)))


# ------------------------------------------------------------------------------------------------------- excepting

@pytest.mark.parametrize("excepting, tuples", [
    ("(0, 0)", {(0, 0)}),
    ("[0, 0]", {(0, 0)}),
    ("(1, 2)", {(1, 2)}),
    ("range(2)", {(0, 1)}),
    ("[(0, 0), (1, 1)]", {(0, 0), (1, 1)}),
    ("((0, 0), (2, 2))", {(0, 0), (2, 2)}),
    ("(5, 5)", {(5, 5)}),
    ("None", set()),
])
def test_alldifferentlist_excepting(run, solver, request, excepting, tuples):
    if excepting != "None":
        if solver == "CHOCO":
            pytest.skip(CHOCO_EXCEPT)
        if excepting != "(5, 5)":
            bug_for(request, "COSOCO", COSOCO_EXCEPT)
    check(run, solver, X32 + f"satisfy(AllDifferentList(x, excepting={excepting}))", D32, lambda *t: different_lists(rows(t, 2), tuples))


def test_alldifferentlist_excepting_with_other_constraints(run, solver):
    if solver == "CHOCO":
        pytest.skip(CHOCO_EXCEPT)
    # the example of the documentation (with fewer meetings): the pair (0, 0) means that the meeting is not scheduled
    check(run, solver, "x = VarArray(size=[3, 2], dom=range(2))\nsatisfy([Sum(x[i]) > 0 for i in (0, 1)], AllDifferentList(x, excepting=(0, 0)))",
          [range(2)] * 6, lambda *t: different_lists(rows(t, 2), {(0, 0)}) and sum(t[0:2]) > 0 and sum(t[2:4]) > 0)


# ----------------------------------------------------------------------------------------------- degenerated cases

@pytest.mark.parametrize("constraint", ["AllDifferentList([x[0]])", "AllDifferentList(x[0:1])"])
def test_alldifferentlist_with_a_single_list(run, solver, constraint):
    # with a single list, the constraint always holds (no constraint is posted)
    r = run(X32 + f"satisfy({constraint}, x[1][0] == 1, x[2][0] == 2)", solver=solver)
    if r.ok:
        assert_solutions(r, brute_force(D32, lambda *t: t[2] == 1 and t[4] == 2))
    else:
        assert_fails(r)


@pytest.mark.parametrize("constraint", ["AllDifferentList(x[0], x[0])", "AllDifferentList(x[0], x[1], x[0])"])
def test_alldifferentlist_with_a_repeated_list(run, constraint):
    # a list cannot be different from itself: an explicit error is reported (ACE fails on such constraints)
    r = run(X32 + f"satisfy({constraint})")
    assert_fails(r)
    assert "A list cannot be given several times to AllDifferentList(), which is the case of [x[0][0], x[0][1]]" in r.stdout, r.report()


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, lists, excepting", [
    ("AllDifferentList(x)", ["x[0][]", "x[1][]", "x[2][]"], None),
    ("AllDifferentList(x[0], x[2])", ["x[0][]", "x[2][]"], None),
    ("AllDifferentList(x, excepting=(0, 0))", ["x[0][]", "x[1][]", "x[2][]"], "(0,0)"),
    ("AllDifferentList(x, excepting=[(0, 0), (1, 2)])", ["x[0][]", "x[1][]", "x[2][]"], "(0,0)(1,2)"),
])
def test_xcsp3_alldifferentlist(run, constraint, lists, excepting):
    r = run(X32 + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/allDifferent")
    assert c is not None, r.report()
    found = [" ".join(e.text.split()) for e in c.findall("list")]
    assert len(found) == len(lists), r.report()
    exc = c.find("except")
    assert (None if exc is None else exc.text.strip()) == excepting


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("constraint", [
    pytest.param("AllDifferentList(x[0], [x[1][0]])", marks=bug(INVALID)),
    pytest.param("AllDifferentList([x[0][0], x[0][1]], [x[1][0], x[1][1], x[2][0]])", marks=bug(INVALID)),
    "AllDifferentList([x[0][0] + 1, x[0][1]], x[1])",
    "AllDifferentList(x[0], [0, 1])",
    "AllDifferentList(x, excepting=0)",
    pytest.param("AllDifferentList(x, excepting=(0,))", marks=bug(INVALID)),
    pytest.param("AllDifferentList(x, excepting=(0, 0, 0))", marks=bug(INVALID)),
    pytest.param("AllDifferentList(x, excepting=[(0, 0), (1,)])", marks=bug(INVALID)),
    "AllDifferentList(x, excepting=('a', 'b'))",
    "AllDifferentList(x, excepting=(0.5, 1))",
    pytest.param("AllDifferentList([])", marks=bug(INVALID)),
    pytest.param("AllDifferentList(None)", marks=bug(INVALID)),
])
def test_invalid_alldifferentlist(run, constraint):
    assert_fails(run(X32 + f"satisfy({constraint})"))


@bug(INVALID)
def test_alldifferentlist_on_an_array_with_holes(run):
    # a list with a hole (None) cannot be compared with complete lists
    assert_fails(run("x = VarArray(size=[3, 2], dom=lambda i, j: None if (i, j) == (1, 1) else range(2))\nsatisfy(AllDifferentList(x))"))
