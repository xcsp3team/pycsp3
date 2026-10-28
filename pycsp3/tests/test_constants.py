"""
Tests of the constants of PyCSP3 (ConstraintDummyConstant): the value of a component that does not depend on any variable, as Maximum() and
Minimum() of integers, Sum() and Count() of no term, or NValues() of one term, used in expressions with integers.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
"""

import pytest

from harness import assert_solutions, brute_force

# a constant c whose value is 3, and a variable v (in the predicates: v)
CV = "c = Maximum(3, 1)\nv = Var(dom=range(-10, 11))\n"
DV = [range(-10, 11)]


@pytest.mark.parametrize("expression, value", [
    ("c + 1", 4), ("1 + c", 4), ("c - 1", 2), ("1 - c", -2), ("c * 2", 6), ("2 * c", 6),
    ("c // 2", 1), ("7 // c", 2), ("c % 2", 1), ("7 % c", 1), ("-7 % c", 2),
])
def test_constant_with_an_integer(run, solver, expression, value):
    r = run(CV + f"satisfy(v == {expression})", solver=solver)
    assert_solutions(r, brute_force(DV, lambda v: v == value))


@pytest.mark.parametrize("expression, value", [
    ("-c", -3), ("+c", 3), ("abs(Minimum(-3, 1))", 3), ("abs(-c)", 3), ("-c + 5", 2),
])
def test_constant_with_a_unary_operator(run, solver, expression, value):
    r = run(CV + f"satisfy(v == {expression})", solver=solver)
    assert_solutions(r, brute_force(DV, lambda v: v == value))


@pytest.mark.parametrize("constraint, predicate", [
    ("x[c] == 1", lambda *t: t[3] == 1),
    ("Sum(x[:c]) == 1", lambda *t: sum(t[:3]) == 1),
    ("Sum(x) in range(c)", lambda *t: sum(t) < 3),
    ("Sum(x) == [5, 6, 7, 2][c]", lambda *t: sum(t) == 2),
])
def test_constant_as_an_index(run, solver, constraint, predicate):
    r = run(f"c = Maximum(3, 1)\nx = VarArray(size=4, dom=range(2))\nsatisfy({constraint})", solver=solver)
    assert_solutions(r, brute_force([range(2)] * 4, predicate))
