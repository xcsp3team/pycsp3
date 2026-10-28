"""
Tests of the constants of PyCSP3 (ConstraintDummyConstant): the value of a component that does not depend on any variable, as Maximum() and
Minimum() of integers, Sum() and Count() of no term, or NValues() of one term, used in expressions with integers.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
"""

import pytest

from harness import assert_solutions, brute_force, declared_variables

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
    ("c + 1", 4), ("1 + c", 4), ("c - 1", 2), ("1 - c", -2), ("c * 2", 6), ("2 * c", 6),
    ("c // 2", 1), ("7 // c", 2), ("c % 2", 1), ("7 % c", 1), ("c + c", 6), ("c * 2 - 1", 5),
])
def test_constant_with_an_integer_compared_with_an_integer(run, solver, expression, value):
    # the result is a constant, and not an integer of Python (the comparison is not evaluated by Python as a Boolean)
    r = run(CV + f"satisfy(({expression} == {value}) | (v == 0), ({expression} == {value + 1}) | (v == 1))", solver=solver)
    assert_solutions(r, brute_force(DV, lambda v: v == 1))


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


@pytest.mark.parametrize("constraint, predicate", [
    ("AllDifferent(c, v)", lambda *t: t[3] != 3),
    ("AllDifferent([c, v])", lambda *t: t[3] != 3),
    ("Count(x, value=c) == 1", lambda *t: t[:3].count(3) == 1),
    ("Count(x, values=[c, 0]) == 1", lambda *t: sum(1 for w in t[:3] if w in (0, 3)) == 1),
    ("Exist(x, value=c)", lambda *t: 3 in t[:3]),
    ("Sum([c, v]) == 5", lambda *t: t[3] == 2),
    ("Sum(x, condition=(\"eq\", c))", lambda *t: sum(t[:3]) == 3),
    ("Sum(x[k] for k in range(c - 1)) == c", lambda *t: t[0] + t[1] == 3),
    ("Maximum(c, v) == 4", lambda *t: t[3] == 4),
    ("Minimum(x[0], c) == v", lambda *t: min(t[0], 3) == t[3]),
    ("NValues(c, v) == 1", lambda *t: t[3] == 3),
])
def test_constant_in_global_constraints(run, solver, constraint, predicate):
    # the constant is given as an argument of the function of a global constraint, which receives its value (t[:3] for x, t[3] for v)
    r = run(f"c = Maximum(3, 1)\nx = VarArray(size=3, dom=range(4))\nv = Var(dom=range(5))\nsatisfy({constraint})", solver=solver)
    assert_solutions(r, brute_force([range(4)] * 3 + [range(5)], predicate))


def test_constant_in_global_constraints_with_comments(run):
    # the comments of the model are kept for the functions of global constraints, whose arguments are checked by a decorator
    r = run("c = Maximum(3, 1)\nx = VarArray(size=3, dom=range(4))\nsatisfy(\n    # all different\n    AllDifferent(x),\n"
            "    # sum\n    Sum(x) > c\n)")
    assert r.ok, r.report()
    assert r.xml.find(".//allDifferent").get("note") == "all different", r.report()
    assert r.xml.find(".//sum").get("note") == "sum", r.report()


@pytest.mark.parametrize("constraint, predicate", [
    ("v in [c, 4]", lambda *t: t[3] in (3, 4)),
    ("v not in [c, 4]", lambda *t: t[3] not in (3, 4)),
    ("v + 1 in [c, 4]", lambda *t: t[3] + 1 in (3, 4)),
    ("v in L", lambda *t: t[3] in (3, 4)),
    ("Sum(x) in [c, 4]", lambda *t: sum(t[:3]) in (3, 4)),
    ("Sum(x) in L", lambda *t: sum(t[:3]) in (3, 4)),
    ("c in x", lambda *t: 3 in t[:3]),
    ("c not in x", lambda *t: 3 not in t[:3]),
    ("(c in [1, 3]) | (v == 0)", lambda *t: True),
    ("(c in cp_array([1, 2])) | (v == 0)", lambda *t: t[3] == 0),
])
def test_constant_in_memberships(run, solver, constraint, predicate):
    # the constant is the value searched for, or among the values (t[:3] for x, t[3] for v); v != 4 is posted too, so that the model has a
    # constraint (and is solved) when the membership is always true
    r = run(f"c = Maximum(3, 1)\nx = VarArray(size=3, dom=range(4))\nv = Var(dom=range(5))\nL = [c, 4]\nsatisfy(v != 4, {constraint})", solver=solver)
    assert_solutions(r, brute_force([range(4)] * 3 + [range(5)], lambda *t: t[3] != 4 and predicate(*t)))


def mjk(t, j, k):
    """The value of m[j][k] in a tuple whose first six values are the ones of m."""
    return t[3 * j + k]


MI = ((1, 2, 3), (4, 5, 6))


@pytest.mark.parametrize("constraint, predicate", [
    ("m[j][c] == v", lambda *t: mjk(t, t[6], 1) == t[8]),
    ("m[j][c - 1] == v", lambda *t: mjk(t, t[6], 0) == t[8]),
    ("mi[j][c] == v", lambda *t: MI[t[6]][1] == t[8]),
    ("m[c, k] == v", lambda *t: mjk(t, 1, t[7]) == t[8]),
    ("m[j, c] == v", lambda *t: mjk(t, t[6], 1) == t[8]),
    ("m[c, 1] == v", lambda *t: mjk(t, 1, 1) == t[8]),
    ("m[c, c] == v", lambda *t: mjk(t, 1, 1) == t[8]),
    ("mi[c, k] == v", lambda *t: MI[1][t[7]] == t[8]),
    ("mi[j, c] == v", lambda *t: MI[t[6]][1] == t[8]),
])
def test_constant_as_an_index_of_a_matrix(run, solver, constraint, predicate):
    # the constant c is 1, as the index of a row or of a column, without any auxiliary variable (t[:6] for m, t[6] for j, t[7] for k, t[8] for v)
    r = run("c = Maximum(1, 0)\nm = VarArray(size=[2, 3], dom=range(2))\nmi = cp_array([[1, 2, 3], [4, 5, 6]])\nj = Var(dom=range(2))\n"
            f"k = Var(dom=range(3))\nv = Var(dom=range(7))\nsatisfy({constraint})", solver=solver)
    assert_solutions(r, brute_force([range(2)] * 6 + [range(2), range(3), range(7)], predicate))
    assert not any(name.startswith("aux") for name in declared_variables(r)), r.report()

