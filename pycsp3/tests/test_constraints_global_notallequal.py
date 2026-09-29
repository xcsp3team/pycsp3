"""
Tests of the constraint NotAllEqual of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#NotAllEqual): the function NotAllEqual(), which posts a constraint
NValues(...) > 1, on variables, on expressions and on integers, in groups of constraints, and in logical expressions.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
"""

import re

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
ACE_TWO = "xcsp3team/ACE#18: ACE fails on notAllEqual (nValues with the condition (gt,1)) on two variables (control(scp.length > 2) in NotAllEqual)"
CHOCO_DUPLICATES = "chocoteam/choco-solver#1248: CHOCO finds solutions several times with nValues on expressions and the condition (gt,1)"
EMPTY_SUPPORTS = ("(to be reported) ACE and CHOCO fail on a table with an empty set of supports, recognized as false by the parser "
                  "(buildCtrFalse(): RuntimeException: Constraint with only conflicts)")

# The cases that a solver says it does not handle, and the symbolic variables (not reported)
COSOCO_EXPRESSIONS = "cosoco does not handle nValues on expressions (s UNSUPPORTED)"
SYMBOLIC = "nValues on symbolic variables is not part of XCSP3-core (ACE and CHOCO fail, cosoco has no symbolic variables)"


def not_equal(values):
    """Returns True if the values are not all equal (at least two of them are different)."""
    return len(set(values)) > 1


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


def nvalues_terms(r):
    """Returns the terms of the element <nValues>, the compact forms of the variables of one-dimensional arrays (as x[] or x[0..1]) being expanded."""
    sizes = {a.get("id"): int(a.get("size")[1:-1]) for a in r.xml.iter("array")}
    terms = []
    for token in r.xml.find("constraints/nValues/list").text.split():
        m = re.fullmatch(r"(\w+)\[(\d*)(?:\.\.(\d+))?\]", token)
        if m is None:  # an expression
            terms.append(token)
        else:
            first = int(m.group(2)) if m.group(2) else 0
            last = int(m.group(3)) if m.group(3) else first if m.group(2) else sizes[m.group(1)] - 1
            terms.extend(m.group(1) + "[" + str(i) + "]" for i in range(first, last + 1))
    return terms


X3 = "x = VarArray(size=3, dom=range(3))\n"
X4 = "x = VarArray(size=4, dom=range(3))\n"


# ------------------------------------------------------------------------------------------------------------ forms

@pytest.mark.parametrize("constraint", [
    "NotAllEqual(x)",
    "NotAllEqual(x[0], x[1], x[2], x[3])",
    "NotAllEqual([x[0], x[1]], x[2], [x[3]])",
    "NotAllEqual(x[:2], x[2:])",
    "NotAllEqual(x[i] for i in range(4))",
    "NotAllEqual(tuple(x))",
    "NotAllEqual([[x[0], x[1]], [x[2], x[3]]])",
    "NotAllEqual(x[::-1])",
])
def test_notallequal_forms(run, solver, constraint):
    check(run, solver, X4 + f"satisfy({constraint})", [range(3)] * 4, lambda *t: not_equal(t))


@pytest.mark.parametrize("n, d", [(2, 2), (3, 3), (5, 2), (2, 5)])
def test_notallequal_sizes(run, solver, request, n, d):
    if n == 2:
        bug_for(request, "ACE", ACE_TWO)
    check(run, solver, f"x = VarArray(size={n}, dom=range({d}))\nsatisfy(NotAllEqual(x))", [range(d)] * n, lambda *t: not_equal(t))


def test_notallequal_on_a_matrix(run, solver):
    check(run, solver, "x = VarArray(size=[2, 2], dom=range(3))\nsatisfy(NotAllEqual(x))", [range(3)] * 4, lambda *t: not_equal(t))


@pytest.mark.parametrize("dom, domains", [
    ("lambda i: {i, 2}", [{0, 2}, {1, 2}, {2}]),
    ("lambda i: range(i, 3)", [range(0, 3), range(1, 3), range(2, 3)]),
    ("lambda i: {i}", [{0}, {1}, {2}]),
    ("lambda i: {1}", [{1}, {1}, {1}]),
], ids=["a common value", "intervals", "no common value", "a single common value"])
def test_notallequal_on_different_domains(run, solver, dom, domains):
    check(run, solver, f"x = VarArray(size=3, dom={dom})\nsatisfy(NotAllEqual(x))", domains, lambda *t: not_equal(t))


def test_notallequal_on_negative_values(run, solver):
    check(run, solver, "x = VarArray(size=3, dom=range(-2, 1))\nsatisfy(NotAllEqual(x))", [range(-2, 1)] * 3, lambda *t: not_equal(t))


def test_notallequal_on_an_array_with_holes(run, solver):
    r = run("x = VarArray(size=4, dom=lambda i: None if i == 1 else range(3))\nsatisfy(NotAllEqual(x))", solver=solver)
    assert r.variables == ["x[0]", "x[2]", "x[3]"]
    assert_solutions(r, brute_force([range(3)] * 3, lambda *t: not_equal(t)))


def test_notallequal_on_symbolic_variables(run, solver):
    pytest.skip(SYMBOLIC)
    check(run, solver, "x = VarArray(size=3, dom={'a', 'b'})\nsatisfy(NotAllEqual(x))", [["a", "b"]] * 3, lambda *t: not_equal(t))


def test_notallequal_with_other_constraints(run, solver):
    # the example of the documentation (hypergraph colouring)
    check(run, solver, "x = VarArray(size=6, dom=range(3))\nhyperedges = [(0, 1, 2), (2, 3, 4), (1, 4, 5)]\n"
                       "satisfy([NotAllEqual(x[i] for i in e) for e in hyperedges])", [range(3)] * 6,
          lambda *t: all(not_equal([t[i] for i in e]) for e in [(0, 1, 2), (2, 3, 4), (1, 4, 5)]))


@pytest.mark.parametrize("constraint, predicate", [
    ("NotAllEqual(x[0], x[1], x[2], x[0])", lambda a, b, c, d: not_equal((a, b, c))),
    ("NotAllEqual(x[0], x, x[3])", lambda *t: not_equal(t)),
    ("NotAllEqual(Sum(x[0], x[1]), Sum(x[0], x[1]), x[2], x[3])", lambda a, b, c, d: not_equal((a + b, c, d))),
])
def test_notallequal_with_a_repeated_term(run, solver, constraint, predicate):
    # a term given several times does not change the number of distinct values: it is kept once (at least three terms remain here)
    check(run, solver, X4 + f"satisfy({constraint})", [range(3)] * 4, predicate)


@pytest.mark.parametrize("constraint, terms", [
    ("NotAllEqual(x[0], x[1], x[0])", ["x[0]", "x[1]"]),
    ("NotAllEqual(x[0], x, x[2])", ["x[0]", "x[1]", "x[2]"]),
    ("NotAllEqual(x[0] + 1, x[0] + 1, x[1] + 1)", ["add(x[0],1)", "add(x[1],1)"]),
    ("NotAllEqual(Sum(x[0], x[1]), Sum(x[0], x[1]), x[2])", ["aux_gb[0]", "x[2]"]),  # the two sums are replaced by the same auxiliary variable
    ("NotAllEqual(x[0], 1, 1, x[1])", ["x[0]", "aux_gb[0]", "x[1]"]),  # the integer is replaced by a single auxiliary variable
])
def test_xcsp3_notallequal_with_a_repeated_term(run, constraint, terms):
    # each term given several times is kept once in the element <nValues>
    r = run(X3 + f"satisfy({constraint})")
    assert r.ok, r.report()
    assert sorted(nvalues_terms(r)) == sorted(terms), r.report()


# ----------------------------------------------------------------------------------------------- degenerated cases

@pytest.mark.parametrize("constraint", ["NotAllEqual(x[0])", "NotAllEqual([x[0]])", "NotAllEqual([])", "NotAllEqual(x[0], [])"])
def test_notallequal_trivially_false(run, solver, request, constraint):
    # with less than two terms, the terms cannot take two different values: the constraint never holds
    bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)
    check(run, solver, X3 + f"satisfy({constraint}, x[1] == 1)", [range(3)] * 3, lambda a, b, c: False)


@pytest.mark.parametrize("constraint", ["NotAllEqual(x[0])", "NotAllEqual([x[0]])", "NotAllEqual([])", "NotAllEqual(x[0], [])",
                                        "NotAllEqual(x[0], x[0])"])  # x[0] kept once: a single term
def test_xcsp3_notallequal_trivially_false(run, constraint):
    # with less than two terms, no element <nValues> is generated, but a table with an empty set of supports; a warning is displayed
    r = run(X3 + f"satisfy({constraint}, x[1] == 1)")
    assert r.ok, r.report()
    assert "A constraint is trivially false" in r.stdout, r.report()
    assert r.xml.find("constraints/nValues") is None, r.report()
    table = r.xml.find("constraints/extension")
    assert table is not None and table.find("supports") is not None and not (table.find("supports").text or "").strip(), r.report()


# ----------------------------------------------------------------------------------------------------- expressions

EXPRESSIONS = [
    ("NotAllEqual(x[0] + 1, x[1] + 1, x[2] + 1)", lambda a, b, c, d: not_equal((a, b, c))),
    ("NotAllEqual(abs(x[0] - x[1]), abs(x[1] - x[2]), abs(x[2] - x[3]))", lambda a, b, c, d: not_equal((abs(a - b), abs(b - c), abs(c - d)))),
    ("NotAllEqual(x[0] + x[1], x[2] + x[3], x[0] * 2)", lambda a, b, c, d: not_equal((a + b, c + d, a * 2))),
    ("NotAllEqual(x[0] > 0, x[1] > 1, x[2] == 2)", lambda a, b, c, d: not_equal((a > 0, b > 1, c == 2))),
    ("NotAllEqual([x[i] + i for i in range(4)])", lambda *t: not_equal([v + i for i, v in enumerate(t)])),
    ("NotAllEqual(x[0] + 1, x[1], x[2] - 1)", lambda a, b, c, d: not_equal((a + 1, b, c - 1))),
    ("NotAllEqual(x[0], x[1] + x[2], x[3])", lambda a, b, c, d: not_equal((a, b + c, d))),
    ("NotAllEqual(Sum(x[0], x[1]), x[2] + x[3])", lambda a, b, c, d: not_equal((a + b, c + d))),
]

# the constraints on at least three integer expressions, for which CHOCO finds solutions several times
DUPLICATED_BY_CHOCO = {c for c, _ in EXPRESSIONS if "Sum" not in c and ">" not in c}


@pytest.mark.parametrize("constraint, predicate", EXPRESSIONS)
def test_notallequal_on_expressions(run, solver, request, constraint, predicate):
    if solver == "COSOCO":
        pytest.skip(COSOCO_EXPRESSIONS)
    if constraint in DUPLICATED_BY_CHOCO:
        bug_for(request, "CHOCO", CHOCO_DUPLICATES)
    if "Sum" in constraint:  # an auxiliary variable and an expression: two terms
        bug_for(request, "ACE", ACE_TWO)
    check(run, solver, X4 + f"satisfy({constraint})", [range(3)] * 4, predicate)


# -------------------------------------------------------------------------------------------------------- integers

@pytest.mark.parametrize("constraint, predicate", [
    ("NotAllEqual(x, 1)", lambda a, b, c: not_equal((a, b, c, 1))),
    ("NotAllEqual(2, x[0], x[1])", lambda a, b, c: not_equal((2, a, b))),
    ("NotAllEqual(x[0], 5)", lambda a, b, c: True),
    ("NotAllEqual(x[0], x[1], -1)", lambda a, b, c: True),
    ("NotAllEqual(x[0], 1, 1)", lambda a, b, c: a != 1),
])
def test_notallequal_with_integers(run, solver, request, constraint, predicate):
    # an integer among the terms is a term like the others (it is replaced by an auxiliary variable, not part of the solutions)
    if constraint in ("NotAllEqual(x[0], 5)", "NotAllEqual(x[0], 1, 1)"):  # two terms (the integer 1 being kept once)
        bug_for(request, "ACE", ACE_TWO)
    check(run, solver, X3 + f"satisfy({constraint}, x[2] != 0)", [range(3)] * 3, lambda a, b, c: predicate(a, b, c) and c != 0)


# ---------------------------------------------------------------------------------------------------------- groups

def test_notallequal_on_rows(run, solver, request):
    bug_for(request, "ACE", ACE_TWO)  # rows of two variables
    check(run, solver, "x = VarArray(size=[3, 2], dom=range(2))\nsatisfy([NotAllEqual(row) for row in x], AllDifferent(x[:, 0]))", [range(2)] * 6,
          lambda *t: all(t[2 * i] != t[2 * i + 1] for i in range(3)) and len({t[0], t[2], t[4]}) == 3)


def test_notallequal_on_sliding_windows(run, solver):
    check(run, solver, "x = VarArray(size=5, dom=range(2))\nsatisfy([NotAllEqual(x[i:i + 3]) for i in range(3)])", [range(2)] * 5,
          lambda *t: all(not_equal(t[i:i + 3]) for i in range(3)))


# ------------------------------------------------------------------------------------------------ logical contexts

@pytest.mark.parametrize("constraint, predicate", [
    ("~NotAllEqual(x)", lambda *t: not not_equal(t)),
    ("NotAllEqual(x) | (x[0] == 0)", lambda *t: not_equal(t) or t[0] == 0),
    ("NotAllEqual(x) & (x[0] == 0)", lambda *t: not_equal(t) and t[0] == 0),
    ("imply(x[0] == 0, NotAllEqual(x))", lambda *t: t[0] != 0 or not_equal(t)),
    ("either(NotAllEqual(x[:2]), NotAllEqual(x[1:]))", lambda *t: not_equal(t[:2]) or not_equal(t[1:])),
])
def test_notallequal_in_logical_expressions(run, solver, constraint, predicate):
    check(run, solver, X3 + f"satisfy({constraint})", [range(3)] * 3, predicate)


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, expected", [
    ("NotAllEqual(x)", ("nValues", "x[]", "(gt,1)")),
    ("NotAllEqual(x[0], x[2])", ("nValues", "x[0] x[2]", "(gt,1)")),
    ("NotAllEqual(x[0] + 1, x[1] + 1)", ("nValues", "add(x[0],1) add(x[1],1)", "(gt,1)")),
])
def test_xcsp3_notallequal(run, constraint, expected):
    r = run(X3 + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints")[0]
    assert (c.tag, " ".join(c.find("list").text.split()), c.find("condition").text.strip()) == expected, r.report()


def test_xcsp3_notallequal_on_sliding_windows(run):
    r = run("x = VarArray(size=4, dom=range(3))\nsatisfy([NotAllEqual(x[i:i + 2]) for i in range(3)])")
    assert r.ok, r.report()
    group = r.xml.find("constraints/group")
    assert group is not None and group.find("nValues") is not None, r.report()
    assert [" ".join(a.text.split()) for a in group.findall("args")] == ["x[0] x[1]", "x[1] x[2]", "x[2] x[3]"], r.report()


def test_xcsp3_notallequal_with_an_integer(run):
    # an integer is replaced by an auxiliary variable whose domain only contains this integer
    r = run(X3 + "satisfy(NotAllEqual(x[0], 5))")
    assert r.ok, r.report()
    assert " ".join(r.xml.find("constraints/nValues/list").text.split()) == "x[0] aux_gb[0]", r.report()
    assert r.xml.find("variables/array[@id='aux_gb']").text.strip() == "5", r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("constraint", [
    "NotAllEqual()",
    "NotAllEqual(x[0], 'a')",
    "NotAllEqual(x[0], 2.5)",
    "NotAllEqual(x[0], True)",
    "NotAllEqual(x[0], range(3))",
    "NotAllEqual(x, excepting=0)",
    "NotAllEqual(None)",
    "NotAllEqual('a')",
    "NotAllEqual(2.5)",
    "NotAllEqual(range(3))",
    "NotAllEqual({'a': x[0]})",
])
def test_invalid_notallequal(run, constraint):
    assert_fails(run(X3 + f"satisfy({constraint})"))


@pytest.mark.parametrize("constraint, message", [
    ("NotAllEqual(None)", "NotAllEqual() requires variables (or expressions), which is not the case of None"),
    ("NotAllEqual(1, 2)", "NotAllEqual() requires at least one variable (or expression), and not only integers, which is not the case of [1, 2]"),
])
def test_invalid_notallequal_message(run, constraint, message):
    r = run(X3 + f"satisfy({constraint})")
    assert not r.ok and message in r.stdout, r.report()


@pytest.mark.parametrize("constraint", ["NotAllEqual(1, 2)", "NotAllEqual(1, 1)", "NotAllEqual(5)"])
def test_notallequal_on_integers_only(run, constraint):
    # as for AllDifferent() and AllEqual(), at least one variable (or expression) is required
    assert_fails(run(X3 + f"satisfy({constraint})"))
