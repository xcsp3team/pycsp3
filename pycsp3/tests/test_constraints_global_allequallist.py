"""
Tests of the constraint AllEqualList of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#AllEqualList): the function AllEqualList(), with the parameter excepting.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
"""

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
ALL = ("ACE", "CHOCO", "COSOCO")
NOT_CORE = ("#125: AllEqualList() generates allEqual-list, which is not part of XCSP3-core and is handled by no solver "
            "(ACE and CHOCO: Missing Implementation, or xcsp3team/XCSP3-Java-Tools#21 with except; cosoco: wrong solutions, xcsp3team/cosoco#81)")
SEVERAL_TUPLES = "#126: excepting with several tuples generates an invalid element <except>, or is refused without explicit message"
INVALID = "#122: invalid arguments of AllEqualList() are accepted, or reported without explicit message"

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
def test_allequallist_forms(run, solver, request, constraint):
    bug_for(request, ALL, NOT_CORE)
    check(run, solver, X32 + f"satisfy({constraint})", D32, lambda *t: equal_lists(rows(t, 2)))


@pytest.mark.parametrize("n, m, d", [(2, 2, 3), (3, 2, 2), (4, 2, 2), (2, 3, 2), (3, 3, 2), (2, 1, 3), (3, 1, 3)],
                         ids=["2 lists", "3 lists", "4 lists", "2 lists of 3 variables", "3 lists of 3 variables", "2 lists of 1 variable",
                              "3 lists of 1 variable"])
def test_allequallist_sizes(run, solver, request, n, m, d):
    # with two lists, PyCSP3 posts x[0][j] == x[1][j] for each index j
    if n > 2 and m > 1:
        bug_for(request, ALL, NOT_CORE)
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
def test_allequallist_on_columns(run, solver, request, size):
    n, m = eval(size)
    if m > 2:
        bug_for(request, ALL, NOT_CORE)
    check(run, solver, f"x = VarArray(size={size}, dom=range(2))\nsatisfy(AllEqualList(columns(x)))", [range(2)] * (n * m),
          lambda *t: equal_lists(list(zip(*rows(t, m)))))


def test_allequallist_on_different_domains(run, solver, request):
    bug_for(request, ALL, NOT_CORE)
    check(run, solver, "x = VarArray(size=[3, 2], dom=lambda i, j: range(i + j, 4))\nsatisfy(AllEqualList(x))",
          [range(i + j, 4) for i in range(3) for j in range(2)], lambda *t: equal_lists(rows(t, 2)))


def test_allequallist_on_negative_values(run, solver, request):
    bug_for(request, ALL, NOT_CORE)
    check(run, solver, "x = VarArray(size=[3, 2], dom=range(-2, 1))\nsatisfy(AllEqualList(x))", [range(-2, 1)] * 6, lambda *t: equal_lists(rows(t, 2)))


def test_allequallist_with_shared_variables(run, solver, request):
    bug_for(request, ALL, NOT_CORE)
    # a variable can occur in several lists: (x0, x1) = (x1, x0) = (x2, x2) iff x0 = x1 = x2
    check(run, solver, "x = VarArray(size=3, dom=range(3))\nsatisfy(AllEqualList([x[0], x[1]], [x[1], x[0]], [x[2], x[2]]))", [range(3)] * 3,
          lambda a, b, c: equal_lists([(a, b), (b, a), (c, c)]))


def test_allequallist_on_symbolic_variables(run, solver):
    pytest.skip(SYMBOLIC)
    check(run, solver, "x = VarArray(size=[3, 2], dom={'a', 'b'})\nsatisfy(AllEqualList(x))", [["a", "b"]] * 6, lambda *t: equal_lists(rows(t, 2)))


def test_allequallist_with_other_constraints(run, solver, request):
    bug_for(request, ALL, NOT_CORE)
    # the example of the documentation (with fewer roles)
    check(run, solver, X32 + "satisfy(AllEqualList(x), x[0][0] != x[0][1], Sum(x[2]) == 3)", D32,
          lambda *t: equal_lists(rows(t, 2)) and t[0] != t[1] and t[4] + t[5] == 3)


@pytest.mark.parametrize("k", [2, 3], ids=["windows of 2 lists", "windows of 3 lists"])
def test_allequallist_in_a_group(run, solver, request, k):
    if k > 2:
        bug_for(request, ALL, NOT_CORE)
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
def test_allequallist_excepting(run, solver, request, excepting, tuples):
    bug_for(request, ALL, SEVERAL_TUPLES if excepting == "[]" or excepting.startswith(("[(", "((")) else NOT_CORE)
    check(run, solver, X32 + f"satisfy(AllEqualList(x, excepting={excepting}))", D32, lambda *t: equal_lists(rows(t, 2), tuples))


def test_allequallist_excepting_on_two_lists(run, solver, request):
    bug_for(request, ALL, NOT_CORE)
    check(run, solver, X32 + "satisfy(AllEqualList(x[0], x[1], excepting=(0, 0)))", D32, lambda *t: equal_lists(rows(t, 2)[:2], {(0, 0)}))


def test_allequallist_excepting_with_other_constraints(run, solver, request):
    bug_for(request, ALL, NOT_CORE)
    # the pair (0, 0) means that the team does not play
    check(run, solver, "x = VarArray(size=[3, 2], dom=range(3))\nsatisfy(AllEqualList(x, excepting=(0, 0)), Sum(x[0]) > 0, x[1][0] == 1)",
          D32, lambda *t: equal_lists(rows(t, 2), {(0, 0)}) and t[0] + t[1] > 0 and t[2] == 1)


# ----------------------------------------------------------------------------------------------- degenerated cases

@pytest.mark.parametrize("constraint", ["AllEqualList([x[0]])", "AllEqualList(x[0:1])"])
def test_allequallist_with_a_single_list(run, solver, constraint):
    # with a single list, the constraint always holds (no constraint is posted)
    r = run(X32 + f"satisfy({constraint}, x[1][0] == 1, x[2][0] == 2)", solver=solver)
    if r.ok:
        assert_solutions(r, brute_force(D32, lambda *t: t[2] == 1 and t[4] == 2))
    else:
        assert_fails(r)


@pytest.mark.parametrize("constraint, predicate", [
    ("AllEqualList(x[0], x[0])", lambda *t: True),
    ("AllEqualList(x[0], x[1], x[0])", lambda *t: t[0:2] == t[2:4]),
    ("AllEqualList(x[0], x[0], excepting=(0, 0))", lambda *t: True),
], ids=["twice", "twice among three", "twice with excepting"])
def test_allequallist_with_a_repeated_list(run, solver, request, constraint, predicate):
    if "x[1]" in constraint or "excepting" in constraint:
        bug_for(request, ALL, NOT_CORE)
    # a list is always equal to itself: the constraint holds on the other lists (or an error is reported)
    r = run(X32 + f"satisfy({constraint})", solver=solver)
    if r.ok:
        assert_solutions(r, brute_force(D32, predicate))
    else:
        assert_fails(r)


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, lists, excepting", [
    pytest.param("AllEqualList(x)", ["x[0][0] x[0][1]", "x[1][0] x[1][1]", "x[2][0] x[2][1]"], None, id="AllEqualList(x)"),
    pytest.param("AllEqualList(x[0], x[2], excepting=(0, 0))", ["x[0][0] x[0][1]", "x[2][0] x[2][1]"], "(0,0)", id="AllEqualList(x[0], x[2], excepting=(0, 0))"),
    pytest.param("AllEqualList(x, excepting=(1, 2))", ["x[0][0] x[0][1]", "x[1][0] x[1][1]", "x[2][0] x[2][1]"], "(1,2)", id="AllEqualList(x, excepting=(1, 2))"),
    pytest.param("AllEqualList(x, excepting=[(0, 0), (1, 2)])", ["x[0][0] x[0][1]", "x[1][0] x[1][1]", "x[2][0] x[2][1]"], "(0,0)(1,2)",
                 id="AllEqualList(x, excepting=[(0, 0), (1, 2)])", marks=bug(SEVERAL_TUPLES)),
])
def test_xcsp3_allequallist(run, constraint, lists, excepting):
    r = run(X32 + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/allEqual")
    assert c is not None, r.report()
    assert [" ".join(e.text.split()) for e in c.findall("list")] == lists, r.report()
    exc = c.find("except")
    assert (None if exc is None else "".join(exc.text.split())) == excepting, r.report()


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
    pytest.param("AllEqualList(x[0], [x[1][0]])", marks=bug(INVALID)),
    pytest.param("AllEqualList([x[0][0], x[0][1]], [x[1][0], x[1][1], x[2][0]])", marks=bug(INVALID)),
    "AllEqualList([x[0][0] + 1, x[0][1]], x[1])",
    "AllEqualList(x[0], [0, 1])",
    "AllEqualList(x, excepting=0)",
    pytest.param("AllEqualList(x, excepting=(0,))", marks=bug(INVALID)),
    pytest.param("AllEqualList(x, excepting=(0, 0, 0))", marks=bug(INVALID)),
    pytest.param("AllEqualList(x, excepting=[(0, 0), (1,)])", marks=bug(INVALID)),
    "AllEqualList(x, excepting=('a', 'b'))",
    "AllEqualList(x, excepting=(0.5, 1))",
    pytest.param("AllEqualList([])", marks=bug(INVALID)),
    pytest.param("AllEqualList(None)", marks=bug(INVALID)),
])
def test_invalid_allequallist(run, constraint):
    assert_fails(run(X32 + f"satisfy({constraint})"))


@bug(INVALID)
def test_allequallist_on_an_array_with_holes(run):
    # a list with a hole (None) cannot be compared with complete lists
    assert_fails(run("x = VarArray(size=[3, 2], dom=lambda i, j: None if (i, j) == (1, 1) else range(2))\nsatisfy(AllEqualList(x))"))
