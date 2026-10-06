"""
Tests of the constraint Count of the section Constraints (Global) of the API (https://pycsp.org/documentation/api/constraints-global/#Count):
the function Count(), which builds a component that becomes a constraint count when compared with a value, a variable, an expression, an interval
or a set (or when given the parameter condition), with the parameters value and values (integers or variables), on variables and on expressions,
as a term of expressions, in groups of constraints, in logical expressions, in objectives, with the option -mini, and through the shortcut
'k in x' (an integer k and a list x of variables), which posts a constraint count.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
According to XCSP3-core, count(X, V, (op, k)) holds iff the number of variables of X assigned a value of V satisfies (op, k), with |X| >= 2 and
|V| >= 1, V being a list of integers or a list of variables, and expressions being accepted instead of variables in X (generalized form).
The example of XCSP3-core (constraint c5, list z1 z3 z3) shows that a variable can be repeated in X: it is then counted as many times.
As decided with the maintainers (questions of #169), PyCSP3 posts a sum when a variable is repeated among the terms (#192), evaluates the counts
whose result is known when compiling (#193), and refuses integers among the terms (#180) and an empty collection of values (#171).
"""

import re

import pytest

from harness import assert_fails, assert_optimum, assert_solutions, brute_force, bug, bug_for, declared_variables

# Known bugs (each bug is reported in the issue given at the start of its reason)
NOT_IN = "#170: 'k not in x' posts the same constraint as 'k in x' (count >= 1)"
NO_VALUE = ("#171: Count() with no value (values=[] or values=set()) is not refused with an explicit error (an empty element <values> is "
            "generated)")
SEVERAL_VARIABLES = ("#175: Count() sorts the variables given as values with '<', which builds expressions "
                     "(warning: A node is evaluated as a Boolean)")
ONE_TERM = "#172: Count() on a single term generates an element <count> with a list of one variable (XCSP3 requires at least two)"
INTEGERS = "#180: Count() does not refuse integers among the terms with an explicit message"
MINI = "#177: with -mini, Count() on 0/1 variables with the value 1 is changed into a sum without its parameter condition"
INVALID = "#176: Count() does not detect explicitly some invalid arguments"
REPEATED = ("#192: a variable repeated among the terms gives an element <count> with a repeated variable (to be posted as a sum), on which "
            "ACE gives wrong solutions and that cosoco refuses")
KNOWN = ("#193: a count whose result is known when compiling (an integer outside 0..|X|, values that no term can take) is posted as an element "
         "<count> (to be evaluated), on which ACE and CHOCO fail and that cosoco refuses")
ACE_NE = ("xcsp3team/ACE#24: ACE fails on a count with the condition (ne,k) when k is 0 or |X| (Problem.count(): control(op == NE && 0 < k && "
          "k < scp.length) without message)")
ACE_AMONG = "xcsp3team/ACE#25: ACE fails on a count with several values and the condition (eq,0) (ERROR: Bad value of k=0)"
CHOCO_RANGE = ("chocoteam/choco-solver#1248 (section 9): CHOCO gives wrong solutions for a count with the condition in or notin an interval "
               "(XCSPParser.dealWithConditionIntvl())")
COSOCO_ALONE = ("xcsp3team/cosoco#89: cosoco crashes (segmentation fault) when the only constraint is a count that always holds, and is "
                "discarded")
COSOCO_CANCEL = ("xcsp3team/cosoco#88: cosoco gives an invalid solution (Solution Error) for a sum whose terms all cancel out, when the condition "
                 "cannot be satisfied")
DUMMY_IN = "#173: Count() on no term cannot be compared with 'in' a set (TypeError: unhashable type: 'ConstraintDummyConstant')"
COMPACTOR = ("#195: the list of a count mixing variables of arrays and simple variables cannot be compacted (compactor.compact(): "
             "ValueError: substring not found)")
EMPTY_SUPPORTS = ("(to be reported) ACE and CHOCO fail on a table with an empty set of supports, recognized as false by the parser "
                  "(buildCtrFalse(): RuntimeException: Constraint with only conflicts)")

# The cases that a solver says it does not handle (not reported)
COSOCO_VARIABLES = "cosoco does not handle a count whose values are several variables (s UNSUPPORTED)"


def n_terms(text):
    """Returns the number of terms of the specified list of an XCSP3 file, a compact form x[i..j] standing for j - i + 1 variables, and x[] for 4."""
    m = [re.fullmatch(r"\w+\[(\d+)\.\.(\d+)\]", t) for t in text.split()]
    return sum(int(r.group(2)) - int(r.group(1)) + 1 if r else 4 if t.endswith("[]") else 1 for r, t in zip(m, text.split()))


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


def count(t, values):
    return sum(v in values for v in t)


X4 = "x = VarArray(size=4, dom=range(3))\n"
D4 = [range(3)] * 4


# ------------------------------------------------------------------------------------------------------------ conditions

@pytest.mark.parametrize("condition, predicate", [
    ("== 2", lambda c: c == 2),
    ("!= 2", lambda c: c != 2),
    ("< 2", lambda c: c < 2),
    ("<= 2", lambda c: c <= 2),
    ("> 2", lambda c: c > 2),
    (">= 2", lambda c: c >= 2),
    ("in range(1, 3)", lambda c: 1 <= c <= 2),
    ("in {1, 3}", lambda c: c in (1, 3)),
    ("in [1, 3]", lambda c: c in (1, 3)),
    ("in {2}", lambda c: c == 2),
    ("in range(0, 5, 2)", lambda c: c % 2 == 0),
    ("not in range(1, 3)", lambda c: not 1 <= c <= 2),
    ("not in {1, 3}", lambda c: c not in (1, 3)),
    ("not in [1, 3]", lambda c: c not in (1, 3)),
    ("!= 0", lambda c: c != 0),
    ("!= 4", lambda c: c != 4),
    ("== 0", lambda c: c == 0),
    ("== 4", lambda c: c == 4),
])
def test_count_conditions(run, solver, request, condition, predicate):
    if condition in ("in range(1, 3)", "not in range(1, 3)"):
        bug_for(request, "CHOCO", CHOCO_RANGE)
    elif condition in ("!= 0", "!= 4"):
        bug_for(request, "ACE", ACE_NE)
    check(run, solver, X4 + f"satisfy(Count(x, value=1) {condition})", D4, lambda *t: predicate(t.count(1)))


@pytest.mark.parametrize("constraint, predicate", [
    ("2 == Count(x, value=1)", lambda c: c == 2),
    ("2 <= Count(x, value=1)", lambda c: c >= 2),
    ("2 > Count(x, value=1)", lambda c: c < 2),
    ("2 != Count(x, value=1)", lambda c: c != 2),
])
def test_count_on_the_right(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, lambda *t: predicate(t.count(1)))


@pytest.mark.parametrize("operand, predicate", [
    ("== x[3]", lambda c, v: c == v),
    ("!= x[3]", lambda c, v: c != v),
    ("< x[3]", lambda c, v: c < v),
    ("<= x[3]", lambda c, v: c <= v),
    ("> x[3]", lambda c, v: c > v),
    (">= x[3]", lambda c, v: c >= v),
    ("== x[3] + 1", lambda c, v: c == v + 1),
    ("== abs(x[3] - 1)", lambda c, v: c == abs(v - 1)),
])
def test_count_compared_with_a_variable_or_an_expression(run, solver, operand, predicate):
    check(run, solver, X4 + f"satisfy(Count(x[:3], value=1) {operand})", D4, lambda a, b, c, d: predicate([a, b, c].count(1), d))


@pytest.mark.parametrize("constraint, predicate", [
    ("Count(x, value=1) == Count(x, value=2)", lambda *t: t.count(1) == t.count(2)),
    ("Count(x, value=1) > Count(x, value=0) + 1", lambda *t: t.count(1) > t.count(0) + 1),
    ("Count(x[:2], value=1) != Count(x[2:], value=1)", lambda a, b, c, d: [a, b].count(1) != [c, d].count(1)),
    ("Count(x, value=1) == Sum(x[:2])", lambda a, b, c, d: [a, b, c, d].count(1) == a + b),
])
def test_count_compared_with_a_count_or_a_sum(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


@pytest.mark.parametrize("condition, predicate", [
    ("('le', 2)", lambda c: c <= 2),
    ("['ge', 3]", lambda c: c >= 3),
    ("('<=', 2)", lambda c: c <= 2),
    ("('!=', 2)", lambda c: c != 2),
    ("('eq', 1)", lambda c: c == 1),
    ("('in', {1, 3})", lambda c: c in (1, 3)),
    ("('notin', {1, 3})", lambda c: c not in (1, 3)),
])
def test_count_with_the_parameter_condition(run, solver, condition, predicate):
    check(run, solver, X4 + f"satisfy(Count(x, value=1, condition={condition}))", D4, lambda *t: predicate(t.count(1)))


def test_count_with_the_parameter_condition_on_a_variable(run, solver):
    check(run, solver, X4 + "satisfy(Count(x[:3], value=1, condition=('eq', x[3])))", D4, lambda a, b, c, d: [a, b, c].count(1) == d)


@pytest.mark.parametrize("constraint, predicate", [
    ("Count(x, value=1) in set()", lambda c: False),
    ("Count(x, value=1) in range(0)", lambda c: False),
    ("Count(x, value=1) not in set()", lambda c: True),
    ("Count(x, value=1) not in range(0)", lambda c: True),
    ("Count(x, value=1) in range(5, 9)", lambda c: False),
    ("Count(x, value=1) == 5", lambda c: False),
    ("Count(x, value=1) == -1", lambda c: False),
    ("Count(x, value=1) < 5", lambda c: True),
    ("Count(x, value=1) <= 4", lambda c: True),
    ("Count(x, value=1) >= 0", lambda c: True),
    ("Count(x, value=1) > -1", lambda c: True),
    ("Count(x, value=1) != 7", lambda c: True),
    ("Count(x, value=1) >= 5", lambda c: False),
    ("Count(x, value=1) <= -1", lambda c: False),
])
def test_count_with_an_empty_or_unreachable_condition(run, solver, request, constraint, predicate):
    if constraint in ("Count(x, value=1) in set()", "Count(x, value=1) in range(0)"):
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)  # the constraint false, posted by a table with an empty set of supports
    elif constraint in ("Count(x, value=1) == 5", "Count(x, value=1) == -1", "Count(x, value=1) != 7", "Count(x, value=1) >= 5",
                        "Count(x, value=1) <= -1"):
        bug_for(request, "ACE", KNOWN)  # ACE: control(0 <= l && l <= list.length)
        if constraint in ("Count(x, value=1) >= 5", "Count(x, value=1) <= -1"):
            bug_for(request, "CHOCO", KNOWN)  # CHOCO: wrong domain definition, lower bound > upper bound
        if constraint != "Count(x, value=1) != 7":
            bug_for(request, "COSOCO", KNOWN)  # cosoco: ExactlyK must have 0 <= k <= size(list), ...
    elif constraint == "Count(x, value=1) in range(5, 9)":
        bug_for(request, "CHOCO", CHOCO_RANGE)
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: predicate(t.count(1)) and t[3] != 1)


@pytest.mark.parametrize("constraint", ["Count(x, value=1) >= 0", "Count(x, value=1) <= 4", "Count(x, value=1) > -1", "Count(x, value=1) < 5"])
def test_count_always_satisfied_alone(run, solver, request, constraint):
    # the only constraint of the model always holds
    if constraint in ("Count(x, value=1) >= 0", "Count(x, value=1) > -1"):
        bug_for(request, "COSOCO", COSOCO_ALONE)
    check(run, solver, X4 + f"satisfy({constraint})", D4, lambda *t: True)


@pytest.mark.parametrize("constraint, holds", [
    ("Count(x, value=1) == 5", False),
    ("Count(x, value=1) >= 5", False),
    ("Count(x, value=1) <= -1", False),
    ("Count(x, value=1) == -1", False),
    ("Count(x, value=1) in range(5, 9)", False),
    ("Count(x, value=1) != 7", True),
    ("Count(x, value=1) <= 4", True),
    ("Count(x, value=1) >= 0", True),
    ("Count(x, value=1) > -1", True),
    ("Count(x, value=7) == 0", True),
    ("Count(x, value=7) >= 1", False),
    ("Count(x, values=[5, 6]) <= 1", True),
    ("7 in x", False),
])
@bug(KNOWN)
def test_xcsp3_count_known_when_compiling(run, constraint, holds):
    # the result of the count is known when compiling (decision of #193): nothing is posted when the constraint always holds, and the
    # constraint false when it never holds
    r = run(X4 + f"satisfy({constraint}, x[3] != 1)")
    assert r.ok and r.xml.find("constraints/count") is None, r.report()
    assert ("trivially false" in r.stdout) != holds, r.report()


# ------------------------------------------------------------------------------------------------------------ values

@pytest.mark.parametrize("arguments, values", [
    ("", (1,)),
    ("value=1", (1,)),
    ("value=0", (0,)),
    ("value=2", (2,)),
    ("values=[1, 2]", (1, 2)),
    ("values={1, 2}", (1, 2)),
    ("values=(1, 2)", (1, 2)),
    ("values=range(1, 3)", (1, 2)),
    ("values=(v for v in [1, 2])", (1, 2)),
    ("values=[2, 1, 2]", (1, 2)),
    ("values=[1]", (1,)),
    ("values=[0, 1, 2]", (0, 1, 2)),
    ("values=[1, 5]", (1,)),
    ("value=None, values=None", (1,)),
])
@pytest.mark.parametrize("condition", ["== 2", ">= 3", "in {0, 4}"])
def test_count_values(run, solver, arguments, values, condition):
    predicate = {"== 2": lambda c: c == 2, ">= 3": lambda c: c >= 3, "in {0, 4}": lambda c: c in (0, 4)}[condition]
    check(run, solver, X4 + f"satisfy(Count(x{', ' if arguments else ''}{arguments}) {condition})", D4, lambda *t: predicate(count(t, values)))


@pytest.mark.parametrize("constraint, predicate", [
    ("Count(x[:3], value=x[3]) == 2", lambda a, b, c, d: [a, b, c].count(d) == 2),
    ("Count(x[:3], values=[x[3]]) == 2", lambda a, b, c, d: [a, b, c].count(d) == 2),
    ("Count(x[:3], value=x[3]) >= 1", lambda a, b, c, d: d in (a, b, c)),
    ("Count(x[:3], value=x[3]) == x[0]", lambda a, b, c, d: [a, b, c].count(d) == a),
    ("Count(x, value=x[0]) == 2", lambda a, b, c, d: [a, b, c, d].count(a) == 2),
    ("Count(x[:3], value=x[3] + 1) == 1", lambda a, b, c, d: [a, b, c].count(d + 1) == 1),
    ("Count(x[:3], value=abs(x[3] - 1)) >= 2", lambda a, b, c, d: [a, b, c].count(abs(d - 1)) >= 2),
    ("Count(x[:2], value=Sum(x[2:])) == 1", lambda a, b, c, d: [a, b].count(c + d) == 1),
])
def test_count_with_a_variable_or_an_expression_as_value(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


@pytest.mark.parametrize("values", ["[x[2], x[3]]", "[x[3], x[2]]", "(x[2], x[3])", "x[2:]", "{x[2], x[3]}"])
def test_count_with_variables_as_values(run, solver, values):
    if solver == "COSOCO":
        pytest.skip(COSOCO_VARIABLES)
    check(run, solver, X4 + f"satisfy(Count(x[:2], values={values}) == 1)", D4, lambda a, b, c, d: count((a, b), (c, d)) == 1)


@pytest.mark.parametrize("values", [
    pytest.param("[x[2], x[3]]", marks=bug(SEVERAL_VARIABLES)),
    pytest.param("[x[3], x[2]]", marks=bug(SEVERAL_VARIABLES)),
    "[x[2], x[2]]",
])
def test_count_with_variables_as_values_displays_no_warning(run, values):
    r = run(X4 + f"satisfy(Count(x[:2], values={values}) == 1)")
    assert r.ok and "Warning" not in r.stdout, r.report()


@pytest.mark.parametrize("arguments, predicate", [
    ("value=7", lambda c: c == 0),
    ("value=-1", lambda c: c == 0),
    ("values=[5, 6]", lambda c: c == 0),
])
@pytest.mark.parametrize("condition", ["== 0", ">= 1"])
def test_count_with_values_out_of_the_domains(run, solver, request, arguments, predicate, condition):
    # no variable can take a value to be counted: the count is always 0
    bug_for(request, "ACE", KNOWN)  # ACE: A constraint Count is posted with an empty scope
    if condition == ">= 1" and arguments != "values=[5, 6]":
        bug_for(request, "COSOCO", KNOWN)  # cosoco: AtLeast, all variables must contain value
    holds = (condition == "== 0")
    check(run, solver, X4 + f"satisfy(Count(x, {arguments}) {condition}, x[3] != 1)", D4, lambda *t: holds and t[3] != 1)


@pytest.mark.parametrize("arguments", ["values=[]", "values=set()", "values=()", "values=frozenset()", "values=range(0)", "values=(v for v in [])"])
@pytest.mark.parametrize("condition", ["== 0", ">= 1"])
@bug(NO_VALUE)
def test_count_with_no_value(run, arguments, condition):
    # an empty collection of values is refused with an explicit error (decision of #171)
    r = run(X4 + f"satisfy(Count(x, {arguments}) {condition})")
    assert_fails(r)
    assert "Count() requires at least one value" in r.stdout + r.stderr, r.report()


def test_count_on_negative_values(run, solver):
    check(run, solver, "x = VarArray(size=4, dom=range(-2, 2))\nsatisfy(Count(x, values=[-2, -1]) == 3)", [range(-2, 2)] * 4,
          lambda *t: count(t, (-2, -1)) == 3)


def test_count_on_different_domains(run, solver):
    check(run, solver, "x = VarArray(size=3, dom=lambda i: {0, i + 1, 5})\nsatisfy(Count(x, values=[1, 5]) >= 2)", [{0, 1, 5}, {0, 2, 5}, {0, 3, 5}],
          lambda *t: count(t, (1, 5)) >= 2)


# ------------------------------------------------------------------------------------------------------------ forms

@pytest.mark.parametrize("terms", [
    "x",
    "x[:]",
    "x[0], x[1], x[2], x[3]",
    "(x[0], x[1], x[2], x[3])",
    "[x[0], x[1], x[2], x[3]]",
    "(x[i] for i in range(4))",
    "x[:2], x[2:]",
    "[x[:2], x[2:]]",
    "x[0], [x[1], [x[2], x[3]]]",
    "{x[0], x[1], x[2], x[3]}",
    "[x[0], None, x[1], x[2], x[3]]",
    "x[3], x[0], x[2], x[1]",
])
def test_count_forms(run, solver, terms):
    check(run, solver, X4 + f"satisfy(Count({terms}, value=1) == 2)", D4, lambda *t: t.count(1) == 2)


@bug(COMPACTOR)
def test_count_on_variables_of_arrays_and_simple_variables(run, solver):
    check(run, solver, "x = VarArray(size=2, dom=range(3))\ny = Var(dom=range(3))\nz = Var(dom=range(3))\nsatisfy(Count(x[0], y, z, value=1) == 2)", [range(3)] * 4,
          lambda a, b, c, d: [a, c, d].count(1) == 2)


def test_count_on_a_matrix(run, solver):
    check(run, solver, "m = VarArray(size=[2, 2], dom=range(3))\nsatisfy(Count(m, value=1) == 2)", D4, lambda *t: t.count(1) == 2)


def test_count_on_an_array_with_holes(run, solver):
    r = check(run, solver, "w = VarArray(size=4, dom=lambda i: None if i == 1 else range(3))\nsatisfy(Count(w, value=1) == 2)", [range(3)] * 3,
              lambda *t: t.count(1) == 2)
    assert r.variables == ["w[0]", "w[2]", "w[3]"]


@pytest.mark.parametrize("n, d, k", [(2, 2, 1), (3, 3, 2), (5, 2, 3), (6, 2, 2), (6, 3, 0)])
def test_count_sizes(run, solver, n, d, k):
    check(run, solver, f"x = VarArray(size={n}, dom=range({d}))\nsatisfy(Count(x, value=1) == {k})", [range(d)] * n, lambda *t: t.count(1) == k)


# ------------------------------------------------------------------------------------------------------------ expressions

@pytest.mark.parametrize("terms, value, counted", [
    ("(x[i] > 0 for i in range(4))", "1", lambda *t: sum(v > 0 for v in t)),
    ("[x[0] == 1, x[1] == 2, x[2] != 0, x[3] < 2]", "1", lambda a, b, c, d: (a == 1) + (b == 2) + (c != 0) + (d < 2)),
    ("(x[i] + 1 for i in range(4))", "2", lambda *t: sum(v + 1 == 2 for v in t)),
    ("x[0] + x[1], x[2], x[3]", "2", lambda a, b, c, d: [a + b, c, d].count(2)),
    ("abs(x[0] - x[1]), x[2], x[3]", "1", lambda a, b, c, d: [abs(a - b), c, d].count(1)),
    ("x[0] * 2, x[1], x[2], x[3]", "2", lambda a, b, c, d: [2 * a, b, c, d].count(2)),
    ("Sum(x[:2]), x[2], x[3]", "2", lambda a, b, c, d: [a + b, c, d].count(2)),
    ("Count(x[:2], value=1), x[2], x[3]", "1", lambda a, b, c, d: [[a, b].count(1), c, d].count(1)),
    ("Maximum(x[:2]), x[2]", "2", lambda a, b, c, d: [max(a, b), c].count(2)),
])
def test_count_on_expressions(run, solver, terms, value, counted):
    check(run, solver, X4 + f"satisfy(Count({terms}, value={value}) == 2)", D4, lambda *t: counted(*t) == 2)


def test_count_on_boolean_expressions_by_default(run, solver):
    # without value, the terms (here, Boolean expressions) evaluating to 1 are counted
    check(run, solver, X4 + "satisfy(Count(x[i] > x[i + 1] for i in range(3)) == 2)", D4, lambda *t: sum(t[i] > t[i + 1] for i in range(3)) == 2)


# ----------------------------------------------------------------------------------------------- degenerated cases

@pytest.mark.parametrize("constraint, predicate", [
    ("Count(x[0], value=1) == 1", lambda a: a == 1),
    ("Count([x[0]], value=1) == 0", lambda a: a != 1),
    ("Count(x[0], values=[1, 2]) >= 1", lambda a: a in (1, 2)),
    ("Count(x[0], value=1) != 1", lambda a: a != 1),
    ("Count(x[0] + 1, value=2) == 1", lambda a: a == 1),
    ("Count(x[0], value=1, condition=('in', {1}))", lambda a: a == 1),
    ("Count(x[0], value=x[3]) == 1", None),
    ("1 in [x[0]]", lambda a: a == 1),
], ids=["one variable", "one variable in a list", "one variable and two values", "one variable with ne", "one expression", "one variable with condition",
        "one variable and a variable as value", "shortcut in"])
def test_count_on_a_single_term(run, solver, request, constraint, predicate):
    if constraint == "Count(x[0], value=1) != 1":
        bug_for(request, "ACE", ONE_TERM)  # ACE fails on a count of one variable with the condition (ne,1)
    elif constraint == "1 in [x[0]]":
        bug_for(request, "COSOCO", ONE_TERM)  # cosoco gives an invalid solution for a count of one variable with the condition (ge,1)
    p = (lambda a, b, c, d: (a == d) and d != 1) if predicate is None else (lambda *t: predicate(t[0]) and t[3] != 1)
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, p)


@pytest.mark.parametrize("constraint", ["Count(x[0], value=1) == 1", "Count([x[0]], value=1) == 0", "Count(x[0], values=[1, 2]) >= 1",
                                        "Count(x[0] + 1, value=2) == 1", "Count(x[0], value=x[3]) == 1", "1 in [x[0]]", "minimize(Count(x[0]))"])
@bug(ONE_TERM)
def test_xcsp3_count_has_at_least_two_terms(run, constraint):
    # XCSP3-core requires |X| >= 2
    r = run(X4 + (f"satisfy({constraint})" if not constraint.startswith("minimize") else constraint))
    assert r.ok, r.report()
    for c in r.xml.iter("count"):
        assert n_terms(c.find("list").text) >= 2, constraint + "\n" + r.report()


@pytest.mark.parametrize("constraint, holds", [
    ("Count([], value=1) == 0", True),
    ("Count([], value=1) >= 1", False),
    ("Count([], value=1) <= 2", True),
    ("Count([]) != 0", False),
    pytest.param("Count([], values=[1, 2]) in {0, 3}", True, marks=bug(DUMMY_IN)),
    pytest.param("Count([], value=1) not in {0, 3}", False, marks=bug(DUMMY_IN)),
    pytest.param("Count([], value=1) in range(2)", True, marks=bug(DUMMY_IN)),
    ("Count([], value=1) == x[3]", None),
])
def test_count_on_no_term(run, solver, request, constraint, holds):
    # the count of no term is 0
    if holds is None:
        check(run, solver, X4 + f"satisfy({constraint})", D4, lambda *t: t[3] == 0)
        return
    if not holds:
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)  # the constraint false, posted by a table with an empty set of supports
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: holds and t[3] != 1)


@pytest.mark.parametrize("constraint, predicate", [
    ("Count(x[0], x[0], x[1], value=1) == 2", lambda a, b, c, d: [a, a, b].count(1) == 2),
    ("Count(x[0], x[0], value=1) == 1", lambda a, b, c, d: False),
    ("Count(x[0], x[0], value=1) == 2", lambda a, b, c, d: a == 1),
    ("Count(x[0], x[1], x[0], x[2], value=1) >= 3", lambda a, b, c, d: [a, b, a, c].count(1) >= 3),
    ("Count(x[0], x[0], x[1], values=[1, 2]) <= 1", lambda a, b, c, d: count((a, a, b), (1, 2)) <= 1),
    ("Count(x[0], x[0], x[1], value=1) <= 1", lambda a, b, c, d: [a, a, b].count(1) <= 1),
    ("Count(x[0], x[0], x[1], value=1) == x[2]", lambda a, b, c, d: [a, a, b].count(1) == c),
], ids=["twice", "only twice, odd", "only twice", "twice among others", "twice with two values", "twice with le", "twice compared with a variable"])
def test_count_with_a_repeated_variable(run, solver, request, constraint, predicate):
    # a variable repeated in the list is counted as many times as it appears (as in the example c5 of count in XCSP3-core)
    bug_for(request, "COSOCO", REPEATED)  # cosoco: scope contains variable x0 many times (wrong solutions when compared with a variable)
    if constraint not in ("Count(x[0], x[0], value=1) == 2", "Count(x[0], x[0], x[1], values=[1, 2]) <= 1", "Count(x[0], x[0], x[1], value=1) == x[2]"):
        bug_for(request, "ACE", REPEATED)  # ACE: wrong solutions
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


@pytest.mark.parametrize("constraint", ["Count(x[0], x[0], x[1], value=1) == 2", "Count(x[0], x[1], x[0], x[2], values=[1, 2]) >= 3",
                                        "Count(x[0], x[0], x[1], value=x[3]) <= 1", "Count(x[0], x[0], x[1], value=1) == x[2]"])
@bug(REPEATED)
def test_xcsp3_count_with_a_repeated_variable(run, constraint):
    # with a variable repeated among the terms, a sum is posted, each distinct term being weighted by its number of occurrences (decision of #192)
    r = run(X4 + f"satisfy({constraint})")
    assert r.ok and r.xml.find("constraints/count") is None and r.xml.find("constraints/sum/coeffs") is not None, r.report()


@pytest.mark.parametrize("constraint", ["Count(x[0], 1, x[1], value=1) == 2", "Count(x[0], 0, x[1], value=1) == 2", "Count(x[:3], 2, value=2) >= 2",
                                        "Count(x[0], 1, 1, value=1) == 3", "Count(1, 2, 1, value=1) == 2", "Count(1, 2, value=1) == 2",
                                        "Count([x[0], 1], values=[1, 2]) <= 1"])
@bug(INTEGERS)
def test_count_with_integers(run, constraint):
    # integers among the terms are refused with an explicit error (decision of #180)
    r = run(X4 + f"satisfy({constraint})")
    assert_fails(r)
    assert "does not accept integers among the terms" in r.stdout + r.stderr, r.report()


# ----------------------------------------------------------------------------------------------- arithmetic with counts

@pytest.mark.parametrize("constraint, predicate", [
    ("Count(x, value=1) + 1 == 3", lambda c: c + 1 == 3),
    ("Count(x, value=1) - 1 == 1", lambda c: c - 1 == 1),
    ("1 - Count(x, value=1) == -1", lambda c: 1 - c == -1),
    ("-Count(x, value=1) == -2", lambda c: -c == -2),
    ("Count(x, value=1) * 2 == 4", lambda c: 2 * c == 4),
    ("2 * Count(x, value=1) >= 5", lambda c: 2 * c >= 5),
    ("Count(x, value=1) // 2 == 1", lambda c: c // 2 == 1),
    ("Count(x, value=1) % 2 == 0", lambda c: c % 2 == 0),
    ("abs(Count(x, value=1) - 2) <= 1", lambda c: abs(c - 2) <= 1),
])
def test_count_in_arithmetic_expressions(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, lambda *t: predicate(t.count(1)))


@pytest.mark.parametrize("constraint, predicate", [
    ("Count(x[:3], value=1) * x[3] == 2", lambda a, b, c, d: [a, b, c].count(1) * d == 2),
    ("Count(x, value=1) + Count(x, value=2) == 3", lambda *t: t.count(1) + t.count(2) == 3),
    ("Count(x, value=1) - Count(x, value=2) == 0", lambda *t: t.count(1) == t.count(2)),
    ("Count(x, value=1) - Count(x, value=1) == 0", lambda *t: True),
    ("Count(x, value=1) - Count(x, value=1) != 0", lambda *t: False),
    ("Sum(x) + Count(x, value=1) == 4", lambda *t: sum(t) + t.count(1) == 4),
    ("Count(x, value=1) - Sum(x[:2]) >= 1", lambda a, b, c, d: [a, b, c, d].count(1) - a - b >= 1),
    ("Maximum(x[:2]) + Count(x, value=0) == 3", lambda a, b, c, d: max(a, b) + [a, b, c, d].count(0) == 3),
    ("(Count(x, value=1) == 2) == (x[0] == 1)", lambda *t: (t.count(1) == 2) == (t[0] == 1)),
    ("Count(x[:2], value=1) * Count(x[2:], value=1) == 2", lambda a, b, c, d: [a, b].count(1) * [c, d].count(1) == 2),
])
def test_count_with_other_terms_in_arithmetic_expressions(run, solver, request, constraint, predicate):
    if constraint == "Count(x, value=1) - Count(x, value=1) != 0":  # recognized as false by the parsers
        bug_for(request, "ACE", EMPTY_SUPPORTS)
        bug_for(request, "COSOCO", COSOCO_CANCEL)
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


# ---------------------------------------------------------------------------------------------------------- groups

M32 = "m = VarArray(size=[3, 2], dom=range(3))\n"
D32 = [range(3)] * 6


@pytest.mark.parametrize("constraints, predicate", [
    ("[Count(m[i], value=1) == 1 for i in range(3)]", lambda *t: all([t[2 * i], t[2 * i + 1]].count(1) == 1 for i in range(3))),
    ("[Count(m[i], value=i) >= 1 for i in range(3)]", lambda *t: all(i in (t[2 * i], t[2 * i + 1]) for i in range(3))),
    ("[Count(m[:, j], value=0) <= 1 for j in range(2)]", lambda *t: all([t[j], t[2 + j], t[4 + j]].count(0) <= 1 for j in range(2))),
    ("[Count(m[i], values=[1, 2]) == i for i in range(3)]", lambda *t: all(count((t[2 * i], t[2 * i + 1]), (1, 2)) == i for i in range(3))),
    ("[Count(m, value=v) == 2 for v in range(3)]", lambda *t: all(t.count(v) == 2 for v in range(3))),
])
def test_count_in_groups(run, solver, request, constraints, predicate):
    if "values=[1, 2]" in constraints:
        bug_for(request, "ACE", ACE_AMONG)  # the first count is compared with 0
    check(run, solver, M32 + f"satisfy({constraints})", D32, predicate)


@pytest.mark.parametrize("values", ["{0, 2}", "frozenset({0, 2})", "S", "[0, 2]", "range(0, 3, 2)"])
def test_count_in_a_set_in_a_comprehension(run, solver, values):
    # S is the set {0, 2}; from Python 3.13, the instruction 'in' with a set is specialized after its first executions (see #166)
    check(run, solver, M32 + f"S = {{0, 2}}\nsatisfy([Count(m[i], value=1) in {values} for i in range(3)])", D32,
          lambda *t: all([t[2 * i], t[2 * i + 1]].count(1) in (0, 2) for i in range(3)))


# ------------------------------------------------------------------------------------------------ logical contexts

@pytest.mark.parametrize("constraint, predicate", [
    ("(Count(x, value=1) == 2) | (x[0] == 2)", lambda *t: t.count(1) == 2 or t[0] == 2),
    ("(Count(x, value=1) == 2) & (x[0] == 1)", lambda *t: t.count(1) == 2 and t[0] == 1),
    ("~(Count(x, value=1) == 2)", lambda *t: t.count(1) != 2),
    ("~(Count(x, value=1) >= 2)", lambda *t: t.count(1) < 2),
    ("imply(x[0] == 2, Count(x, value=1) == 2)", lambda *t: t[0] != 2 or t.count(1) == 2),
    ("iff(x[0] == 2, Count(x, value=1) == 2)", lambda *t: (t[0] == 2) == (t.count(1) == 2)),
    ("xor(x[0] == 2, Count(x, value=1) > 1)", lambda *t: (t[0] == 2) != (t.count(1) > 1)),
    ("If(x[0] == 2, Then=Count(x[1:], value=1) == 2)", lambda *t: t[0] != 2 or t[1:].count(1) == 2),
    ("(Count(x, value=1) in {1, 3}) | (x[0] == 2)", lambda *t: t.count(1) in (1, 3) or t[0] == 2),
    ("(Count(x, value=1) not in {1, 3}) | (x[0] == 2)", lambda *t: t.count(1) not in (1, 3) or t[0] == 2),
    ("(Count(x, values=[1, 2]) == 2) | (x[0] == 0)", lambda *t: count(t, (1, 2)) == 2 or t[0] == 0),
    ("(Count(x[1:], value=x[0]) == 2) | (x[0] == 0)", lambda *t: t[1:].count(t[0]) == 2 or t[0] == 0),
    ("(Count(x[:3], value=1) == x[3]) | (x[0] == 0)", lambda *t: t[:3].count(1) == t[3] or t[0] == 0),
    ("either(Count(x, value=1) == 2, Count(x, value=2) == 2)", lambda *t: t.count(1) == 2 or t.count(2) == 2),
    ("both(Count(x, value=1) >= 1, Count(x, value=2) >= 1)", lambda *t: 1 in t and 2 in t),
])
def test_count_in_logical_expressions(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


# ------------------------------------------------------------------------------------------------------------ objectives

@pytest.mark.parametrize("objective, value, maximize", [
    ("minimize(Count(x, value=0))", lambda *t: t.count(0), False),
    ("maximize(Count(x, values=[1, 2]))", lambda *t: count(t, (1, 2)), True),
    ("minimize(Count(x, value=0) + x[0])", lambda *t: t.count(0) + t[0], False),
    ("maximize(Count(x[1:], value=x[0]))", lambda *t: t[1:].count(t[0]), True),
    ("maximize(Count(x, value=1) - Count(x, value=2))", lambda *t: t.count(1) - t.count(2), True),
    ("minimize(Count(x[i] > 0 for i in range(4)))", lambda *t: sum(v > 0 for v in t), False),
])
def test_count_in_objectives(run, solver, objective, value, maximize):
    r = run(X4 + f"satisfy(x[0] != x[1], Sum(x) >= 3)\n{objective}", solver=solver)
    assert_optimum(r, brute_force(D4, lambda a, b, c, d: a != b and a + b + c + d >= 3), value, maximize=maximize)


# ------------------------------------------------------------------------------------------------ examples of the doc

def test_count_example(run, solver):
    # the first example of the documentation (rostering)
    check(run, solver, "x = VarArray(size=7, dom=range(3))\nsatisfy(Count(x, value=0) >= 2, Count(x, value=2) == 1)", [range(3)] * 7,
          lambda *t: t.count(0) >= 2 and t.count(2) == 1)


def test_count_example_with_values(run, solver):
    # the second example of the documentation, with less days
    check(run, solver, "y = VarArray(size=6, dom=range(3))\nsatisfy(Count(y, values=[1, 2]) == 4)", [range(3)] * 6, lambda *t: count(t, (1, 2)) == 4)


# ------------------------------------------------------------------------------------------------ the shortcut 'k in x'

@pytest.mark.parametrize("constraint, predicate", [
    ("1 in x", lambda *t: 1 in t),
    ("2 in x[:2]", lambda *t: 2 in t[:2]),
    ("1 in (x[0], x[1])", lambda *t: 1 in t[:2]),
    ("1 in [x[0], x[2], x[3]]", lambda a, b, c, d: 1 in (a, c, d)),
    ("0 in x[1:]", lambda *t: 0 in t[1:]),
    pytest.param("1 not in x", lambda *t: 1 not in t, marks=bug(NOT_IN)),
    pytest.param("2 not in x[:2]", lambda *t: 2 not in t[:2], marks=bug(NOT_IN)),
    pytest.param("1 not in (x[0], x[1])", lambda *t: 1 not in t[:2], marks=bug(NOT_IN)),
    pytest.param("1 not in [x[0], x[2], x[3]]", lambda a, b, c, d: 1 not in (a, c, d), marks=bug(NOT_IN)),
])
def test_value_in_a_list_of_variables(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


@pytest.mark.parametrize("constraint, holds", [("7 in x", False), ("-1 in x", False),
                                               pytest.param("7 not in x", True, marks=bug(NOT_IN)),
                                               pytest.param("-1 not in x", True, marks=bug(NOT_IN))])
def test_value_out_of_the_domains_in_a_list_of_variables(run, solver, request, constraint, holds):
    bug_for(request, "ACE", KNOWN)  # ACE: A constraint Count is posted with an empty scope
    if not holds:
        bug_for(request, "COSOCO", KNOWN)  # cosoco: AtLeast, all variables must contain value
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: holds and t[3] != 1)


@pytest.mark.parametrize("constraint, predicate", [
    ("(1 in x) | (x[0] == 2)", lambda *t: 1 in t or t[0] == 2),
    ("[1 in x[i:i + 2] for i in range(3)]", lambda *t: all(1 in t[i:i + 2] for i in range(3))),
    ("[v in x for v in range(3)]", lambda *t: all(v in t for v in range(3))),
    pytest.param("[1 not in x[i:i + 2] for i in range(0, 4, 2)]", lambda *t: 1 not in t, marks=bug(NOT_IN)),
])
def test_value_in_a_list_of_variables_in_expressions_and_groups(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


@pytest.mark.parametrize("constraint, condition", [
    ("1 in x", "(ge,1)"),
    pytest.param("1 not in x", "(eq,0)", marks=bug(NOT_IN)),
])
def test_xcsp3_value_in_a_list_of_variables(run, constraint, condition):
    r = run(X4 + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/count")
    assert c is not None and " ".join(c.find("values").text.split()) == "1" and c.find("condition").text.strip() == condition, r.report()


# ------------------------------------------------------------------------------------------------------------ -mini

B4 = "b = VarArray(size=4, dom={0, 1})\n"
DB4 = [(0, 1)] * 4

MINI_CASES = [
    ("Count(b, value=1) == 2", lambda *t: sum(t) == 2),
    ("Count(b) >= 3", lambda *t: sum(t) >= 3),
    ("Count(b, value=1) in {1, 3}", lambda *t: sum(t) in (1, 3)),
    ("Count(b, value=1) not in {1, 3}", lambda *t: sum(t) not in (1, 3)),
    ("Count(b[:3], value=1) == b[3]", lambda a, b, c, d: a + b + c == d),
    ("Count(b[i] == 1 for i in range(4)) == 2", lambda *t: sum(t) == 2),
    ("Count(b, value=0) == 1", lambda *t: t.count(0) == 1),
    ("Count(b, values=[1]) == 2", lambda *t: sum(t) == 2),
    pytest.param("Count(b, value=1, condition=('eq', 2))", lambda *t: sum(t) == 2, marks=bug(MINI)),
    pytest.param("Count(b, condition=('ge', 3))", lambda *t: sum(t) >= 3, marks=bug(MINI)),
    pytest.param("1 in b", lambda *t: 1 in t, marks=bug(MINI)),
    pytest.param("[1 in b[i:i + 2] for i in range(3)]", lambda *t: all(1 in t[i:i + 2] for i in range(3)), marks=bug(MINI)),
]


@pytest.mark.parametrize("constraint, predicate", MINI_CASES)
def test_count_with_mini(run, solver, constraint, predicate):
    check(run, solver, B4 + f"satisfy({constraint})", DB4, predicate, args=("-mini",))


@pytest.mark.parametrize("constraint", ["Count(b, value=1) == 2", "Count(b) >= 3", "Count(b[:3], value=1) == b[3]", "Count(b[i] == 1 for i in range(4)) == 2",
                                        pytest.param("Count(b, value=1, condition=('eq', 2))", marks=bug(MINI)),
                                        pytest.param("1 in b", marks=bug(MINI))])
def test_xcsp3_count_with_mini(run, constraint):
    # with -mini, counting the value 1 on 0/1 variables is a sum
    r = run(B4 + f"satisfy({constraint})", args=("-mini",))
    assert r.ok, r.report()
    assert r.xml.find("constraints/count") is None and r.xml.find("constraints/sum") is not None, r.report()


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, expected", [
    ("Count(x, value=1) == 2", ("x[]", "1", "(eq,2)")),
    ("Count(x) >= 1", ("x[]", "1", "(ge,1)")),
    ("Count(x, values=[2, 0, 2]) <= 3", ("x[]", "0 2", "(le,3)")),
    ("Count(x, values={2, 1}) != 1", ("x[]", "1 2", "(ne,1)")),
    ("Count(x[:3], value=x[3]) == 1", ("x[0..2]", "x[3]", "(eq,1)")),
    ("Count(x[:3], value=1) == x[3]", ("x[0..2]", "1", "(eq,x[3])")),
    ("Count(x, value=1) in range(1, 3)", ("x[]", "1", "(in,1..2)")),
    ("Count(x, value=1) not in {1, 3}", ("x[]", "1", "(notin,{1,3})")),
    ("Count(x[i] > 0 for i in range(4)) == 2", ("gt(x[0],0) gt(x[1],0) gt(x[2],0) gt(x[3],0)", "1", "(eq,2)")),
    ("1 in x", ("x[]", "1", "(ge,1)")),
])
def test_xcsp3_count(run, constraint, expected):
    r = run(X4 + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/count")
    assert c is not None, r.report()
    assert [e.tag for e in c] == ["list", "values", "condition"], r.report()  # the order of XCSP3
    got = (" ".join(c.find("list").text.split()), " ".join(c.find("values").text.split()), c.find("condition").text.strip())
    assert got == expected, r.report()


def test_xcsp3_count_with_an_expression_as_value(run):
    # the value of a count is an integer or a variable: an expression is replaced by an auxiliary variable
    r = run(X4 + "satisfy(Count(x[:3], value=x[3] + 1) == 1)")
    assert r.ok, r.report()
    values = r.xml.find("constraints/count/values").text.split()
    assert len(values) == 1 and values[0].startswith("aux_gb"), r.report()
    assert declared_variables(r)[values[0]] == [1, 2, 3], r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

INVALID_CASES = [
    ("Count(x, value=1)", "is not a constraint: it must be subject to a condition"),
    ("Count(x, value=1) == 2.5", "Wrong type for 2.5"),
    ("Count(x, value=1) == 'a'", "Wrong type for a"),
    ("Count(x, value=1) == None", "Wrong type for None"),
    ("Count(x, value=1) == True", "A Boolean cannot be the operand of a condition"),
    ("Count(x, value=1) in {True, 2}", "A Boolean cannot be the operand of a condition"),
    ("Count(x, value=1, condition=('le',))", "a condition must a pair"),
    ("Count(x, value=1, condition=('foo', 3))", "The operator foo of the condition"),
    ("Count() == 0", "missing 1 required positional argument"),
    ("Count(x, values=[1, x[0]]) == 2", "Count() requires the values to be all integers or all variables"),
    ("Count(x, value=True) == 2", "Count() does not accept Booleans as values"),
    ("Count(x, values=[True, 2]) == 2", "Count() does not accept Booleans as values"),
    ("Count(x, value=1.5) == 2", "Count() requires an integer, a variable or an expression as value"),
    ("Count(x, value='a') == 2", "Count() requires an integer, a variable or an expression as value"),
    ("Count(x, value=[1, 2]) == 2", "Count() requires an integer, a variable or an expression as value"),
    ("Count(x, value=range(3)) == 2", "Count() requires an integer, a variable or an expression as value"),
    ("Count(x, values=1) == 2", "Count() requires a list, a tuple, a set or a range of values"),
    ("Count(x, values=[1.5]) == 2", "Count() requires the values to be all integers or all variables"),
    ("Count(x, values=[x[0], None]) == 2", "Count() requires the values to be all integers or all variables"),
    ("Count(x, value=1, values=[2]) == 2", "Count() accepts either the parameter value or the parameter values, not both"),
    ("Count(s, value='a') == 2", "Count() requires integer variables"),
    ("Count(x, True) == 2", "Count() does not accept Booleans as terms"),
    ("Count(x, 'a') == 2", "Wrong type for"),
]
BUGGY_INVALID_CASES = {"Count(x, values=[1, x[0]]) == 2", "Count(x, value=True) == 2", "Count(x, values=[True, 2]) == 2", "Count(x, value=1.5) == 2",
                       "Count(x, value='a') == 2", "Count(x, value=[1, 2]) == 2", "Count(x, value=range(3)) == 2", "Count(x, values=1) == 2",
                       "Count(x, values=[1.5]) == 2", "Count(x, values=[x[0], None]) == 2", "Count(x, value=1, values=[2]) == 2",
                       "Count(s, value='a') == 2", "Count(x, True) == 2"}
# the invalid cases that already fail, but without an explicit error
NOT_EXPLICIT = {"Count(x, value=True) == 2", "Count(x, values=[True, 2]) == 2", "Count(x, value=1.5) == 2", "Count(x, value='a') == 2",
                "Count(x, value=[1, 2]) == 2", "Count(x, value=range(3)) == 2", "Count(x, values=1) == 2", "Count(x, values=[x[0], None]) == 2",
                "Count(s, value='a') == 2"}


@pytest.mark.parametrize("constraint", [pytest.param(c, marks=bug(INVALID)) if c in NOT_EXPLICIT else c for c, _ in INVALID_CASES])
def test_invalid_count(run, constraint):
    assert_fails(run(X4 + "s = VarArray(size=2, dom={'a', 'b'})\n" + f"satisfy({constraint})"))


@pytest.mark.parametrize("constraint, message", [pytest.param(c, m, marks=bug(INVALID)) if c in BUGGY_INVALID_CASES else (c, m) for c, m in INVALID_CASES])
def test_invalid_count_message(run, constraint, message):
    r = run(X4 + "s = VarArray(size=2, dom={'a', 'b'})\n" + f"satisfy({constraint})")
    assert not r.ok and message in r.stdout + r.stderr, r.report()
