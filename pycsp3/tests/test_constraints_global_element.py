"""
Tests of the constraint Element of the section Constraints (Global) of the API (https://pycsp.org/documentation/api/constraints-global/#Element):
expressions of the form c[i] (a list of integers indexed by a variable) and m[j][k] (a matrix of integers indexed by two variables), when all the
integers are identical, with conditions, in logical expressions, as terms of other constraints and in objectives; the constraint Element
without index (member), written v in [...] with a list of variables (and possibly integers); and an index (variable or expression) that can take
a value outside the indexes of the list, which is restricted to the indexes of the list, with a warning unless -force_element_index is given.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
According to XCSP3-core, element(X, i, (op, k)) holds iff X[i] op k, the first index being 0; when all the integers of X are equal to the same
integer c, and i can only take indexes of X, element(X, i, (op, k)) holds iff c op k.
"""

import pytest

from harness import assert_optimum, assert_solutions, brute_force, bug_for

# Known bugs of PyCSP3
INT_CONDITION = ("#294: an element on a list of integers compared with an integer has an integer as operand of its condition, which XCSP3-core "
                 "does not allow, and ACE does not handle (unimplemented case for element)")

# Known bugs of the solvers
CHOCO_MATRIX = ("CHOCO 4.10.15-beta (embedded in PyCSP3) misses solutions of element on a matrix of variables, except with (eq,k) and (ne,k), "
                "fixed in CHOCO 6.0.2 (not reported)")
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


def check_with_v(run, solver, request, code, constraint, domains, predicate, iv, args=(), empty_supports=True):
    # v != 4 is posted too, so that the model has a constraint (and is solved) when the constraint is always true (t[iv] for v); a constraint
    # always false gives a table with an empty set of supports, unless the index can be outside the list (the constant is then an auxiliary variable)
    if empty_supports and constraint in ALWAYS_FALSE:
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)
    check(run, solver, code + f"satisfy(v != 4, {constraint})", domains, lambda *t: t[iv] != 4 and predicate(*t), args)


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
WARNING_OUTSIDE = "of an element can take values outside the indexes"
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
    "c = cp_array([2, 2, 2])\ni = Var(dom=range(4))\nv = Var(dom=range(4))\nsatisfy(c[i] == v)",
    M23 + "j = Var(dom=range(3))\nk = Var(dom=range(3))\nsatisfy(m[j][k] == 1)",
    M23 + "j = Var(dom=range(2))\nk = Var(dom=range(4))\nsatisfy(m[j][k] == 1)",
    M23 + "j = Var(dom=range(2))\nk = Var(dom=range(3))\nsatisfy(m[j + 1][k] == 1)",
    M23 + "j = Var(dom=range(2))\nk = Var(dom=range(3))\nsatisfy(m[j + 1, k] == 1)",
    M23 + "j = Var(dom=range(2))\nk = Var(dom=range(3))\nsatisfy(m[j][k + 1] == 1)",
    M23 + "j = Var(dom=range(2))\nk = Var(dom=range(3))\nsatisfy(m[j, k + 1] == 1)",
    T23 + "satisfy(t[j][k] == v)",
    T23 + "satisfy(t[j, k] == v)",
])
@pytest.mark.parametrize("args", [(), ("-force_element_index",)], ids=["warning", "option"])
def test_element_with_an_index_outside_the_list(run, code, args):
    # an index that can take a value outside the indexes of the list is restricted to the list, with a warning unless -force_element_index is given
    r = run(code, args=args)
    assert r.ok and (WARNING_OUTSIDE in r.stdout) == (len(args) == 0), r.report()


@pytest.mark.parametrize("code, domains, predicate", [
    (X3 + "i = Var(dom=range(5))\nsatisfy(x[i] == 2)", [range(3)] * 3 + [range(5)], lambda *t: t[3] < 3 and t[t[3]] == 2),
    (X3 + "i = Var(dom={-1, 2})\nsatisfy(x[i] == 2)", [range(3)] * 3 + [[-1, 2]], lambda *t: t[3] == 2 and t[2] == 2),
    (X3 + "j = Var(dom=range(3))\nsatisfy(x[j + 1] == 2)", [range(3)] * 4, lambda *t: t[3] < 2 and t[t[3] + 1] == 2),
    (X3 + "j = Var(dom=range(3))\nsatisfy(x[j - 1] == 2)", [range(3)] * 4, lambda *t: t[3] > 0 and t[t[3] - 1] == 2),
    ("t = cp_array([3, 0, 2])\ni = Var(dom=range(4))\nv = Var(dom=range(4))\nsatisfy(t[i] == v)", [range(4)] * 2, lambda i, v: i < 3 and (3, 0, 2)[i] == v),
    ("c = cp_array([2, 2, 2])\ni = Var(dom=range(4))\nv = Var(dom=range(4))\nsatisfy(c[i] == v)", [range(4)] * 2, lambda i, v: i < 3 and v == 2),
    (M22 + "j = Var(dom=range(3))\nk = Var(dom=range(2))\nsatisfy(m[j][k] == 1)", [range(2)] * 4 + [range(3), range(2)],
     lambda *t: t[4] < 2 and t[2 * t[4] + t[5]] == 1),
    (M22 + "j = Var(dom=range(2))\nk = Var(dom=range(2))\nsatisfy(m[j + 1][k] == 1)", [range(2)] * 6, lambda *t: t[4] < 1 and t[2 * (t[4] + 1) + t[5]] == 1),
    (M22 + "j = Var(dom=range(2))\nk = Var(dom=range(2))\nsatisfy(m[j][k + 1] == 1)", [range(2)] * 6, lambda *t: t[5] < 1 and t[2 * t[4] + t[5] + 1] == 1),
    (M22 + "j = Var(dom=range(2))\nk = Var(dom=range(2))\nsatisfy(m[j, k + 1] == 1)", [range(2)] * 6, lambda *t: t[5] < 1 and t[2 * t[4] + t[5] + 1] == 1),
    ("t = cp_array([[1, 2], [1, 2]])\nj = Var(dom=range(3))\nk = Var(dom=range(2))\nv = Var(dom=range(3))\nsatisfy(t[j][k] == v)",
     [range(3), range(2), range(3)], lambda j, k, v: j < 2 and (1, 2)[k] == v),
    ("t = cp_array([[1, 2], [1, 2]])\nj = Var(dom=range(3))\nk = Var(dom=range(2))\nv = Var(dom=range(3))\nsatisfy(t[j, k] == v)",
     [range(3), range(2), range(3)], lambda j, k, v: j < 2 and (1, 2)[k] == v),
])
@pytest.mark.parametrize("args", [(), ("-force_element_index",)], ids=["warning", "option"])
def test_element_with_an_index_outside_the_list_restricted(run, solver, code, domains, predicate, args):
    # the index cannot take a value outside the indexes of the list, with or without -force_element_index
    check(run, solver, code, domains, predicate, args=args)


# a list of identical integers c and an index i that can take the value 3, outside the list (in the predicates: t[0] for i, t[1] for v, t[2:] for x)
C3_OUTSIDE = "c = cp_array([2, 2, 2])\ni = Var(dom=range(4))\nv = Var(dom=range(5))\nx = VarArray(size=3, dom=range(3))\n"
DC_OUTSIDE = [range(4), range(5)] + [range(3)] * 3
# a matrix of identical integers m and a matrix of identical rows t, with an index j of rows that can take the value 2, outside the matrix
M_OUTSIDE = "m = cp_array([[2, 2, 2], [2, 2, 2]])\nt = cp_array([[1, 2, 3], [1, 2, 3]])\nj = Var(dom=range(3))\nk = Var(dom=range(3))\nv = Var(dom=range(5))\n"
DM_OUTSIDE = [range(3), range(3), range(5)]


@pytest.mark.parametrize("code", [
    pytest.param(C3_OUTSIDE + f"satisfy({constraint})", id=constraint) for constraint in [
        "c[i] == 2", "c[i] == 3", "c[i] != 2", "c[i] < 3", "c[i] in {1, 2}", "c[i] not in {1, 2}", "c[i] + v == 5",
        "(c[i] == v) | (v == 0)", "(c[i] == 2) | (v == 1)", "(c[i] == 3) | (v == 1)", "~(c[i] == 2)", "If(v == 1, Then=c[i] == 3)",
        "x[c[i]] == 1", "c[i] in x", "v in [c[i], 4]", "AllDifferent(c[i], v)", "Count(x, value=c[i]) == 1", "Sum([c[i], v]) == 4", "Sum(x) == c[i]"]
] + [
    pytest.param(C3_OUTSIDE + f"satisfy(v != 0)\n{objective}", id=objective) for objective in ["minimize(c[i])", "minimize(c[i] + v)"]
] + [
    pytest.param(M_OUTSIDE + f"satisfy({constraint})", id=constraint) for constraint in [
        "m[j][k] == v", "m[j][k] == 2", "m[j, k] == 3", "t[j][k] == v", "t[j][k] == 1", "t[j, k] != 2"]
])
@pytest.mark.parametrize("args", [(), ("-force_element_index",)], ids=["warning", "option"])
def test_element_on_identical_integers_with_an_index_outside_the_list(run, code, args):
    # as for any list, the index is restricted to the list, with a warning unless -force_element_index is given (minimize(c[i]) has nothing
    # to optimize, the objective being the constant 2, as when the index is inside the list)
    r = run(code, args=args)
    assert (r.ok or "there is nothing to optimize" in r.stdout) and (WARNING_OUTSIDE in r.stdout) == (len(args) == 0), r.report()


@pytest.mark.parametrize("constraint, predicate", [
    ("c[i] == v", lambda *t: t[1] == 2),
    ("c[i] == 2", lambda *t: True),
    ("c[i] == 3", lambda *t: False),
    ("c[i] != 2", lambda *t: False),
    ("c[i] < 3", lambda *t: True),
    ("c[i] in {1, 2}", lambda *t: True),
    ("c[i] not in {1, 2}", lambda *t: False),
    ("c[i] + v == 5", lambda *t: t[1] == 3),
    ("x[c[i]] == 1", lambda *t: t[4] == 1),
    ("c[i] in x", lambda *t: 2 in t[2:]),
    ("v in [c[i], 4]", lambda *t: t[1] in (2, 4)),
    ("AllDifferent(c[i], v)", lambda *t: t[1] != 2),
    ("Count(x, value=c[i]) == 1", lambda *t: t[2:].count(2) == 1),
    ("Sum([c[i], v]) == 4", lambda *t: t[1] == 2),
    ("Sum(x) == c[i]", lambda *t: sum(t[2:]) == 2),
])
@pytest.mark.parametrize("args", [(), ("-force_element_index",)], ids=["warning", "option"])
def test_element_on_identical_integers_with_an_index_outside_the_list_restricted(run, solver, request, constraint, predicate, args):
    # the index i cannot take the value 3, outside the list, with or without -force_element_index
    check_with_v(run, solver, request, C3_OUTSIDE, constraint, DC_OUTSIDE, lambda *t: t[0] < 3 and predicate(*t), 1, args, empty_supports=False)


@pytest.mark.parametrize("constraint, predicate", [
    ("m[j][k] == v", lambda *t: t[2] == 2),
    ("m[j][k] == 2", lambda *t: True),
    ("m[j, k] == 3", lambda *t: False),
    ("t[j][k] == v", lambda *t: t[2] == t[1] + 1),
    ("t[j][k] == 1", lambda *t: t[1] == 0),
    ("t[j, k] != 2", lambda *t: t[1] != 1),
])
@pytest.mark.parametrize("args", [(), ("-force_element_index",)], ids=["warning", "option"])
def test_element_on_a_matrix_of_identical_integers_with_an_index_outside_the_matrix_restricted(run, solver, request, constraint, predicate, args):
    # the index j cannot take the value 2, outside the matrix, with or without -force_element_index
    if constraint == "t[j, k] != 2":
        bug_for(request, "ACE", INT_CONDITION)
    check_with_v(run, solver, request, M_OUTSIDE, constraint, DM_OUTSIDE, lambda *t: t[0] < 2 and predicate(*t), 2, args, empty_supports=False)


# an index i that can take the value 3, outside the lists x (variables), t (integers) and c (identical integers), in logical expressions
# (in the predicates: t[0] for i, t[1] for v, t[2:] for x)
LOGICAL = ("i = Var(dom=range(4))\nv = Var(dom=range(5))\nx = VarArray(size=3, dom=range(3))\nt = cp_array([3, 0, 2])\nc = cp_array([2, 2, 2])\n")
DL = [range(4), range(5)] + [range(3)] * 3


def x_eq(t, k):  # x[i] == k, false when i is outside the list
    return t[0] < 3 and t[2 + t[0]] == k


@pytest.mark.parametrize("constraint, predicate", [
    ("(x[i] == 2) | (v == 1)", lambda *t: x_eq(t, 2) or t[1] == 1),
    ("~(x[i] == 2)", lambda *t: not x_eq(t, 2)),
    ("If(v == 1, Then=x[i] == 2)", lambda *t: t[1] != 1 or x_eq(t, 2)),
    ("If(x[i] == 2, Then=v == 1)", lambda *t: not x_eq(t, 2) or t[1] == 1),
    ("If(i < 3, Then=x[i] == 2)", lambda *t: t[0] >= 3 or x_eq(t, 2)),  # the index is checked by the model
    ("iff(x[i] == 2, v == 1)", lambda *t: x_eq(t, 2) == (t[1] == 1)),
    ("xor(x[i] == 2, v == 1)", lambda *t: x_eq(t, 2) != (t[1] == 1)),
    ("((x[i] == 2) & (v == 1)) | (v == 0)", lambda *t: (x_eq(t, 2) and t[1] == 1) or t[1] == 0),
    ("both(x[i] == 2, v == 1)", lambda *t: x_eq(t, 2) and t[1] == 1),  # a conjunction posted directly restricts the index
    ("(x[i] + v == 3) | (v == 0)", lambda *t: (t[0] < 3 and t[2 + t[0]] + t[1] == 3) or t[1] == 0),
    ("(x[i] in {1, 2}) | (v == 0)", lambda *t: (t[0] < 3 and t[2 + t[0]] in (1, 2)) or t[1] == 0),
    ("(x[x[i]] == 1) | (v == 0)", lambda *t: (t[0] < 3 and t[2 + t[2 + t[0]]] == 1) or t[1] == 0),
    ("(t[i] == v) | (v == 0)", lambda *t: (t[0] < 3 and (3, 0, 2)[t[0]] == t[1]) or t[1] == 0),
    ("~(t[i] == 2)", lambda *t: not (t[0] < 3 and (3, 0, 2)[t[0]] == 2)),
    ("(c[i] == 2) | (v == 1)", lambda *t: t[0] < 3 or t[1] == 1),
    ("(c[i] == v) | (v == 0)", lambda *t: (t[0] < 3 and t[1] == 2) or t[1] == 0),
    ("~(c[i] == 2)", lambda *t: t[0] >= 3),
    ("If(v == 1, Then=c[i] == 3)", lambda *t: t[1] != 1),
    ("If(c[i] == 2, Then=v == 1)", lambda *t: t[0] >= 3 or t[1] == 1),
    ("If(i < 3, Then=c[i] == v)", lambda *t: t[0] >= 3 or t[1] == 2),  # as in the model LinearToProgram
])
@pytest.mark.parametrize("args", [(), ("-force_element_index",)], ids=["warning", "option"])
def test_element_with_an_index_outside_the_list_in_logical_expressions(run, solver, constraint, predicate, args):
    # in a logical expression, an element whose index is outside the list does not hold, and its index is not restricted for the whole model
    check(run, solver, LOGICAL + f"satisfy({constraint})", DL, predicate, args=args)


@pytest.mark.parametrize("constraint, predicate", [
    ("(x[k + 1] == 2) | (v == 0)", lambda k, v, *x: (k + 1 < 3 and x[k + 1] == 2) or v == 0),
    ("~(x[k + 1] == 2)", lambda k, v, *x: not (k + 1 < 3 and x[k + 1] == 2)),
    ("(c[k + 1] == v) | (v == 0)", lambda k, v, *x: (k + 1 < 3 and v == 2) or v == 0),
    ("~(c[k + 1] == 2)", lambda k, v, *x: k + 1 >= 3),
])
def test_element_with_an_expression_as_index_outside_the_list_in_logical_expressions(run, solver, constraint, predicate):
    # the expression k + 1 can take the value 3, outside the lists x (variables) and c (identical integers)
    code = "k = Var(dom=range(3))\nv = Var(dom=range(3))\nx = VarArray(size=3, dom=range(3))\nc = cp_array([2, 2, 2])\n"
    check(run, solver, code + f"satisfy({constraint})", [range(3)] * 5, predicate)


def test_element_with_an_index_outside_the_list_as_objective(run, solver):
    # an objective restricts the index of its elements to the list (t[0] for i, t[1] for v, t[2:] for x)
    r = run(LOGICAL + "satisfy(v != 0)\nminimize(x[i] + v)", solver=solver)
    assert_optimum(r, brute_force(DL, lambda *t: t[0] < 3 and t[1] != 0), lambda *t: t[2 + t[0]] + t[1])


# a matrix m of variables, a matrix t of identical rows and a matrix n of identical integers, with indexes j and k that can take the value 2,
# outside the rows of the matrices (in the predicates: t[:6] for m, t[6] for j, t[7] for k, t[8] for v)
LOGICAL_M = ("m = VarArray(size=[2, 3], dom=range(2))\nj = Var(dom=range(3))\nk = Var(dom=range(3))\nv = Var(dom=range(2))\n"
             "t = cp_array([[1, 2, 3], [1, 2, 3]])\nn = cp_array([[2, 2, 2], [2, 2, 2]])\n")
DLM = [range(2)] * 6 + [range(3), range(3), range(2)]


def m_eq(t, k, d=0):  # m[j][k + d] == k, false when an index is outside the matrix
    return t[6] < 2 and t[7] + d < 3 and t[3 * t[6] + t[7] + d] == k


@pytest.mark.parametrize("constraint, predicate", [
    ("(m[j][k] == 1) | (v == 0)", lambda *t: m_eq(t, 1) or t[8] == 0),
    ("~(m[j, k] == 1)", lambda *t: not m_eq(t, 1)),
    ("(m[j][k + 1] == 1) | (v == 0)", lambda *t: m_eq(t, 1, 1) or t[8] == 0),
    ("~(m[j, k + 1] == 1)", lambda *t: not m_eq(t, 1, 1)),
    ("(t[j][k] == v) | (v == 0)", lambda *t: (t[6] < 2 and t[7] + 1 == t[8]) or t[8] == 0),
    ("~(t[j, k] == 2)", lambda *t: not (t[6] < 2 and t[7] == 1)),
    ("(n[j][k] == 2) | (v == 1)", lambda *t: t[6] < 2 or t[8] == 1),
])
@pytest.mark.parametrize("args", [(), ("-force_element_index",)], ids=["warning", "option"])
def test_element_on_a_matrix_with_an_index_outside_the_matrix_in_logical_expressions(run, solver, request, constraint, predicate, args):
    # in a logical expression, an element whose row index is outside the matrix does not hold (its value being an auxiliary variable)
    if constraint.startswith(("(m[", "~(m[")):
        bug_for(request, "CHOCO", CHOCO_MATRIX)
    check(run, solver, LOGICAL_M + f"satisfy({constraint})", DLM, predicate, args=args)
