"""
Tests of the constraint AllEqual of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#AllEqual): the function AllEqual(), on variables and on expressions,
with the parameter excepting, and in groups of constraints.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
"""

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
ALL = ("ACE", "CHOCO", "COSOCO")
COSOCO_EXCEPT = "xcsp3team/cosoco#78: cosoco loses solutions or fails with except (here, allEqual with except, or a group of them)"
COSOCO_REPEATED = "xcsp3team/cosoco#80: cosoco loses solutions of allEqual with a variable given twice"

# The cases that a solver says it does not handle, and the symbolic variables (not reported)
CHOCO_EXCEPT = "CHOCO does not handle allEqual with except (RuntimeException: UNSUPPORTED)"
COSOCO_EXPRESSIONS = "cosoco does not handle allEqual on expressions (AllEqual constraint with expression is not yet supported)"
SYMBOLIC = "allEqual on symbolic variables is not part of XCSP3-core (ACE and CHOCO fail, cosoco has no symbolic variables)"
COSOCO_HOLES = "#127: pycsp3 fails when recording the values given by cosoco (individually) for the holes of an array"


def equal(values, excepting=()):
    """Returns True if the values are all equal, the values in excepting being ignored."""
    return len({v for v in values if v not in excepting}) <= 1


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


X3 = "x = VarArray(size=3, dom=range(3))\n"
X4 = "x = VarArray(size=4, dom=range(3))\n"


# ------------------------------------------------------------------------------------------------------------ forms

@pytest.mark.parametrize("constraint", [
    "AllEqual(x)",
    "AllEqual(x[0], x[1], x[2], x[3])",
    "AllEqual([x[0], x[1]], x[2], [x[3]])",
    "AllEqual(x[:2], x[2:])",
    "AllEqual(x[i] for i in range(4))",
    "AllEqual(tuple(x))",
    "AllEqual([[x[0], x[1]], [x[2], x[3]]])",
    "AllEqual(x[::-1])",
])
def test_allequal_forms(run, solver, constraint):
    check(run, solver, X4 + f"satisfy({constraint})", [range(3)] * 4, lambda *t: equal(t))


@pytest.mark.parametrize("n, d", [(2, 2), (3, 3), (5, 2), (2, 5)])
def test_allequal_sizes(run, solver, n, d):
    check(run, solver, f"x = VarArray(size={n}, dom=range({d}))\nsatisfy(AllEqual(x))", [range(d)] * n, lambda *t: equal(t))


def test_allequal_on_a_matrix(run, solver):
    check(run, solver, "x = VarArray(size=[2, 2], dom=range(3))\nsatisfy(AllEqual(x))", [range(3)] * 4, lambda *t: equal(t))


@pytest.mark.parametrize("dom, domains", [
    ("lambda i: {i, 2}", [{0, 2}, {1, 2}, {2}]),
    ("lambda i: range(i, 3)", [range(0, 3), range(1, 3), range(2, 3)]),
    ("lambda i: {i}", [{0}, {1}, {2}]),
], ids=["a common value", "intervals", "no common value"])
def test_allequal_on_different_domains(run, solver, dom, domains):
    check(run, solver, f"x = VarArray(size=3, dom={dom})\nsatisfy(AllEqual(x))", domains, lambda *t: equal(t))


def test_allequal_on_negative_values(run, solver):
    check(run, solver, "x = VarArray(size=3, dom=range(-2, 1))\nsatisfy(AllEqual(x))", [range(-2, 1)] * 3, lambda *t: equal(t))


def test_allequal_on_an_array_with_holes(run, solver, request):
    bug_for(request, "COSOCO", COSOCO_HOLES)
    r = run("x = VarArray(size=4, dom=lambda i: None if i == 1 else range(3))\nsatisfy(AllEqual(x))", solver=solver)
    assert r.variables == ["x[0]", "x[2]", "x[3]"]
    assert_solutions(r, brute_force([range(3)] * 3, lambda *t: equal(t)))


def test_allequal_on_symbolic_variables(run, solver):
    pytest.skip(SYMBOLIC)
    check(run, solver, "x = VarArray(size=3, dom={'a', 'b'})\nsatisfy(AllEqual(x))", [["a", "b"]] * 3, lambda *t: equal(t))


def test_allequal_with_other_constraints(run, solver):
    # the example of the documentation (with smaller domains)
    check(run, solver, "x = VarArray(size=4, dom=range(10))\nsatisfy(Sum(x) == 12, AllEqual(x))", [range(10)] * 4, lambda *t: sum(t) == 12 and equal(t))


def test_allequal_with_a_repeated_variable(run, solver, request):
    bug_for(request, "COSOCO", COSOCO_REPEATED)
    # a variable is always equal to itself
    check(run, solver, X3 + "satisfy(AllEqual(x[0], x[1], x[0]))", [range(3)] * 3, lambda a, b, c: a == b)


# ----------------------------------------------------------------------------------------------- degenerated cases

@pytest.mark.parametrize("constraint", ["AllEqual(x[0])", "AllEqual([x[0]])", "AllEqual([])", "AllEqual(x[0], [])"])
def test_allequal_trivially_true(run, solver, constraint):
    # with less than two terms, the constraint always holds
    check(run, solver, X3 + f"satisfy({constraint}, x[1] == 1, x[2] == 2)", [range(3)] * 3, lambda a, b, c: (b, c) == (1, 2))


@pytest.mark.parametrize("constraint", ["AllEqual(x[0])", "AllEqual([x[0]])", "AllEqual(x[0], [])", "AllEqual(x[0] + 1)", "AllEqual(Sum(x[0], x[1]))"])
def test_xcsp3_allequal_with_a_single_term(run, constraint):
    # with a single term, no element <allEqual> is generated (the syntax requires at least two variables), and no auxiliary variable
    r = run(X3 + f"satisfy({constraint}, x[1] == 1, x[2] == 2)")
    assert r.ok, r.report()
    assert r.xml.find("constraints/allEqual") is None and r.xml.find("variables/var[@id='aux_gb[0]']") is None, r.report()


# ----------------------------------------------------------------------------------------------------- expressions

EXPRESSIONS = [
    ("AllEqual(x[0] + 1, x[1] + 1, x[2] + 1)", lambda a, b, c, d: equal((a, b, c))),
    ("AllEqual(abs(x[0] - x[1]), abs(x[1] - x[2]), abs(x[2] - x[3]))", lambda a, b, c, d: equal((abs(a - b), abs(b - c), abs(c - d)))),
    ("AllEqual(x[0] + x[1], x[2] + x[3], x[0] * 2)", lambda a, b, c, d: equal((a + b, c + d, a * 2))),
    ("AllEqual(x[0] > 0, x[1] > 1, x[2] == 2)", lambda a, b, c, d: equal((a > 0, b > 1, c == 2))),
    ("AllEqual([x[i] + i for i in range(4)])", lambda *t: equal([v + i for i, v in enumerate(t)])),
    ("AllEqual(x[0] + 1, x[1], x[2] - 1)", lambda a, b, c, d: equal((a + 1, b, c - 1))),
    ("AllEqual(x[0], x[1] + x[2], x[3])", lambda a, b, c, d: equal((a, b + c, d))),
    ("AllEqual(Sum(x[0], x[1]), x[2] + x[3])", lambda a, b, c, d: equal((a + b, c + d))),
]


@pytest.mark.parametrize("constraint, predicate", EXPRESSIONS)
def test_allequal_on_expressions(run, solver, constraint, predicate):
    if solver == "COSOCO":
        pytest.skip(COSOCO_EXPRESSIONS)
    check(run, solver, X4 + f"satisfy({constraint})", [range(3)] * 4, predicate)


@pytest.mark.parametrize("constraint, text", [
    ("AllEqual(x[0] + 1, x[1], x[2] - 1)", "add(x[0],1) x[1] sub(x[2],1)"),
    ("AllEqual(x[0], x[1] + x[2], x[3])", "x[0] add(x[1],x[2]) x[3]"),
])
def test_xcsp3_allequal_on_variables_and_expressions(run, constraint, text):
    # variables and expressions may be mixed, as for AllDifferent() (the order of the terms does not matter)
    r = run(X4 + f"satisfy({constraint})")
    assert r.ok, r.report()
    assert sorted(r.xml.find("constraints/allEqual").text.split()) == sorted(text.split()), r.report()


@pytest.mark.parametrize("constraint, predicate", EXPRESSIONS)
def test_allequal_on_expressions_with_option_mini(run, solver, constraint, predicate):
    # with the option -mini, the expressions are replaced by auxiliary variables (which are not part of the solutions recorded by the harness)
    check(run, solver, X4 + f"satisfy({constraint})", [range(3)] * 4, predicate, args=["-mini"])


# ------------------------------------------------------------------------------------------------------- excepting

@pytest.mark.parametrize("excepting, values", [
    ("0", {0}),
    ("[0]", {0}),
    ("(0,)", {0}),
    ("{0}", {0}),
    ("[0, 2]", {0, 2}),
    ("range(2)", {0, 1}),
    ("9", {9}),
    ("[]", set()),
    ("None", set()),
])
def test_allequal_excepting(run, solver, request, excepting, values):
    if excepting not in ("None", "[]"):  # an empty collection is as None (no element <except>)
        if solver == "CHOCO":
            pytest.skip(CHOCO_EXCEPT)
        if excepting != "9":
            bug_for(request, "COSOCO", COSOCO_EXCEPT)
    check(run, solver, X4 + f"satisfy(AllEqual(x, excepting={excepting}))", [range(3)] * 4, lambda *t: equal(t, values))


def test_allequal_excepting_with_other_constraints(run, solver, request):
    if solver == "CHOCO":
        pytest.skip(CHOCO_EXCEPT)
    bug_for(request, "COSOCO", COSOCO_EXCEPT)
    # the example of the documentation (with smaller domains)
    check(run, solver, "x = VarArray(size=4, dom=range(3))\nsatisfy(Count(x, value=0) == 1, AllEqual(x, excepting=0))", [range(3)] * 4,
          lambda *t: t.count(0) == 1 and equal(t, {0}))


def test_allequal_excepting_on_expressions(run, solver):
    if solver == "CHOCO":
        pytest.skip(CHOCO_EXCEPT)
    if solver == "COSOCO":
        pytest.skip(COSOCO_EXPRESSIONS)
    check(run, solver, X4 + "satisfy(AllEqual(x[0] + 1, x[1] + 1, x[2] + 1, excepting=1))", [range(3)] * 4, lambda a, b, c, d: equal((a + 1, b + 1, c + 1), {1}))


# ---------------------------------------------------------------------------------------------------------- groups

def test_allequal_on_rows(run, solver):
    check(run, solver, "x = VarArray(size=[3, 2], dom=range(3))\nsatisfy([AllEqual(row) for row in x], AllDifferent(x[:, 0]))", [range(3)] * 6,
          lambda *t: all(t[2 * i] == t[2 * i + 1] for i in range(3)) and len({t[0], t[2], t[4]}) == 3)


def test_allequal_on_sliding_windows(run, solver, request):
    if solver == "CHOCO":
        pytest.skip(CHOCO_EXCEPT)
    bug_for(request, "COSOCO", COSOCO_EXCEPT)
    check(run, solver, "x = VarArray(size=5, dom=range(3))\nsatisfy([AllEqual(x[i:i + 2], excepting=0) for i in range(4)])", [range(3)] * 5,
          lambda *t: all(equal(t[i:i + 2], {0}) for i in range(4)))


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, expected", [
    ("AllEqual(x)", ("allEqual", "x[]", None)),
    ("AllEqual(x, excepting=0)", ("allEqual", "x[]", "0")),
    ("AllEqual(x[0], x[2])", ("allEqual", "x[0] x[2]", None)),
    ("AllEqual(x[0] + 1, x[1] + 1)", ("allEqual", "add(x[0],1) add(x[1],1)", None)),
])
def test_xcsp3_allequal(run, constraint, expected):
    r = run(X3 + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints")[0]
    lst = c.find("list")
    text = (lst.text if lst is not None else c.text).strip()
    exc = c.find("except")
    assert (c.tag, " ".join(text.split()), None if exc is None else exc.text.strip()) == expected, r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("constraint", [
    "AllEqual(x[0], 'a')",
    "AllEqual(None)",
    "AllEqual(5)",
    "AllEqual(x, excepting='a')",
    "AllEqual(x, excepting=2.5)",
    "AllEqual(x, excepting=[0, 'a'])",
    "AllEqual(x, excepting=x[0])",
])
def test_invalid_allequal(run, constraint):
    assert_fails(run(X3 + f"satisfy({constraint})"))


def test_invalid_allequal_message(run):
    r = run(X3 + "satisfy(AllEqual(None))")
    assert not r.ok and "AllEqual() requires variables (or expressions), which is not the case of None" in r.stdout, r.report()


@pytest.mark.parametrize("constraint, predicate", [("AllEqual(x, 1)", lambda a, b, c: a == b == c == 1), ("AllEqual(2, x[0], x[1])", lambda a, b, c: a == b == 2)])
def test_allequal_with_an_integer(run, solver, constraint, predicate):
    # an integer among the terms: either all the terms are equal to it, or an error is reported
    r = run(X3 + f"satisfy({constraint}, x[2] != 0)", solver=solver)
    if r.ok:
        assert_solutions(r, brute_force([range(3)] * 3, lambda a, b, c: predicate(a, b, c) and c != 0))
    else:
        assert_fails(r)
