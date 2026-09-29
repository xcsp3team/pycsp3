"""
Tests of the constraint Precedence of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#Precedence): the function Precedence(), with the parameters values and covered,
in groups of constraints and in logical expressions.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
According to XCSP3-core, precedence(X, V) holds iff, for each i, if v[i+1] is assigned to a variable of X, then v[i] is assigned to a variable
of X that precedes it (the first occurrence of v[i] precedes the first occurrence of v[i+1]); without values, V is the ordered union of the
domains of the variables; with covered, the last value of V must also be assigned (and so, all the values of V).
"""

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
COVERED = "#150: Precedence() ignores covered=True when values is not given, or when a single value is given"
ACE_COVERED = ("xcsp3team/ACE#21: ACE fails on precedence with covered when the list has not more variables than values "
               "(control(!covered || list.length > values.length) in Precedence)")
EMPTY_SUPPORTS = ("(to be reported) ACE and CHOCO fail on a table with an empty set of supports, recognized as false by the parser "
                  "(buildCtrFalse(): RuntimeException: Constraint with only conflicts)")

# The cases that a solver says it does not handle, and the symbolic variables (not reported)
SYMBOLIC = "precedence on symbolic variables is not part of XCSP3-core"


def precedence(t, values, covered=False):
    """Returns True if the tuple t satisfies precedence(t, values), with covered if specified."""
    first = {}
    for j, v in enumerate(t):
        first.setdefault(v, j)
    for a, b in zip(values, values[1:]):
        if b in first and (a not in first or first[a] >= first[b]):
            return False
    return not covered or values[-1] in first


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


X4 = "x = VarArray(size=4, dom=range(3))\n"
D4 = [range(3)] * 4


# ------------------------------------------------------------------------------------------------------------ forms

@pytest.mark.parametrize("values, expected", [
    ("[0, 1, 2]", [0, 1, 2]),
    ("range(3)", [0, 1, 2]),
    ("(0, 1, 2)", [0, 1, 2]),
    ("(v for v in [0, 1, 2])", [0, 1, 2]),
    ("[0, 1]", [0, 1]),
    ("[1, 0]", [1, 0]),
    ("[2, 0, 1]", [2, 0, 1]),
    ("[0, 2]", [0, 2]),
    ("[0, 5]", [0, 5]),
    ("[5, 0]", [5, 0]),
    ("[-1, 1, 2]", [-1, 1, 2]),
])
def test_precedence_with_values(run, solver, values, expected):
    check(run, solver, X4 + f"satisfy(Precedence(x, values={values}))", D4, lambda *t: precedence(t, expected))


@pytest.mark.parametrize("within", ["x", "x[:]", "tuple(x)", "[x[0], x[1], x[2], x[3]]", "(x[i] for i in range(4))", "[x[:2], x[2:]]"])
def test_precedence_forms(run, solver, within):
    check(run, solver, X4 + f"satisfy(Precedence({within}, values=[0, 1, 2]))", D4, lambda *t: precedence(t, [0, 1, 2]))


@pytest.mark.parametrize("values, expected", [("[0, 1, 2]", [0, 1, 2]), ("[1, 0]", [1, 0]), ("[0, 5]", [0, 5]), ("[2, 0, 1]", [2, 0, 1])])
def test_precedence_covered(run, solver, values, expected):
    # with covered, all the values must be assigned
    check(run, solver, X4 + f"satisfy(Precedence(x, values={values}, covered=True))", D4, lambda *t: precedence(t, expected, covered=True))


@pytest.mark.parametrize("n, d", [(2, 2), (3, 3), (5, 2), (4, 4)])
def test_precedence_sizes(run, solver, n, d):
    check(run, solver, f"x = VarArray(size={n}, dom=range({d}))\nsatisfy(Precedence(x, values=range({d})))", [range(d)] * n, lambda *t: precedence(t, list(range(d))))


def test_precedence_on_negative_values(run, solver):
    check(run, solver, "x = VarArray(size=4, dom=range(-2, 1))\nsatisfy(Precedence(x, values=[0, -2, -1]))", [range(-2, 1)] * 4, lambda *t: precedence(t, [0, -2, -1]))


def test_precedence_on_an_array_with_holes(run, solver):
    r = run("x = VarArray(size=4, dom=lambda i: None if i == 1 else range(3))\nsatisfy(Precedence(x, values=[0, 1, 2]))", solver=solver)
    assert r.variables == ["x[0]", "x[2]", "x[3]"]
    assert_solutions(r, brute_force([range(3)] * 3, lambda *t: precedence(t, [0, 1, 2])))


def test_precedence_on_symbolic_variables(run, solver):
    pytest.skip(SYMBOLIC)


def test_precedence_with_a_repeated_variable(run, solver):
    # a variable may appear several times: only its first occurrence counts, and so is kept
    check(run, solver, X4 + "satisfy(Precedence([x[0], x[1], x[0], x[2]], values=[0, 1, 2]))", D4, lambda a, b, c, d: precedence((a, b, a, c), [0, 1, 2]))


def test_xcsp3_precedence_with_a_repeated_variable(run):
    r = run(X4 + "satisfy(Precedence([x[0], x[1], x[0], x[2]], values=[0, 1, 2]))")
    assert r.ok, r.report()
    assert " ".join(r.xml.find("constraints/precedence/list").text.split()) == "x[0..2]", r.report()


@pytest.mark.parametrize("within, values", [
    ("[x[0], x[1] + 1, x[2]]", lambda a, b, c, d: (a, b + 1, c)),
    ("[x[0], 1, x[2]]", lambda a, b, c, d: (a, 1, c)),
    ("[x[0] * 2, x[1], abs(x[2] - x[3])]", lambda a, b, c, d: (a * 2, b, abs(c - d))),
])
def test_precedence_on_expressions(run, solver, within, values):
    # the expressions and the integers are replaced by auxiliary variables
    check(run, solver, X4 + f"satisfy(Precedence({within}, values=[0, 1, 2]))", D4, lambda *t: precedence(values(*t), [0, 1, 2]))


@pytest.mark.parametrize("n, values", [(3, [0, 1, 2]), (2, [0, 1]), (3, [0, 1, 2, 3]), (2, [1, 0, 2])],
                         ids=["as many values as variables (3)", "as many values as variables (2)", "more values", "more values (other order)"])
def test_precedence_covered_with_not_more_variables_than_values(run, solver, request, n, values):
    # with covered, the values must all be assigned: with more values than variables, there is no solution
    bug_for(request, "ACE", ACE_COVERED)
    check(run, solver, f"x = VarArray(size={n}, dom=range(4))\nsatisfy(Precedence(x, values={values}, covered=True))", [range(4)] * n,
          lambda *t: precedence(t, values, covered=True))


# ----------------------------------------------------------------------------------------------------- without values

@pytest.mark.parametrize("dom, domains", [
    ("range(3)", [range(3)] * 4),
    ("lambda i: range(i, i + 2)", [range(i, i + 2) for i in range(4)]),
    ("lambda i: {0, 2} if i < 2 else {1, 3}", [{0, 2}, {0, 2}, {1, 3}, {1, 3}]),
], ids=["same domains", "shifted domains", "disjoint domains"])
def test_precedence_without_values(run, solver, dom, domains):
    # without values, the ordered union of the domains is considered (XCSP3-core)
    union = sorted(set().union(*[set(d) for d in domains]))
    check(run, solver, f"x = VarArray(size=4, dom={dom})\nsatisfy(Precedence(x))", domains, lambda *t: precedence(t, union))


@pytest.mark.parametrize("dom, domains", [
    ("range(3)", [range(3)] * 4),
    ("lambda i: range(i, i + 2)", [range(i, i + 2) for i in range(4)]),
], ids=["same domains", "shifted domains"])
@bug(COVERED)
def test_precedence_without_values_covered(run, solver, dom, domains):
    # without values, covered applies to the ordered union of the domains
    union = sorted(set().union(*[set(d) for d in domains]))
    check(run, solver, f"x = VarArray(size=4, dom={dom})\nsatisfy(Precedence(x, covered=True))", domains, lambda *t: precedence(t, union, covered=True))


# ------------------------------------------------------------------------------------------------ examples of the doc

def test_precedence_example(run, solver):
    # the first example of the documentation (graph colouring, with a smaller cycle)
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    check(run, solver, f"x = VarArray(size=4, dom=range(4))\nsatisfy([x[i] != x[j] for (i, j) in {edges}], Precedence(x, values=range(4)))", [range(4)] * 4,
          lambda *t: all(t[i] != t[j] for (i, j) in edges) and precedence(t, [0, 1, 2, 3]))


def test_precedence_example_with_covered(run, solver):
    # the second example of the documentation
    check(run, solver, "y = VarArray(size=7, dom=range(3))\nsatisfy(Precedence(y, values=[0, 1, 2], covered=True))", [range(3)] * 7,
          lambda *t: precedence(t, [0, 1, 2], covered=True))


# ----------------------------------------------------------------------------------------------- degenerated cases

@pytest.mark.parametrize("constraint, predicate", [
    ("Precedence([x[0]], values=[0, 1, 2])", lambda a, b, c, d: a == 0 or a not in (1, 2)),  # a single variable cannot take 1 or 2
    ("Precedence(x[0], values=[1, 2])", lambda a, b, c, d: a != 2),
    ("Precedence([x[0]])", lambda a, b, c, d: a == 0),  # the smallest value of the domain
    ("Precedence([x[0]], values=[0, 1], covered=True)", lambda a, b, c, d: False),  # 0 and 1 cannot both be assigned
    ("Precedence([x[0]], values=[2], covered=True)", lambda a, b, c, d: a == 2),
    ("Precedence(x, values=[1], covered=True)", lambda *t: 1 in t),  # a single value must be assigned
    ("Precedence(x, values=[1])", lambda *t: True),  # a single value, not covered: no constraint
    ("Precedence(x, values=[])", lambda *t: True),
    ("Precedence([])", lambda *t: True),
], ids=["one variable", "one variable (not in a list)", "one variable without values", "one variable covered", "one variable one value covered",
        "one value covered", "one value", "no value", "no variable"])
def test_precedence_degenerated(run, solver, request, constraint, predicate):
    if constraint == "Precedence([x[0]], values=[0, 1], covered=True)":  # the constraint false, posted by a table with an empty set of supports
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)
    elif "covered" in constraint and not constraint.startswith("Precedence([x[0]]"):
        request.applymarker(bug(COVERED))
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: predicate(*t) and t[3] != 1)


# ---------------------------------------------------------------------------------------------------------- groups

def test_precedence_on_sliding_windows(run, solver):
    check(run, solver, "x = VarArray(size=5, dom=range(3))\nsatisfy([Precedence(x[i:i + 3], values=[0, 1]) for i in range(3)])", [range(3)] * 5,
          lambda *t: all(precedence(t[i:i + 3], [0, 1]) for i in range(3)))


# ------------------------------------------------------------------------------------------------ logical contexts

@pytest.mark.parametrize("constraint, predicate", [
    ("~Precedence(x, values=[0, 1])", lambda *t: not precedence(t, [0, 1])),
    ("Precedence(x, values=[0, 1]) | (x[0] == 2)", lambda *t: precedence(t, [0, 1]) or t[0] == 2),
    ("Precedence(x, values=[0, 1]) & (x[0] == 2)", lambda *t: precedence(t, [0, 1]) and t[0] == 2),
    ("imply(x[0] == 2, Precedence(x, values=[1, 0]))", lambda *t: t[0] != 2 or precedence(t, [1, 0])),
    ("Precedence(x, values=[0, 1, 2], covered=True) | (x[0] == 2)", lambda *t: precedence(t, [0, 1, 2], covered=True) or t[0] == 2),
], ids=["not", "or", "and", "imply", "or covered"])
def test_precedence_in_logical_expressions(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, expected", [
    ("Precedence(x)", ("x[]", None, None)),
    pytest.param("Precedence(x, covered=True)", ("x[]", "0 1 2", "true"), marks=bug(COVERED)),  # the union of the domains
    ("Precedence(x, values=[0, 1, 2])", ("x[]", "0 1 2", None)),
    ("Precedence(x, values=range(3), covered=True)", ("x[]", "0 1 2", "true")),
    ("Precedence(x[1:], values=(2, 0))", ("x[1..3]", "2 0", None)),
])
def test_xcsp3_precedence(run, constraint, expected):
    r = run(X4 + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/precedence")
    assert c is not None, r.report()
    lst, values = c.find("list"), c.find("values")
    got = (" ".join((lst.text if lst is not None else c.text).split()), None if values is None else " ".join(values.text.split()),
           None if values is None else values.get("covered"))
    assert got == expected, r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("arguments", [
    "None",
    "x, values={0, 1}",
    "x, values=[0, 'a']",
    "x, values=2",
    "x, values=[0, 0, 1]",
    "[x[0], 'a'], values=[0, 1]",
])
def test_invalid_precedence(run, arguments):
    assert_fails(run(X4 + f"satisfy(Precedence({arguments}))"))
