"""
Tests of the constraint Element of the section Constraints (Global) of the API (https://pycsp.org/documentation/api/constraints-global/#Element):
expressions of the form c[i] (a list of integers indexed by a variable) and m[j][k] (a matrix of integers indexed by two variables), when all the
integers are identical, with conditions, in logical expressions, as terms of other constraints and in objectives.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
According to XCSP3-core, element(X, i, (op, k)) holds iff X[i] op k, the first index being 0; when all the integers of X are equal to the same
integer c, and i can only take indexes of X, element(X, i, (op, k)) holds iff c op k.
"""

import pytest

from harness import assert_optimum, assert_solutions, brute_force, bug

# Known bugs (each bug is reported in the issue given at the start of its reason)
IDENTICAL = ("#281: a list of identical integers indexed by a variable is replaced by this integer, so that c[i] == 2 (two integers "
             "compared by Python) fails, and c[i] cannot be an objective")

# a list of identical integers c, an index i and a variable v (in the predicates: t[0] for i, t[1] for v)
C3 = "c = cp_array([2, 2, 2])\ni = Var(dom=range(3))\nv = Var(dom=range(5))\n"
DC = [range(3), range(5)]


def check(run, solver, code, domains, predicate):
    r = run(code, solver=solver)
    assert_solutions(r, brute_force(domains, predicate))
    return r


@pytest.mark.parametrize("constraint, predicate", [
    ("c[i] == v", lambda *t: t[1] == 2),
    ("c[i] != v", lambda *t: t[1] != 2),
    ("c[i] < v", lambda *t: 2 < t[1]),
    ("c[i] + v == 5", lambda *t: t[1] == 3),
    ("-c[i] + v == 0", lambda *t: t[1] == 2),
    pytest.param("c[i] == 2", lambda *t: True, marks=bug(IDENTICAL)),
    pytest.param("c[i] == 3", lambda *t: False, marks=bug(IDENTICAL)),
    pytest.param("c[i] != 2", lambda *t: False, marks=bug(IDENTICAL)),
    pytest.param("c[i] < 3", lambda *t: True, marks=bug(IDENTICAL)),
    pytest.param("c[i] in {1, 2}", lambda *t: True, marks=bug(IDENTICAL)),
    pytest.param("c[i] not in {1, 2}", lambda *t: False, marks=bug(IDENTICAL)),
])
def test_element_on_identical_integers(run, solver, constraint, predicate):
    check(run, solver, C3 + f"satisfy({constraint})", DC, predicate)


@pytest.mark.parametrize("constraint, predicate", [
    ("(c[i] == v) | (v == 0)", lambda *t: t[1] in (0, 2)),
    pytest.param("(c[i] == 2) | (v == 1)", lambda *t: True, marks=bug(IDENTICAL)),
    ("(c[i] == 3) | (v == 1)", lambda *t: t[1] == 1),
    pytest.param("~(c[i] == 2)", lambda *t: False, marks=bug(IDENTICAL)),
    pytest.param("If(v == 1, Then=c[i] == 3)", lambda *t: t[1] != 1, marks=bug(IDENTICAL)),
])
def test_element_on_identical_integers_in_logical_expressions(run, solver, constraint, predicate):
    check(run, solver, C3 + f"satisfy({constraint})", DC, predicate)


@pytest.mark.parametrize("constraint, predicate", [
    ("x[c[i]] == 1", lambda *t: t[4] == 1),
    ("c[i] in x", lambda *t: 2 in t[2:]),
    ("v in [c[i], 4]", lambda *t: t[1] in (2, 4)),
    ("AllDifferent(c[i], v)", lambda *t: t[1] != 2),
    ("Count(x, value=c[i]) == 1", lambda *t: t[2:].count(2) == 1),
    ("Sum([c[i], v]) == 4", lambda *t: t[1] == 2),
    ("Sum(x) == c[i]", lambda *t: sum(t[2:]) == 2),
])
def test_element_on_identical_integers_as_a_term(run, solver, constraint, predicate):
    # the element is used as an integer: index of another list, value of a member, term of a global constraint (t[2:] for x)
    check(run, solver, C3 + f"x = VarArray(size=3, dom=range(3))\nsatisfy({constraint})", DC + [range(3)] * 3, predicate)


# an index j of rows, an index k of columns and a variable v (in the predicates: t[0] for j, t[1] for k, t[2] for v)
JKV = "j = Var(dom=range(2))\nk = Var(dom=range(3))\nv = Var(dom=range(5))\n"
DM = [range(2), range(3), range(5)]


@pytest.mark.parametrize("matrix, constraint, predicate", [
    ("[[2, 2, 2], [2, 2, 2]]", "m[j][k] == v", lambda *t: t[2] == 2),
    pytest.param("[[2, 2, 2], [2, 2, 2]]", "m[j][k] == 2", lambda *t: True, marks=bug(IDENTICAL)),
    pytest.param("[[2, 2, 2], [2, 2, 2]]", "m[j, k] == 3", lambda *t: False, marks=bug(IDENTICAL)),
    ("[[1, 2, 3], [1, 2, 3]]", "m[j][k] == v", lambda *t: t[2] == t[1] + 1),  # identical rows, whose integers are different
])
def test_element_on_a_matrix_of_identical_integers(run, solver, matrix, constraint, predicate):
    check(run, solver, f"m = cp_array({matrix})\n" + JKV + f"satisfy({constraint})", DM, predicate)


@bug(IDENTICAL)
def test_element_on_a_list_of_one_integer(run, solver):
    check(run, solver, "c = cp_array([2])\nk = Var(dom={0})\nv = Var(dom=range(5))\nsatisfy(c[k] == 2)", [[0], range(5)], lambda *t: True)


@pytest.mark.parametrize("objective, function", [
    pytest.param("minimize(c[i])", lambda *t: 2, marks=bug(IDENTICAL)),
    ("minimize(c[i] + v)", lambda *t: 2 + t[1]),
])
def test_element_on_identical_integers_as_objective(run, solver, objective, function):
    # c[i] is the constant 2: the optimum is 2, or there is nothing to optimize (as for the other constants of PyCSP3, #221)
    r = run(C3 + "satisfy(v != 0)\n" + objective, solver=solver)
    if "there is nothing to optimize" in r.stdout:
        assert "The objective is the constant 2: there is nothing to optimize" in r.stdout, r.report()
    else:
        assert_optimum(r, brute_force(DC, lambda *t: t[1] != 0), function)
