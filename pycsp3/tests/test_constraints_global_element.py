"""
Tests of the constraint Element of the section Constraints (Global) of the API (https://pycsp.org/documentation/api/constraints-global/#Element):
expressions of the form c[i] (a list of integers indexed by a variable) and m[j][k] (a matrix of integers indexed by two variables), when all the
integers are identical, with conditions, in logical expressions, as terms of other constraints and in objectives; the constraint Element
without index (member), written v in [...] with a list of variables (and possibly integers); and an index (variable or expression) that can take
a value outside the indexes of the list, which is an error, unless -force_element_index is given (the index is then restricted to the list).

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
According to XCSP3-core, element(X, i, (op, k)) holds iff X[i] op k, the first index being 0; when all the integers of X are equal to the same
integer c, and i can only take indexes of X, element(X, i, (op, k)) holds iff c op k.
"""

import pytest

from harness import assert_optimum, assert_solutions, brute_force, bug, bug_for

# Known bugs of PyCSP3
OUTSIDE = ("#282: an index that can take a value outside the list is neither an error nor restricted with -force_element_index for a list of "
           "identical integers and a matrix of identical rows, and is restricted without error for an expression as index of a matrix "
           "(m[j][k + 1], m[j, k + 1], m[j + 1, k])")

# Known bugs of the solvers
EMPTY_SUPPORTS = ("(to be reported) ACE and CHOCO fail on a table with an empty set of supports, recognized as false by the parser "
                  "(buildCtrFalse(): RuntimeException: Constraint with only conflicts)")

# a list of identical integers c, an index i and a variable v (in the predicates: t[0] for i, t[1] for v)
C3 = "c = cp_array([2, 2, 2])\ni = Var(dom=range(3))\nv = Var(dom=range(5))\n"
DC = [range(3), range(5)]


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


# the constraints always false (a table with an empty set of supports is posted)
ALWAYS_FALSE = ("c[i] == 3", "c[i] != 2", "c[i] not in {1, 2}", "~(c[i] == 2)", "m[j, k] == 3")


def check_with_v(run, solver, request, code, constraint, domains, predicate, iv):
    # v != 4 is posted too, so that the model has a constraint (and is solved) when the constraint is always true (t[iv] for v)
    if constraint in ALWAYS_FALSE:
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)
    check(run, solver, code + f"satisfy(v != 4, {constraint})", domains, lambda *t: t[iv] != 4 and predicate(*t))


@pytest.mark.parametrize("constraint, predicate", [
    ("c[i] == v", lambda *t: t[1] == 2),
    ("c[i] != v", lambda *t: t[1] != 2),
    ("c[i] < v", lambda *t: 2 < t[1]),
    ("c[i] + v == 5", lambda *t: t[1] == 3),
    ("-c[i] + v == 0", lambda *t: t[1] == 2),
    ("c[i] == 2", lambda *t: True),
    ("c[i] == 3", lambda *t: False),
    ("c[i] != 2", lambda *t: False),
    ("c[i] < 3", lambda *t: True),
    ("c[i] in {1, 2}", lambda *t: True),
    ("c[i] not in {1, 2}", lambda *t: False),
])
def test_element_on_identical_integers(run, solver, request, constraint, predicate):
    check_with_v(run, solver, request, C3, constraint, DC, predicate, 1)


@pytest.mark.parametrize("constraint, predicate", [
    ("(c[i] == v) | (v == 0)", lambda *t: t[1] in (0, 2)),
    ("(c[i] == 2) | (v == 1)", lambda *t: True),
    ("(c[i] == 3) | (v == 1)", lambda *t: t[1] == 1),
    ("~(c[i] == 2)", lambda *t: False),
    ("If(v == 1, Then=c[i] == 3)", lambda *t: t[1] != 1),
])
def test_element_on_identical_integers_in_logical_expressions(run, solver, request, constraint, predicate):
    check_with_v(run, solver, request, C3, constraint, DC, predicate, 1)


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
    ("[[2, 2, 2], [2, 2, 2]]", "m[j][k] == 2", lambda *t: True),
    ("[[2, 2, 2], [2, 2, 2]]", "m[j, k] == 3", lambda *t: False),
    ("[[1, 2, 3], [1, 2, 3]]", "m[j][k] == v", lambda *t: t[2] == t[1] + 1),  # identical rows, whose integers are different
])
def test_element_on_a_matrix_of_identical_integers(run, solver, request, matrix, constraint, predicate):
    check_with_v(run, solver, request, f"m = cp_array({matrix})\n" + JKV, constraint, DM, predicate, 2)


def test_element_on_a_list_of_one_integer(run, solver, request):
    check_with_v(run, solver, request, "c = cp_array([2])\nk = Var(dom={0})\nv = Var(dom=range(5))\n", "c[k] == 2", [[0], range(5)], lambda *t: True, 1)


@pytest.mark.parametrize("objective, function", [
    ("minimize(c[i])", lambda *t: 2),
    ("minimize(c[i] + v)", lambda *t: 2 + t[1]),
])
def test_element_on_identical_integers_as_objective(run, solver, objective, function):
    # c[i] is the constant 2: the optimum is 2, or there is nothing to optimize (as for the other constants of PyCSP3, #221)
    r = run(C3 + "satisfy(v != 0)\n" + objective, solver=solver)
    if "there is nothing to optimize" in r.stdout:
        assert "The objective is the constant 2: there is nothing to optimize" in r.stdout, r.report()
    else:
        assert_optimum(r, brute_force(DC, lambda *t: t[1] != 0), function)


@pytest.mark.parametrize("constraint, predicate", [
    ("v in [x[0], x[1]]", lambda *t: t[3] in t[:2]),
    ("v in [x[0], 2]", lambda *t: t[3] in (t[0], 2)),
    ("v not in [x[0], 2]", lambda *t: t[3] not in (t[0], 2)),
    ("v + 1 in [x[0], 2]", lambda *t: t[3] + 1 in (t[0], 2)),
    ("v in L", lambda *t: t[3] in (t[0], 2)),
    ("v in [x[0], x[1], x[2], 4]", lambda *t: t[3] in t[:3] + (4,)),
])
def test_element_member_of_a_list_written_literally(run, solver, constraint, predicate):
    # Python changes into a tuple a list given literally on the right of 'in' (t[:3] for x, t[3] for v)
    check(run, solver, f"x = VarArray(size=3, dom=range(4))\nv = Var(dom=range(5))\nL = [x[0], 2]\nsatisfy({constraint})", [range(4)] * 3 + [range(5)],
          predicate)


# the lists and the matrices, with an index (variable or expression) that can take a value outside the indexes
X3 = "x = VarArray(size=3, dom=range(3))\n"
M23 = "m = VarArray(size=[2, 3], dom=range(2))\n"
M22 = "m = VarArray(size=[2, 2], dom=range(2))\n"
T23 = "t = cp_array([[1, 2, 0], [1, 2, 0]])\nj = Var(dom=range(3))\nk = Var(dom=range(3))\nv = Var(dom=range(3))\n"


@pytest.mark.parametrize("code", [
    X3 + "i = Var(dom=range(4))\nsatisfy(x[i] == 2)",
    X3 + "i = Var(dom={-1, 2})\nsatisfy(x[i] == 2)",
    X3 + "j = Var(dom=range(3))\nsatisfy(x[j + 1] == 2)",
    X3 + "j = Var(dom=range(3))\nsatisfy(x[j - 1] == 2)",
    X3 + "j = Var(dom=range(3))\nsatisfy(x[abs(j - 3)] == 2)",
    "x = VarArray(size=3, dom=range(4))\nsatisfy(x[x[0]] == 2)",
    "t = cp_array([3, 0, 2])\ni = Var(dom=range(4))\nv = Var(dom=range(4))\nsatisfy(t[i] == v)",
    pytest.param("c = cp_array([2, 2, 2])\ni = Var(dom=range(4))\nv = Var(dom=range(4))\nsatisfy(c[i] == v)", marks=bug(OUTSIDE)),
    M23 + "j = Var(dom=range(3))\nk = Var(dom=range(3))\nsatisfy(m[j][k] == 1)",
    M23 + "j = Var(dom=range(2))\nk = Var(dom=range(4))\nsatisfy(m[j][k] == 1)",
    M23 + "j = Var(dom=range(2))\nk = Var(dom=range(3))\nsatisfy(m[j + 1][k] == 1)",
    pytest.param(M23 + "j = Var(dom=range(2))\nk = Var(dom=range(3))\nsatisfy(m[j + 1, k] == 1)", marks=bug(OUTSIDE)),
    pytest.param(M23 + "j = Var(dom=range(2))\nk = Var(dom=range(3))\nsatisfy(m[j][k + 1] == 1)", marks=bug(OUTSIDE)),
    pytest.param(M23 + "j = Var(dom=range(2))\nk = Var(dom=range(3))\nsatisfy(m[j, k + 1] == 1)", marks=bug(OUTSIDE)),
    pytest.param(T23 + "satisfy(t[j][k] == v)", marks=bug(OUTSIDE)),
    pytest.param(T23 + "satisfy(t[j, k] == v)", marks=bug(OUTSIDE)),
])
def test_element_with_an_index_outside_the_list(run, code):
    # an index that can take a value outside the indexes of the list is an error, unless -force_element_index is given
    r = run(code)
    assert not r.ok and "-force_element_index" in r.stdout, r.report()


@pytest.mark.parametrize("code, domains, predicate", [
    (X3 + "i = Var(dom=range(5))\nsatisfy(x[i] == 2)", [range(3)] * 3 + [range(5)], lambda *t: t[3] < 3 and t[t[3]] == 2),
    (X3 + "i = Var(dom={-1, 2})\nsatisfy(x[i] == 2)", [range(3)] * 3 + [[-1, 2]], lambda *t: t[3] == 2 and t[2] == 2),
    (X3 + "j = Var(dom=range(3))\nsatisfy(x[j + 1] == 2)", [range(3)] * 4, lambda *t: t[3] < 2 and t[t[3] + 1] == 2),
    (X3 + "j = Var(dom=range(3))\nsatisfy(x[j - 1] == 2)", [range(3)] * 4, lambda *t: t[3] > 0 and t[t[3] - 1] == 2),
    ("t = cp_array([3, 0, 2])\ni = Var(dom=range(4))\nv = Var(dom=range(4))\nsatisfy(t[i] == v)", [range(4)] * 2, lambda i, v: i < 3 and (3, 0, 2)[i] == v),
    pytest.param("c = cp_array([2, 2, 2])\ni = Var(dom=range(4))\nv = Var(dom=range(4))\nsatisfy(c[i] == v)", [range(4)] * 2, lambda i, v: i < 3 and v == 2,
                 marks=bug(OUTSIDE)),
    (M22 + "j = Var(dom=range(3))\nk = Var(dom=range(2))\nsatisfy(m[j][k] == 1)", [range(2)] * 4 + [range(3), range(2)],
     lambda *t: t[4] < 2 and t[2 * t[4] + t[5]] == 1),
    (M22 + "j = Var(dom=range(2))\nk = Var(dom=range(2))\nsatisfy(m[j + 1][k] == 1)", [range(2)] * 6, lambda *t: t[4] < 1 and t[2 * (t[4] + 1) + t[5]] == 1),
    (M22 + "j = Var(dom=range(2))\nk = Var(dom=range(2))\nsatisfy(m[j][k + 1] == 1)", [range(2)] * 6, lambda *t: t[5] < 1 and t[2 * t[4] + t[5] + 1] == 1),
    (M22 + "j = Var(dom=range(2))\nk = Var(dom=range(2))\nsatisfy(m[j, k + 1] == 1)", [range(2)] * 6, lambda *t: t[5] < 1 and t[2 * t[4] + t[5] + 1] == 1),
    pytest.param("t = cp_array([[1, 2], [1, 2]])\nj = Var(dom=range(3))\nk = Var(dom=range(2))\nv = Var(dom=range(3))\nsatisfy(t[j][k] == v)",
     [range(3), range(2), range(3)], lambda j, k, v: j < 2 and (1, 2)[k] == v, marks=bug(OUTSIDE)),
    pytest.param("t = cp_array([[1, 2], [1, 2]])\nj = Var(dom=range(3))\nk = Var(dom=range(2))\nv = Var(dom=range(3))\nsatisfy(t[j, k] == v)",
     [range(3), range(2), range(3)], lambda j, k, v: j < 2 and (1, 2)[k] == v, marks=bug(OUTSIDE)),
])
def test_element_with_an_index_outside_the_list_and_the_option(run, solver, code, domains, predicate):
    # with -force_element_index, the index cannot take a value outside the indexes of the list
    check(run, solver, code, domains, predicate, args=("-force_element_index",))
