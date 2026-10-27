"""
Tests of the constraint Element of the section Constraints (Global) of the API (https://pycsp.org/documentation/api/constraints-global/#Element):
expressions of the form x[i] (a list of variables or of integers indexed by a variable, or an expression), m[i][j] (a matrix indexed by two
variables), with conditions given by operators, as terms of expressions, in groups of constraints, in logical expressions and in objectives,
and the constraint Element without index (member), written v in x.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
According to XCSP3-core, element(X, i, (op, k)) holds iff X[i] op k, X being a list of (at least two) integer variables or integers (in that
case, the condition contains a variable), the first index being 0; element(X, v) (without index) holds iff v is equal to one variable of X;
element-matrix(M, <i, j>, (op, k)) holds iff M[i][j] op k.
"""

import pytest

from harness import assert_fails, assert_optimum, assert_solutions, brute_force, bug, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
LOGICAL_OUTSIDE = ("#284: with -force_element_index, an index that can be outside the list is restricted to the list for the whole model, "
                   "even when the element is in a logical expression (as said in the page Element of the documentation)")
BOOLEAN = ("#291: the element of a list of 0/1 variables cannot be used with | and ~ (TypeError), and the element of a list of 0/1 "
           "integers cannot be posted alone (assert without message)")
INVALID = ("#292: invalid arguments of an element: assert without message, TypeError raised inside PyCSP3, or a symbolic variable "
           "accepted as value")
ROWS_TUPLE = "#293: a row of integers indexed by a variable compared with a tuple of variables fails (whereas a list works)"
EMPTY_SUPPORTS = ("(to be reported) ACE and CHOCO fail on a table with an empty set of supports, recognized as false by the parser "
                  "(buildCtrFalse(): RuntimeException: Constraint with only conflicts)")
ACE_EQ = ("xcsp3team/ACE#26: ACE gives wrong solutions for nValues with the condition (eq,k), 1 < k < |X|, and fails when the variables have "
          "different types of domains")
ACE_NOTIN_INTERVAL = ("xcsp3team/ACE#36: ACE gives the solutions of (in,a..b) for element with (notin,a..b) (Problem.postExprSubjectToCondition() "
                      "ignores the operator of an interval)")
ACE_MEMBER = ("xcsp3team/ACE#36: ACE gives wrong solutions for element without index (member) with a variable as value (Table.starredMember() puts "
              "the value first, whereas the scope has the list first)")
ACE_INDEX_AS_VALUE = "xcsp3team/ACE#36: ACE gives wrong solutions for element on a list of integers or on a matrix when the index is also the value"
ACE_REPEATED = "xcsp3team/ACE#36: ACE fails without message on element when a variable appears several times in the list (ERROR: i=j x=...)"
ACE_SAME_INDEXES = ("xcsp3team/ACE#36: ACE fails without message on element on a non-square matrix when the same variable is the index of the "
                    "row and of the column")
COSOCO_NOTIN = ("xcsp3team/cosoco#106: cosoco crashes (segmentation fault) on element with (notin,S): the case notin is missing in "
                "buildConstraintElement()")
COSOCO_IN_INTERVAL = "xcsp3team/cosoco#106: cosoco crashes (segmentation fault) on element with (in,a..b): the interval is read as an empty set"
COSOCO_MATRIX_VALUE = ("xcsp3team/cosoco#106: cosoco crashes (segmentation fault) on element on a matrix of integers with an integer as value (the "
                       "parser gives the integer as a variable)")
COSOCO_INDEX_IN_LIST = ("xcsp3team/cosoco#106: cosoco misses solutions of element when the index is in the list (ElementConstant::filter() removes the "
                        "value from the index instead of the position of the index)")
COSOCO_REPEATED = "xcsp3team/cosoco#106: cosoco gives wrong solutions for element when a variable appears several times in the list"
COSOCO_MATRIX_CONSTANT = ("xcsp3team/cosoco#106: cosoco gives a Solution Error for element on a non-square matrix of variables with an integer as value "
                          "(ElementMatrixConstant::isSatisfiedBy() multiplies the row by the number of rows)")
COSOCO_INDEX_AS_VALUE = "xcsp3team/cosoco#106: cosoco gives a Solution Error for element on a list of integers when the index is also the value"
COSOCO_IN_SET = ("(to be reported) cosoco crashes (segmentation fault) on an intension where in(v,set(...)), with variables in the set, is in a "
                 "disjunction or an implication")
CHOCO_MEMBER = ("chocoteam/choco-solver#1270: CHOCO finds solutions several times for element without index (member), also with CHOCO 6.0.2 "
                "and the develop version (an index variable is introduced)")
CHOCO_INTERVAL = ("CHOCO 4.10.15-beta (embedded in PyCSP3) and CHOCO 6.0.2 find wrong solutions for element with (in,a..b) and (notin,a..b), "
                  "fixed in the develop version of CHOCO (4e5f043, not reported)")
CHOCO_MATRIX = ("CHOCO 4.10.15-beta (embedded in PyCSP3) misses solutions of element on a matrix of variables, except with (eq,k) and (ne,k), "
                "fixed in CHOCO 6.0.2 (not reported)")

# The cases that a solver says it does not handle (not reported)
COSOCO_UNSUPPORTED_MEMBER = "cosoco does not handle element without index (member) (s UNSUPPORTED)"
COSOCO_UNSUPPORTED_MATRIX = ("cosoco does not handle element on a matrix with a condition other than eq (not yet supported, s UNSUPPORTED), "
                             "nor a variable given twice (as the two indexes, or as index and value: badly defined)")
COSOCO_UNSUPPORTED_NOTIN_INTERVAL = "cosoco does not handle element with (notin,a..b) (not yet implemented, s UNSUPPORTED)"
UNSUPPORTED = (COSOCO_UNSUPPORTED_MEMBER, COSOCO_UNSUPPORTED_MATRIX, COSOCO_UNSUPPORTED_NOTIN_INTERVAL)

# a list of 3 variables x, an index i and a variable v (in the predicates: t[:3] for x, t[3] for i, t[4] for v)
X3 = "x = VarArray(size=3, dom=range(4))\ni = Var(dom=range(3))\nv = Var(dom=range(5))\n"
DX = [range(4)] * 3 + [range(3), range(5)]

# a list of 4 integers t, an index i and a variable v (in the predicates: t[0] for i, t[1] for v)
T4 = "t = cp_array([3, 0, 2, 0])\ni = Var(dom=range(4))\nv = Var(dom=range(5))\n"
DT = [range(4), range(5)]
T = (3, 0, 2, 0)

# a matrix m of 2 x 3 variables, two indexes j and k, and a variable v (in the predicates: t[:6] for m, t[6] for j, t[7] for k, t[8] for v)
M23 = "m = VarArray(size=[2, 3], dom=range(2))\nj = Var(dom=range(2))\nk = Var(dom=range(3))\nv = Var(dom=range(3))\n"
DM = [range(2)] * 6 + [range(2), range(3), range(3)]


def xi(t):
    """The value of x[i] in a tuple of DX."""
    return t[t[3]]


def ti(t):
    """The value of t[i] in a tuple of DT."""
    return T[t[0]]


def mjk(t):
    """The value of m[j][k] in a tuple of DM."""
    return t[3 * t[6] + t[7]]


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


def mark(request, solver, reasons):
    """
    Marks the running test as failing because of a bug, or skips it for a case not handled by the solver, according to the reason given
    for the solver in reasons (a dict solver -> reason, the key "*" being for all the solvers).
    """
    reason = reasons.get(solver, reasons.get("*"))
    if reason in UNSUPPORTED:
        pytest.skip(reason)
    if reason is not None:
        request.applymarker(bug(reason))


# ------------------------------------------------------------------------------------------------ conditions (variables)

CONDITIONS_MARKS = {
    "x[i] in range(1, 3)": {"CHOCO": CHOCO_INTERVAL, "COSOCO": COSOCO_IN_INTERVAL},
    "x[i] not in range(1, 3)": {"ACE": ACE_NOTIN_INTERVAL, "CHOCO": CHOCO_INTERVAL, "COSOCO": COSOCO_UNSUPPORTED_NOTIN_INTERVAL},
    "x[i] not in {1, 3}": {"COSOCO": COSOCO_NOTIN},
    "x[i] not in [0, 3]": {"COSOCO": COSOCO_NOTIN},
    "x[i] not in {2}": {"COSOCO": COSOCO_NOTIN},
}


@pytest.mark.parametrize("constraint, predicate", [
    ("x[i] == v", lambda t: xi(t) == t[4]),
    ("x[i] == 2", lambda t: xi(t) == 2),
    ("x[i] != 2", lambda t: xi(t) != 2),
    ("x[i] != v", lambda t: xi(t) != t[4]),
    ("x[i] < 2", lambda t: xi(t) < 2),
    ("x[i] < v", lambda t: xi(t) < t[4]),
    ("x[i] <= 1", lambda t: xi(t) <= 1),
    ("x[i] <= v", lambda t: xi(t) <= t[4]),
    ("x[i] > 2", lambda t: xi(t) > 2),
    ("x[i] > v", lambda t: xi(t) > t[4]),
    ("x[i] >= 1", lambda t: xi(t) >= 1),
    ("x[i] >= v", lambda t: xi(t) >= t[4]),
    ("x[i] in {1, 3}", lambda t: xi(t) in (1, 3)),
    ("x[i] in range(1, 3)", lambda t: xi(t) in (1, 2)),
    ("x[i] in range(0, 4, 2)", lambda t: xi(t) in (0, 2)),
    ("x[i] in [0, 3]", lambda t: xi(t) in (0, 3)),
    ("x[i] in (2,)", lambda t: xi(t) == 2),
    ("x[i] in {5, 6}", lambda t: False),
    ("x[i] not in {1, 3}", lambda t: xi(t) not in (1, 3)),
    ("x[i] not in range(1, 3)", lambda t: xi(t) not in (1, 2)),
    ("x[i] not in [0, 3]", lambda t: xi(t) not in (0, 3)),
    ("x[i] not in {2}", lambda t: xi(t) != 2),
    ("v == x[i]", lambda t: xi(t) == t[4]),
    ("2 == x[i]", lambda t: xi(t) == 2),
    ("2 < x[i]", lambda t: xi(t) > 2),
    ("v >= x[i]", lambda t: xi(t) <= t[4]),
    ("x[i] == v + 1", lambda t: xi(t) == t[4] + 1),
    ("x[i] <= v - 2", lambda t: xi(t) <= t[4] - 2),
    ("x[i] == abs(v - 2)", lambda t: xi(t) == abs(t[4] - 2)),
    ("x[i] == x[0]", lambda t: xi(t) == t[0]),
    ("x[i] > x[0]", lambda t: xi(t) > t[0]),
    ("x[i] == i", lambda t: xi(t) == t[3]),
    ("x[i] != i", lambda t: xi(t) != t[3]),
    ("x[i] == 7", lambda t: False),
    ("x[i] == -1", lambda t: False),
    ("x[i] == x[i]", lambda t: True),
    ("x[i] != x[i]", lambda t: False),
])
def test_element_conditions(run, solver, request, constraint, predicate):
    mark(request, solver, CONDITIONS_MARKS.get(constraint, {}))
    check(run, solver, X3 + f"satisfy({constraint})", DX, lambda *t: predicate(t))


@pytest.mark.parametrize("constraint, predicate", [
    ("x[i] in set()", lambda t: False),
    ("x[i] in range(2, 2)", lambda t: False),
    ("x[i] in []", lambda t: False),
    ("x[i] not in set()", lambda t: True),
    ("x[i] not in range(2, 2)", lambda t: True),
])
def test_element_with_an_empty_set_of_values(run, solver, request, constraint, predicate):
    # never in an empty set: the constraint is false with 'in', and always true with 'not in'
    if " in " in constraint and "not in" not in constraint:
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)  # the constraint false, posted by a table with an empty set of supports
    check(run, solver, X3 + f"satisfy({constraint}, x[0] != 3)", DX, lambda *t: predicate(t) and t[0] != 3)


# ------------------------------------------------------------------------------------------------ conditions (integers)

INTEGERS_MARKS = {
    "t[i] == i": {"ACE": ACE_INDEX_AS_VALUE, "COSOCO": COSOCO_INDEX_AS_VALUE},
    "t[i] == 7": {"ACE": EMPTY_SUPPORTS, "CHOCO": EMPTY_SUPPORTS},  # the constraint false, posted by a table with an empty set of supports
}


@pytest.mark.parametrize("constraint, predicate", [
    ("t[i] == v", lambda t: ti(t) == t[1]),
    ("t[i] == 0", lambda t: ti(t) == 0),
    ("t[i] == 2", lambda t: ti(t) == 2),
    ("t[i] != 0", lambda t: ti(t) != 0),
    ("t[i] != v", lambda t: ti(t) != t[1]),
    ("t[i] < v", lambda t: ti(t) < t[1]),
    ("t[i] < 2", lambda t: ti(t) < 2),
    ("t[i] >= 2", lambda t: ti(t) >= 2),
    ("t[i] > v", lambda t: ti(t) > t[1]),
    ("t[i] in {0, 2}", lambda t: ti(t) in (0, 2)),
    ("t[i] not in {0, 2}", lambda t: ti(t) not in (0, 2)),
    ("t[i] in range(1, 3)", lambda t: ti(t) in (1, 2)),
    ("v == t[i]", lambda t: ti(t) == t[1]),
    ("t[i] == v + 1", lambda t: ti(t) == t[1] + 1),
    ("t[i] == i", lambda t: ti(t) == t[0]),
    ("t[i] == 7", lambda t: False),
])
def test_element_on_integers(run, solver, request, constraint, predicate):
    mark(request, solver, INTEGERS_MARKS.get(constraint, {}))
    check(run, solver, T4 + f"satisfy({constraint})", DT, lambda *t: predicate(t))


@pytest.mark.parametrize("constraint, predicate", [
    ("c[i] == v", lambda *t: t[1] == 2),
    ("c[i] != v", lambda *t: t[1] != 2),
    ("c[i] < v", lambda *t: 2 < t[1]),
    ("c[i] == 2", lambda *t: True),
    ("c[i] == 3", lambda *t: False),
    ("c[i] in {1, 2}", lambda *t: True),
    ("c[i] + v == 5", lambda *t: t[1] == 3),
])
def test_element_on_identical_integers(run, solver, request, constraint, predicate):
    # all the integers of the list are equal: the element is this integer, for any index (#281)
    if constraint == "c[i] == 3":
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)  # the constraint false, posted by a table with an empty set of supports
    check(run, solver, "c = cp_array([2, 2, 2])\ni = Var(dom=range(3))\nv = Var(dom=range(5))\n" + f"satisfy({constraint}, v != 4)", [range(3), range(5)],
          lambda *t: predicate(*t) and t[1] != 4)


@pytest.mark.parametrize("values, domain", [("[-2, 5, -2]", range(-3, 6)), ("[7, 1]", range(8)), ("[0, 1, 0, 1]", range(2))])
def test_element_on_different_integers(run, solver, values, domain):
    lst = eval(values)
    check(run, solver, f"t = cp_array({values})\ni = Var(dom=range({len(lst)}))\nv = Var(dom={domain!r})\nsatisfy(t[i] == v)",
          [range(len(lst)), domain], lambda i, v: lst[i] == v)


# ------------------------------------------------------------------------------------------------------------ indexes

@pytest.mark.parametrize("code, domains, predicate", [
    # index with holes
    ("x = VarArray(size=3, dom=range(3))\ni = Var(dom={0, 2})\nsatisfy(x[i] == 1)", [range(3)] * 3 + [[0, 2]], lambda *t: t[t[3]] == 1),
    # index given by a variable without domain (its domain becomes the indexes of the list)
    ("x = VarArray(size=3, dom=range(3))\ni = Var(id='i')\nsatisfy(x[i] == 1)", [range(3)] * 3 + [range(3)], lambda *t: t[t[3]] == 1),
    # index of a variable array
    pytest.param("x = VarArray(size=3, dom=range(3))\nsatisfy(x[x[0]] == 2)", [range(3)] * 3, lambda *t: t[t[0]] == 2, id="x[x[0]] == 2"),
    ("x = VarArray(size=3, dom=range(3))\nsatisfy(x[x[2]] == x[1])", [range(3)] * 3, lambda *t: t[t[2]] == t[1]),
    ("x = VarArray(size=3, dom=range(3))\ni = Var(dom=range(3))\nsatisfy(x[x[i]] == 2)", [range(3)] * 4, lambda *t: t[t[t[3]]] == 2),
    ("t = cp_array([2, 0, 1])\nx = VarArray(size=3, dom=range(3))\nsatisfy(t[x[0]] == x[1])", [range(3)] * 3, lambda *t: (2, 0, 1)[t[0]] == t[1]),
    ("t = cp_array([2, 0, 1])\nx = VarArray(size=3, dom=range(3))\ni = Var(dom=range(3))\nsatisfy(x[t[i]] == 1)", [range(3)] * 4,
     lambda *t: t[(2, 0, 1)[t[3]]] == 1),
    ("t = cp_array([2, 0, 1])\ni = Var(dom=range(3))\nv = Var(dom=range(3))\nsatisfy(t[t[i]] == v)", [range(3)] * 2,
     lambda i, v: (2, 0, 1)[(2, 0, 1)[i]] == v),
    # index given by a 0/1 variable, or a Boolean expression
    ("x = VarArray(size=2, dom=range(3))\nb = Var(dom={0, 1})\nsatisfy(x[b] == 2)", [range(3)] * 2 + [range(2)], lambda *t: t[t[2]] == 2),
    ("x = VarArray(size=2, dom=range(3))\ni = Var(dom=range(3))\nsatisfy(x[i == 1] == 2)", [range(3)] * 2 + [range(3)],
     lambda *t: t[int(t[2] == 1)] == 2),
])
def test_element_with_variables_as_indexes(run, solver, request, code, domains, predicate):
    if "satisfy(x[x[0]] == 2)" in code:
        bug_for(request, "COSOCO", COSOCO_INDEX_IN_LIST)
    check(run, solver, code, domains, predicate)


@pytest.mark.parametrize("index, values, predicate", [
    ("j + 1", "j = Var(dom=range(2))", lambda *t: t[t[3] + 1] == 2),
    ("j - 1", "j = Var(dom=range(1, 4))", lambda *t: t[t[3] - 1] == 2),
    ("2 * j", "j = Var(dom=range(2))", lambda *t: t[2 * t[3]] == 2),
    ("j % 3", "j = Var(dom=range(5))", lambda *t: t[t[3] % 3] == 2),
    ("abs(j - 1)", "j = Var(dom=range(3))", lambda *t: t[abs(t[3] - 1)] == 2),
    ("2 - j", "j = Var(dom=range(3))", lambda *t: t[2 - t[3]] == 2),
    ("j + 0", "j = Var(dom=range(3))", lambda *t: t[t[3]] == 2),
    ("1 * j", "j = Var(dom=range(3))", lambda *t: t[t[3]] == 2),
    ("j // 2", "j = Var(dom=range(6))", lambda *t: t[t[3] // 2] == 2),
    ("Sum(b)", "b = VarArray(size=2, dom={0, 1})", lambda *t: t[t[3] + t[4]] == 2),
    ("Maximum(b)", "b = VarArray(size=2, dom={0, 1})", lambda *t: t[max(t[3], t[4])] == 2),
    ("Count(b, value=0)", "b = VarArray(size=2, dom={0, 1})", lambda *t: t[(t[3] == 0) + (t[4] == 0)] == 2),
])
def test_element_with_expressions_as_indexes(run, solver, index, values, predicate):
    # an expression as index is replaced by an auxiliary variable
    nb = 2 if values.startswith("b") else 1
    domain = eval(values.partition("dom=")[2][:-1])
    check(run, solver, f"x = VarArray(size=3, dom=range(3))\n{values}\nsatisfy(x[{index}] == 2)", [range(3)] * 3 + [domain] * nb, predicate)


@pytest.mark.parametrize("code", [
    "x = VarArray(size=3, dom=range(3))\ni = Var(dom=range(4))\nsatisfy(x[i] == 2)",
    "x = VarArray(size=3, dom=range(3))\ni = Var(dom={-1, 2})\nsatisfy(x[i] == 2)",
    "x = VarArray(size=3, dom=range(3))\nj = Var(dom=range(3))\nsatisfy(x[j + 1] == 2)",
    "x = VarArray(size=3, dom=range(3))\nj = Var(dom=range(3))\nsatisfy(x[j - 1] == 2)",
    "x = VarArray(size=3, dom=range(4))\nsatisfy(x[x[0]] == 2)",
    "t = cp_array([3, 0, 2])\ni = Var(dom=range(4))\nv = Var(dom=range(4))\nsatisfy(t[i] == v)",
    "c = cp_array([2, 2, 2])\ni = Var(dom=range(4))\nv = Var(dom=range(4))\nsatisfy(c[i] == v)",
    "m = VarArray(size=[2, 3], dom=range(2))\nj = Var(dom=range(3))\nk = Var(dom=range(3))\nsatisfy(m[j][k] == 1)",
    "m = VarArray(size=[2, 3], dom=range(2))\nj = Var(dom=range(2))\nk = Var(dom=range(4))\nsatisfy(m[j][k] == 1)",
    "m = VarArray(size=[2, 3], dom=range(2))\nj = Var(dom=range(2))\nk = Var(dom=range(3))\nsatisfy(m[j][k + 1] == 1)",
    "m = VarArray(size=[2, 3], dom=range(2))\nj = Var(dom=range(2))\nk = Var(dom=range(3))\nsatisfy(m[j, k + 1] == 1)",
    "m = VarArray(size=[2, 3], dom=range(2))\nj = Var(dom=range(2))\nk = Var(dom=range(3))\nsatisfy(m[j + 1, k] == 1)",
    "x = VarArray(size=3, dom=range(3))\nj = Var(dom=range(3))\nsatisfy(x[abs(j - 3)] == 2)",
    "m = VarArray(size=[2, 3], dom=range(2))\nj = Var(dom=range(2))\nk = Var(dom=range(3))\nsatisfy(m[j + 1][k] == 1)",
    "t = cp_array([[1, 2, 0], [1, 2, 0]])\nj = Var(dom=range(3))\nk = Var(dom=range(3))\nv = Var(dom=range(3))\nsatisfy(t[j][k] == v)",
    "t = cp_array([[1, 2, 0], [1, 2, 0]])\nj = Var(dom=range(3))\nk = Var(dom=range(3))\nv = Var(dom=range(3))\nsatisfy(t[j, k] == v)",
])
def test_element_with_an_index_outside_the_list(run, code):
    # an index (variable or expression) that can take a value outside the indexes of the list is an error, unless -force_element_index is given
    r = run(code)
    assert not r.ok and "-force_element_index" in r.stdout, r.report()


@pytest.mark.parametrize("code, domains, predicate", [
    ("x = VarArray(size=3, dom=range(3))\ni = Var(dom=range(5))\nsatisfy(x[i] == 2)", [range(3)] * 3 + [range(5)], lambda *t: t[3] < 3 and t[t[3]] == 2),
    ("x = VarArray(size=3, dom=range(3))\ni = Var(dom={-1, 2})\nsatisfy(x[i] == 2)", [range(3)] * 3 + [[-1, 2]], lambda *t: t[3] == 2 and t[2] == 2),
    ("x = VarArray(size=3, dom=range(3))\nj = Var(dom=range(3))\nsatisfy(x[j + 1] == 2)", [range(3)] * 4, lambda *t: t[3] < 2 and t[t[3] + 1] == 2),
    ("x = VarArray(size=3, dom=range(3))\nj = Var(dom=range(3))\nsatisfy(x[j - 1] == 2)", [range(3)] * 4, lambda *t: t[3] > 0 and t[t[3] - 1] == 2),
    ("t = cp_array([3, 0, 2])\ni = Var(dom=range(4))\nv = Var(dom=range(4))\nsatisfy(t[i] == v)", [range(4)] * 2, lambda i, v: i < 3 and (3, 0, 2)[i] == v),
    ("c = cp_array([2, 2, 2])\ni = Var(dom=range(4))\nv = Var(dom=range(4))\nsatisfy(c[i] == v)", [range(4)] * 2, lambda i, v: i < 3 and v == 2),
    ("m = VarArray(size=[2, 2], dom=range(2))\nj = Var(dom=range(3))\nk = Var(dom=range(2))\nsatisfy(m[j][k] == 1)", [range(2)] * 4 + [range(3), range(2)],
     lambda *t: t[4] < 2 and t[2 * t[4] + t[5]] == 1),
    ("m = VarArray(size=[2, 2], dom=range(2))\nj = Var(dom=range(2))\nk = Var(dom=range(2))\nsatisfy(m[j][k + 1] == 1)", [range(2)] * 6,
     lambda *t: t[5] < 1 and t[2 * t[4] + t[5] + 1] == 1),
    ("m = VarArray(size=[2, 2], dom=range(2))\nj = Var(dom=range(2))\nk = Var(dom=range(2))\nsatisfy(m[j, k + 1] == 1)", [range(2)] * 6,
     lambda *t: t[5] < 1 and t[2 * t[4] + t[5] + 1] == 1),
    ("t = cp_array([[1, 2], [1, 2]])\nj = Var(dom=range(3))\nk = Var(dom=range(2))\nv = Var(dom=range(3))\nsatisfy(t[j][k] == v)", [range(3), range(2), range(3)],
     lambda j, k, v: j < 2 and (1, 2)[k] == v),
])
def test_element_with_an_index_outside_the_list_and_the_option(run, solver, code, domains, predicate):
    # with -force_element_index, the index cannot take a value outside the indexes of the list
    check(run, solver, code, domains, predicate, args=("-force_element_index",))


# ------------------------------------------------------------------------------------------------------------ lists

@pytest.mark.parametrize("code, domains, predicate", [
    ("x = VarArray(size=4, dom=range(3))\nj = Var(dom=range(3))\nsatisfy(x[1:][j] == 2)", [range(3)] * 4 + [range(3)], lambda *t: t[1 + t[4]] == 2),
    ("x = VarArray(size=4, dom=range(3))\nj = Var(dom=range(2))\nsatisfy(x[::2][j] == 2)", [range(3)] * 4 + [range(2)], lambda *t: t[2 * t[4]] == 2),
    ("x = VarArray(size=4, dom=range(3))\nj = Var(dom=range(2))\nsatisfy(x[:2][j] == 2)", [range(3)] * 4 + [range(2)], lambda *t: t[t[4]] == 2),
    ("x = VarArray(size=4, dom=range(3))\nj = Var(dom=range(2))\nsatisfy(x[2:][j] == x[0])", [range(3)] * 4 + [range(2)], lambda *t: t[2 + t[4]] == t[0]),
    # repeated variables
    pytest.param("x = VarArray(size=2, dom=range(3))\nj = Var(dom=range(3))\nsatisfy(cp_array(x[0], x[0], x[1])[j] == 2)", [range(3)] * 2 + [range(3)],
                 lambda *t: (t[0], t[0], t[1])[t[2]] == 2, id="repeated variables"),
    # the index in the list
    ("x = VarArray(size=2, dom=range(3))\nj = Var(dom=range(3))\nsatisfy(cp_array(x[0], x[1], j)[j] == 2)", [range(3)] * 3,
     lambda *t: (t[0], t[1], t[2])[t[2]] == 2),
    # variables and integers
    ("x = VarArray(size=2, dom=range(3))\nj = Var(dom=range(3))\nv = Var(dom=range(3))\nsatisfy(cp_array(x[0], 2, x[1])[j] == v)", [range(3)] * 4,
     lambda *t: (t[0], 2, t[1])[t[2]] == t[3]),
    # expressions
    ("x = VarArray(size=2, dom=range(3))\nj = Var(dom=range(3))\nv = Var(dom=range(4))\nsatisfy(cp_array(x[0] + 1, x[1], x[0])[j] == v)",
     [range(3)] * 3 + [range(4)], lambda *t: (t[0] + 1, t[1], t[0])[t[2]] == t[3]),
    # variables of different domains
    ("x = VarArray(size=3, dom=lambda a: range(a + 1))\nj = Var(dom=range(3))\nv = Var(dom=range(3))\nsatisfy(x[j] == v)",
     [range(1), range(2), range(3), range(3), range(3)], lambda *t: t[t[3]] == t[4]),
    ("x = VarArray(size=3, dom=range(-2, 2))\nj = Var(dom=range(3))\nv = Var(dom=range(-3, 3))\nsatisfy(x[j] == v)",
     [range(-2, 2)] * 3 + [range(3), range(-3, 3)], lambda *t: t[t[3]] == t[4]),
    ("b = VarArray(size=3, dom={0, 1})\nj = Var(dom=range(3))\nsatisfy(b[j] == 1)", [range(2)] * 3 + [range(3)], lambda *t: t[t[3]] == 1),
    ("b = VarArray(size=3, dom={0, 1})\nj = Var(dom=range(3))\nsatisfy(b[j])", [range(2)] * 3 + [range(3)], lambda *t: t[t[3]] == 1),
    pytest.param("t = cp_array([0, 1, 1])\nj = Var(dom=range(3))\nsatisfy(t[j])", [range(3)], lambda j: j > 0, marks=bug(BOOLEAN)),
    ("z = VarArray(size=3, dom={0, 2, 5})\nj = Var(dom=range(3))\nv = Var(dom=range(6))\nsatisfy(z[j] == v)", [[0, 2, 5]] * 3 + [range(3), range(6)],
     lambda *t: t[t[3]] == t[4]),
])
def test_element_lists(run, solver, request, code, domains, predicate):
    if "cp_array(x[0], x[0], x[1])" in code:
        mark(request, solver, {"ACE": ACE_REPEATED, "COSOCO": COSOCO_REPEATED})
    check(run, solver, code, domains, predicate)


HOLES_1D = "x = VarArray(size=3, dom=lambda a: None if a == 1 else range(3))\n"  # x[1] is a hole
HOLES_2D = "m = VarArray(size=[2, 2], dom=lambda a, b: None if b > a else range(2))\nj = Var(dom=range(2))\nk = Var(dom=range(2))\n"  # m[0][1] is a hole


@pytest.mark.parametrize("code", [
    HOLES_1D + "j = Var(dom={0, 2})\nsatisfy(x[j] == 2)",
    HOLES_1D + "j = Var(dom=range(2))\nsatisfy(x[j] == 2)",
    HOLES_1D + "j = Var(dom=range(3))\nsatisfy(x[j] == 2)",
    HOLES_1D + "j = Var(dom=range(3))\nsatisfy((x[j] == 2) | (j == 1))",
    HOLES_2D + "satisfy(m[j][k] == 1)",
    HOLES_2D + "satisfy(m[j, k] == 1)",
    HOLES_2D + "satisfy(m[j][1] == 1)",
    HOLES_2D + "satisfy(m[0][k] == 1)",
])
def test_element_on_an_array_with_holes(run, code):
    # an array with holes (None) cannot be indexed by a variable, the index of a variable in the list without holes being not its index (#283)
    r = run(code)
    assert not r.ok and "has holes (None)" in r.stdout, r.report()


@pytest.mark.parametrize("code, domains, predicate", [
    (HOLES_1D + "j = Var(dom=range(2))\nsatisfy(x[::2][j] == 2)", [range(3)] * 2 + [range(2)], lambda x0, x2, j: (x0, x2)[j] == 2),
    (HOLES_2D + "satisfy(m[j][0] == 1)", [range(2)] * 5, lambda m00, m10, m11, j, k: (m00, m10)[j] == 1),
    (HOLES_2D + "satisfy(m[1][k] == 1)", [range(2)] * 5, lambda m00, m10, m11, j, k: (m10, m11)[k] == 1),
])
def test_element_on_a_part_without_holes_of_an_array_with_holes(run, solver, code, domains, predicate):
    check(run, solver, code, domains, predicate)


# ------------------------------------------------------------------------------------------------------------ matrices

MATRIX_MARKS = {
    "m[j][k] == v": {"CHOCO": CHOCO_MATRIX},
    "m[j][k] == 1": {"COSOCO": COSOCO_MATRIX_CONSTANT},
    "m[j][k] != 1": {"COSOCO": COSOCO_UNSUPPORTED_MATRIX},
    "m[j][k] != v": {"CHOCO": CHOCO_MATRIX, "COSOCO": COSOCO_UNSUPPORTED_MATRIX},
    "m[j][k] < v": {"CHOCO": CHOCO_MATRIX, "COSOCO": COSOCO_UNSUPPORTED_MATRIX},
    "m[j][k] >= v": {"CHOCO": CHOCO_MATRIX, "COSOCO": COSOCO_UNSUPPORTED_MATRIX},
    "m[j][k] > 0": {"COSOCO": COSOCO_UNSUPPORTED_MATRIX},
    "m[j][k] in {1, 2}": {"COSOCO": COSOCO_UNSUPPORTED_MATRIX},
    "m[j][k] in range(1, 3)": {"CHOCO": CHOCO_INTERVAL, "COSOCO": COSOCO_UNSUPPORTED_MATRIX},
    "m[j][k] not in {0}": {"CHOCO": CHOCO_MATRIX, "COSOCO": COSOCO_UNSUPPORTED_MATRIX},
    "v == m[j][k]": {"CHOCO": CHOCO_MATRIX},
    "m[j][k] == j": {"ACE": ACE_INDEX_AS_VALUE, "CHOCO": CHOCO_MATRIX, "COSOCO": COSOCO_UNSUPPORTED_MATRIX},
    "m[j][k] == m[0][0]": {"CHOCO": CHOCO_MATRIX},
    "m[j][k] == v - 1": {"CHOCO": CHOCO_MATRIX},
    "m[j, k] == v": {"CHOCO": CHOCO_MATRIX},
    "m[j][2 - k] == v": {"CHOCO": CHOCO_MATRIX},
    "m[1 - j][k] == v": {"CHOCO": CHOCO_MATRIX},
    "m[j][j] == v": {"ACE": ACE_SAME_INDEXES, "CHOCO": CHOCO_MATRIX, "COSOCO": COSOCO_UNSUPPORTED_MATRIX},
    "m[j][k] + v == 2": {"CHOCO": CHOCO_MATRIX},
}


@pytest.mark.parametrize("constraint, predicate", [
    ("m[j][k] == v", lambda t: mjk(t) == t[8]),
    ("m[j][k] == 1", lambda t: mjk(t) == 1),
    ("m[j][k] != 1", lambda t: mjk(t) != 1),
    ("m[j][k] != v", lambda t: mjk(t) != t[8]),
    ("m[j][k] < v", lambda t: mjk(t) < t[8]),
    ("m[j][k] >= v", lambda t: mjk(t) >= t[8]),
    ("m[j][k] > 0", lambda t: mjk(t) > 0),
    ("m[j][k] in {1, 2}", lambda t: mjk(t) in (1, 2)),
    ("m[j][k] in range(1, 3)", lambda t: mjk(t) in (1, 2)),
    ("m[j][k] not in {0}", lambda t: mjk(t) != 0),
    ("v == m[j][k]", lambda t: mjk(t) == t[8]),
    ("m[j][k] == j", lambda t: mjk(t) == t[6]),
    ("m[j][k] == m[0][0]", lambda t: mjk(t) == t[0]),
    ("m[j][k] == v - 1", lambda t: mjk(t) == t[8] - 1),
    ("m[j][k] == 2", lambda t: False),
    ("m[j, k] == v", lambda t: mjk(t) == t[8]),
    ("m[j][0] == v", lambda t: t[3 * t[6]] == t[8]),
    ("m[1][k] == v", lambda t: t[3 + t[7]] == t[8]),
    ("m[j, 2] == v", lambda t: t[3 * t[6] + 2] == t[8]),
    ("m[0, k] == v", lambda t: t[t[7]] == t[8]),
    ("m[:, 1][j] == v", lambda t: t[3 * t[6] + 1] == t[8]),
    ("m[j][2 - k] == v", lambda t: t[3 * t[6] + 2 - t[7]] == t[8]),
    ("m[1 - j][k] == v", lambda t: t[3 * (1 - t[6]) + t[7]] == t[8]),
    ("m[j][j] == v", lambda t: t[3 * t[6] + t[6]] == t[8]),
    ("m[j][k] + v == 2", lambda t: mjk(t) + t[8] == 2),
])
def test_element_on_a_matrix(run, solver, request, constraint, predicate):
    mark(request, solver, MATRIX_MARKS.get(constraint, {}))
    check(run, solver, M23 + f"satisfy({constraint})", DM, lambda *t: predicate(t))


@pytest.mark.parametrize("constraint, predicate", [
    ("t[j][k] == v", lambda j, k, v: ((1, 2, 3), (4, 5, 6))[j][k] == v),
    ("t[j][k] == 5", lambda j, k, v: ((1, 2, 3), (4, 5, 6))[j][k] == 5),
    ("t[j][k] in {1, 5}", lambda j, k, v: ((1, 2, 3), (4, 5, 6))[j][k] in (1, 5)),
    ("t[j][k] < v", lambda j, k, v: ((1, 2, 3), (4, 5, 6))[j][k] < v),
    ("t[j, k] == v", lambda j, k, v: ((1, 2, 3), (4, 5, 6))[j][k] == v),
    ("t[j][1] == v", lambda j, k, v: ((1, 2, 3), (4, 5, 6))[j][1] == v),
    ("t[0][k] == v", lambda j, k, v: (1, 2, 3)[k] == v),
    ("t[j][k] == j + k", lambda j, k, v: ((1, 2, 3), (4, 5, 6))[j][k] == j + k),
    ("u[j][k] == v", lambda j, k, v: (1, 2, 0)[k] == v),
])
def test_element_on_a_matrix_of_integers(run, solver, request, constraint, predicate):
    mark(request, solver, {"t[j][k] == 5": {"COSOCO": COSOCO_MATRIX_VALUE}, "t[j][k] in {1, 5}": {"COSOCO": COSOCO_UNSUPPORTED_MATRIX},
                           "t[j][k] < v": {"COSOCO": COSOCO_UNSUPPORTED_MATRIX}}.get(constraint, {}))
    code = "t = cp_array([[1, 2, 3], [4, 5, 6]])\nu = cp_array([[1, 2, 0], [1, 2, 0]])\nj = Var(dom=range(2))\nk = Var(dom=range(3))\nv = Var(dom=range(7))\n"
    check(run, solver, code + f"satisfy({constraint})", [range(2), range(3), range(7)], predicate)


# ------------------------------------------------------------------------------------------------ terms of expressions

@pytest.mark.parametrize("constraint, predicate", [
    ("x[i] + v == 5", lambda t: xi(t) + t[4] == 5),
    ("x[i] * 2 == v", lambda t: xi(t) * 2 == t[4]),
    ("abs(x[i] - v) > 1", lambda t: abs(xi(t) - t[4]) > 1),
    ("x[i] + 1 == v", lambda t: xi(t) + 1 == t[4]),
    ("v - x[i] == 1", lambda t: t[4] - xi(t) == 1),
    ("-x[i] == -2", lambda t: xi(t) == 2),
    ("x[i] // 2 == 1", lambda t: xi(t) // 2 == 1),
    ("x[i] % 2 == 1", lambda t: xi(t) % 2 == 1),
    ("max(x[i], v) == 3", lambda t: max(xi(t), t[4]) == 3),
    ("x[i] + x[0] == 5", lambda t: xi(t) + t[0] == 5),
    ("x[i] + x[i] == 4", lambda t: xi(t) == 2),
    ("x[i] + x[2 - i] == 3", lambda t: xi(t) + t[2 - t[3]] == 3),
    ("x[i] < x[2 - i]", lambda t: xi(t) < t[2 - t[3]]),
    ("x[i] == x[2 - i]", lambda t: xi(t) == t[2 - t[3]]),
])
def test_element_as_a_term(run, solver, constraint, predicate):
    # the element is replaced by an auxiliary variable
    check(run, solver, X3 + f"satisfy({constraint})", DX, lambda *t: predicate(t))


@pytest.mark.parametrize("constraint, predicate", [
    ("Sum(t[x[a]] for a in range(3)) == 3", lambda *x: sum((2, 0, 1)[a] for a in x) == 3),
    ("Sum(t[x[a]] * (a + 1) for a in range(3)) == 4", lambda *x: sum((2, 0, 1)[x[a]] * (a + 1) for a in range(3)) == 4),
    ("AllDifferent(t[x[a]] for a in range(3))", lambda *x: len({(2, 0, 1)[a] for a in x}) == 3),
    ("Maximum(t[x[a]] for a in range(3)) == 1", lambda *x: max((2, 0, 1)[a] for a in x) == 1),
    ("Count([t[x[0]], t[x[1]]], value=2) == 1", lambda *x: [(2, 0, 1)[x[0]], (2, 0, 1)[x[1]]].count(2) == 1),
    pytest.param("NValues(t[x[a]] for a in range(3)) == 2", lambda *x: len({(2, 0, 1)[a] for a in x}) == 2, id="NValues"),
    ("Sum(x[x[a]] for a in range(2)) == 3", lambda *x: x[x[0]] + x[x[1]] == 3),
    ("AllDifferent(x[x[a]] for a in range(3))", lambda *x: len({x[a] for a in x}) == 3),
    ("[t[x[a]] == a for a in range(3)]", lambda *x: all((2, 0, 1)[x[a]] == a for a in range(3))),
    ("[x[x[a]] != a for a in range(3)]", lambda *x: all(x[x[a]] != a for a in range(3))),
])
def test_elements_in_global_constraints(run, solver, request, constraint, predicate):
    if constraint.startswith("NValues"):
        bug_for(request, "ACE", ACE_EQ)
    check(run, solver, "t = cp_array([2, 0, 1])\nx = VarArray(size=3, dom=range(3))\n" + f"satisfy({constraint})", [range(3)] * 3, predicate)


@pytest.mark.parametrize("table, positive", [("in {(1, 2), (2, 3)}", True), ("in [(1, 2), (2, 3)]", True), ("not in {(1, 2), (2, 3)}", False)])
@pytest.mark.parametrize("term, value", [("x[i]", xi), ("Sum(x[:2])", lambda t: t[0] + t[1]), ("Maximum(x[:2])", lambda t: max(t[:2]))])
def test_element_in_a_table(run, solver, term, value, table, positive):
    # a component in the scope of a table is replaced by an auxiliary variable, as an expression (#285)
    check(run, solver, X3 + f"satisfy(({term}, v) {table})", DX, lambda *t: ((value(t), t[4]) in ((1, 2), (2, 3))) == positive)


def test_element_in_a_function(run, solver):
    check(run, solver, X3 + "def c(a):\n    return x[i] != a\n\nsatisfy(c(a) for a in range(2))", DX, lambda *t: xi(t) not in (0, 1))


# ------------------------------------------------------------------------------------------------ logical contexts

@pytest.mark.parametrize("constraint, predicate", [
    ("(x[i] == 2) | (v == 1)", lambda t: xi(t) == 2 or t[4] == 1),
    ("(x[i] == 2) & (v == 1)", lambda t: xi(t) == 2 and t[4] == 1),
    ("~(x[i] == 2)", lambda t: xi(t) != 2),
    ("~(x[i] <= v)", lambda t: xi(t) > t[4]),
    ("imply(x[i] == 2, v == 1)", lambda t: xi(t) != 2 or t[4] == 1),
    ("iff(x[i] == 2, v == 1)", lambda t: (xi(t) == 2) == (t[4] == 1)),
    ("xor(x[i] == 2, v == 1)", lambda t: (xi(t) == 2) != (t[4] == 1)),
    ("If(x[i] == 2, Then=v == 1)", lambda t: xi(t) != 2 or t[4] == 1),
    ("If(v == 1, Then=x[i] == 2, Else=x[i] == 0)", lambda t: xi(t) == (2 if t[4] == 1 else 0)),
    ("either(x[i] == 2, v == 1)", lambda t: xi(t) == 2 or t[4] == 1),
    ("both(x[i] >= 1, v == 1)", lambda t: xi(t) >= 1 and t[4] == 1),
    ("disjunction(x[i] == a for a in [0, 3])", lambda t: xi(t) in (0, 3)),
    ("conjunction(x[i] != 0, x[i] != 3)", lambda t: xi(t) in (1, 2)),
    ("(x[i] == v) | (v == 0)", lambda t: xi(t) == t[4] or t[4] == 0),
    ("(x[i] < v) | (x[0] == 3)", lambda t: xi(t) < t[4] or t[0] == 3),
    ("(x[i] in {1, 3}) | (v == 1)", lambda t: xi(t) in (1, 3) or t[4] == 1),
    ("(x[i] not in {1, 3}) | (v == 1)", lambda t: xi(t) not in (1, 3) or t[4] == 1),
    ("(x[i] == 2) == (v == 1)", lambda t: (xi(t) == 2) == (t[4] == 1)),
    ("(x[i] + 1 == v) | (v == 0)", lambda t: xi(t) + 1 == t[4] or t[4] == 0),
    ("(x[i] == 2) | (x[2 - i] == 2)", lambda t: xi(t) == 2 or t[2 - t[3]] == 2),
])
def test_element_in_logical_expressions(run, solver, constraint, predicate):
    # the element is replaced by an auxiliary variable
    check(run, solver, X3 + f"satisfy({constraint})", DX, lambda *t: predicate(t))


@pytest.mark.parametrize("constraint, predicate", [
    ("(t[i] == v) | (v == 1)", lambda t: ti(t) == t[1] or t[1] == 1),
    ("~(t[i] == v)", lambda t: ti(t) != t[1]),
    ("imply(v == 1, t[i] == 0)", lambda t: t[1] != 1 or ti(t) == 0),
])
def test_element_on_integers_in_logical_expressions(run, solver, constraint, predicate):
    check(run, solver, T4 + f"satisfy({constraint})", DT, lambda *t: predicate(t))


@pytest.mark.parametrize("constraint, predicate", [
    ("(m[j][k] == 1) | (v == 1)", lambda t: mjk(t) == 1 or t[8] == 1),
    ("~(m[j][k] == v)", lambda t: mjk(t) != t[8]),
    ("imply(v == 2, m[j][k] == 0)", lambda t: t[8] != 2 or mjk(t) == 0),
])
def test_element_on_a_matrix_in_logical_expressions(run, solver, request, constraint, predicate):
    bug_for(request, "CHOCO", CHOCO_MATRIX)
    check(run, solver, M23 + f"satisfy({constraint})", DM, lambda *t: predicate(t))


@pytest.mark.parametrize("constraint, predicate", [
    pytest.param("b[i] | b[2 - i]", lambda *t: t[t[3]] == 1 or t[2 - t[3]] == 1, marks=bug(BOOLEAN)),
    ("b[i] & (b[0] == 0)", lambda *t: t[t[3]] == 1 and t[0] == 0),
    pytest.param("~b[i]", lambda *t: t[t[3]] == 0, marks=bug(BOOLEAN)),
    ("imply(b[0], b[i])", lambda *t: t[0] == 0 or t[t[3]] == 1),
])
def test_element_on_01_variables_in_logical_expressions(run, solver, constraint, predicate):
    # the element of a list of 0/1 variables is a Boolean
    check(run, solver, "b = VarArray(size=3, dom={0, 1})\ni = Var(dom=range(3))\n" + f"satisfy({constraint})", [range(2)] * 3 + [range(3)], predicate)


@bug(LOGICAL_OUTSIDE)
@pytest.mark.parametrize("constraint, predicate", [
    ("(x[j] == 2) | (j == 3)", lambda *t: t[3] == 3 or t[t[3]] == 2),
    ("If(j >= 1, Then=x[j - 1] == 2)", lambda *t: t[3] == 0 or t[t[3] - 1] == 2),
    ("imply(j < 3, x[j] == 2)", lambda *t: t[3] == 3 or t[t[3]] == 2),
])
def test_element_with_an_index_outside_the_list_in_logical_expressions(run, solver, constraint, predicate):
    # with -force_element_index, the index is restricted to the indexes of the list only where the element is (as in the doc of Element)
    check(run, solver, "x = VarArray(size=3, dom=range(3))\nj = Var(dom=range(4))\n" + f"satisfy({constraint})", [range(3)] * 3 + [range(4)], predicate,
          args=("-force_element_index",))


# ------------------------------------------------------------------------------------------------------------ member

@pytest.mark.parametrize("constraint, predicate", [
    pytest.param("v in x", lambda *t: t[4] in t[:4], id="v in x"),
    ("v in x[:3]", lambda *t: t[4] in t[:3]),
    ("v in x[:2]", lambda *t: t[4] in t[:2]),
    pytest.param("v in {x[0], x[1], x[2], x[3]}", lambda *t: t[4] in t[:4], id="v in a set"),
    ("v in [x[0], x[1], x[2], x[3]]", lambda *t: t[4] in t[:4]),
    ("v in [x[0], x[1]]", lambda *t: t[4] in t[:2]),
    ("v in (x[0], x[1], x[2], x[3])", lambda *t: t[4] in t[:4]),
    ("v in [x[0], x[1], x[2], x[3], 2]", lambda *t: t[4] in t[:4] + (2,)),
    ("v in [2, x[0]]", lambda *t: t[4] in (2, t[0])),
    ("v in {x[0], 2}", lambda *t: t[4] in (2, t[0])),
    ("v not in [x[0], 2]", lambda *t: t[4] not in (2, t[0])),
    ("v not in x", lambda *t: t[4] not in t[:4]),
    ("v not in [x[0], x[1], x[2], x[3]]", lambda *t: t[4] not in t[:4]),
    ("1 in x", lambda *t: 1 in t[:4]),
    ("1 not in x", lambda *t: 1 not in t[:4]),
    ("v + 1 in x", lambda *t: t[4] + 1 in t[:4]),
    ("v + 1 not in x", lambda *t: t[4] + 1 not in t[:4]),
    ("abs(v - 1) in x[:2]", lambda *t: abs(t[4] - 1) in t[:2]),
    ("x[0] in x[1:]", lambda *t: t[0] in t[1:4]),
])
def test_element_member(run, solver, request, constraint, predicate):
    # v in x (without index) holds iff v is equal to one variable of x
    if constraint in ("v in x", "v in {x[0], x[1], x[2], x[3]}", "v in [x[0], x[1], x[2], x[3]]", "v in (x[0], x[1], x[2], x[3])", "v + 1 in x"):  # element without index
        mark(request, solver, {"ACE": ACE_MEMBER, "CHOCO": CHOCO_MEMBER, "COSOCO": COSOCO_UNSUPPORTED_MEMBER})
    check(run, solver, "x = VarArray(size=4, dom=range(2))\nv = Var(dom=range(3))\n" + f"satisfy({constraint})", [range(2)] * 4 + [range(3)], predicate)


@pytest.mark.parametrize("constraint, predicate", [
    ("(v in x) | (v == 0)", lambda *t: t[4] in t[:4] or t[4] == 0),
    ("(v in x[:3]) | (v == 0)", lambda *t: t[4] in t[:3] or t[4] == 0),
    ("(v not in x) | (x[0] == 1)", lambda *t: t[4] not in t[:4] or t[0] == 1),
    ("(v in x) & (v != 0)", lambda *t: t[4] in t[:4] and t[4] != 0),
    ("(v + 1 in x) | (v == 2)", lambda *t: t[4] + 1 in t[:4] or t[4] == 2),
    ("(v in [x[0], x[1], 2]) | (v == 0)", lambda *t: t[4] in (t[0], t[1], 2) or t[4] == 0),
    ("imply(v == 2, belong(v, x))", lambda *t: t[4] != 2 or t[4] in t[:4]),
    ("imply(v == 0, not_belong(v, x))", lambda *t: t[4] != 0 or t[4] not in t[:4]),
    ("either(v == 0, belong(v, x))", lambda *t: t[4] == 0 or t[4] in t[:4]),
])
def test_element_member_in_logical_expressions(run, solver, request, constraint, predicate):
    # in a logical expression, member is the intension in(v,set(...)), whatever the number of variables (#288)
    if "not" not in constraint and "&" not in constraint:
        bug_for(request, "COSOCO", COSOCO_IN_SET)
    check(run, solver, "x = VarArray(size=4, dom=range(2))\nv = Var(dom=range(3))\n" + f"satisfy({constraint})", [range(2)] * 4 + [range(3)], predicate)


@pytest.mark.parametrize("constraint, predicate", [
    ("(v in y) | (v == 0)", lambda *t: t[6] in t[:6] or t[6] == 0),
    ("(v not in y) | (y[0] == 1)", lambda *t: t[6] not in t[:6] or t[0] == 1),
])
def test_element_member_of_many_variables_in_logical_expressions(run, solver, request, constraint, predicate):
    if "not" not in constraint:
        bug_for(request, "COSOCO", COSOCO_IN_SET)
    check(run, solver, "y = VarArray(size=6, dom=range(2))\nv = Var(dom=range(3))\n" + f"satisfy({constraint}, Sum(y) <= 2)", [range(2)] * 6 + [range(3)],
          lambda *t: predicate(*t) and sum(t[:6]) <= 2)


@pytest.mark.parametrize("constraint, predicate", [
    ("v in m", lambda *t: t[4] in t[:4]),
    ("v in [m[0], m[1]]", lambda *t: t[4] in t[:4]),
    ("v not in m", lambda *t: t[4] not in t[:4]),
    ("1 in m", lambda *t: 1 in t[:4]),
])
def test_element_member_of_a_two_dimensional_list(run, solver, request, constraint, predicate):
    # the variables of a two-dimensional list are considered (#287)
    if constraint in ("v in m", "v in [m[0], m[1]]"):  # an element without index
        mark(request, solver, {"ACE": ACE_MEMBER, "CHOCO": CHOCO_MEMBER, "COSOCO": COSOCO_UNSUPPORTED_MEMBER})
    check(run, solver, "m = VarArray(size=[2, 2], dom=range(2))\nv = Var(dom=range(3))\n" + f"satisfy({constraint})", [range(2)] * 4 + [range(3)], predicate)


@pytest.mark.parametrize("constraint", ["x[i] in x[1:]", "Sum(x[:2]) in x[2:]", "x[i] not in x[1:]", "Maximum(x[:2]) in (x[2], x[3])"])
def test_element_member_of_a_component(run, constraint):
    # the values of the condition of a component (element, sum, ...) are integers (#249): a component cannot be a member of a list of variables
    r = run("x = VarArray(size=4, dom=range(2))\ni = Var(dom=range(4))\n" + f"satisfy({constraint})")
    assert not r.ok and "must be integers" in r.stdout, r.report()


# ------------------------------------------------------------------------------------------------------------ objectives

@pytest.mark.parametrize("objective, function", [
    ("minimize(x[i])", lambda *t: t[t[3]]),
    ("maximize(x[i])", lambda *t: t[t[3]]),
    ("minimize(x[i] + v)", lambda *t: t[t[3]] + t[4]),
    ("maximize(x[i] * 2 - v)", lambda *t: t[t[3]] * 2 - t[4]),
    ("maximize(Sum(x[i], x[0]))", lambda *t: t[t[3]] + t[0]),
])
def test_element_as_objective(run, solver, objective, function):
    r = run(X3 + "satisfy(x[0] != x[1], x[1] != x[2], v != x[2])\n" + objective, solver=solver)
    assert_optimum(r, brute_force(DX, lambda *t: t[0] != t[1] and t[1] != t[2] and t[4] != t[2]), function, maximize=objective.startswith("maximize"))


@pytest.mark.parametrize("objective, function", [
    ("minimize(t[i])", lambda i, v: T[i]),
    ("maximize(t[i] - v)", lambda i, v: T[i] - v),
    ("maximize(t[i])", lambda i, v: T[i]),
])
def test_element_on_integers_as_objective(run, solver, objective, function):
    r = run(T4 + "satisfy(i != 0, v != 2)\n" + objective, solver=solver)
    assert_optimum(r, brute_force(DT, lambda i, v: i != 0 and v != 2), function, maximize=objective.startswith("maximize"))


@pytest.mark.parametrize("objective, function", [
    ("maximize(m[j][k])", lambda *t: mjk(t)),
    ("minimize(m[j][k] + v)", lambda *t: mjk(t) + t[8]),
    ("maximize(u[j][k])", lambda *t: ((1, 4, 2), (3, 0, 5))[t[6]][t[7]]),
])
def test_element_on_a_matrix_as_objective(run, solver, request, objective, function):
    if "m[j][k]" in objective:
        bug_for(request, "CHOCO", CHOCO_MATRIX)
    r = run(M23 + "u = cp_array([[1, 4, 2], [3, 0, 5]])\nsatisfy(m[0][0] != m[1][1], v != 1, k != 1)\n" + objective, solver=solver)
    assert_optimum(r, brute_force(DM, lambda *t: t[0] != t[4] and t[8] != 1 and t[7] != 1), function, maximize=objective.startswith("maximize"))


def test_element_on_identical_integers_as_objective(run, solver):
    # the element of identical integers is an objective as any element (#281)
    r = run("c = cp_array([2, 2, 2])\ni = Var(dom=range(3))\nv = Var(dom=range(5))\nsatisfy(v != 4)\nminimize(c[i] + v)", solver=solver)
    assert_optimum(r, brute_force([range(3), range(5)], lambda i, v: v != 4), lambda i, v: 2 + v)


# ------------------------------------------------------------------------------------------------ methods of components

@pytest.mark.parametrize("constraint, predicate", [
    ("x[i].among({1, 3})", lambda t: xi(t) in (1, 3)),
    ("x[i].is_in(range(1, 3))", lambda t: xi(t) in (1, 2)),
    ("x[i].not_among({1, 3})", lambda t: xi(t) not in (1, 3)),
    ("x[i].is_not_in([0])", lambda t: xi(t) != 0),
])
def test_element_methods(run, solver, request, constraint, predicate):
    mark(request, solver, {"x[i].is_in(range(1, 3))": {"CHOCO": CHOCO_INTERVAL, "COSOCO": COSOCO_IN_INTERVAL},
                           "x[i].not_among({1, 3})": {"COSOCO": COSOCO_NOTIN}, "x[i].is_not_in([0])": {"COSOCO": COSOCO_NOTIN}}.get(constraint, {}))
    check(run, solver, X3 + f"satisfy({constraint})", DX, lambda *t: predicate(t))


# ------------------------------------------------------------------------------------------------ rows of integers

@pytest.mark.parametrize("constraint, predicate", [
    ("r[k] == [v, w]", lambda k, v, w: [v, w] == [[1, 2], [3, 0]][k]),
    pytest.param("r[k] == (v, w)", lambda k, v, w: [v, w] == [[1, 2], [3, 0]][k], marks=bug(ROWS_TUPLE)),
    ("v in r[k]", lambda k, v, w: v in [[1, 2], [3, 0]][k]),
    ("r[k] == {v, w}", lambda k, v, w: sorted([v, w]) == sorted([[1, 2], [3, 0]][k])),
])
def test_element_on_rows_of_integers(run, solver, constraint, predicate):
    # a list of rows of integers indexed by a variable gives a row, compared with a list (or a set) of variables
    code = "r = cp_array([[1, 2], [3, 0]])\nk = Var(dom=range(2))\nv = Var(dom=range(4))\nw = Var(dom=range(4))\n"
    check(run, solver, code + f"satisfy({constraint})", [range(2), range(4), range(4)], predicate)


# ------------------------------------------------------------------------------------------------ examples of the doc

@pytest.mark.parametrize("code, solution", [
    ("x = VarArray(size=4, dom=range(5))\ni = Var(range(4))\nv = Var(range(5))\nsatisfy(x[i] == v, v == 3)", "x == [0, 0, 0, 3], i == 3, v == 3"),
    ("costs = cp_array([5, 3, 8, 2])\ni = Var(range(4))\nc = Var(range(10))\nsatisfy(costs[i] == c, c >= 6)", "i == 2, c == 8"),
    ("x = VarArray(size=4, dom=range(5))\ni = Var(range(3))\ny = Var(range(5))\nsatisfy(x[i] + y == 7, x[i + 1] != 0)", "x == [0, 0, 3, 1], i == 2, y == 4"),
    ("m = VarArray(size=[3, 3], dom=range(5))\ni = Var(range(3))\nj = Var(range(3))\nsatisfy(m[i][j] == 4)", "i == 2, j == 2, m[2][2] == 4"),
])
def test_element_api_examples(run, solver, code, solution):
    # the examples of the API page: the solution given is a solution
    r = run(code + f"\nsatisfy({solution})\nprint('result', solve(solver={solver}).name)")
    assert r.ok and "result SAT" in r.lines, r.report()


def test_element_api_example_on_integers(run, solver):
    # the solution given in the second example of the API page is the only one
    r = run("costs = cp_array([5, 3, 8, 2])\ni = Var(range(4))\nc = Var(range(10))\nsatisfy(costs[i] == c, c >= 6)", solver=solver)
    assert_solutions(r, {(2, 8)})


@pytest.mark.parametrize("code, n", [
    ("x = VarArray(size=4, dom=range(3))\ni = Var(range(4))\nv = Var(range(3))\nsatisfy(x[i] == v)", 324),
    ("x = VarArray(size=4, dom=range(3))\ni = Var(range(4))\nsatisfy(x[i] == 1)", 108),
    ("x = cp_array([2, 1, 0, 1])\ni = Var(range(4))\nv = Var(range(3))\nsatisfy(x[i] == v)", 4),
    ("x = VarArray(size=[3, 2], dom=range(4))\ni = Var(range(3))\nj = Var(range(2))\nsatisfy(x[i][j] == 1)", 6144),
    ("x = cp_array([[2, 1], [0, 1], [3, 2]])\ni = Var(range(3))\nj = Var(range(2))\nv = Var(range(4))\nsatisfy(x[i][j] == v)", 6),
])
def test_element_examples_of_the_constraint_pages(run, solver, request, code, n):
    # the numbers of solutions given in the pages Element and ElementMatrix
    if "x[i][j] == 1" in code:
        bug_for(request, "COSOCO", COSOCO_MATRIX_CONSTANT)
    r = run(code, solver=solver)
    assert r.ok and r.status == "SAT" and len(r.solutions) == n == len(set(r.solutions)), r.report()


@pytest.mark.parametrize("variant", ["", "-variant=aux1", "-variant=aux2"])
def test_element_example_with_an_index_outside_the_list(run, solver, variant):
    # the model TestElementIdx1 of the page Element: x[y] with y in -1..9 (-force_element_index needed without variant)
    code = ("x = VarArray(size=10, dom=range(6))\ny = Var(dom=range(-1, 10))\nif not variant():\n    satisfy(x[y] == 2)\nelif variant('aux1'):\n"
            "    satisfy((aux := Var()) == y, x[aux] == 2)\nelif variant('aux2'):\n    aux = Var()\n    satisfy(aux == y, x[aux] == 2)\n"
            "satisfy(x[a] == a % 6 for a in range(10))\n")
    args = (variant,) if variant else ("-force_element_index",)
    check(run, solver, code, [[a % 6] for a in range(10)] + [range(-1, 10)], lambda *t: t[10] in (2, 8), args=args)


IDX2 = ("x = Var(range(4))\nstart = cp_array([0, 2])\nif not variant():\n    satisfy(If(x >= 2, Then=start[x - 2] == 2))\nelif variant('aux1'):\n"
        "    satisfy(If(x >= 2, Then=[(y := Var()) == x - 2, start[y] == 2]))\nelse:\n    y = Var()\n    satisfy(If(x >= 2, Then=[y == x - 2, start[y] == 2]))")
IDX3 = ("x = Var(range(4))\nstart = cp_array([0, 2])\nif not variant():\n    satisfy(If(x < 2, Then=start[x] == 2))\nelif variant('aux1'):\n"
        "    satisfy(If(x < 2, Then=[(aux := Var()) == x, start[aux] == 2]))\nelse:\n    aux = Var()\n    satisfy(If(x < 2, Then=[aux == x, start[aux] == 2]))")


@pytest.mark.parametrize("code, expected", [(IDX2, {(0,), (1,), (3,)}), (IDX3, {(1,), (2,), (3,)})], ids=["TestElementIdx2", "TestElementIdx3"])
@pytest.mark.parametrize("variant", ["", "-variant=aux1", "-variant=aux2"])
def test_element_examples_in_a_conditional_structure(run, solver, request, code, expected, variant):
    # the models TestElementIdx2 and TestElementIdx3 of the page Element: an element in the part Then of If(), whose index can be outside
    # the list (-force_element_index needed without variant)
    if variant == "":
        request.applymarker(bug(LOGICAL_OUTSIDE))
    r = run(code, solver=solver, args=(variant,) if variant else ("-force_element_index",))
    if variant:  # the variable y (or aux) is free when x does not satisfy the condition of If(), so a value of x can be given several times
        assert r.ok and r.status == "SAT" and set(r.solutions) == expected, r.report()
    else:
        assert_solutions(r, expected)


# ------------------------------------------------------------------------------------------------------------ -mini

@pytest.mark.parametrize("code, domains, predicate", [
    (X3 + "satisfy(x[i] == v)", DX, lambda *t: xi(t) == t[4]),
    (X3 + "satisfy(x[i] < v)", DX, lambda *t: xi(t) < t[4]),
    (T4 + "satisfy(t[i] == v)", DT, lambda *t: ti(t) == t[1]),
    (M23 + "satisfy(m[j][k] == v)", DM, lambda *t: mjk(t) == t[8]),
    ("x = VarArray(size=4, dom=range(2))\nv = Var(dom=range(3))\nsatisfy(v not in x)", [range(2)] * 4 + [range(3)], lambda *t: t[4] not in t[:4]),
])
def test_element_with_mini(run, solver, request, code, domains, predicate):
    if "m[j][k]" in code:
        bug_for(request, "CHOCO", CHOCO_MATRIX)
    check(run, solver, code, domains, predicate, args=("-mini",))


# ------------------------------------------------------------------------------------------------------------ XCSP3 files

def _text(element):
    return " ".join(element.text.split()) if element is not None and element.text else None


@pytest.mark.parametrize("constraint, expected", [
    ("x[i] == v", ("x[]", "i", "v", None)),
    ("x[i] == 2", ("x[]", "i", "2", None)),
    ("v == x[i]", ("x[]", "i", "v", None)),
    ("x[i] != 2", ("x[]", "i", None, "(ne,2)")),
    ("x[i] < v", ("x[]", "i", None, "(lt,v)")),
    ("x[i] in {1, 3}", ("x[]", "i", None, "(in,{1,3})")),
    ("x[i] not in range(1, 3)", ("x[]", "i", None, "(notin,1..2)")),
    ("x[1:][j] == v", ("x[1] x[2]", "j", "v", None)),
    ("x[::2][j] == v", ("x[0] x[2]", "j", "v", None)),
    ("t[i] == v", ("3 0 2", "i", "v", None)),
])
def test_xcsp3_element(run, constraint, expected):
    r = run(X3 + "j = Var(dom=range(2))\nt = cp_array([3, 0, 2])\n" + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/element")
    assert c is not None and len(r.xml.find("constraints")) == 1, r.report()
    assert (_text(c.find("list")), _text(c.find("index")), _text(c.find("value")), _text(c.find("condition"))) == expected, r.report()
    assert c.find("list").get("startIndex") is None and c.find("index").get("rank") is None, r.report()


@pytest.mark.parametrize("constraint, expected", [
    ("t[i] == 0", "in(i,set(1,3))"),
    ("t[i] < 2", "in(i,set(1,3))"),
    ("t[i] in {0, 2}", "in(i,set(1,2,3))"),
    ("t[i] not in range(1, 3)", "in(i,set(0,1,3))"),
    ("t[i].is_not_in({3})", "in(i,set(1,2,3))"),
    ("t[i] == 3", "eq(i,0)"),
    ("t[i] > 2", "eq(i,0)"),
])
def test_xcsp3_element_on_integers_with_an_integer(run, constraint, expected):
    # XCSP3-core requires a variable in the condition of an element on integers: the element is a unary constraint on the index (#294)
    r = run(T4 + f"satisfy({constraint})")
    assert r.ok and r.xml.find("constraints/element") is None and _text(r.xml.find("constraints/intension")) == expected, r.report()


def test_xcsp3_element_on_integers_with_an_integer_with_mini(run):
    # in the mini-tracks, 'in' is not a primitive form of intension: a unary table is posted
    r = run(T4 + "satisfy(t[i] < 2)", args=("-mini",))
    assert r.ok and r.xml.find("constraints/element") is None, r.report()
    c = r.xml.find("constraints/extension")
    assert c is not None and (_text(c.find("list")), _text(c.find("supports"))) == ("i", "1 3"), r.report()


@pytest.mark.parametrize("constraint, expected", [
    ("m[j][k] == v", ("m[][]", "j k", "v")),
    ("m[j, k] == 1", ("m[][]", "j k", "1")),
    ("t[j][k] == v", ("(1,2,3)(4,5,6)", "j k", "v")),
])
def test_xcsp3_element_on_a_matrix(run, constraint, expected):
    r = run(M23 + "t = cp_array([[1, 2, 3], [4, 5, 6]])\n" + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/element")
    assert c is not None and (_text(c.find("matrix")), _text(c.find("index")), _text(c.find("value"))) == expected, r.report()


@pytest.mark.parametrize("constraint, expected", [
    ("m[j][0] == v", "m[0][0] m[1][0]"),
    ("m[1][k] == v", "m[1][]"),
    ("m[:, 2][j] == v", "m[0][2] m[1][2]"),
])
def test_xcsp3_element_on_a_row_or_a_column(run, constraint, expected):
    r = run(M23 + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/element")
    assert c is not None and _text(c.find("list")) == expected and c.find("matrix") is None, r.report()


def test_xcsp3_element_member(run):
    # v in x (x having at least 4 variables) gives an element without index
    r = run("x = VarArray(size=4, dom=range(2))\nv = Var(dom=range(3))\nsatisfy(v in x)")
    assert r.ok, r.report()
    c = r.xml.find("constraints/element")
    assert c is not None and (_text(c.find("list")), c.find("index"), _text(c.find("value"))) == ("x[]", None, "v"), r.report()


@pytest.mark.parametrize("constraint", ["v in x", "v in x[:2]", "v in [x[0], 2]"])
def test_element_member_with_mini(run, constraint):
    # in the mini-tracks, the element <index> is necessarily present, and the only forms of intension are primitive: member is refused (#289)
    r = run("x = VarArray(size=4, dom=range(2))\nv = Var(dom=range(3))\n" + f"satisfy({constraint})", args=("-mini",))
    assert not r.ok and "is not accepted in the mini-tracks" in r.stdout, r.report()


@pytest.mark.parametrize("objective", ["maximize(m[j][k])", "minimize(t[j][k])", "maximize(m[j, k])", "maximize(m[j][k] + v)"])
def test_xcsp3_element_on_a_matrix_as_objective(run, objective):
    # there is no objective of type element in XCSP3: the element is replaced by an auxiliary variable (#290)
    r = run(M23 + "t = cp_array([[1, 2, 3], [4, 5, 6]])\n" + objective)
    assert r.ok, r.report()
    o = r.xml.find("objectives")[0]
    assert o.get("type") in (None, "expression") and o.find("matrix") is None, r.report()


def test_xcsp3_element_with_an_expression_as_index(run):
    r = run("x = VarArray(size=3, dom=range(3))\nj = Var(dom=range(2))\nsatisfy(x[j + 1] == 2)")
    assert r.ok, r.report()
    c = r.xml.find("constraints/element")
    assert c is not None and _text(c.find("index")) == "aux_gb[0]", r.report()


def test_xcsp3_element_in_a_group(run):
    r = run("x = VarArray(size=3, dom=range(3))\ny = VarArray(size=3, dom=range(3))\nsatisfy(y[x[a]] == a for a in range(3))")
    assert r.ok, r.report()
    assert r.xml.find("constraints/group/element") is not None and len(r.xml.findall("constraints/group/args")) == 3, r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("constraint", [
    "x[i] == None",
    "x[i] == 'a'",
    "x[i] == 2.5",
    "x[i] == True",
    pytest.param("x[i] == [1, 2]", marks=bug(INVALID)),
    "x[i] == {1: 2}",
    pytest.param("x[i]", marks=bug(INVALID)),
    pytest.param("t[i]", marks=bug(INVALID)),
    pytest.param("x[i] == s[0]", marks=bug(INVALID)),
    "s[i] == 'a'",
    pytest.param("x[s[0]] == 2", marks=bug(INVALID)),
    pytest.param("x[2.5] == 2", marks=bug(INVALID)),
    "x[:0][i] == 2",
    "[x[0], x[1]][i] == 2",
    "(x[0], x[1])[i] == 2",
    "cp_array(['a', 'b', 'c'])[i] == 2",
    "cp_array([True, False, True])[i] == v",
    "m[i][i][i] == 2",
    "m[i][i][0] == 2",
    "x[i] in {y, 2}",
    "x[i][0] == 2",
])
def test_invalid_element(run, constraint):
    code = X3 + "t = cp_array([3, 0, 2])\ns = VarArray(size=3, dom={'a', 'b'})\ny = Var(dom=range(3))\nm = VarArray(size=[3, 3, 3], dom=range(3))\n"
    assert_fails(run(code + f"satisfy({constraint})"))


@pytest.mark.parametrize("constraint, message", [
    ("x[:0][i] == 2", "A constraint Element on an empty list of variables is encountered"),
    pytest.param("x[i]", "is not a constraint: it must be subject to a condition", marks=bug(INVALID)),
    pytest.param("t[i]", "is not a constraint: it must be subject to a condition", marks=bug(INVALID)),
    ("x[i] in {y, 2}", "must be integers, which is not the case of y"),
])
def test_invalid_element_message(run, constraint, message):
    r = run(X3 + "t = cp_array([3, 0, 2])\ny = Var(dom=range(3))\n" + f"satisfy({constraint})")
    assert not r.ok and message in r.stdout, r.report()


@pytest.mark.parametrize("constraint", ["~(x[i] in {1, 3})", "~(v in x)"])
def test_element_negated_with_in(run, constraint):
    # ~ cannot be applied to an expression with 'in' (evaluated as a Boolean by Python): 'not in' must be used instead
    r = run(X3 + f"satisfy({constraint})")
    assert not r.ok and "write 'not in' instead" in r.stdout, r.report()
