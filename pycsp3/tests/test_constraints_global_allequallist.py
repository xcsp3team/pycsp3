"""
Tests of the constraint AllEqualList of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#AllEqualList): the function AllEqualList(), with the parameter excepting.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
"""

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
ALL = ("ACE", "CHOCO", "COSOCO")

# The symbolic lists (not reported)
SYMBOLIC = "allEqual-list on symbolic variables is not part of XCSP3-core (ACE and CHOCO fail, cosoco has no symbolic variables)"


def equal_lists(lists, excepting=()):
    """Returns True if the lists (tuples) are all equal, the tuples in excepting being ignored."""
    kept = {tuple(t) for t in lists if tuple(t) not in excepting}
    return len(kept) <= 1


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
    "AllEqualList(x)",
    "AllEqualList(x[0], x[1], x[2])",
    "AllEqualList([x[0], x[1], x[2]])",
    "AllEqualList(x[i] for i in range(3))",
    "AllEqualList([x[0][0], x[0][1]], [x[1][0], x[1][1]], [x[2][0], x[2][1]])",
    "AllEqualList((x[0][0], x[0][1]), (x[1][0], x[1][1]), (x[2][0], x[2][1]))",
    "AllEqualList(tuple(x[i]) for i in range(3))",
    "AllEqualList(x[::-1])",
])
def test_allequallist_forms(run, solver, constraint):
    check(run, solver, X32 + f"satisfy({constraint})", D32, lambda *t: equal_lists(rows(t, 2)))


@pytest.mark.parametrize("n, m, d", [(2, 2, 3), (3, 2, 2), (4, 2, 2), (2, 3, 2), (3, 3, 2), (2, 1, 3), (3, 1, 3)],
                         ids=["2 lists", "3 lists", "4 lists", "2 lists of 3 variables", "3 lists of 3 variables", "2 lists of 1 variable",
                              "3 lists of 1 variable"])
def test_allequallist_sizes(run, solver, n, m, d):
    # PyCSP3 posts x[0][j] == x[i][j] for each list i > 0 and each index j
    check(run, solver, f"x = VarArray(size=[{n}, {m}], dom=range({d}))\nsatisfy(AllEqualList(x))", [range(d)] * (n * m), lambda *t: equal_lists(rows(t, m)))


@pytest.mark.parametrize("constraint, text", [("AllEqualList(x)", "x[][]"), ("AllEqualList(x, excepting=(0,))", "x[][] except 0")])
def test_xcsp3_allequallist_on_lists_of_one_variable(run, constraint, text):
    # allEqual-list requires lists of at least two variables: allEqual is posted on the variables
    r = run(f"x = VarArray(size=[3, 1], dom=range(3))\nsatisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/allEqual")
    assert c is not None, r.report()
    lst, exc = c.find("list"), c.find("except")
    assert (lst.text if lst is not None else c.text).strip() + ("" if exc is None else " except " + exc.text.strip()) == text, r.report()


@pytest.mark.parametrize("size", ["[3, 2]", "[2, 3]"], ids=["2 columns", "3 columns"])
def test_allequallist_on_columns(run, solver, size):
    n, m = eval(size)
    check(run, solver, f"x = VarArray(size={size}, dom=range(2))\nsatisfy(AllEqualList(columns(x)))", [range(2)] * (n * m),
          lambda *t: equal_lists(list(zip(*rows(t, m)))))


def test_allequallist_on_different_domains(run, solver):
    check(run, solver, "x = VarArray(size=[3, 2], dom=lambda i, j: range(i + j, 4))\nsatisfy(AllEqualList(x))",
          [range(i + j, 4) for i in range(3) for j in range(2)], lambda *t: equal_lists(rows(t, 2)))


def test_allequallist_on_negative_values(run, solver):
    check(run, solver, "x = VarArray(size=[3, 2], dom=range(-2, 1))\nsatisfy(AllEqualList(x))", [range(-2, 1)] * 6, lambda *t: equal_lists(rows(t, 2)))


def test_allequallist_with_shared_variables(run, solver):
    # a variable can occur in several lists: (x0, x1) = (x1, x0) = (x2, x2) iff x0 = x1 = x2
    check(run, solver, "x = VarArray(size=3, dom=range(3))\nsatisfy(AllEqualList([x[0], x[1]], [x[1], x[0]], [x[2], x[2]]))", [range(3)] * 3,
          lambda a, b, c: equal_lists([(a, b), (b, a), (c, c)]))


def test_allequallist_on_symbolic_variables(run, solver):
    pytest.skip(SYMBOLIC)
    check(run, solver, "x = VarArray(size=[3, 2], dom={'a', 'b'})\nsatisfy(AllEqualList(x))", [["a", "b"]] * 6, lambda *t: equal_lists(rows(t, 2)))


def test_allequallist_with_other_constraints(run, solver):
    # the example of the documentation (with fewer roles)
    check(run, solver, X32 + "satisfy(AllEqualList(x), x[0][0] != x[0][1], Sum(x[2]) == 3)", D32,
          lambda *t: equal_lists(rows(t, 2)) and t[0] != t[1] and t[4] + t[5] == 3)


@pytest.mark.parametrize("k", [2, 3], ids=["windows of 2 lists", "windows of 3 lists"])
def test_allequallist_in_a_group(run, solver, k):
    check(run, solver, f"x = VarArray(size=[4, 2], dom=range(2))\nsatisfy([AllEqualList(x[i:i + {k}]) for i in range({5 - k})])", [range(2)] * 8,
          lambda *t: all(equal_lists(rows(t, 2)[i:i + k]) for i in range(5 - k)))


# ------------------------------------------------------------------------------------------------------- excepting

EXCEPTING = [
    ("(0, 0)", {(0, 0)}),
    ("[0, 0]", {(0, 0)}),
    ("(1, 2)", {(1, 2)}),
    ("range(2)", {(0, 1)}),
    ("[(0, 0), (1, 1)]", {(0, 0), (1, 1)}),
    ("((0, 0), (2, 2))", {(0, 0), (2, 2)}),
    ("[(0, 0), (1, 1), (2, 2)]", {(0, 0), (1, 1), (2, 2)}),
    ("(5, 5)", {(5, 5)}),
    ("[]", set()),
    ("None", set()),
]


@pytest.mark.parametrize("excepting, tuples", EXCEPTING, ids=[e for e, _ in EXCEPTING])
def test_allequallist_excepting(run, solver, excepting, tuples):
    check(run, solver, X32 + f"satisfy(AllEqualList(x, excepting={excepting}))", D32, lambda *t: equal_lists(rows(t, 2), tuples))


def test_allequallist_excepting_on_two_lists(run, solver):
    check(run, solver, X32 + "satisfy(AllEqualList(x[0], x[1], excepting=(0, 0)))", D32, lambda *t: equal_lists(rows(t, 2)[:2], {(0, 0)}))


def test_allequallist_excepting_with_other_constraints(run, solver):
    # the pair (0, 0) means that the team does not play
    check(run, solver, "x = VarArray(size=[3, 2], dom=range(3))\nsatisfy(AllEqualList(x, excepting=(0, 0)), Sum(x[0]) > 0, x[1][0] == 1)",
          D32, lambda *t: equal_lists(rows(t, 2), {(0, 0)}) and t[0] + t[1] > 0 and t[2] == 1)


# ----------------------------------------------------------------------------------------------- degenerated cases

@pytest.mark.parametrize("constraint", ["AllEqualList([x[0]])", "AllEqualList(x[0:1])"])
def test_allequallist_with_a_single_list(run, solver, constraint):
    # with a single list, the constraint always holds (no constraint is posted, and a warning is displayed)
    r = run(X32 + f"satisfy({constraint}, x[1][0] == 1, x[2][0] == 2)", solver=solver)
    if r.ok:
        assert "A constraint AllEqualList discarded because defined with 1 list" in r.stdout, r.report()
        assert_solutions(r, brute_force(D32, lambda *t: t[2] == 1 and t[4] == 2))
    else:
        assert_fails(r)


@pytest.mark.parametrize("constraint, predicate", [
    ("AllEqualList(x[0], x[0])", lambda *t: True),
    ("AllEqualList(x[0], x[1], x[0])", lambda *t: t[0:2] == t[2:4]),
    ("AllEqualList(x[0], x[0], excepting=(0, 0))", lambda *t: True),
], ids=["twice", "twice among three", "twice with excepting"])
def test_allequallist_with_a_repeated_list(run, solver, constraint, predicate):
    # a list is always equal to itself: the constraint holds on the other lists (or an error is reported)
    r = run(X32 + f"satisfy({constraint})", solver=solver)
    if r.ok:
        assert_solutions(r, brute_force(D32, predicate))
    else:
        assert_fails(r)


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, n_constraints", [
    pytest.param("AllEqualList(x)", 4, id="AllEqualList(x)"),  # x[0][j] == x[i][j] for i in 1..2 and j in 0..1
    pytest.param("AllEqualList(x[0], x[2], excepting=(0, 0))", 1, id="AllEqualList(x[0], x[2], excepting=(0, 0))"),  # one pair of lists
    pytest.param("AllEqualList(x, excepting=(1, 2))", 3, id="AllEqualList(x, excepting=(1, 2))"),  # three pairs of lists
    pytest.param("AllEqualList(x, excepting=[(0, 0), (1, 2)])", 3, id="AllEqualList(x, excepting=[(0, 0), (1, 2)])"),  # several tuples
    pytest.param("AllEqualList(x, excepting=[])", 4, id="AllEqualList(x, excepting=[])"),  # as without excepting
])
def test_xcsp3_allequallist(run, constraint, n_constraints):
    # allEqual-list is not part of XCSP3-core: a decomposition into intensional constraints is posted
    r = run(X32 + f"satisfy({constraint})")
    assert r.ok, r.report()
    assert next(r.xml.iter("allEqual"), None) is None, r.report()
    n = sum(len(g.findall("args")) for g in r.xml.iter("group")) + len(r.xml.findall("constraints/intension"))
    assert n == n_constraints, r.report()


def test_xcsp3_allequallist_on_two_lists(run):
    # the documentation says that, with two lists and no excepting, a group of intensional constraints x[i] == y[i] is posted
    r = run(X32 + "satisfy(AllEqualList(x[0], x[2]))")
    assert r.ok, r.report()
    assert r.xml.find("constraints/allEqual") is None, r.report()
    g = r.xml.find("constraints/group")
    assert g is not None, r.report()
    assert " ".join(g.find("intension").text.split()) == "eq(%0,%1)", r.report()
    assert [" ".join(e.text.split()) for e in g.findall("args")] == ["x[0][0] x[2][0]", "x[0][1] x[2][1]"], r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("constraint", [
    "AllEqualList(x[0], [x[1][0]])",
    "AllEqualList([x[0][0], x[0][1]], [x[1][0], x[1][1], x[2][0]])",
    "AllEqualList([x[0][0] + 1, x[0][1]], x[1])",
    "AllEqualList(x[0], [0, 1])",
    "AllEqualList(x, excepting=0)",
    "AllEqualList(x, excepting=(0,))",
    "AllEqualList(x, excepting=(0, 0, 0))",
    "AllEqualList(x, excepting=[(0, 0), (1,)])",
    "AllEqualList(x, excepting=('a', 'b'))",
    "AllEqualList(x, excepting=(0.5, 1))",
    "AllEqualList([])",
    "AllEqualList(None)",
])
def test_invalid_allequallist(run, constraint):
    assert_fails(run(X32 + f"satisfy({constraint})"))


def test_allequallist_on_an_array_with_holes(run):
    # a list with a hole (None) cannot be compared with complete lists
    r = run("x = VarArray(size=[3, 2], dom=lambda i, j: None if (i, j) == (1, 1) else range(2))\nsatisfy(AllEqualList(x))")
    assert_fails(r)
    assert "The lists given to AllEqualList() cannot contain None (e.g., a hole of an array), which is the case of [x[1][0], None]" in r.stdout, r.report()


@pytest.mark.parametrize("constraint, message", [
    ("AllEqualList(None)", "AllEqualList() requires lists of variables, which is not the case of None"),
    ("AllEqualList([])", "AllEqualList() requires lists of variables, which is not the case of []"),
    ("AllEqualList(x[0], [x[1][0]])", "The lists given to AllEqualList() must have the same length, which is not the case of [x[0][0], x[0][1]] and [x[1][0]]"),
    ("AllEqualList(x, excepting=(0,))", "The tuples of excepting given to AllEqualList() must have the length of the lists (2), which is not the case of (0,)"),
    ("AllEqualList(x, excepting=(0, 0, 0))", "The tuples of excepting given to AllEqualList() must have the length of the lists (2), which is not the case of (0, 0, 0)"),
    ("AllEqualList(x, excepting=[(0, 0), (1,)])", "The tuples of excepting given to AllEqualList() must have the length of the lists (2), which is not the case of (1,)"),
    ("AllEqualList(x, excepting=((0, 0), (1,)))", "The tuples of excepting given to AllEqualList() must have the length of the lists (2), which is not the case of (1,)"),
    ("AllEqualList(x, excepting=0)", "excepting given to AllEqualList() must be a tuple of integers, or a collection of such tuples, which is not the case of 0"),
    ("AllEqualList(x, excepting=('a', 'b'))", "The values of excepting given to AllEqualList() must be integers, which is not the case of ('a', 'b')"),
])
def test_invalid_allequallist_messages(run, constraint, message):
    r = run(X32 + f"satisfy({constraint})")
    assert not r.ok and message in r.stdout, r.report()
