"""
Tests of the constraint NValues of the section Constraints (Global) of the API (https://pycsp.org/documentation/api/constraints-global/#NValues):
the functions NValues() and NumberDistinctValues() (an alias), which build a component that becomes a constraint nValues when compared with a value,
a variable, an expression, an interval or a set (or when given the parameter condition), with the parameter excepting, on variables and on
expressions, as a term of expressions, in groups of constraints, in logical expressions and in objectives.
The function NotAllEqual(), which posts NValues(...) > 1, is tested in test_constraints_global_notallequal.py.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
According to XCSP3-core, nValues(X, E, (op, k)) holds iff |{x : x in X} \\ E| satisfies (op, k), with |X| >= 2 and E a list of integers (possibly
absent, but not empty), and expressions being accepted instead of variables in X (generalized form). An objective of type nValues has no element
<except>. As decided for NotAllEqual (#134), PyCSP3 keeps once each term given several times; the option -mini has nothing to do for NValues
(#133: nValues is not part of the mini-tracks).
"""

import re

import pytest

from harness import assert_fails, assert_optimum, assert_solutions, brute_force, bug, bug_for, declared_variables

# Known bugs (each bug is reported in the issue given at the start of its reason)
ACE_EQ = ("xcsp3team/ACE#26: ACE gives wrong solutions for nValues with the condition (eq,k), 1 < k < |X|, and fails when the variables have "
          "different types of domains")
ACE_LIMIT = ("xcsp3team/ACE#28: ACE fails without message on nValues when the limit k is not in 1..|X| (control(1 <= k && k <= list.length) "
             "in the constructor of NValuesCst), although the instance is valid")
PARSER_EXCEPT = ("xcsp3team/XCSP3-Java-Tools#23: the parser of ACE and CHOCO (CtrLoaderInteger.nValues()) ignores the element <except> "
                 "when the list contains expressions")
CHOCO_LIMIT = ("CHOCO 4.10.15-beta (embedded in PyCSP3) finds solutions several times with nValues and the conditions le, ne, ge, gt, and wrong "
               "solutions with ne (the limit variable built by condToVar() is not determined by the list); fixed since CHOCO 5.0.0 (checked with "
               "6.0.2), so not reported")
CHOCO_DUPLICATES = "chocoteam/choco-solver#1248 (section 5): CHOCO finds solutions several times with nValues on expressions"
COSOCO_UNSORTED_SET = "xcsp3team/cosoco#94: cosoco crashes (segmentation fault) on (in,set) when the values of the set are not in increasing order"
EMPTY_SUPPORTS = ("(to be reported) ACE and CHOCO fail on a table with an empty set of supports, recognized as false by the parser "
                  "(buildCtrFalse(): RuntimeException: Constraint with only conflicts)")
OBJ_EXCEPT = "#215: an objective NValues(..., excepting=...) is written with an element <except>, which objectives do not have in XCSP3"
ONE_TERM = "#216: a constraint nValues on a single term is posted (XCSP3 requires at least two terms)"
NO_TERM_CONDITION = "#217: NValues() on no term ignores the parameter condition: the constraint is always false"
EXCEPTING = ("#218: excepting: an empty collection gives an empty element <except>, a range is refused, a Boolean is accepted, a value given "
             "several times is accepted")
CONSTANT_OBJECTIVE = "#221: the objective is a constant, reported by TypeError: Wrong type for Dummy"
NEGATED_MEMBERSHIP = "#222: ~(e in S) fails with AssertionError: non authorized type -2, instead of an explicit message"

# The cases that a solver says it does not handle, and the symbolic variables (not reported)
CHOCO_EXCEPT = "CHOCO does not handle nValues with except (Missing Implementation: buildCtrNValuesExcept)"
COSOCO_EXCEPT = "cosoco does not handle nValues with except (s UNSUPPORTED)"
CHOCO_IN = "CHOCO does not handle nValues with the conditions in and notin (Missing Implementation: buildCtrNValues)"
COSOCO_CONDITION = ("cosoco does not handle nValues with the condition ne, nor with a variable as limit with another operator than eq "
                    "(Such nValues constraint Not yes supported)")
COSOCO_MAXIMIZE = "cosoco does not handle the objective maximize of type nValues (Objective expression not yet supported, s UNSUPPORTED)"
COSOCO_EXPRESSIONS = "cosoco does not handle nValues on expressions (s UNSUPPORTED)"
SYMBOLIC = "nValues on symbolic variables is not part of XCSP3-core (ACE and CHOCO fail, cosoco has no symbolic variables)"


def skip_except(solver):
    """Skips the test for CHOCO and cosoco, which say that they do not handle nValues with except."""
    if solver in ("CHOCO", "COSOCO"):
        pytest.skip(CHOCO_EXCEPT if solver == "CHOCO" else COSOCO_EXCEPT)


def nv(t, excepting=()):
    """Returns the number of distinct values of the tuple t, the values of excepting being ignored."""
    return len(set(t) - set(excepting))


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


def n_terms(text):
    """Returns the number of terms of the specified list of an XCSP3 file, a compact form x[i..j] standing for j - i + 1 variables, and x[] for 4."""
    m = [re.fullmatch(r"\w+\[(\d+)\.\.(\d+)\]", t) for t in text.split()]
    return sum(int(r.group(2)) - int(r.group(1)) + 1 if r else 4 if t.endswith("[]") else 1 for r, t in zip(m, text.split()))


X4 = "x = VarArray(size=4, dom=range(3))\n"
D4 = [range(3)] * 4


# ------------------------------------------------------------------------------------------------------------ conditions

@pytest.mark.parametrize("condition, predicate", [
    ("== 1", lambda n: n == 1),
    ("== 2", lambda n: n == 2),
    ("== 3", lambda n: n == 3),
    ("!= 2", lambda n: n != 2),
    ("< 2", lambda n: n < 2),
    ("<= 2", lambda n: n <= 2),
    ("> 2", lambda n: n > 2),
    (">= 2", lambda n: n >= 2),
    ("in range(2, 4)", lambda n: 2 <= n <= 3),
    ("in {1, 3}", lambda n: n in (1, 3)),
    ("in [1, 3]", lambda n: n in (1, 3)),
    ("in {2}", lambda n: n == 2),
    ("not in range(2, 4)", lambda n: not 2 <= n <= 3),
    ("not in {1, 3}", lambda n: n not in (1, 3)),
    ("not in [2]", lambda n: n != 2),
])
def test_nvalues_conditions(run, solver, request, condition, predicate):
    if solver == "CHOCO" and " in " in f" {condition}":
        pytest.skip(CHOCO_IN)
    if solver == "COSOCO" and condition.startswith("!="):
        pytest.skip(COSOCO_CONDITION)
    if condition in ("== 2", "== 3"):
        bug_for(request, "ACE", ACE_EQ)
    if condition in ("!= 2", "<= 2"):
        bug_for(request, "CHOCO", CHOCO_LIMIT)
    check(run, solver, X4 + f"satisfy(NValues(x) {condition})", D4, lambda *t: predicate(nv(t)))


@pytest.mark.parametrize("condition, predicate", [
    ("== 0", lambda n: False),
    ("== 5", lambda n: False),
    ("== -1", lambda n: False),
    ("!= 0", lambda n: True),
    (">= 1", lambda n: True),
    ("<= 4", lambda n: True),
    ("> 4", lambda n: False),
    ("< 1", lambda n: False),
    ("in range(5, 9)", lambda n: False),
    ("not in range(5, 9)", lambda n: True),
    ("in {0, 5}", lambda n: False),
])
def test_nvalues_with_an_unreachable_condition(run, solver, request, condition, predicate):
    # the number of distinct values of 4 terms is between 1 and 4
    if solver == "CHOCO" and " in " in f" {condition}":
        pytest.skip(CHOCO_IN)
    if solver == "COSOCO" and condition.startswith("!="):
        pytest.skip(COSOCO_CONDITION)
    if condition in ("== 0", "== 5", "== -1", "> 4", "< 1"):
        bug_for(request, "ACE", ACE_LIMIT)
    if condition in ("!= 0", ">= 1", "<= 4"):
        bug_for(request, "CHOCO", CHOCO_LIMIT)
    check(run, solver, X4 + f"satisfy(NValues(x) {condition}, x[0] != 1)", D4, lambda *t: predicate(nv(t)) and t[0] != 1)


@pytest.mark.parametrize("constraint, predicate", [
    ("NValues(x) in set()", lambda n: False),
    ("NValues(x) in range(0)", lambda n: False),
    ("NValues(x) not in set()", lambda n: True),
    ("NValues(x) not in range(0)", lambda n: True),
])
def test_nvalues_with_an_empty_condition(run, solver, request, constraint, predicate):
    if not predicate(1):
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)  # the constraint false, posted by a table with an empty set of supports
    check(run, solver, X4 + f"satisfy({constraint}, x[0] != 1)", D4, lambda *t: predicate(nv(t)) and t[0] != 1)


@pytest.mark.parametrize("constraint, predicate", [
    ("2 == NValues(x)", lambda n: n == 2),
    ("2 <= NValues(x)", lambda n: n >= 2),
    ("2 > NValues(x)", lambda n: n < 2),
    ("2 != NValues(x)", lambda n: n != 2),
])
def test_nvalues_on_the_right(run, solver, request, constraint, predicate):
    if solver == "COSOCO" and "!=" in constraint:
        pytest.skip(COSOCO_CONDITION)
    if constraint == "2 == NValues(x)":
        bug_for(request, "ACE", ACE_EQ)
    if constraint == "2 != NValues(x)":
        bug_for(request, "CHOCO", CHOCO_LIMIT)
    check(run, solver, X4 + f"satisfy({constraint})", D4, lambda *t: predicate(nv(t)))


@pytest.mark.parametrize("operand, predicate", [
    ("== x[3]", lambda n, v: n == v),
    ("!= x[3]", lambda n, v: n != v),
    ("< x[3]", lambda n, v: n < v),
    ("<= x[3]", lambda n, v: n <= v),
    ("> x[3]", lambda n, v: n > v),
    (">= x[3]", lambda n, v: n >= v),
    ("== x[3] + 1", lambda n, v: n == v + 1),
    ("== abs(x[3] - 1)", lambda n, v: n == abs(v - 1)),
])
def test_nvalues_compared_with_a_variable_or_an_expression(run, solver, request, operand, predicate):
    if solver == "COSOCO" and not operand.startswith("=="):
        pytest.skip(COSOCO_CONDITION)
    if operand in ("!= x[3]", "<= x[3]", "> x[3]", ">= x[3]"):
        bug_for(request, "CHOCO", CHOCO_LIMIT)
    check(run, solver, X4 + f"satisfy(NValues(x[:3]) {operand})", D4, lambda a, b, c, d: predicate(nv((a, b, c)), d))


@pytest.mark.parametrize("constraint, predicate", [
    ("NValues(x[:2]) == NValues(x[2:])", lambda a, b, c, d: nv((a, b)) == nv((c, d))),
    ("NValues(x[:3]) > NValues(x[2:]) + 1", lambda a, b, c, d: nv((a, b, c)) > nv((c, d)) + 1),
    ("NValues(x) == Sum(x[:2])", lambda a, b, c, d: nv((a, b, c, d)) == a + b),
    ("NValues(x) == Count(x, value=0)", lambda *t: nv(t) == t.count(0)),
    ("NValues(x) == NValues(x)", lambda *t: True),
])
def test_nvalues_compared_with_a_nvalues_a_sum_or_a_count(run, solver, constraint, predicate):
    if solver == "COSOCO" and ">" in constraint:
        pytest.skip(COSOCO_CONDITION)
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


@pytest.mark.parametrize("condition, predicate", [
    ("('le', 2)", lambda n: n <= 2),
    ("['ge', 3]", lambda n: n >= 3),
    ("('<=', 2)", lambda n: n <= 2),
    ("('!=', 2)", lambda n: n != 2),
    ("('eq', 1)", lambda n: n == 1),
    ("('in', {1, 3})", lambda n: n in (1, 3)),
    ("('notin', {1, 3})", lambda n: n not in (1, 3)),
    ("('in', range(2, 4))", lambda n: 2 <= n <= 3),
])
def test_nvalues_with_the_parameter_condition(run, solver, request, condition, predicate):
    if solver == "CHOCO" and "in" in condition:
        pytest.skip(CHOCO_IN)
    if solver == "COSOCO" and "!=" in condition:
        pytest.skip(COSOCO_CONDITION)
    if condition in ("('le', 2)", "('<=', 2)", "('!=', 2)"):
        bug_for(request, "CHOCO", CHOCO_LIMIT)
    check(run, solver, X4 + f"satisfy(NValues(x, condition={condition}))", D4, lambda *t: predicate(nv(t)))


def test_nvalues_with_the_parameter_condition_on_a_variable(run, solver):
    check(run, solver, X4 + "satisfy(NValues(x[:3], condition=('eq', x[3])))", D4, lambda a, b, c, d: nv((a, b, c)) == d)


@pytest.mark.parametrize("condition", ["{3, 1}", "{-1, 3}", "{3, 2, 1}"])
def test_nvalues_in_a_set_given_in_any_order(run, solver, request, condition):
    # the values of the set may be written in the order of Python, which is not always the increasing order (here, {-1, 3} is written {3,-1})
    if solver == "CHOCO":
        pytest.skip(CHOCO_IN)
    if condition == "{-1, 3}":
        bug_for(request, "COSOCO", COSOCO_UNSORTED_SET)
    check(run, solver, X4 + f"satisfy(NValues(x) in {condition})", D4, lambda *t: nv(t) in eval(condition))


# ------------------------------------------------------------------------------------------------------------ excepting

@pytest.mark.parametrize("excepting, values", [
    ("0", (0,)),
    ("2", (2,)),
    ("[0, 1]", (0, 1)),
    ("{0, 1}", (0, 1)),
    ("(0, 1)", (0, 1)),
    ("[0, 1, 2]", (0, 1, 2)),
    ("[[0], [1]]", (0, 1)),
    ("{2, 0}", (0, 2)),
    ("-1", (-1,)),
    ("7", (7,)),
    ("[-1, 1]", (-1, 1)),
])
@pytest.mark.parametrize("condition, predicate", [
    ("== 1", lambda n: n == 1),
    ("== 0", lambda n: n == 0),
    ("<= 1", lambda n: n <= 1),
    (">= 2", lambda n: n >= 2),
    ("!= 1", lambda n: n != 1),
])
def test_nvalues_excepting(run, solver, excepting, values, condition, predicate):
    skip_except(solver)
    check(run, solver, X4 + f"satisfy(NValues(x, excepting={excepting}) {condition})", D4, lambda *t: predicate(nv(t, values)))


@pytest.mark.parametrize("excepting, values", [
    ("range(2)", (0, 1)),
    ("range(0, 3, 2)", (0, 2)),
    ("frozenset({0, 1})", (0, 1)),
    ("[]", ()),
    ("()", ()),
    ("set()", ()),
    ("None", ()),
])
def test_nvalues_excepting_given_by_a_range_or_an_empty_collection(run, solver, request, excepting, values):
    if values:
        skip_except(solver)
    if excepting.startswith("range"):
        request.applymarker(bug(EXCEPTING))  # refused
    elif not values and excepting != "None":
        bug_for(request, ("ACE", "CHOCO"), EXCEPTING)  # an empty element <except>, on which ACE and CHOCO fail
    check(run, solver, X4 + f"satisfy(NValues(x, excepting={excepting}) == 1)", D4, lambda *t: nv(t, values) == 1)


@pytest.mark.parametrize("excepting", ["[]", "()", "set()", "None"])
def test_xcsp3_nvalues_with_an_empty_excepting(run, request, excepting):
    # XCSP3 requires at least one value in the element <except>: an empty collection means no value to ignore
    if excepting != "None":
        request.applymarker(bug(EXCEPTING))
    r = run(X4 + f"satisfy(NValues(x, excepting={excepting}) == 1)")
    assert r.ok, r.report()
    e = r.xml.find("constraints/nValues/except")
    assert e is None or (e.text or "").split(), r.report()


def test_nvalues_excepting_with_the_parameter_condition(run, solver):
    skip_except(solver)
    check(run, solver, X4 + "satisfy(NValues(x, excepting=0, condition=('le', 1)))", D4, lambda *t: nv(t, (0,)) <= 1)


def test_nvalues_excepting_compared_with_a_variable(run, solver):
    skip_except(solver)
    check(run, solver, X4 + "satisfy(NValues(x[:3], excepting=0) == x[3])", D4, lambda a, b, c, d: nv((a, b, c), (0,)) == d)


def test_nvalues_excepting_on_a_matrix(run, solver):
    skip_except(solver)
    check(run, solver, "m = VarArray(size=[2, 2], dom=range(3))\nsatisfy(NValues(m, excepting=0) == 1)", [range(3)] * 4, lambda *t: nv(t, (0,)) == 1)


# ------------------------------------------------------------------------------------------------------------ forms

@pytest.mark.parametrize("terms", [
    "x",
    "x[0], x[1], x[2], x[3]",
    "[x[0], x[1]], x[2], [x[3]]",
    "x[:2], x[2:]",
    "(x[i] for i in range(4))",
    "tuple(x)",
    "[[x[0], x[1]], [x[2], x[3]]]",
    "x[::-1]",
    "x, x[0]",
])
def test_nvalues_forms(run, solver, terms):
    check(run, solver, X4 + f"satisfy(NValues({terms}) >= 3)", D4, lambda *t: nv(t) >= 3)


@pytest.mark.parametrize("constraint, predicate", [
    ("NumberDistinctValues(x) <= 2", lambda *t: nv(t) <= 2),
    ("NumberDistinctValues(x, excepting=0) == 1", lambda *t: nv(t, (0,)) == 1),
    ("NumberDistinctValues(x[0], x[1], x[2]) != 1", lambda a, b, c, d: nv((a, b, c)) != 1),
    ("NumberDistinctValues(x, condition=('ge', 3))", lambda *t: nv(t) >= 3),
])
def test_number_distinct_values(run, solver, request, constraint, predicate):
    if "excepting" in constraint:
        skip_except(solver)
    if solver == "COSOCO" and "!=" in constraint:
        pytest.skip(COSOCO_CONDITION)
    if "<=" in constraint or "!=" in constraint:
        bug_for(request, "CHOCO", CHOCO_LIMIT)
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


@pytest.mark.parametrize("n, d, k", [(2, 2, 1), (2, 3, 2), (3, 3, 1), (5, 2, 2), (2, 5, 1), (3, 4, 3)])
def test_nvalues_sizes(run, solver, request, n, d, k):
    if 1 < k < n:
        bug_for(request, "ACE", ACE_EQ)
    check(run, solver, f"x = VarArray(size={n}, dom=range({d}))\nsatisfy(NValues(x) == {k})", [range(d)] * n, lambda *t: nv(t) == k)


@pytest.mark.parametrize("n, condition, predicate", [
    (2, "!= 1", lambda n: n != 1),
    (2, "== 2", lambda n: n == 2),
    (2, ">= 2", lambda n: n >= 2),
    (2, "<= 1", lambda n: n <= 1),
    (2, "< 2", lambda n: n < 2),
    (3, "!= 1", lambda n: n != 1),
    (3, "!= 2", lambda n: n != 2),
])
def test_nvalues_on_few_variables(run, solver, request, n, condition, predicate):
    if condition.startswith("!="):
        if solver == "COSOCO":
            pytest.skip(COSOCO_CONDITION)
        bug_for(request, "CHOCO", CHOCO_LIMIT)
    check(run, solver, f"x = VarArray(size={n}, dom=range(3))\nsatisfy(NValues(x) {condition})", [range(3)] * n, lambda *t: predicate(nv(t)))


def test_nvalues_on_a_matrix(run, solver, request):
    bug_for(request, "CHOCO", CHOCO_LIMIT)
    check(run, solver, "m = VarArray(size=[2, 2], dom=range(3))\nsatisfy(NValues(m) <= 2)", [range(3)] * 4, lambda *t: nv(t) <= 2)


def test_nvalues_on_an_array_with_holes(run, solver, request):
    bug_for(request, "CHOCO", CHOCO_LIMIT)
    r = run("x = VarArray(size=4, dom=lambda i: None if i == 1 else range(3))\nsatisfy(NValues(x) <= 2)", solver=solver)
    assert r.variables == ["x[0]", "x[2]", "x[3]"]
    assert_solutions(r, brute_force([range(3)] * 3, lambda *t: nv(t) <= 2))


def test_nvalues_on_variables_of_arrays_and_simple_variables(run, solver):
    check(run, solver, "x = VarArray(size=2, dom=range(3))\nz = Var(range(3))\ny = VarArray(size=2, dom=range(3))\nsatisfy(NValues(x, z, y) >= 4)",
          [range(3)] * 5, lambda *t: nv(t) >= 4)


@pytest.mark.parametrize("dom, domains, condition, predicate", [
    ("lambda i: {i, 2}", [{0, 2}, {1, 2}, {2}], "<= 2", lambda n: n <= 2),
    ("lambda i: range(i, 3)", [range(0, 3), range(1, 3), range(2, 3)], "<= 2", lambda n: n <= 2),
    ("lambda i: {i}", [{0}, {1}, {2}], "<= 2", lambda n: n <= 2),
    ("lambda i: {0, 5} if i == 0 else range(3)", [{0, 5}, range(3), range(3)], ">= 3", lambda n: n >= 3),
    ("lambda i: {i, 2}", [{0, 2}, {1, 2}, {2}], "== 2", lambda n: n == 2),
    ("lambda i: range(i, 3)", [range(0, 3), range(1, 3), range(2, 3)], "== 2", lambda n: n == 2),
    ("lambda i: {0, 1} if i == 0 else range(3)", [{0, 1}, range(3), range(3)], "== 2", lambda n: n == 2),
], ids=["a common value", "intervals", "no common value", "a value out of the others", "a common value eq", "intervals eq", "a 01 variable eq"])
def test_nvalues_on_different_domains(run, solver, request, dom, domains, condition, predicate):
    if condition == "== 2":
        bug_for(request, "ACE", ACE_EQ)
    if condition == "<= 2" and any(len(d) > 1 for d in domains):
        bug_for(request, "CHOCO", CHOCO_LIMIT)
    check(run, solver, f"x = VarArray(size=3, dom={dom})\nsatisfy(NValues(x) {condition})", domains, lambda *t: predicate(nv(t)))


def test_nvalues_on_negative_values(run, solver):
    skip_except(solver)
    check(run, solver, "x = VarArray(size=3, dom=range(-2, 1))\nsatisfy(NValues(x, excepting=-1) <= 1)", [range(-2, 1)] * 3,
          lambda *t: nv(t, (-1,)) <= 1)


def test_nvalues_on_symbolic_variables(run, solver):
    pytest.skip(SYMBOLIC)
    check(run, solver, "x = VarArray(size=3, dom={'a', 'b'})\nsatisfy(NValues(x) == 2)", [["a", "b"]] * 3, lambda *t: nv(t) == 2)


# ------------------------------------------------------------------------------------------------------------ expressions

EXPRESSIONS = [
    ("NValues(x[0] + 1, x[1] + 1, x[2] + 1) <= 2", lambda a, b, c, d: nv((a, b, c)) <= 2),
    ("NValues(x[0], x[1] + 1, x[2]) >= 3", lambda a, b, c, d: nv((a, b + 1, c)) >= 3),
    ("NValues(x[0] > 0, x[1] > 1, x[2] == 2) == 1", lambda a, b, c, d: nv((a > 0, b > 1, c == 2)) == 1),
    ("NValues([x[i] + i for i in range(4)]) <= 2", lambda *t: nv([v + i for i, v in enumerate(t)]) <= 2),
    ("NValues(x[0] * 2, x[1], abs(x[2] - x[3])) == 1", lambda a, b, c, d: nv((a * 2, b, abs(c - d))) == 1),
    ("NValues(x[0] + 1, x[1] + 1, excepting=1) == 1", lambda a, b, c, d: nv((a + 1, b + 1), (1,)) == 1),
    ("NValues(x[0] + 1, x[1], x[2], excepting=[1, 2]) <= 1", lambda a, b, c, d: nv((a + 1, b, c), (1, 2)) <= 1),
    ("NValues(x[0] + x[1], x[2] + x[3]) != 1", lambda a, b, c, d: a + b != c + d),
]



@pytest.mark.parametrize("constraint, predicate", EXPRESSIONS)
def test_nvalues_on_expressions(run, solver, request, constraint, predicate):
    if solver == "COSOCO":
        pytest.skip(COSOCO_EXPRESSIONS)
    if constraint == "NValues(x[0] + 1, x[1] + 1, x[2] + 1) <= 2":
        bug_for(request, "CHOCO", CHOCO_DUPLICATES)
    if constraint == "NValues(x[0] + x[1], x[2] + x[3]) != 1":
        bug_for(request, "CHOCO", CHOCO_LIMIT)
    if "excepting" in constraint:
        bug_for(request, ("ACE", "CHOCO"), PARSER_EXCEPT)
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


@pytest.mark.parametrize("constraint, predicate", [
    ("NValues(Sum(x[:2]), x[2], x[3]) <= 2", lambda a, b, c, d: nv((a + b, c, d)) <= 2),
    ("NValues(Maximum(x[:2]), Minimum(x[2:]), x[0]) == 1", lambda a, b, c, d: nv((max(a, b), min(c, d), a)) == 1),
    ("NValues(Count(x, value=0), x[0], x[1]) == 1", lambda a, b, c, d: nv(([a, b, c, d].count(0), a, b)) == 1),
    ("NValues(NValues(x[:2]), x[2], x[3]) == 1", lambda a, b, c, d: nv((nv((a, b)), c, d)) == 1),
])
def test_nvalues_on_components(run, solver, request, constraint, predicate):
    # a component (Sum, Maximum, Count, ...) among the terms is replaced by an auxiliary variable
    if "<=" in constraint:
        bug_for(request, "CHOCO", CHOCO_LIMIT)
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


# ------------------------------------------------------------------------------------------------ degenerated cases

@pytest.mark.parametrize("constraint, predicate", [
    ("NValues(x[0]) == 1", lambda a: True),
    ("NValues(x[0]) == 2", lambda a: False),
    ("NValues(x[0]) >= 1", lambda a: True),
    ("NValues([x[0]]) != 1", lambda a: False),
    pytest.param("NValues(x[0], excepting=0) == 1", lambda a: a != 0, marks=bug(ONE_TERM)),
    pytest.param("NValues(x[0], excepting=0) == 0", lambda a: a == 0, marks=bug(ONE_TERM)),
    pytest.param("NValues([x[0]], excepting=[0, 1]) >= 1", lambda a: a == 2, marks=bug(ONE_TERM)),
    ("NValues(x[0], condition=('eq', 1))", lambda a: True),
    ("NValues(x[0], condition=('eq', 2))", lambda a: False),
    pytest.param("NValues(x[0], excepting=0, condition=('eq', 0))", lambda a: a == 0, marks=bug(ONE_TERM)),
    ("NValues(x[0] + 1) == 1", lambda a: True),
    pytest.param("NValues(x[0] + 1, excepting=1) == 1", lambda a: a != 0, marks=bug(ONE_TERM)),
])
def test_nvalues_on_a_single_term(run, solver, request, constraint, predicate):
    # the number of distinct values of a single term t is 1, or (t not in E) with excepting=E
    if "== 2" in constraint or "!= 1" in constraint:
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)
    if "('eq', 2)" in constraint:
        bug_for(request, "ACE", ACE_LIMIT)  # a constraint nValues on the single term x[0] is posted
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: predicate(t[0]) and t[3] != 1)


@pytest.mark.parametrize("constraint", [
    "NValues(x[0]) == 1",
    "NValues(x[0], excepting=0) == 1",
    "NValues([x[0]], excepting=[0, 1]) >= 1",
    "NValues(x[0], condition=('eq', 1))",
    "NValues(x[0], excepting=0, condition=('eq', 0))",
    "NValues(x[0], x[0], excepting=0) == 1",
    "NValues(x[0], x[0], condition=('le', 1))",
    "NValues(x[0] + 1, excepting=1) == 1",
])
def test_xcsp3_nvalues_has_at_least_two_terms(run, request, constraint):
    # XCSP3-core requires |X| >= 2
    if "excepting" in constraint or "condition" in constraint:
        request.applymarker(bug(ONE_TERM))
    r = run(X4 + f"satisfy({constraint}, x[3] != 1)")
    assert r.ok, r.report()
    for c in r.xml.iter("nValues"):
        assert n_terms(c.find("list").text) >= 2, constraint + "\n" + r.report()


@pytest.mark.parametrize("constraint, holds", [
    ("NValues([]) == 0", True),
    ("NValues([]) >= 1", False),
    ("NValues([]) <= 2", True),
    ("NValues([]) != 0", False),
    ("NValues([]) in {0, 3}", True),
    ("NValues([], excepting=0) == 0", True),
    ("NValues([], x[3]) == 1", None),
    pytest.param("NValues([], condition=('eq', 0))", True, marks=bug(NO_TERM_CONDITION)),
    ("NValues([], condition=('ge', 1))", False),
    pytest.param("NValues([], excepting=0, condition=('le', 0))", True, marks=bug(NO_TERM_CONDITION)),
])
def test_nvalues_on_no_term(run, solver, request, constraint, holds):
    # the number of distinct values of no term is 0
    if holds is None:
        check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: t[3] != 1)
        return
    if not holds:
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)  # the constraint false, posted by a table with an empty set of supports
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: holds and t[3] != 1)


@pytest.mark.parametrize("constraint, predicate", [
    ("NValues(x[0], x[1], x[0]) == 1", lambda a, b, c, d: a == b),
    ("NValues(x[0], x, x[3]) >= 3", lambda *t: nv(t) >= 3),
    ("NValues(x[0], x[0]) == 1", lambda a, b, c, d: True),
    ("NValues(x[0], x[0], x[1], x[2]) <= 2", lambda a, b, c, d: nv((a, b, c)) <= 2),
    ("NValues(x[0], x[0], x[1], excepting=0) == 1", lambda a, b, c, d: nv((a, b), (0,)) == 1),
    ("NValues(x[0], x[0], excepting=0) == 1", lambda a, b, c, d: a != 0),
    ("NValues(x[0] + 1, x[0] + 1, x[1]) == 1", lambda a, b, c, d: a + 1 == b),
    ("NValues(x[0] + 1, 1 + x[0], x[1]) == 1", lambda a, b, c, d: a + 1 == b),
    ("NValues(Sum(x[:2]), Sum(x[:2]), x[2]) == 1", lambda a, b, c, d: a + b == c),
])
def test_nvalues_with_a_repeated_term(run, solver, request, constraint, predicate):
    # a term given several times does not change the number of distinct values: it is kept once (#134)
    if constraint == "NValues(x[0], x[0], excepting=0) == 1":
        request.applymarker(bug(ONE_TERM))  # a constraint nValues on the single term x[0] (kept once) is posted
    elif "excepting" in constraint:
        skip_except(solver)
    if solver == "COSOCO" and "+ 1" in constraint:
        pytest.skip(COSOCO_EXPRESSIONS)
    if constraint == "NValues(x[0], x[0], x[1], x[2]) <= 2":
        bug_for(request, "CHOCO", CHOCO_LIMIT)
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: predicate(*t) and t[3] != 1)


@pytest.mark.parametrize("constraint, predicate", [
    ("NValues(x, 1) <= 2", lambda *t: nv(t + (1,)) <= 2),
    ("NValues(x[0], 5) == 2", lambda *t: True),
    ("NValues(x[0], 5) == 1", lambda *t: False),
    ("NValues(x[0], 1, 1) == 1", lambda *t: t[0] == 1),
    ("NValues(2, x[0], x[1]) == 1", lambda *t: t[0] == t[1] == 2),
    ("NValues(x[0], 0, excepting=0) == 1", lambda *t: t[0] != 0),
    ("NValues(x[0], 0, excepting=0) == 0", lambda *t: t[0] == 0),
])
def test_nvalues_with_integers(run, solver, request, constraint, predicate):
    # an integer among the terms is a term like the others (it is replaced by an auxiliary variable, not part of the solutions)
    if "excepting" in constraint:
        skip_except(solver)
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: predicate(*t) and t[3] != 1)


@pytest.mark.parametrize("constraint, holds", [
    ("NValues(1, 2) == 2", True),
    ("NValues(1, 1) == 1", True),
    ("NValues(5) == 1", True),
    ("NValues(1, 2, 1) == 3", False),
    ("NValues(1, 2, excepting=1) == 1", True),
])
def test_nvalues_on_integers_only(run, solver, request, constraint, holds):
    # each integer is replaced by an auxiliary variable whose domain only contains this integer
    if "excepting" in constraint:
        skip_except(solver)
    if constraint == "NValues(1, 2, 1) == 3":
        bug_for(request, "ACE", ACE_LIMIT)  # nValues on two auxiliary variables with the condition (eq,3)
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: holds and t[3] != 1)


# ----------------------------------------------------------------------------------------------- arithmetic with NValues

@pytest.mark.parametrize("constraint, predicate", [
    ("NValues(x) + 1 == 3", lambda n: n + 1 == 3),
    ("NValues(x) - 1 == 1", lambda n: n - 1 == 1),
    ("1 - NValues(x) == -1", lambda n: 1 - n == -1),
    ("-NValues(x) == -2", lambda n: -n == -2),
    ("NValues(x) * 2 == 4", lambda n: 2 * n == 4),
    ("NValues(x) // 2 == 1", lambda n: n // 2 == 1),
    ("NValues(x) % 2 == 0", lambda n: n % 2 == 0),
    ("abs(NValues(x) - 2) <= 0", lambda n: n == 2),
])
def test_nvalues_in_arithmetic_expressions(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, lambda *t: predicate(nv(t)))


@pytest.mark.parametrize("constraint, predicate", [
    ("NValues(x[:3]) * x[3] == 2", lambda a, b, c, d: nv((a, b, c)) * d == 2),
    ("NValues(x[:2]) + NValues(x[2:]) == 3", lambda a, b, c, d: nv((a, b)) + nv((c, d)) == 3),
    ("NValues(x[:3]) - NValues(x[1:]) == 1", lambda a, b, c, d: nv((a, b, c)) - nv((b, c, d)) == 1),
    ("Sum(x) + NValues(x) == 4", lambda *t: sum(t) + nv(t) == 4),
    ("Sum(NValues(x), x[0]) == 3", lambda *t: nv(t) + t[0] == 3),
    ("(NValues(x) == 2) == (x[0] == 1)", lambda *t: (nv(t) == 2) == (t[0] == 1)),
])
def test_nvalues_with_other_terms_in_arithmetic_expressions(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


@pytest.mark.parametrize("constraint, predicate", [
    ("NValues(x, excepting=0) + x[0] <= 1", lambda *t: nv(t, (0,)) + t[0] <= 1),
    ("NValues(x, excepting=0) * 2 == 0", lambda *t: nv(t, (0,)) == 0),
    ("NValues(x[:2], excepting=0) == NValues(x[2:], excepting=0)", lambda a, b, c, d: nv((a, b), (0,)) == nv((c, d), (0,))),
    ("Sum(NValues(x, excepting=[0, 1]), x[0]) == 0", lambda *t: nv(t, (0, 1)) + t[0] == 0),
])
def test_nvalues_excepting_in_arithmetic_expressions(run, solver, constraint, predicate):
    # with excepting, the number of distinct values can be 0 (#214)
    skip_except(solver)
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


@pytest.mark.parametrize("constraint, domain", [
    ("NValues(x) + x[0] == 3", (1, 4)),
    ("NValues(x, excepting=0) + x[0] == 3", (0, 4)),
    ("NValues(x, excepting=[0, 1]) + x[0] == 3", (0, 4)),
])
def test_xcsp3_auxiliary_variable_of_nvalues(run, constraint, domain):
    # the domain of the auxiliary variable replacing NValues contains all its possible values (with excepting, 0, #214)
    r = run(X4 + f"satisfy({constraint})")
    values = declared_variables(r)["aux_gb[0]"]
    assert values[0] <= domain[0] and values[-1] >= domain[1], r.report()


# ---------------------------------------------------------------------------------------------------------- groups

M32 = "m = VarArray(size=[3, 2], dom=range(3))\n"
D32 = [range(3)] * 6


@pytest.mark.parametrize("constraints, predicate", [
    ("[NValues(m[i]) == 1 for i in range(3)]", lambda *t: all(t[2 * i] == t[2 * i + 1] for i in range(3))),
    ("[NValues(m[:, j]) >= 3 for j in range(2)]", lambda *t: all(nv((t[j], t[2 + j], t[4 + j])) >= 3 for j in range(2))),
    ("[NValues(m[i], excepting=i) <= 1 for i in range(3)]", lambda *t: all(nv((t[2 * i], t[2 * i + 1]), (i,)) <= 1 for i in range(3))),
    ("[NValues(m[i]) == i for i in range(3)]", lambda *t: all(nv((t[2 * i], t[2 * i + 1])) == i for i in range(3))),
    ("[NValues(m[i], excepting=0) == 1 for i in range(3)]", lambda *t: all(nv((t[2 * i], t[2 * i + 1]), (0,)) == 1 for i in range(3))),
])
def test_nvalues_in_groups(run, solver, request, constraints, predicate):
    if "excepting" in constraints:
        skip_except(solver)
    if constraints == "[NValues(m[i]) == i for i in range(3)]":
        bug_for(request, "ACE", ACE_LIMIT)  # NValues(m[0]) == 0
    check(run, solver, M32 + f"satisfy({constraints})", D32, predicate)


@pytest.mark.parametrize("values", ["{1}", "frozenset({1})", "S", "[1]", "range(1, 2)"])
def test_nvalues_in_a_set_in_a_comprehension(run, solver, values):
    # S is the set {1}; from Python 3.13, the instruction 'in' with a set is specialized after its first executions (see #166)
    if solver == "CHOCO":
        pytest.skip(CHOCO_IN)
    check(run, solver, M32 + f"S = {{1}}\nsatisfy([NValues(m[i]) in {values} for i in range(3)])", D32,
          lambda *t: all(t[2 * i] == t[2 * i + 1] for i in range(3)))


def test_nvalues_on_sliding_windows(run, solver, request):
    bug_for(request, "CHOCO", CHOCO_LIMIT)
    check(run, solver, "x = VarArray(size=5, dom=range(3))\nsatisfy([NValues(x[i:i + 3]) <= 2 for i in range(3)])", [range(3)] * 5,
          lambda *t: all(nv(t[i:i + 3]) <= 2 for i in range(3)))


# ------------------------------------------------------------------------------------------------ logical contexts

@pytest.mark.parametrize("constraint, predicate", [
    ("(NValues(x) == 2) | (x[0] == 2)", lambda *t: nv(t) == 2 or t[0] == 2),
    ("(NValues(x) == 2) & (x[0] == 1)", lambda *t: nv(t) == 2 and t[0] == 1),
    ("~(NValues(x) == 2)", lambda *t: nv(t) != 2),
    ("~(NValues(x) >= 2)", lambda *t: nv(t) < 2),
    ("imply(x[0] == 2, NValues(x) == 1)", lambda *t: t[0] != 2 or nv(t) == 1),
    ("iff(x[0] == 2, NValues(x) == 1)", lambda *t: (t[0] == 2) == (nv(t) == 1)),
    ("xor(x[0] == 2, NValues(x) > 2)", lambda *t: (t[0] == 2) != (nv(t) > 2)),
    ("If(x[0] == 2, Then=NValues(x[1:]) == 1)", lambda *t: t[0] != 2 or nv(t[1:]) == 1),
    ("(NValues(x) in {1, 3}) | (x[0] == 2)", lambda *t: nv(t) in (1, 3) or t[0] == 2),
    ("(NValues(x) not in {1, 3}) | (x[0] == 2)", lambda *t: nv(t) not in (1, 3) or t[0] == 2),
    ("(NValues(x[1:]) == x[0]) | (x[0] == 0)", lambda *t: nv(t[1:]) == t[0] or t[0] == 0),
    ("either(NValues(x[:2]) == 1, NValues(x[2:]) == 1)", lambda *t: t[0] == t[1] or t[2] == t[3]),
    ("both(NValues(x[:3]) >= 2, NValues(x[1:]) <= 2)", lambda *t: nv(t[:3]) >= 2 and nv(t[1:]) <= 2),
])
def test_nvalues_in_logical_expressions(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


@pytest.mark.parametrize("constraint, predicate", [
    ("(NValues(x, excepting=0) == 0) | (x[0] == 2)", lambda *t: nv(t, (0,)) == 0 or t[0] == 2),
    ("~(NValues(x, excepting=0) >= 1)", lambda *t: nv(t, (0,)) == 0),
    ("imply(x[0] == 0, NValues(x, excepting=0) < 1)", lambda *t: t[0] != 0 or nv(t, (0,)) == 0),
    ("(NValues(x, excepting=0) == 1) | (x[0] == 2)", lambda *t: nv(t, (0,)) == 1 or t[0] == 2),
])
def test_nvalues_excepting_in_logical_expressions(run, solver, constraint, predicate):
    # with excepting, the number of distinct values can be 0 (#214)
    skip_except(solver)
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


# ------------------------------------------------------------------------------------------------------------ objectives

@pytest.mark.parametrize("objective, value, maximize", [
    ("minimize(NValues(x))", lambda *t: nv(t), False),
    ("maximize(NValues(x))", lambda *t: nv(t), True),
    ("minimize(NValues(x[1:]) + x[0])", lambda *t: nv(t[1:]) + t[0], False),
    ("maximize(NValues(x[:2]) - NValues(x[2:]))", lambda a, b, c, d: nv((a, b)) - nv((c, d)), True),
    ("minimize(NValues(x, 2))", lambda *t: nv(t + (2,)), False),
])
def test_nvalues_in_objectives(run, solver, objective, value, maximize):
    if solver == "COSOCO" and objective == "maximize(NValues(x))":
        pytest.skip(COSOCO_MAXIMIZE)
    r = run(X4 + f"satisfy(x[0] != x[1], Sum(x) >= 3)\n{objective}", solver=solver)
    assert_optimum(r, brute_force(D4, lambda a, b, c, d: a != b and a + b + c + d >= 3), value, maximize=maximize)


@pytest.mark.parametrize("objective, value, maximize", [
    ("minimize(NValues(x[0] + 1, x[1], x[2] * 2))", lambda a, b, c, d: nv((a + 1, b, c * 2)), False),
    ("maximize(NValues(abs(x[0] - x[1]), x[2], x[3]))", lambda a, b, c, d: nv((abs(a - b), c, d)), True),
])
def test_nvalues_on_expressions_in_objectives(run, solver, objective, value, maximize):
    if solver == "COSOCO":
        pytest.skip(COSOCO_EXPRESSIONS)
    r = run(X4 + f"satisfy(x[0] != x[1], Sum(x) >= 3)\n{objective}", solver=solver)
    assert_optimum(r, brute_force(D4, lambda a, b, c, d: a != b and a + b + c + d >= 3), value, maximize=maximize)


@pytest.mark.parametrize("objective, value, maximize", [
    ("minimize(NValues(x, excepting=0))", lambda *t: nv(t, (0,)), False),
    ("maximize(NValues(x, excepting=0))", lambda *t: nv(t, (0,)), True),
    ("minimize(NValues(x, excepting=[1, 2]))", lambda *t: nv(t, (1, 2)), False),
    ("maximize(NValues(x, excepting=[0, 1]))", lambda *t: nv(t, (0, 1)), True),
])
def test_nvalues_excepting_in_objectives(run, solver, request, objective, value, maximize):
    skip_except(solver)
    request.applymarker(bug(OBJ_EXCEPT))
    r = run(X4 + f"satisfy(x[0] != x[1], Sum(x) >= 3)\n{objective}", solver=solver)
    assert_optimum(r, brute_force(D4, lambda a, b, c, d: a != b and a + b + c + d >= 3), value, maximize=maximize)


@pytest.mark.parametrize("objective", ["minimize(NValues(x, excepting=0))", "maximize(NValues(x, excepting=[0, 1]))"])
def test_xcsp3_nvalues_excepting_in_objectives(run, request, objective):
    # in XCSP3, an objective of type nValues has no element <except>
    request.applymarker(bug(OBJ_EXCEPT))
    r = run(X4 + f"satisfy(x[0] != x[1])\n{objective}")
    assert r.ok, r.report()
    assert r.xml.find("objectives")[0].find("except") is None, r.report()


@pytest.mark.parametrize("objective", ["minimize(NValues(x))", "maximize(NValues(x[0], x[1] + 1))"])
def test_xcsp3_nvalues_in_objectives(run, objective):
    r = run(X4 + f"satisfy(x[0] != x[1])\n{objective}")
    assert r.ok, r.report()
    o = r.xml.find("objectives")[0]
    assert o.get("type") == "nValues", r.report()


# ------------------------------------------------------------------------------------------------ examples of the doc

def test_nvalues_example(run, solver):
    # the first example of the documentation (graph colouring), with less colours
    r = run("x = VarArray(size=6, dom=range(3))\nedges = [(0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 5)]\n"
            "satisfy([x[i] != x[j] for (i, j) in edges])\nminimize(NValues(x))", solver=solver)
    edges = [(0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 5)]
    assert_optimum(r, brute_force([range(3)] * 6, lambda *t: all(t[i] != t[j] for (i, j) in edges)), lambda *t: nv(t))


def test_nvalues_example_with_excepting(run, solver):
    skip_except(solver)
    # the second example of the documentation (teams), with less players
    check(run, solver, "y = VarArray(size=5, dom=range(4))\nsatisfy(Count(y, value=0) == 2, NValues(y, excepting=0) == 2)", [range(4)] * 5,
          lambda *t: t.count(0) == 2 and nv(t, (0,)) == 2)


def test_number_distinct_values_example(run, solver):
    # the first example of the documentation of NumberDistinctValues(), with less colours
    check(run, solver, "x = VarArray(size=6, dom=range(3))\nedges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]\n"
                       "satisfy([x[i] != x[j] for (i, j) in edges], NumberDistinctValues(x) <= 2)", [range(3)] * 6,
          lambda *t: all(t[i] != t[i + 1] for i in range(5)) and nv(t) <= 2)


def test_number_distinct_values_example_with_excepting(run, solver):
    skip_except(solver)
    # the second example of the documentation of NumberDistinctValues(), with less nodes
    check(run, solver, "x = VarArray(size=5, dom=range(4))\nsatisfy(Count(x, value=0) == 2, NumberDistinctValues(x, excepting=0) == 2)",
          [range(4)] * 5, lambda *t: t.count(0) == 2 and nv(t, (0,)) == 2)


@pytest.mark.parametrize("code, solution", [
    ("x = VarArray(size=6, dom=range(6))\nedges = [(0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 5)]\nsatisfy([x[i] != x[j] for (i, j) in edges])\n"
     "minimize(NValues(x))", [0, 1, 1, 0, 0, 1]),
    ("y = VarArray(size=8, dom=range(4))\nsatisfy(Count(y, value=0) == 2, NValues(y, excepting=0) == 2)", [0, 0, 1, 1, 1, 1, 1, 2]),
    ("x = VarArray(size=6, dom=range(6))\nedges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]\nsatisfy([x[i] != x[j] for (i, j) in edges], "
     "NumberDistinctValues(x) <= 3)", [0, 1, 0, 1, 0, 1]),
    ("x = VarArray(size=6, dom=range(4))\nsatisfy(Count(x, value=0) == 2, NumberDistinctValues(x, excepting=0) == 2)", [0, 0, 1, 1, 1, 2]),
], ids=["NValues 1", "NValues 2", "NumberDistinctValues 1", "NumberDistinctValues 2"])
def test_solutions_given_in_the_doc(run, solver, code, solution):
    # the solution given by the documentation satisfies the constraints of the example
    if "excepting" in code:
        skip_except(solver)
    name = code[0]
    r = run(code + f"\nsatisfy({name} == {solution})", solver=solver)
    assert r.ok and r.status in ("SAT", "OPTIMUM") and len(r.raw_solutions) > 0, r.report()


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, expected", [
    ("NValues(x) == 2", ("x[]", None, "(eq,2)")),
    ("NValues(x[0], x[2]) <= 1", ("x[0] x[2]", None, "(le,1)")),
    ("NValues(x, excepting=0) >= 2", ("x[]", "0", "(ge,2)")),
    ("NValues(x, excepting=[0, 1]) == 1", ("x[]", "0 1", "(eq,1)")),
    ("NValues(x) in range(2, 4)", ("x[]", None, "(in,2..3)")),
    ("NValues(x) not in {1, 3}", ("x[]", None, "(notin,{1,3})")),
    ("NValues(x[:3]) == x[3]", ("x[0..2]", None, "(eq,x[3])")),
    ("NValues(x[0] + 1, x[1] + 1) != 1", ("add(x[0],1) add(x[1],1)", None, "(ne,1)")),
    ("NumberDistinctValues(x, condition=('lt', 3))", ("x[]", None, "(lt,3)")),
])
def test_xcsp3_nvalues(run, constraint, expected):
    r = run(X4 + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/nValues")
    e = c.find("except")
    assert (" ".join(c.find("list").text.split()), None if e is None else " ".join(e.text.split()), c.find("condition").text.strip()) == expected, \
        r.report()


def test_xcsp3_nvalues_in_a_group(run):
    r = run("x = VarArray(size=4, dom=range(3))\nsatisfy([NValues(x[i:i + 2], excepting=0) == 1 for i in range(3)])")
    assert r.ok, r.report()
    group = r.xml.find("constraints/group")
    assert group is not None and group.find("nValues") is not None, r.report()
    assert [" ".join(a.text.split()) for a in group.findall("args")] == ["x[0] x[1]", "x[1] x[2]", "x[2] x[3]"], r.report()


def test_xcsp3_nvalues_with_an_integer(run):
    # an integer is replaced by an auxiliary variable whose domain only contains this integer
    r = run(X4 + "satisfy(NValues(x[0], 5) == 2)")
    assert r.ok, r.report()
    assert " ".join(r.xml.find("constraints/nValues/list").text.split()) == "x[0] aux_gb[0]", r.report()
    assert r.xml.find("variables/array[@id='aux_gb']").text.strip() == "5", r.report()


@pytest.mark.parametrize("constraint, terms", [
    ("NValues(x[0], x[1], x[0]) == 2", "x[0] x[1]"),
    ("NValues(x[0], x, x[3]) == 2", "x[]"),
    ("NValues(x[0] + 1, x[0] + 1, x[1]) == 2", "add(x[0],1) x[1]"),
])
def test_xcsp3_nvalues_with_a_repeated_term(run, constraint, terms):
    # each term given several times is kept once in the element <nValues> (#134)
    r = run(X4 + f"satisfy({constraint})")
    assert r.ok, r.report()
    assert " ".join(r.xml.find("constraints/nValues/list").text.split()) == terms, r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("constraint", [
    "NValues() == 1",
    "NValues(None) == 1",
    "NValues(x[0], 'a') == 1",
    "NValues(x[0], 2.5) == 1",
    "NValues(x[0], True) == 2",
    "NValues(True, False) == 2",
    "NValues(x[0], range(3)) == 1",
    "NValues('a') == 1",
    "NValues({'a': x[0]}) == 1",
    "NValues(x) == 'a'",
    "NValues(x) == 2.5",
    "NValues(x) == True",
    "NValues(x) == None",
    "NValues(x)",
    "NValues(x, foo=1) == 2",
    "NValues(x, excepting=x[0]) == 2",
    "NValues(x, excepting='a') == 2",
    "NValues(x, excepting=2.5) == 2",
    "NValues(x, excepting=[0, 'a']) == 2",
    "NValues(x, excepting=[x[0]]) == 2",
    pytest.param("NValues(x, excepting=True) == 2", marks=bug(EXCEPTING)),
    pytest.param("NValues(x, excepting=[0, False]) == 2", marks=bug(EXCEPTING)),
    pytest.param("NValues(x, excepting=[0, 0]) == 2", marks=bug(EXCEPTING)),  # a value given several times is refused (decision C of #213)
    pytest.param("NValues(x, excepting=[[0], 1, [0]]) == 2", marks=bug(EXCEPTING)),
    "NValues(x, condition=2)",
    "NValues(x, condition=('eq',))",
    "NValues(x, condition=('foo', 2))",
    "NValues(x, condition=('eq', 'a'))",
    "NValues(x, condition=('eq', 2.5))",
    "NValues(x, condition=('eq', True))",
])
def test_invalid_nvalues(run, constraint):
    assert_fails(run(X4 + f"satisfy({constraint})"))


@pytest.mark.parametrize("constraint, message", [
    ("NValues(None) == 1", "NValues() requires variables (or expressions), which is not the case of None"),
    ("NValues(x)", "is not a constraint: it must be subject to a condition"),
    ("NValues(x) == True", "A Boolean cannot be the operand of a condition"),
    ("NValues(x, condition=('foo', 2))", "The operator foo of the condition ('foo', 2) is unknown"),
])
def test_invalid_nvalues_message(run, constraint, message):
    r = run(X4 + f"satisfy({constraint})")
    assert not r.ok and message in r.stdout, r.report()


@pytest.mark.parametrize("objective", ["minimize(NValues(x[0]))", "maximize(NValues([]))", "minimize(NValues(x[0], x[0]))"])
def test_nvalues_constant_in_objectives(run, objective):
    # the number of distinct values of less than two terms is a constant: there is nothing to optimize
    assert_fails(run(X4 + f"satisfy(x[0] != x[1])\n{objective}"))


@bug(CONSTANT_OBJECTIVE)
@pytest.mark.parametrize("objective", ["minimize(NValues(x[0]))", "maximize(NValues([]))", "minimize(Sum([]))", "minimize(Count([], value=1))"])
def test_constant_in_objectives_message(run, objective):
    r = run(X4 + f"satisfy(x[0] != x[1])\n{objective}")
    assert not r.ok and "constant" in r.stdout, r.report()


@bug(NEGATED_MEMBERSHIP)
@pytest.mark.parametrize("constraint", ["~(NValues(x) in {1, 3})", "~(NValues(x) not in {1, 3})", "~(Sum(x) in {1, 3})", "~(x[0] in {1, 2})"])
def test_negated_membership_message(run, constraint):
    # Python converts the result of 'in' into a Boolean, and ~True is -2: 'not in' (or 'in') must be used instead
    r = run(X4 + f"satisfy({constraint})")
    assert not r.ok and "not in" in r.stdout, r.report()
