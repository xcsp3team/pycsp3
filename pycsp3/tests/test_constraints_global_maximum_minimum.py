"""
Tests of the constraints Maximum and Minimum of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#Maximum): the functions Maximum() and Minimum(), on variables, integers and expressions,
with conditions given by operators or by the parameter condition, as terms of expressions, in groups of constraints, in logical expressions and
in objectives.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force; each test is run
for Maximum() (compared with max()) and for Minimum() (compared with min()).
According to XCSP3-core, maximum(X, (op, k)) holds iff max(X) op k, and minimum(X, (op, k)) iff min(X) op k, X being a list of (at least two)
integer variables, or of integer expressions (generalized form); an objective of type maximum or minimum has also a list of at least two terms.
"""

import re

import pytest

from harness import assert_fails, assert_optimum, assert_solutions, brute_force, bug, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
NO_TERM = "#246: Maximum() and Minimum() of no term fail with an assert without message"
SYMBOLIC = "#247: Maximum() and Minimum() accept symbolic variables"
BOOLEAN = "#247: a Boolean among the terms of Maximum() and Minimum() is reported as a value of a domain"
INTEGERS = "#248: Maximum() and Minimum() of integers only are not evaluated (an auxiliary variable for each integer)"
VARIABLE_IN_A_SET = "#249: a variable in the set of values of 'in' fails with an assert without message"
REPEATED = ("#250: a term given several times to Maximum() and Minimum() is written several times (ACE finds wrong solutions for "
            "maximum on a list made of a single variable given several times)")
EMPTY_SUPPORTS = ("(to be reported) ACE and CHOCO fail on a table with an empty set of supports, recognized as false by the parser "
                  "(buildCtrFalse(): RuntimeException: Constraint with only conflicts)")
ACE_NE = "xcsp3team/ACE#34: ACE fails on maximum and minimum with (ne,k): ERROR (ExtremumCst.buildFrom(): AssertionError: NE is not implemented)"
COSOCO_CONDITIONS = ("xcsp3team/cosoco#99: cosoco finds wrong solutions for maximum and minimum with (ne,k) (posted as (eq,k)), (lt|le|gt|ge,y) (posted "
                     "as op(y,max(X))), an interval (bounds swapped, notin seen as in) and a set (seen as an interval)")
COSOCO_SEGFAULT = ("xcsp3team/cosoco#99: cosoco crashes (segmentation fault) on maximum with (eq,y) when a value of y between the bounds of the list is "
                   "in no domain of the list (MaximumVariableEQ: null sentinel, checked in MinimumVariableEQ)")
CHOCO_INTERVAL = ("CHOCO 4.10.15-beta (embedded in PyCSP3) and CHOCO 6.0.2 find wrong solutions for maximum and minimum with (in,a..b) and "
                  "(notin,a..b), fixed in the develop version of CHOCO (859fdde, not reported)")

# The cases that a solver says it does not handle (not reported)
COSOCO_EXPRESSIONS = "cosoco does not handle maximum and minimum on expressions, except with (eq,y) (Maximum over set is not yet supported, s UNSUPPORTED)"
COSOCO_REPEATED = "cosoco does not accept a variable given several times in the list of minimum (scope contains variable x[0] many times)"

FUNCTIONS = [pytest.param("Maximum", max, id="Maximum"), pytest.param("Minimum", min, id="Minimum")]

X3 = "x = VarArray(size=3, dom=range(4))\n"
D3 = [range(4)] * 3
XY = X3 + "y = Var(dom=range(5))\n"
DY = D3 + [range(5)]


def code_of(code, name):
    """The code with F( replaced by Maximum( or Minimum(."""
    return re.sub(r"(?<![A-Za-z_])F\(", name + "(", code)


def mark_conditions(request, constraint):
    """Marks the running test (using the fixture solver) according to the condition of the extremum, given by an operator or the parameter condition."""
    c = constraint.replace("'", "")
    if re.search(r"!= \d|\(ne, \d", c):
        bug_for(request, ("ACE", "COSOCO"), ACE_NE if request.node.callspec.params["solver"] == "ACE" else COSOCO_CONDITIONS)
    if re.search(r"F\(x\) (<|<=|>|>=) (y|x\[0\])|y >= F\(x\)|\((le|<), y\)", c) or " in " in c or "(in," in c or "(notin," in c:
        bug_for(request, "COSOCO", COSOCO_CONDITIONS)
    if "range(1, 3)" in c:
        bug_for(request, "CHOCO", CHOCO_INTERVAL)


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


# ------------------------------------------------------------------------------------------------------------ conditions

@pytest.mark.parametrize("constraint, predicate", [
    ("F(x) == 2", lambda f, *t: f(t[:3]) == 2),
    ("F(x) == y", lambda f, *t: f(t[:3]) == t[3]),
    ("F(x) != 2", lambda f, *t: f(t[:3]) != 2),
    ("F(x) != y", lambda f, *t: f(t[:3]) != t[3]),
    ("F(x) < 2", lambda f, *t: f(t[:3]) < 2),
    ("F(x) < y", lambda f, *t: f(t[:3]) < t[3]),
    ("F(x) <= 1", lambda f, *t: f(t[:3]) <= 1),
    ("F(x) <= y", lambda f, *t: f(t[:3]) <= t[3]),
    ("F(x) > 2", lambda f, *t: f(t[:3]) > 2),
    ("F(x) > y", lambda f, *t: f(t[:3]) > t[3]),
    ("F(x) >= 1", lambda f, *t: f(t[:3]) >= 1),
    ("F(x) >= y", lambda f, *t: f(t[:3]) >= t[3]),
    ("F(x) in {1, 3}", lambda f, *t: f(t[:3]) in (1, 3)),
    ("F(x) in range(1, 3)", lambda f, *t: f(t[:3]) in (1, 2)),
    ("F(x) in range(0, 4, 2)", lambda f, *t: f(t[:3]) in (0, 2)),
    ("F(x) in [0, 3]", lambda f, *t: f(t[:3]) in (0, 3)),
    ("F(x) in (2,)", lambda f, *t: f(t[:3]) == 2),
    ("F(x) in {5, 6}", lambda f, *t: False),
    ("F(x) not in {1, 3}", lambda f, *t: f(t[:3]) not in (1, 3)),
    ("F(x) not in range(1, 3)", lambda f, *t: f(t[:3]) not in (1, 2)),
    ("F(x) not in [0, 3]", lambda f, *t: f(t[:3]) not in (0, 3)),
    ("F(x) not in {2}", lambda f, *t: f(t[:3]) != 2),
    ("y == F(x)", lambda f, *t: f(t[:3]) == t[3]),
    ("2 == F(x)", lambda f, *t: f(t[:3]) == 2),
    ("2 < F(x)", lambda f, *t: f(t[:3]) > 2),
    ("y >= F(x)", lambda f, *t: f(t[:3]) <= t[3]),
    ("F(x) == y + 1", lambda f, *t: f(t[:3]) == t[3] + 1),
    ("F(x) <= y - 2", lambda f, *t: f(t[:3]) <= t[3] - 2),
    ("F(x) == abs(y - 2)", lambda f, *t: f(t[:3]) == abs(t[3] - 2)),
    ("F(x) == x[0]", lambda f, *t: f(t[:3]) == t[0]),
    ("F(x) > x[0]", lambda f, *t: f(t[:3]) > t[0]),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_conditions(run, solver, request, name, f, constraint, predicate):
    mark_conditions(request, constraint)
    check(run, solver, XY + "satisfy(" + code_of(constraint, name) + ", y != 4)", DY, lambda *t: predicate(f, *t) and t[3] != 4)


@pytest.mark.parametrize("constraint, predicate", [
    ("F(x) in set()", lambda *t: False),
    ("F(x) in range(2, 2)", lambda *t: False),
    ("F(x) in []", lambda *t: False),
    ("F(x) not in set()", lambda *t: True),
    ("F(x) not in range(2, 2)", lambda *t: True),
    ("F(x, condition=('in', set()))", lambda *t: False),
    ("F(x, condition=('notin', range(2, 2)))", lambda *t: True),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_with_an_empty_set_of_values(run, solver, request, name, f, constraint, predicate):
    # never in an empty set: the constraint is false with 'in' (a table without support), and always true with 'not in'
    if " in " in constraint and "not in" not in constraint or "'in'" in constraint:
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)
    check(run, solver, X3 + "satisfy(" + code_of(constraint, name) + ", x[0] != 3)", D3, lambda *t: predicate(*t) and t[0] != 3)


@pytest.mark.parametrize("condition, predicate", [
    ("('eq', 2)", lambda f, *t: f(t[:3]) == 2),
    ("('ne', 2)", lambda f, *t: f(t[:3]) != 2),
    ("('le', y)", lambda f, *t: f(t[:3]) <= t[3]),
    ("['gt', 1]", lambda f, *t: f(t[:3]) > 1),
    ("('==', 2)", lambda f, *t: f(t[:3]) == 2),
    ("('<', y)", lambda f, *t: f(t[:3]) < t[3]),
    ("('in', {1, 3})", lambda f, *t: f(t[:3]) in (1, 3)),
    ("('in', range(1, 3))", lambda f, *t: f(t[:3]) in (1, 2)),
    ("('notin', [0, 3])", lambda f, *t: f(t[:3]) not in (0, 3)),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_with_the_parameter_condition(run, solver, request, name, f, condition, predicate):
    mark_conditions(request, condition)
    check(run, solver, XY + f"satisfy({name}(x, condition={condition}), y != 4)", DY, lambda *t: predicate(f, *t) and t[3] != 4)


# ------------------------------------------------------------------------------------------------------------ forms

@pytest.mark.parametrize("terms", [
    "x", "x[0], x[1], x[2]", "[x[0], x[1], x[2]]", "(x[0], x[1], x[2])", "x[i] for i in range(3)", "[x[i] for i in range(3)]",
    "x[:2], x[2]", "x[0], x[1:]", "[x[:1], [x[1], [x[2]]]]", "x[0], [x[1], x[2]]",
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_forms(run, solver, name, f, terms):
    check(run, solver, X3 + f"satisfy({name}({terms}) == 2)", D3, lambda *t: f(t) == 2)


@pytest.mark.parametrize("n, d, value", [(2, 2, 1), (2, 5, 3), (3, 3, 0), (4, 3, 2), (5, 2, 1), (6, 2, 0)])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_sizes(run, solver, name, f, n, d, value):
    check(run, solver, f"x = VarArray(size={n}, dom=range({d}))\nsatisfy({name}(x) == {value})", [range(d)] * n, lambda *t: f(t) == value)


@pytest.mark.parametrize("dom, domain, values", [
    ("{0, 2, 5}", [0, 2, 5], [0, 2, 5]),
    ("range(-3, 2)", range(-3, 2), [-3, -1, 1]),
    ("{-5, 0, 5}", [-5, 0, 5], [-5, 5]),
    ("{0, 1}", [0, 1], [0, 1]),
    ("{7}", [7], [7]),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_on_different_domains(run, solver, name, f, dom, domain, values):
    for v in values:
        check(run, solver, f"x = VarArray(size=3, dom={dom})\nsatisfy({name}(x) == {v})", [domain] * 3, lambda *t: f(t) == v)


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_on_variables_with_different_domains(run, solver, request, name, f):
    if name == "Maximum":
        bug_for(request, "COSOCO", COSOCO_SEGFAULT)  # the value 3 of w is in no domain
    check(run, solver, "x = Var(dom=range(3))\ny = Var(dom={1, 4})\nz = Var(dom=range(-2, 1))\nw = Var(dom=range(-2, 5))\n"
                       f"satisfy({name}(x, y, z) == w)", [range(3), [1, 4], range(-2, 1), range(-2, 5)],
          lambda *t: f(t[:3]) == t[3])


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_on_an_array_with_holes(run, solver, name, f):
    # the cells None of an array are discarded
    check(run, solver, f"x = VarArray(size=[2, 2], dom=lambda i, j: range(3) if i >= j else None)\nsatisfy({name}(x) == 1)", [range(3)] * 3,
          lambda *t: f(t) == 1)


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_on_a_matrix(run, solver, name, f):
    check(run, solver, f"x = VarArray(size=[2, 2], dom=range(3))\nsatisfy({name}(x) == 1, x[0][0] != x[1][1])", [range(3)] * 4,
          lambda *t: f(t) == 1 and t[0] != t[3])


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_on_several_arrays(run, solver, name, f):
    check(run, solver, X3 + f"y = VarArray(size=2, dom=range(2, 5))\nsatisfy({name}(x, y) == 3)", D3 + [range(2, 5)] * 2, lambda *t: f(t) == 3)


# ------------------------------------------------------------------------------------------------------------ terms

@pytest.mark.parametrize("terms, values", [
    ("x[0] + 1, x[1]", lambda t: (t[0] + 1, t[1])),
    ("x[0] * 2, x[1] - 1", lambda t: (t[0] * 2, t[1] - 1)),
    ("abs(x[0] - 2), x[1], x[2]", lambda t: (abs(t[0] - 2), t[1], t[2])),
    ("x[0] + x[1], x[2]", lambda t: (t[0] + t[1], t[2])),
    ("x[0] == 1, x[1]", lambda t: (int(t[0] == 1), t[1])),
    ("-x[0], -x[1]", lambda t: (-t[0], -t[1])),
    ("x[0] * x[1], x[2] + 1", lambda t: (t[0] * t[1], t[2] + 1)),
    ("x[i] + i for i in range(3)", lambda t: tuple(t[i] + i for i in range(3))),
    ("x[0], x[1] * [2]", lambda t: (t[0], t[1] * 2)),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_on_expressions(run, solver, request, name, f, terms, values):
    # the generalized form (view): a list of expressions
    if solver == "COSOCO":
        pytest.skip(COSOCO_EXPRESSIONS)
    for k in (1, 2):
        check(run, solver, X3 + f"satisfy({name}({terms}) == {k})", D3, lambda *t: f(values(t)) == k)


@pytest.mark.parametrize("terms, values", [
    ("x[0], 2", lambda t: (t[0], 2)),
    ("x[0], x[1], 3", lambda t: (t[0], t[1], 3)),
    ("2, x[0], x[1]", lambda t: (2, t[0], t[1])),
    ("x[0], -1", lambda t: (t[0], -1)),
    ("x[0], 2, 2", lambda t: (t[0], 2, 2)),
    ("x[0] + 1, 2", lambda t: (t[0] + 1, 2)),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_with_integers(run, solver, name, f, terms, values):
    # an integer is replaced by an auxiliary variable whose domain is this integer
    check(run, solver, XY + f"satisfy({name}({terms}) == y)", DY, lambda *t: f(values(t)) == t[3])


@pytest.mark.parametrize("terms", ["3, 1", "1, 3, 2", "-2, 0"])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_of_integers(run, solver, name, f, terms):
    values = eval("(" + terms + ")")
    check(run, solver, "y = Var(dom=range(-3, 5))\n" + f"satisfy({name}({terms}) == y)", [range(-3, 5)], lambda v: f(values) == v)


@pytest.mark.parametrize("terms, values", [
    ("Sum(x[:2]), x[2]", lambda t: (t[0] + t[1], t[2])),
    ("x[0], Count(x[1:], value=1)", lambda t: (t[0], t[1:].count(1))),
    ("x[2], x[:2] * [1, 2]", lambda t: (t[2], t[0] + 2 * t[1])),
    ("Maximum(x[:2]), x[2]", lambda t: (max(t[:2]), t[2])),
    ("Minimum(x[:2]), x[2]", lambda t: (min(t[:2]), t[2])),
    ("NValues(x), x[0]", lambda t: (len(set(t)), t[0])),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_on_components(run, solver, name, f, terms, values):
    # the components (Sum, Count, ...) among the terms are replaced by auxiliary variables
    for k in (1, 3):
        check(run, solver, X3 + f"satisfy({name}({terms}) == {k})", D3, lambda *t: f(values(t)) == k)


# ------------------------------------------------------------------------------------------------ degenerated cases

@pytest.mark.parametrize("constraint, predicate", [
    ("F(x[0]) == 2", lambda f, *t: t[0] == 2),
    ("F([x[0]]) < 2", lambda f, *t: t[0] < 2),
    ("F(x[0] + 1) == 2", lambda f, *t: t[0] == 1),
    ("F(x[0]) in {1, 3}", lambda f, *t: t[0] in (1, 3)),
    ("F(x[0], None) == 2", lambda f, *t: t[0] == 2),
    ("F(3) == x[0]", lambda f, *t: t[0] == 3),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_on_a_single_term(run, solver, name, f, constraint, predicate):
    check(run, solver, X3 + "satisfy(" + code_of(constraint, name) + ", x[1] == x[2])", D3, lambda *t: predicate(f, *t) and t[1] == t[2])


@pytest.mark.parametrize("constraint", ["F(x[0]) == 2", "F(x[0], condition=('eq', 2))", "F(x[0] + 1, condition=('le', 2))", "F(3) == x[0]",
                                        "F(x[0], condition=('in', {1, 3}))", "F([x[0]], condition=('notin', range(1, 3)))"])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_xcsp3_extremum_has_at_least_two_terms(run, name, f, constraint):
    # XCSP3-core requires at least two terms: a single term subject to a condition is an expression
    r = run(X3 + "satisfy(" + code_of(constraint, name) + ")")
    assert r.ok, r.report()
    assert r.xml.find("constraints/" + name.lower()) is None, r.report()


@pytest.mark.parametrize("condition, predicate", [
    ("('ge', 2)", lambda *t: t[0] >= 2),
    ("('ne', x[1])", lambda *t: t[0] != t[1]),
    ("('in', {1, 3})", lambda *t: t[0] in (1, 3)),
    ("('notin', range(1, 3))", lambda *t: t[0] not in (1, 2)),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_on_a_single_term_with_the_parameter_condition(run, solver, name, f, condition, predicate):
    # the condition is applied to the term
    check(run, solver, X3 + f"satisfy({name}(x[0], condition={condition}), x[1] == x[2])", D3, lambda *t: predicate(*t) and t[1] == t[2])


@pytest.mark.parametrize("terms, values", [
    ("x[0], x[0]", lambda t: (t[0],)),
    ("x[0], x[0], x[1]", lambda t: (t[0], t[1])),
    ("x[0], x[1], x[0], x[1]", lambda t: (t[0], t[1])),
    ("x[0] + 1, x[0] + 1, x[1]", lambda t: (t[0] + 1, t[1])),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_with_a_repeated_term(run, solver, request, name, f, terms, values):
    if solver == "COSOCO" and "+" in terms:
        pytest.skip(COSOCO_EXPRESSIONS)
    if solver == "COSOCO" and name == "Minimum":
        pytest.skip(COSOCO_REPEATED)
    if name == "Maximum" and terms == "x[0], x[0]":
        bug_for(request, "ACE", REPEATED)
    for k in (1, 2):
        check(run, solver, X3 + f"satisfy({name}({terms}) == {k})", D3, lambda *t: f(values(t)) == k)


@pytest.mark.parametrize("constraint, expected", [
    ("F(x[0], x[0], x[1]) == 2", "x[0] x[1]"),
    ("F(x[0], x[1], x[0], x[1]) == 2", "x[0] x[1]"),
    ("F(x[0] + 1, x[0] + 1, x[1]) == 2", "x[1] add(x[0],1)"),
    ("F(Sum(x[:2]), Sum(x[:2]), x[2]) == 2", "aux_gb[0] x[2]"),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
@bug(REPEATED)
def test_xcsp3_extremum_with_a_repeated_term(run, name, f, constraint, expected):
    # each term is kept once (the extremum does not depend on repetitions)
    r = run(X3 + "satisfy(" + code_of(constraint, name) + ")")
    assert r.ok, r.report()
    c = r.xml.find("constraints/" + name.lower())
    assert c is not None and c.find("list").text.strip() == expected, r.report()


@pytest.mark.parametrize("name, f", FUNCTIONS)
@bug(REPEATED)
def test_xcsp3_extremum_of_a_single_repeated_term(run, name, f):
    # a single term remains: the extremum is this term
    r = run(X3 + f"satisfy({name}(x[0], x[0]) == 2, x[1] != x[2])\nminimize({name}(x[1], x[1]))")
    assert r.ok, r.report()
    o = r.xml.find("objectives/minimize")
    assert r.xml.find("constraints/" + name.lower()) is None and o.get("type") is None and o.text.strip() == "x[1]", r.report()


# ------------------------------------------------------------------------------------------------ terms of expressions

@pytest.mark.parametrize("constraint, predicate", [
    ("F(x) + 1 == y", lambda f, *t: f(t[:3]) + 1 == t[3]),
    ("F(x) * 2 <= y", lambda f, *t: f(t[:3]) * 2 <= t[3]),
    ("y - F(x) == 1", lambda f, *t: t[3] - f(t[:3]) == 1),
    ("-F(x) == -2", lambda f, *t: f(t[:3]) == 2),
    ("F(x) // 2 == 1", lambda f, *t: f(t[:3]) // 2 == 1),
    ("F(x) % 2 == 1", lambda f, *t: f(t[:3]) % 2 == 1),
    ("F(x) + F(x[:2]) == 3", lambda f, *t: f(t[:3]) + f(t[:2]) == 3),
    ("F(x[:2]) == F(x[1:])", lambda f, *t: f(t[:2]) == f(t[1:3])),
    ("F(x[:2]) - F(x[1:]) == 1", lambda f, *t: f(t[:2]) - f(t[1:3]) == 1),
    ("abs(F(x) - y) <= 1", lambda f, *t: abs(f(t[:3]) - t[3]) <= 1),
    ("F(x) != F(x[1:])", lambda f, *t: f(t[:3]) != f(t[1:3])),
    ("F(x) == F(x)", lambda f, *t: True),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_as_a_term(run, solver, name, f, constraint, predicate):
    check(run, solver, XY + "satisfy(" + code_of(constraint, name) + ")", DY, lambda *t: predicate(f, *t))


@pytest.mark.parametrize("dom, domain", [("{0, 2, 5}", [0, 2, 5]), ("range(-3, 2)", range(-3, 2)), ("{-4, 1, 3}", [-4, 1, 3])])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_as_a_term_on_different_domains(run, solver, name, f, dom, domain):
    # the domain of the auxiliary variable must contain all the possible values of the extremum
    check(run, solver, f"x = VarArray(size=2, dom={dom})\ny = Var(dom=range(-3, 7))\nsatisfy({name}(x) + 1 == y)", [domain] * 2 + [range(-3, 7)],
          lambda *t: f(t[:2]) + 1 == t[2])


# ---------------------------------------------------------------------------------------------------------- groups

@pytest.mark.parametrize("constraints, predicate", [
    ("[F(x[i], x[i + 1]) <= 2 for i in range(2)]", lambda f, *t: all(f(t[i], t[i + 1]) <= 2 for i in range(2))),
    ("[F(x[i], x[i + 1]) == x[i] for i in range(2)]", lambda f, *t: all(f(t[i], t[i + 1]) == t[i] for i in range(2))),
    pytest.param("[F(x[i], x[i + 1]) != i for i in range(2)]", lambda f, *t: all(f(t[i], t[i + 1]) != i for i in range(2)), id="!= i"),
    ("[F(x[i], y) == i + 1 for i in range(3)]", lambda f, *t: all(f(t[i], t[3]) == i + 1 for i in range(3))),
    ("[F(x[:2]) == 2, F(x[1:]) == 1]", lambda f, *t: f(t[:2]) == 2 and f(t[1:3]) == 1),
    ("[F(x[i] + 1, y) > 2 for i in range(2)]", lambda f, *t: all(f(t[i] + 1, t[3]) > 2 for i in range(2))),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_in_groups(run, solver, request, name, f, constraints, predicate):
    if solver == "COSOCO" and "+ 1, y" in constraints:
        pytest.skip(COSOCO_EXPRESSIONS)
    if "!= i" in constraints:
        bug_for(request, "ACE", ACE_NE)
        bug_for(request, "COSOCO", COSOCO_CONDITIONS)
    check(run, solver, XY + "satisfy(" + code_of(constraints, name) + ")", DY, lambda *t: predicate(f, *t))


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_in_a_function(run, solver, name, f):
    check(run, solver, X3 + f"def c(i):\n    return {name}(x[i], x[i + 1]) == 2\n\nsatisfy(c(i) for i in range(2))", D3,
          lambda *t: all(f(t[i], t[i + 1]) == 2 for i in range(2)))


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_in_a_slide(run, solver, name, f):
    check(run, solver, X3 + f"satisfy(Slide({name}(x[i], x[i + 1]) >= 1 for i in range(2)))", D3, lambda *t: all(f(t[i], t[i + 1]) >= 1 for i in range(2)))


# ------------------------------------------------------------------------------------------------ logical contexts

@pytest.mark.parametrize("constraint, predicate", [
    ("(F(x) == 2) | (y == 1)", lambda f, *t: f(t[:3]) == 2 or t[3] == 1),
    ("(F(x) == 2) & (y == 1)", lambda f, *t: f(t[:3]) == 2 and t[3] == 1),
    ("~(F(x) == 2)", lambda f, *t: f(t[:3]) != 2),
    ("~(F(x) <= y)", lambda f, *t: f(t[:3]) > t[3]),
    ("imply(F(x) == 2, y == 1)", lambda f, *t: f(t[:3]) != 2 or t[3] == 1),
    ("iff(F(x) == 2, y == 1)", lambda f, *t: (f(t[:3]) == 2) == (t[3] == 1)),
    ("xor(F(x) == 2, y == 1)", lambda f, *t: (f(t[:3]) == 2) != (t[3] == 1)),
    ("If(F(x) == 2, Then=y == 1)", lambda f, *t: f(t[:3]) != 2 or t[3] == 1),
    ("If(y == 1, Then=F(x) == 2, Else=F(x) == 0)", lambda f, *t: f(t[:3]) == (2 if t[3] == 1 else 0)),
    ("either(F(x) == 2, y == 1)", lambda f, *t: f(t[:3]) == 2 or t[3] == 1),
    ("both(F(x) >= 1, y == 1)", lambda f, *t: f(t[:3]) >= 1 and t[3] == 1),
    ("disjunction(F(x) == v for v in [0, 3])", lambda f, *t: f(t[:3]) in (0, 3)),
    ("conjunction(F(x[:2]) == 1, F(x[1:]) == 2)", lambda f, *t: f(t[:2]) == 1 and f(t[1:3]) == 2),
    ("(F(x) == y) | (y == 0)", lambda f, *t: f(t[:3]) == t[3] or t[3] == 0),
    ("(F(x) < y) | (F(x[:2]) == 3)", lambda f, *t: f(t[:3]) < t[3] or f(t[:2]) == 3),
    ("(F(x) in {1, 3}) | (y == 1)", lambda f, *t: f(t[:3]) in (1, 3) or t[3] == 1),
    ("(F(x) not in {1, 3}) | (y == 1)", lambda f, *t: f(t[:3]) not in (1, 3) or t[3] == 1),
    ("(F(x) == 2) == (y == 1)", lambda f, *t: (f(t[:3]) == 2) == (t[3] == 1)),
    ("(F(x) + 1 == y) | (y == 0)", lambda f, *t: f(t[:3]) + 1 == t[3] or t[3] == 0),
    ("(F(x[0] + 1, x[1]) == 2) | (y == 1)", lambda f, *t: f(t[0] + 1, t[1]) == 2 or t[3] == 1),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_in_logical_expressions(run, solver, name, f, constraint, predicate):
    # the extremum is replaced by an auxiliary variable
    check(run, solver, XY + "satisfy(" + code_of(constraint, name) + ")", DY, lambda *t: predicate(f, *t))


@pytest.mark.parametrize("constraint, predicate", [
    ("(F(z) == 2) | (y == 1)", lambda f, *t: f(t[:2]) == 2 or t[2] == 1),
    ("(F(z) < y) | (y == 0)", lambda f, *t: f(t[:2]) < t[2] or t[2] == 0),
    ("~(F(z) == 5)", lambda f, *t: f(t[:2]) != 5),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_in_logical_expressions_on_domains_with_holes(run, solver, name, f, constraint, predicate):
    # the auxiliary variable replacing the extremum has only the possible values of the extremum (here 0, 2 and 5)
    check(run, solver, "z = VarArray(size=2, dom={0, 2, 5})\ny = Var(dom=range(4))\nsatisfy(" + code_of(constraint, name) + ")", [[0, 2, 5]] * 2 + [range(4)],
          lambda *t: predicate(f, *t))


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_in_a_meta_constraint(run, name, f):
    # a meta-constraint explicitly asked for (not in XCSP3-core): the constraint is kept
    r = run(XY + f"satisfy(Or({name}(x) == 2, y == 1, meta=True))")
    assert r.ok, r.report()
    assert r.xml.find("constraints/or/" + name.lower()) is not None, r.report()


# ------------------------------------------------------------------------------------------------------------ objectives

@pytest.mark.parametrize("objective, function", [
    ("minimize(F(x))", lambda f, *t: f(t)),
    ("maximize(F(x))", lambda f, *t: f(t)),
    ("minimize(F(x[0] + 1, x[1], x[2] * 2))", lambda f, *t: f(t[0] + 1, t[1], t[2] * 2)),
    ("maximize(F(x[i] * (3 - i) for i in range(3)))", lambda f, *t: f(t[i] * (3 - i) for i in range(3))),
    ("minimize(F(x[0], 2))", lambda f, *t: f(t[0], 2)),
    ("maximize(F(x[0], x[0], x[1]))", lambda f, *t: f(t[0], t[1])),
    ("minimize(F(x) + 1)", lambda f, *t: f(t) + 1),
    ("maximize(F(x) * 2 - x[0])", lambda f, *t: f(t) * 2 - t[0]),
    ("maximize(F(x[:2]) - F(x[1:]))", lambda f, *t: f(t[:2]) - f(t[1:])),
    ("minimize(F(x[0]))", lambda f, *t: t[0]),
    ("maximize(F(Sum(x[:2]), x[2]))", lambda f, *t: f(t[0] + t[1], t[2])),
    ("minimize(F(x[0], x[1:] * [2, 3]))", lambda f, *t: f(t[0], 2 * t[1] + 3 * t[2])),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_as_objective(run, solver, name, f, objective, function):
    if solver == "COSOCO" and "x[0], x[0]" in objective:
        pytest.skip(COSOCO_REPEATED + ", used for the bound of the objective")
    code = code_of(objective, name)
    r = run(X3 + "satisfy(x[0] != x[1], x[1] != x[2])\n" + code, solver=solver)
    expected = brute_force(D3, lambda *t: t[0] != t[1] and t[1] != t[2])
    assert_optimum(r, expected, lambda *t: function(f, *t), maximize=code.startswith("maximize"))


@pytest.mark.parametrize("name, f", FUNCTIONS)
@bug(INTEGERS)
def test_extremum_of_integers_as_objective(run, name, f):
    # the extremum of integers is a constant: there is nothing to optimize
    assert_fails(run(X3 + f"satisfy(x[0] != x[1])\nminimize({name}(3, 1))"))


# ------------------------------------------------------------------------------------------------ examples of the doc

def test_maximum_example(run, solver):
    # the makespan of the example of the doc: its optimal value is 14, and the solution given is optimal
    r = run("durations = [3, 5, 2, 4]\ns = VarArray(size=4, dom=range(20))\nsatisfy(NoOverlap(origins=s, lengths=durations))\n"
            "minimize(Maximum(s[i] + durations[i] for i in range(4)))\n"
            f"print('result', solve(solver={solver}).name, bound())")
    assert r.ok and "result OPTIMUM 14" in r.lines, r.report()
    if solver == "COSOCO":
        pytest.skip(COSOCO_EXPRESSIONS)
    r = run("durations = [3, 5, 2, 4]\ns = VarArray(size=4, dom=range(20))\nsatisfy(NoOverlap(origins=s, lengths=durations), s == [0, 3, 8, 10])\n"
            "satisfy(Maximum(s[i] + durations[i] for i in range(4)) == 14)", solver=solver)
    assert r.ok and r.status == "SAT" and len(r.raw_solutions) == 1, r.report()


def test_minimum_example(run, solver):
    # the fair division of the example of the doc: its optimal value is 25, and the solution given is optimal
    r = run("x = VarArray(size=4, dom=range(100))\nsatisfy(Sum(x) == 100)\nmaximize(Minimum(x))\n" f"print('result', solve(solver={solver}).name, bound())")
    assert r.ok and "result OPTIMUM 25" in r.lines, r.report()
    r = run("x = VarArray(size=4, dom=range(100))\nsatisfy(Sum(x) == 100, x == [25, 25, 25, 25], Minimum(x) == 25)", solver=solver)
    assert r.ok and r.status == "SAT" and len(r.raw_solutions) == 1, r.report()


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, expected", [
    ("F(x) == 2", ("x[]", "(eq,2)")),
    ("F(x) <= y", ("x[]", "(le,y)")),
    ("F(x) in {1, 3}", ("x[]", "(in,{1,3})")),
    ("F(x) in range(1, 3)", ("x[]", "(in,1..2)")),
    ("F(x) not in {1, 3}", ("x[]", "(notin,{1,3})")),
    ("2 < F(x)", ("x[]", "(gt,2)")),
    ("F(x[0], x[2]) != 1", ("x[0] x[2]", "(ne,1)")),
    ("F(x[0] + 1, x[1]) == 2", ("add(x[0],1) x[1]", "(eq,2)")),
    ("F(x, condition=('eq', 2))", ("x[]", "(eq,2)")),
    ("F(x, condition=('in', range(1, 3)))", ("x[]", "(in,1..2)")),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_xcsp3_extremum(run, name, f, constraint, expected):
    r = run(XY + "satisfy(" + code_of(constraint, name) + ")")
    assert r.ok, r.report()
    c = r.xml.find("constraints/" + name.lower())
    assert c is not None, r.report()
    assert (c.find("list").text.strip(), c.find("condition").text.strip()) == expected, r.report()


@pytest.mark.parametrize("objective, expected", [
    ("minimize(F(x))", ("minimize", "x[]")),
    ("maximize(F(x))", ("maximize", "x[]")),
    ("minimize(F(x[0] * 2, x[1]))", ("minimize", "mul(x[0],2) x[1]")),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_xcsp3_extremum_as_objective(run, name, f, objective, expected):
    r = run(X3 + code_of(objective, name))
    assert r.ok, r.report()
    o = r.xml.find("objectives/" + expected[0])
    assert o is not None and o.get("type") == name.lower() and o.text.strip() == expected[1], r.report()


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_xcsp3_extremum_in_a_group(run, name, f):
    r = run(X3 + f"satisfy({name}(x[i], x[i + 1]) <= 2 for i in range(2))")
    assert r.ok, r.report()
    assert r.xml.find("constraints/group/" + name.lower()) is not None and len(r.xml.findall("constraints/group/args")) == 2, r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("arguments", [
    "",
    "[]",
    "x[i] for i in range(0)",
    "None",
    "[None, None]",
    "x, 'a'",
    "x, 1.5",
    "x, range(3)",
    "x, {'a': 1}",
    "True, x[0]",
    "x[0], False",
    "x, condition='eq'",
    "x, condition=('eq',)",
    "x, condition=('foo', 2)",
    "x, condition=('eq', 'a')",
    "x, condition=('eq', True)",
    "x, condition=('in', 2)",
    "x, condition=('eq', {1, 2})",
    "x, condition=('lt', range(3))",
    "x, foo=2",
    "s",
    "x[0], s[0]",
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_invalid_extremum(run, request, name, f, arguments):
    if arguments in ("[]", "x[i] for i in range(0)", "None", "[None, None]"):
        request.applymarker(bug(NO_TERM))
    if arguments in ("s", "x[0], s[0]"):
        request.applymarker(bug(SYMBOLIC))
    code = X3 + "s = VarArray(size=2, dom={'a', 'b'})\n" + f"satisfy({name}({arguments}) == 1)"
    if "condition=" in arguments:
        code = X3 + f"satisfy({name}({arguments}))"
    assert_fails(run(code))


@pytest.mark.parametrize("operand", ["2.5", "'a'", "True", "None", "[y, 2]", "{1: 2}"])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_invalid_extremum_operand(run, request, name, f, operand):
    if operand == "[y, 2]":
        request.applymarker(bug(VARIABLE_IN_A_SET))
    constraint = f"{name}(x) in {operand}" if operand == "[y, 2]" else f"{name}(x) == {operand}"
    assert_fails(run(XY + f"satisfy({constraint})"))


@pytest.mark.parametrize("arguments, message", [
    ("[]", "() requires at least one term"),
    ("None", "() requires at least one term"),
    ("True, x[0]", "() does not accept Booleans as terms, which is the case of True"),
    ("s", "() requires integer variables (or expressions), which is not the case of s[0]"),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_invalid_extremum_message(run, request, name, f, arguments, message):
    request.applymarker(bug(SYMBOLIC if arguments == "s" else BOOLEAN if "True" in arguments else NO_TERM))
    r = run(X3 + "s = VarArray(size=2, dom={'a', 'b'})\n" + f"satisfy({name}({arguments}) == 1)")
    assert not r.ok and name + message in r.stdout, r.report()


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_negated_with_in(run, name, f):
    # ~ cannot be applied to an expression with 'in' (evaluated as a Boolean by Python): 'not in' must be used instead
    r = run(X3 + f"satisfy(~({name}(x) in {{1, 3}}))")
    assert not r.ok and "write 'not in' instead" in r.stdout, r.report()


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_without_condition(run, name, f):
    # a component Maximum (or Minimum) must be subject to a condition to be a constraint
    r = run(X3 + f"satisfy({name}(x))")
    assert not r.ok and "is not a constraint: it must be subject to a condition" in r.stdout, r.report()
