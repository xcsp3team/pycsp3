"""
Tests of the constraint Sum of the section Constraints (Global) of the API (https://pycsp.org/documentation/api/constraints-global/#Sum):
the function Sum(), which builds a component that becomes a constraint sum when compared with a value, a variable, an expression, an interval or a
set (or when given the parameter condition), with or without coefficients (x * [1, 2, 3], Sum(c * x[i] for i in ...), variables as coefficients),
on variables and on expressions, as a term of expressions, in groups of constraints, in logical expressions, in objectives, and with the option -mini.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
According to XCSP3-core, sum(X, C, (op, k)) holds iff the sum of the c[i] * x[i] satisfies (op, k), with |X| = |C| >= 2, expressions being accepted
instead of variables (generalized forms). In the mini-tracks of the XCSP3 competitions, the list of a sum only contains variables and the operator of
the condition is relational (lt, le, gt, ge, eq or ne), its operand being a value or a variable.
"""

import re

import pytest

from harness import assert_fails, assert_optimum, assert_solutions, brute_force, bug, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
NEG_ORDER = "(to be reported) -Sum(x) writes the element <coeffs> after <condition>, and ACE and CHOCO fail (StringIndexOutOfBoundsException)"
SUM_TIMES = "(to be reported) Sum(x) * y, a sum multiplied by a variable or an expression, fails with an assert without message"
EMPTY_CONDITION = ("(to be reported) Sum(x) in range(0), in set() and not in range(0) write the conditions (in,0..-1), (in,{}) and (notin,0..-1), "
                   "on which the solvers fail")
HOLES_COEFFS = "(to be reported) coefficients given for an array with holes (w * [1, 2, 3, 4]) are not discarded with the holes: assert fails"
MINI_SET = "(to be reported) with -mini, a sum keeps its condition in or notin, which is not accepted in the mini-tracks"
ONE_TERM = "(to be reported) a sum on a single variable with a coefficient is written as <sum> with one term, while XCSP3-core requires at least two"
INVALID = "(to be reported) an invalid argument of Sum() is not reported explicitly (or not reported at all)"
ACE_NOTIN = ("(to be reported) ACE gives the solutions of in instead of those of notin for a sum on a small space "
             "(Problem.sum(): the table is built with api.in(...) whatever the operator)")
ACE_CANCEL = ("(to be reported) ACE fails on a sum whose terms all cancel out (Problem.sum(): newCoeffs[0] read on an empty array once the terms "
              "of coefficient 0 are discarded)")
CHOCO_NOTIN = ("(to be reported) CHOCO gives wrong solutions, several times, for a sum with notin (buildSum(): resu != sum, with resu a new variable "
               "taking any value of the set)")
COSOCO_BASIC = ("(to be reported) cosoco gives wrong solutions for a sum mixing expressions such as eq(x,k) and variables that are not 0/1, without "
                "coefficients (matchParams() accepts any variable, while BasicNodeVar assumes a 0/1 variable)")
COSOCO_CANCEL = ("(to be reported) cosoco gives an invalid solution (Solution Error) for a sum whose terms all cancel out, when the condition "
                 "cannot be satisfied")
EMPTY_SUPPORTS = ("(to be reported) ACE and CHOCO fail on a table with an empty set of supports, recognized as false by the parser "
                  "(buildCtrFalse(): RuntimeException: Constraint with only conflicts)")


def notin_bugs(request, text):
    """Marks the running test with the bugs of ACE and CHOCO on notin, if the text contains a condition notin."""
    if "not in" in text or "notin" in text:
        bug_for(request, "ACE", ACE_NOTIN)
        bug_for(request, "CHOCO", CHOCO_NOTIN)



def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


X4 = "x = VarArray(size=4, dom=range(3))\n"
D4 = [range(3)] * 4


# ------------------------------------------------------------------------------------------------------------ conditions

@pytest.mark.parametrize("condition, predicate", [
    ("== 3", lambda s: s == 3),
    ("!= 3", lambda s: s != 3),
    ("< 3", lambda s: s < 3),
    ("<= 3", lambda s: s <= 3),
    ("> 5", lambda s: s > 5),
    (">= 5", lambda s: s >= 5),
    ("in range(2, 5)", lambda s: 2 <= s <= 4),
    ("in {1, 3, 5}", lambda s: s in (1, 3, 5)),
    ("in [1, 3, 5]", lambda s: s in (1, 3, 5)),
    ("in {4}", lambda s: s == 4),
    ("in range(0, 9, 2)", lambda s: s % 2 == 0),
    ("not in range(2, 5)", lambda s: not 2 <= s <= 4),
    ("not in {1, 3, 5}", lambda s: s not in (1, 3, 5)),
    ("not in [1, 3, 5]", lambda s: s not in (1, 3, 5)),
])
def test_sum_conditions(run, solver, request, condition, predicate):
    notin_bugs(request, condition)
    check(run, solver, X4 + f"satisfy(Sum(x) {condition})", D4, lambda *t: predicate(sum(t)))


@pytest.mark.parametrize("constraint, predicate", [
    ("3 <= Sum(x)", lambda s: s >= 3),
    ("3 == Sum(x)", lambda s: s == 3),
    ("3 > Sum(x)", lambda s: s < 3),
    ("3 != Sum(x)", lambda s: s != 3),
])
def test_sum_on_the_right(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, lambda *t: predicate(sum(t)))


@pytest.mark.parametrize("operand, predicate", [
    ("== x[3]", lambda s, v: s == v),
    ("!= x[3]", lambda s, v: s != v),
    ("< x[3]", lambda s, v: s < v),
    ("<= x[3]", lambda s, v: s <= v),
    ("> x[3]", lambda s, v: s > v),
    (">= x[3]", lambda s, v: s >= v),
    ("== x[3] + 1", lambda s, v: s == v + 1),
    ("== x[3] * 2", lambda s, v: s == v * 2),
    ("<= abs(x[3] - 1)", lambda s, v: s <= abs(v - 1)),
    ("> 2 * x[3]", lambda s, v: s > 2 * v),
])
def test_sum_compared_with_a_variable_or_an_expression(run, solver, operand, predicate):
    check(run, solver, X4 + f"satisfy(Sum(x[:3]) {operand})", D4, lambda a, b, c, d: predicate(a + b + c, d))


@pytest.mark.parametrize("constraint, predicate", [
    ("Sum(x[:2]) == Sum(x[2:])", lambda a, b, c, d: a + b == c + d),
    ("Sum(x[:2]) > Sum(x[2:]) + 1", lambda a, b, c, d: a + b > c + d + 1),
    ("Sum(x[:2]) <= Sum(x[2:]) - 1", lambda a, b, c, d: a + b <= c + d - 1),
    ("Sum(x[:2]) != Sum(x[1:])", lambda a, b, c, d: a + b != b + c + d),
    ("Sum(x[:2] * [1, 2]) >= Sum(x[2:] * [2, 1])", lambda a, b, c, d: a + 2 * b >= 2 * c + d),
])
def test_sum_compared_with_a_sum(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


@pytest.mark.parametrize("condition, predicate", [
    ("('le', 3)", lambda s: s <= 3),
    ("['ge', 5]", lambda s: s >= 5),
    ("('<=', 3)", lambda s: s <= 3),
    ("('!=', 3)", lambda s: s != 3),
    ("('eq', 4)", lambda s: s == 4),
    ("('in', range(2, 5))", lambda s: 2 <= s <= 4),
    ("('in', {1, 3})", lambda s: s in (1, 3)),
    ("('notin', {1, 3})", lambda s: s not in (1, 3)),
])
def test_sum_with_the_parameter_condition(run, solver, request, condition, predicate):
    notin_bugs(request, condition)
    check(run, solver, X4 + f"satisfy(Sum(x, condition={condition}))", D4, lambda *t: predicate(sum(t)))


def test_sum_with_the_parameter_condition_on_a_variable(run, solver):
    check(run, solver, X4 + "satisfy(Sum(x[:3], condition=('eq', x[3])))", D4, lambda a, b, c, d: a + b + c == d)


@pytest.mark.parametrize("constraint, predicate", [
    ("Sum(x) in range(0)", lambda s: False),
    ("Sum(x) in set()", lambda s: False),
    ("Sum(x) not in range(0)", lambda s: True),
    ("Sum(x) not in set()", lambda s: True),
    ("Sum(x) in range(9, 20)", lambda s: False),
    ("Sum(x) in range(-5, 0)", lambda s: False),
    ("Sum(x) not in range(0, 9)", lambda s: False),
])
def test_sum_with_an_empty_or_unreachable_condition(run, solver, request, constraint, predicate):
    if constraint in ("Sum(x) in range(0)", "Sum(x) not in range(0)"):
        bug_for(request, ("ACE", "CHOCO"), EMPTY_CONDITION)
    elif constraint == "Sum(x) in set()":
        bug_for(request, ("ACE", "CHOCO", "COSOCO"), EMPTY_CONDITION)
    elif constraint == "Sum(x) not in set()":
        bug_for(request, ("ACE", "CHOCO"), EMPTY_CONDITION)
    else:
        notin_bugs(request, constraint)
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: predicate(sum(t)) and t[3] != 1)


# ------------------------------------------------------------------------------------------------------------ forms

@pytest.mark.parametrize("terms", [
    "x",
    "x[:]",
    "x[0], x[1], x[2], x[3]",
    "(x[0], x[1], x[2], x[3])",
    "[x[0], x[1], x[2], x[3]]",
    "x[i] for i in range(4)",
    "x[:2], x[2:]",
    "[x[:2], x[2:]]",
    "x[0], [x[1], [x[2], x[3]]]",
    "{x[0], x[1], x[2], x[3]}",
    "[x[0], None, x[1], x[2], x[3]]",
])
def test_sum_forms(run, solver, terms):
    check(run, solver, X4 + f"satisfy(Sum({terms}) == 4)", D4, lambda *t: sum(t) == 4)


def test_sum_on_a_matrix(run, solver):
    check(run, solver, "m = VarArray(size=[2, 2], dom=range(3))\nsatisfy(Sum(m) == 5)", D4, lambda *t: sum(t) == 5)


def test_sum_on_an_array_with_holes(run, solver):
    r = check(run, solver, "w = VarArray(size=4, dom=lambda i: None if i == 1 else range(3))\nsatisfy(Sum(w) == 3)", [range(3)] * 3, lambda *t: sum(t) == 3)
    assert r.variables == ["w[0]", "w[2]", "w[3]"]


@bug(HOLES_COEFFS)
def test_sum_with_coefficients_on_an_array_with_holes(run, solver):
    check(run, solver, "w = VarArray(size=4, dom=lambda i: None if i == 1 else range(3))\nsatisfy(Sum(w * [1, 2, 3, 4]) == 5)", [range(3)] * 3,
          lambda a, c, d: a + 3 * c + 4 * d == 5)


@pytest.mark.parametrize("n, d, k", [(2, 2, 1), (3, 3, 4), (5, 2, 3), (6, 2, 2)])
def test_sum_sizes(run, solver, n, d, k):
    check(run, solver, f"x = VarArray(size={n}, dom=range({d}))\nsatisfy(Sum(x) == {k})", [range(d)] * n, lambda *t: sum(t) == k)


def test_sum_on_negative_values(run, solver):
    check(run, solver, "x = VarArray(size=4, dom=range(-2, 2))\nsatisfy(Sum(x) == -1)", [range(-2, 2)] * 4, lambda *t: sum(t) == -1)


def test_sum_on_different_domains(run, solver):
    check(run, solver, "x = VarArray(size=3, dom=lambda i: {0, 2 * i + 1, 5})\nsatisfy(Sum(x) in range(6, 9))", [{0, 1, 5}, {0, 3, 5}, {0, 5}],
          lambda *t: 6 <= sum(t) <= 8)


# ------------------------------------------------------------------------------------------------------------ coefficients

@pytest.mark.parametrize("terms, coeffs", [
    ("x * [1, 2, 3, 4]", [1, 2, 3, 4]),
    ("x * (1, 2, 3, 4)", [1, 2, 3, 4]),
    ("x * range(1, 5)", [1, 2, 3, 4]),
    ("x * 2", [2, 2, 2, 2]),
    ("[1, 2, 3, 4] * x", [1, 2, 3, 4]),
    ("x * [1, -2, 3, -4]", [1, -2, 3, -4]),
    ("x * [0, 2, 0, 1]", [0, 2, 0, 1]),
    ("x * [0, 2, 3, 1]", [0, 2, 3, 1]),
    ("x * [5, 10, 100, 1000]", [5, 10, 100, 1000]),
    ("x[i] * (i + 1) for i in range(4)", [1, 2, 3, 4]),
    ("(i + 1) * x[i] for i in range(4)", [1, 2, 3, 4]),
    ("x[i] * i for i in range(4)", [0, 1, 2, 3]),
    ("-x[0], x[1], -x[2], x[3]", [-1, 1, -1, 1]),
    ("x[0] * 2, x[1], x[2] * -1, x[3]", [2, 1, -1, 1]),
    ("x[:2] * [1, 2], x[2:] * [3, 4]", [1, 2, 3, 4]),
    ("Sum(x[:2] * [1, 2]), x[2], x[3]", [1, 2, 1, 1]),
    ("x[:3] * [1, 2, 3], x[3]", [1, 2, 3, 1]),
])
@pytest.mark.parametrize("condition", ["== 5", "<= 4", "in range(3, 8)"])
def test_sum_with_coefficients(run, solver, terms, coeffs, condition):
    predicate = {"== 5": lambda s: s == 5, "<= 4": lambda s: s <= 4, "in range(3, 8)": lambda s: 3 <= s <= 7}[condition]
    check(run, solver, X4 + f"satisfy(Sum({terms}) {condition})", D4, lambda *t: predicate(sum(c * v for c, v in zip(coeffs, t))))


@pytest.mark.parametrize("constraint, predicate", [
    ("x * [1, 2, 3, 4] == 5", lambda s: s == 5),
    ("x * [1, 2, 3, 4] <= 5", lambda s: s <= 5),
    ("x * [1, 2, 3, 4] > 10", lambda s: s > 10),
    ("x * [1, 2, 3, 4] != 5", lambda s: s != 5),
    ("5 >= x * [1, 2, 3, 4]", lambda s: s <= 5),
])
def test_scalar_product_without_sum(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, lambda *t: predicate(t[0] + 2 * t[1] + 3 * t[2] + 4 * t[3]))


def test_sum_with_variables_as_coefficients(run, solver):
    check(run, solver, "x = VarArray(size=2, dom=range(3))\nc = VarArray(size=2, dom=range(3))\nsatisfy(Sum(x * c) == 3)", D4,
          lambda a, b, c, d: a * c + b * d == 3)


def test_sum_with_variables_and_integers_as_coefficients(run, solver):
    check(run, solver, "x = VarArray(size=3, dom=range(3))\nc = Var(dom=range(3))\nsatisfy(Sum(x * [1, c, 2]) == 4)", D4,
          lambda a, b, d, c: a + c * b + 2 * d == 4)


# ------------------------------------------------------------------------------------------------------------ expressions

@pytest.mark.parametrize("terms, value", [
    ("x[i] > 0 for i in range(4)", lambda *t: sum(v > 0 for v in t)),
    ("abs(x[i] - 1) for i in range(4)", lambda *t: sum(abs(v - 1) for v in t)),
    ("(x[i] == 1) * 3 for i in range(4)", lambda *t: sum(3 * (v == 1) for v in t)),
    ("x[0], x[1] + 1, x[2] * 2, x[3]", lambda a, b, c, d: a + b + 1 + 2 * c + d),
    ("x[0] - x[1], x[2], x[3]", lambda a, b, c, d: a - b + c + d),
    ("x[0] * x[1], x[2], x[3]", lambda a, b, c, d: a * b + c + d),
    ("max(x[0], x[1]), x[2]", lambda a, b, c, d: max(a, b) + c),
    ("Count(x, value=1), x[0]", lambda *t: t.count(1) + t[0]),
    ("Maximum(x[:2]), x[2]", lambda a, b, c, d: max(a, b) + c),
    ("Sum(x[:2]) == 2, x[2], x[3]", lambda a, b, c, d: (a + b == 2) + c + d),
    ("x[0] == 2, x[1], x[2]", lambda a, b, c, d: (a == 2) + b + c),
    ("x[0] != 2, x[1], x[2]", lambda a, b, c, d: (a != 2) + b + c),
    ("(x[0] == 2) * 3, x[1]", lambda a, b, c, d: 3 * (a == 2) + b),
    ("x[0] + x[1], x[2] + x[3]", lambda *t: sum(t)),
])
def test_sum_on_expressions(run, solver, request, terms, value):
    if terms in ("Sum(x[:2]) == 2, x[2], x[3]", "x[0] == 2, x[1], x[2]", "x[0] != 2, x[1], x[2]"):
        bug_for(request, "COSOCO", COSOCO_BASIC)
    check(run, solver, X4 + f"satisfy(Sum({terms}) == 3)", D4, lambda *t: value(*t) == 3)


# ------------------------------------------------------------------------------------------------ integers among the terms

@pytest.mark.parametrize("constraint, predicate", [
    ("Sum(x[0], 2, x[1]) == 3", lambda a, b, c, d: a + b == 1),
    ("Sum(x[0], 0, x[1]) == 2", lambda a, b, c, d: a + b == 2),
    ("Sum(x[0], 1, 1) == 3", lambda a, b, c, d: a == 1),
    ("Sum(x[0], -1, x[1]) == 1", lambda a, b, c, d: a + b == 2),
    ("Sum(1, x[0]) == x[1]", lambda a, b, c, d: a + 1 == b),
    ("Sum(1, 2) == 3", lambda *t: True),
    ("Sum(1, 2) == 4", lambda *t: False),
    ("Sum(1, 2) <= x[0]", lambda *t: t[0] >= 3),
    ("Sum(0) == 0", lambda *t: True),
    ("Sum([]) == 0", lambda *t: True),
    ("Sum([]) <= x[0]", lambda *t: True),
    ("Sum([]) == 1", lambda *t: False),
    ("Sum(x * [0, 0, 0, 0]) == 0", lambda *t: True),
    ("Sum(x * [0, 0, 0, 0]) == 1", lambda *t: False),
])
def test_sum_with_integers(run, solver, request, constraint, predicate):
    if constraint in ("Sum([]) == 1", "Sum(x * [0, 0, 0, 0]) == 1"):  # the constraint false, posted by a table with an empty set of supports
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: predicate(*t) and t[3] != 1)


# ----------------------------------------------------------------------------------------------- arithmetic with sums

@pytest.mark.parametrize("constraint, predicate", [
    ("Sum(x[:3]) + x[3] == 3", lambda a, b, c, d: a + b + c + d == 3),
    ("Sum(x) + 1 == 3", lambda *t: sum(t) + 1 == 3),
    ("Sum(x) - 1 == 2", lambda *t: sum(t) - 1 == 2),
    ("1 - Sum(x) == -2", lambda *t: 1 - sum(t) == -2),
    ("1 + Sum(x) == 3", lambda *t: 1 + sum(t) == 3),
    ("-Sum(x) == -3", lambda *t: -sum(t) == -3),
    ("-Sum(x) <= -5", lambda *t: -sum(t) <= -5),
    ("Sum(x) * 2 == 6", lambda *t: 2 * sum(t) == 6),
    ("2 * Sum(x) == 6", lambda *t: 2 * sum(t) == 6),
    ("Sum(x) * -1 == -3", lambda *t: -sum(t) == -3),
    ("Sum(x[:3]) * x[3] == 4", lambda a, b, c, d: (a + b + c) * d == 4),
    ("Sum(x[:2]) * Sum(x[2:]) == 4", lambda a, b, c, d: (a + b) * (c + d) == 4),
    ("Sum(x[:3]) * (x[3] + 1) == 4", lambda a, b, c, d: (a + b + c) * (d + 1) == 4),
    ("x[3] * Sum(x[:3]) == 4", lambda a, b, c, d: (a + b + c) * d == 4),
    ("Sum(x) // 2 == 1", lambda *t: sum(t) // 2 == 1),
    ("Sum(x) % 2 == 0", lambda *t: sum(t) % 2 == 0),
    ("abs(Sum(x) - 3) <= 1", lambda *t: abs(sum(t) - 3) <= 1),
    ("Sum(x[:2]) - Sum(x[2:]) == 0", lambda a, b, c, d: a + b == c + d),
    ("Sum(x[:2]) + Sum(x[2:]) == 3", lambda *t: sum(t) == 3),
    ("Sum(x[:2]) * 2 + x[2] == 3", lambda a, b, c, d: 2 * (a + b) + c == 3),
    ("x * [1, 2, 3, 4] + 1 == 5", lambda a, b, c, d: a + 2 * b + 3 * c + 4 * d + 1 == 5),
    ("x[:2] * [1, 2] - x[2:] * [1, 1] == 0", lambda a, b, c, d: a + 2 * b == c + d),
    ("Minimum(Sum(x[:2]), Sum(x[2:])) == 1", lambda a, b, c, d: min(a + b, c + d) == 1),
    ("(Sum(x[:2]) == 2) == (x[2] == 1)", lambda a, b, c, d: (a + b == 2) == (c == 1)),
    ("Sum(x) - Sum(x) == 0", lambda *t: True),
    ("Sum(x) - Sum(x) != 0", lambda *t: False),
    ("Sum(x[:2]) - Sum(x[:2]) >= 1", lambda *t: False),
])
def test_sum_in_arithmetic_expressions(run, solver, request, constraint, predicate):
    if constraint.startswith("-Sum(x)"):
        bug_for(request, ("ACE", "CHOCO"), NEG_ORDER)
    elif constraint.startswith("Sum(x[:3]) *") or constraint.startswith("Sum(x[:2]) * Sum"):
        bug_for(request, ("ACE", "CHOCO", "COSOCO"), SUM_TIMES)
    elif constraint.startswith("Sum(x) - Sum(x)") or constraint.startswith("Sum(x[:2]) - Sum(x[:2])"):
        bug_for(request, "ACE", ACE_CANCEL)
        if not constraint.endswith("== 0"):  # the sum being always 0, the constraint is false
            bug_for(request, "COSOCO", COSOCO_CANCEL)
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


# ----------------------------------------------------------------------------------------------- degenerated cases

@pytest.mark.parametrize("constraint, predicate", [
    ("Sum(x[0]) == 1", lambda a: a == 1),
    ("Sum([x[0]]) == 1", lambda a: a == 1),
    ("Sum(x[0] * 3) == 3", lambda a: 3 * a == 3),
    ("Sum(-x[0]) == -1", lambda a: a == 1),
    ("Sum(x[:1] * [2]) <= 2", lambda a: 2 * a <= 2),
    ("Sum(x[0], condition=('eq', 1))", lambda a: a == 1),
    ("Sum([x[0]]) in {1, 2}", lambda a: a in (1, 2)),
    ("Sum(x[0], 2) == 3", lambda a: a == 1),
], ids=["one variable", "one variable in a list", "one variable with a coefficient", "one negated variable", "one variable (scalar product)",
        "one variable with condition", "one variable in a set", "one variable and one integer"])
def test_sum_on_a_single_variable(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: predicate(t[0]) and t[3] != 1)


@bug(ONE_TERM)
def test_xcsp3_sum_has_at_least_two_terms(run):
    # XCSP3-core requires |X| = |C| >= 2
    for constraint in ["Sum(x[0] * 3) == 3", "Sum(-x[0]) == -1", "Sum(x[:1] * [2]) <= 2", "Sum(x[0], condition=('eq', 1))"]:
        r = run(X4 + f"satisfy({constraint})")
        assert r.ok, r.report()
        for c in r.xml.iter("sum"):
            assert len(c.find("list").text.split()) >= 2, constraint + "\n" + r.report()


@pytest.mark.parametrize("constraint, predicate, args", [
    ("Sum(x[0], x[0], x[1]) == 3", lambda a, b, c, d: 2 * a + b == 3, ()),
    ("Sum(x[0], x[0], x[1]) == 3", lambda a, b, c, d: 2 * a + b == 3, ("-group_sum_coeffs",)),
    ("Sum(x[0], x[0]) == 2", lambda a, b, c, d: a == 1, ()),
    ("Sum(x * [1, 2, 3, 4], x[0]) == 5", lambda a, b, c, d: 2 * a + 2 * b + 3 * c + 4 * d == 5, ()),
    ("Sum(x[0], -x[0], x[1]) == 1", lambda a, b, c, d: b == 1, ()),
], ids=["twice", "twice (group_sum_coeffs)", "only twice", "with coefficients", "opposite"])
def test_sum_with_a_repeated_variable(run, solver, constraint, predicate, args):
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate, args=args)


# ---------------------------------------------------------------------------------------------------------- groups

M32 = "m = VarArray(size=[3, 2], dom=range(3))\n"
D32 = [range(3)] * 6


@pytest.mark.parametrize("constraints, predicate", [
    ("[Sum(m[i]) == 2 for i in range(3)]", lambda *t: all(t[2 * i] + t[2 * i + 1] == 2 for i in range(3))),
    ("[Sum(m[i]) == i for i in range(3)]", lambda *t: all(t[2 * i] + t[2 * i + 1] == i for i in range(3))),
    ("[Sum(m[i] * [1, 2]) == 2 for i in range(3)]", lambda *t: all(t[2 * i] + 2 * t[2 * i + 1] == 2 for i in range(3))),
    ("[Sum(m[i] * [1, i + 1]) == 2 for i in range(3)]", lambda *t: all(t[2 * i] + (i + 1) * t[2 * i + 1] == 2 for i in range(3))),
    ("[Sum(m[:, j]) <= 3 for j in range(2)]", lambda *t: all(t[j] + t[2 + j] + t[4 + j] <= 3 for j in range(2))),
])
def test_sum_in_groups(run, solver, constraints, predicate):
    check(run, solver, M32 + f"satisfy({constraints})", D32, predicate)


# ------------------------------------------------------------------------------------------------ logical contexts

@pytest.mark.parametrize("constraint, predicate", [
    ("(Sum(x) == 3) | (x[0] == 1)", lambda *t: sum(t) == 3 or t[0] == 1),
    ("(Sum(x) == 3) & (x[0] == 1)", lambda *t: sum(t) == 3 and t[0] == 1),
    ("~(Sum(x) == 3)", lambda *t: sum(t) != 3),
    ("~(Sum(x) <= 3)", lambda *t: sum(t) > 3),
    ("imply(x[0] == 1, Sum(x) == 3)", lambda *t: t[0] != 1 or sum(t) == 3),
    ("iff(x[0] == 1, Sum(x) == 3)", lambda *t: (t[0] == 1) == (sum(t) == 3)),
    ("xor(x[0] == 0, Sum(x) > 5)", lambda *t: (t[0] == 0) != (sum(t) > 5)),
    ("If(x[0] == 1, Then=Sum(x[1:]) == 2)", lambda *t: t[0] != 1 or sum(t[1:]) == 2),
    ("(Sum(x) in {1, 3}) | (x[0] == 1)", lambda *t: sum(t) in (1, 3) or t[0] == 1),
    ("(Sum(x) not in range(2, 5)) | (x[0] == 1)", lambda *t: not 2 <= sum(t) <= 4 or t[0] == 1),
    ("(Sum(x * [1, 2, 3, 4]) == 5) | (x[0] == 1)", lambda a, b, c, d: a + 2 * b + 3 * c + 4 * d == 5 or a == 1),
    ("(Sum(x[:3]) == x[3]) | (x[0] == 1)", lambda a, b, c, d: a + b + c == d or a == 1),
])
def test_sum_in_logical_expressions(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


# ------------------------------------------------------------------------------------------------------------ objectives

@pytest.mark.parametrize("objective, value, maximize", [
    ("minimize(Sum(x))", lambda *t: sum(t), False),
    ("maximize(Sum(x * [1, 2, 3, 4]))", lambda a, b, c, d: a + 2 * b + 3 * c + 4 * d, True),
    ("maximize(x * [1, -2, 3, -4])", lambda a, b, c, d: a - 2 * b + 3 * c - 4 * d, True),
    ("minimize(Sum(x[:2]) + x[2])", lambda a, b, c, d: a + b + c, False),
    ("minimize(Sum(abs(x[i] - 1) for i in range(4)))", lambda *t: sum(abs(v - 1) for v in t), False),
    ("minimize(Sum(x[i] > 0 for i in range(4)))", lambda *t: sum(v > 0 for v in t), False),
    ("minimize(Sum(x[0]))", lambda *t: t[0], False),
    ("maximize(Sum(x[:2]) - Sum(x[2:]))", lambda a, b, c, d: a + b - c - d, True),
    ("maximize(Sum(x) * 2)", lambda *t: 2 * sum(t), True),
])
def test_sum_in_objectives(run, solver, objective, value, maximize):
    r = run(X4 + f"satisfy(x[0] != x[1], Sum(x) >= 3)\n{objective}", solver=solver)
    assert_optimum(r, brute_force(D4, lambda a, b, c, d: a != b and a + b + c + d >= 3), value, maximize=maximize)


# ------------------------------------------------------------------------------------------------ examples of the doc

def test_sum_example(run, solver):
    # the first example of the documentation (knapsack)
    weights = [4, 3, 5, 2, 6, 3]
    check(run, solver, f"x = VarArray(size=6, dom={{0, 1}})\nsatisfy(Sum(x) == 3, Sum(x * {weights}) <= 10)", [(0, 1)] * 6,
          lambda *t: sum(t) == 3 and sum(w * v for w, v in zip(weights, t)) <= 10)


def test_sum_example_with_expressions(run, solver):
    # the second example of the documentation, with smaller domains
    check(run, solver, "y = VarArray(size=3, dom=range(4))\nz = Var(dom=range(20))\nsatisfy(z == 6, Sum(y[i] * (i + 1) for i in range(3)) == z)",
          [range(4)] * 3 + [range(20)], lambda a, b, c, z: z == 6 and a + 2 * b + 3 * c == z)


# ------------------------------------------------------------------------------------------------------------ -mini

MINI_CASES = [
    ("Sum(x) == 3", lambda a, b, c, d: a + b + c + d == 3),
    ("Sum(x) in {1, 3}", lambda a, b, c, d: a + b + c + d in (1, 3)),
    ("Sum(x) in range(2, 5)", lambda a, b, c, d: 2 <= a + b + c + d <= 4),
    ("Sum(x) not in range(2, 5)", lambda a, b, c, d: not 2 <= a + b + c + d <= 4),
    ("Sum(x) not in {1, 3}", lambda a, b, c, d: a + b + c + d not in (1, 3)),
    ("Sum(x * [1, 2, 3, 4]) == 5", lambda a, b, c, d: a + 2 * b + 3 * c + 4 * d == 5),
    ("Sum(x[i] > 0 for i in range(4)) == 2", lambda *t: sum(v > 0 for v in t) == 2),
    ("Sum(x[0], x[1] + 1, x[2]) == 3", lambda a, b, c, d: a + b + 1 + c == 3),
    ("Sum(x[:3]) == x[3] + 1", lambda a, b, c, d: a + b + c == d + 1),
    ("Sum(x, condition=('in', {1, 3}))", lambda a, b, c, d: a + b + c + d in (1, 3)),
]


@pytest.mark.parametrize("constraint, predicate", MINI_CASES)
def test_sum_with_mini(run, solver, request, constraint, predicate):
    notin_bugs(request, constraint)
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate, args=("-mini",))


@pytest.mark.parametrize("constraint", [pytest.param(c, marks=bug(MINI_SET)) if re.search(r"\) (not )?in |'in'", c) else c for c, _ in MINI_CASES])
def test_xcsp3_sum_with_mini(run, constraint):
    # in the mini-tracks, the list of a sum only contains variables, and its condition is relational with a value or a variable as operand
    r = run(X4 + f"satisfy({constraint})", args=("-mini",))
    assert r.ok, r.report()
    for c in r.xml.iter("sum"):
        assert all(re.fullmatch(r"[\w\[\]\.]+", token) for token in c.find("list").text.split()), r.report()
        assert re.fullmatch(r"\((lt|le|gt|ge|eq|ne),[\w\[\]\-]+\)", c.find("condition").text.strip()), r.report()


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, expected", [
    ("Sum(x) == 3", ("x[]", None, "(eq,3)")),
    ("Sum(x * [1, 2, 3, 4]) <= 5", ("x[]", "1 2 3 4", "(le,5)")),
    ("Sum(x * 2) == 4", ("x[]", "2x4", "(eq,4)")),
    ("Sum(x[:3]) == x[3]", ("x[0..2]", None, "(eq,x[3])")),
    ("Sum(x) in range(2, 5)", ("x[]", None, "(in,2..4)")),
    ("Sum(x) not in {1, 3}", ("x[]", None, "(notin,{1,3})")),
    ("Sum(x[:2]) == Sum(x[2:])", ("x[]", "1 1 -1 -1", "(eq,0)")),
    pytest.param("-Sum(x) == -3", ("x[]", "-1x4", "(eq,-3)"), marks=bug(NEG_ORDER)),
    ("Sum(x[i] > 0 for i in range(4)) == 2", ("gt(x[0],0) gt(x[1],0) gt(x[2],0) gt(x[3],0)", None, "(eq,2)")),
])
def test_xcsp3_sum(run, constraint, expected):
    r = run(X4 + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/sum")
    assert c is not None, r.report()
    assert [e.tag for e in c] == ["list"] + (["coeffs"] if expected[1] is not None else []) + ["condition"], r.report()  # the order of XCSP3
    coeffs = c.find("coeffs")
    got = (" ".join(c.find("list").text.split()), None if coeffs is None else " ".join(coeffs.text.split()), c.find("condition").text.strip())
    assert got == expected, r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("constraint", [
    pytest.param("Sum(x)", marks=bug(INVALID)),
    "Sum(x) == 2.5",
    "Sum(x) == 'a'",
    "Sum(x) == None",
    pytest.param("Sum(x) == True", marks=bug(INVALID)),
    "Sum(x, condition=('le',))",
    pytest.param("Sum(x, condition=('foo', 3))", marks=bug(INVALID)),
    "Sum(x, condition='(le,3)')",
    pytest.param("Sum(x, condition=('le', 'a'))", marks=bug(INVALID)),
    "Sum(x, 'a') == 0",
    "Sum(x, 1.5) == 0",
    "Sum(x, True) == 0",
    "Sum() == 0",
    "Sum(x * [1, 2]) == 5",
    "Sum(x * [1, 2, 3, 4, 5]) == 5",
    pytest.param("Sum(x * ['a', 'b', 'c', 'd']) == 5", marks=bug(INVALID)),
    "Sum(x * [1.5, 2, 3, 4]) == 5",
    pytest.param("Sum(s) == 1", marks=bug(INVALID)),
])
def test_invalid_sum(run, constraint):
    assert_fails(run(X4 + "s = VarArray(size=2, dom={'a', 'b'})\n" + f"satisfy({constraint})"))
