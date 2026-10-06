"""
Tests of the functions of the section Constraints (Global) of the API that are shortcuts for the constraint Count
(https://pycsp.org/documentation/api/constraints-global/#Exist): Exist(), NotExist(), ExactlyOne(), AtLeastOne(), AtMostOne() (with the parameter
value), AnyHold(), NoneHold() and AllHold(), and the parameter reified_by of Exist(); on 0/1 variables, on integer variables and on expressions,
in groups of constraints, in logical expressions, and with the options -mini and -exist_by_element.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
Without value, a term is counted when it evaluates to 1 (as Count(), whose default value is 1), and with a value, when it takes this value:
Exist(X) holds iff at least one term is counted (as AtLeastOne(X) and AnyHold(X)), NotExist(X) iff no term is counted (as NoneHold(X)),
ExactlyOne(X) iff exactly one term is counted, AtMostOne(X) iff at most one term is counted, and AllHold(X) iff all the terms are counted.
A variable repeated among the terms is counted as many times as it appears (as for count in XCSP3-core).
As decided with the maintainers (questions of #169), without value, the terms must be 0/1 (variables with domain {0, 1} or Boolean expressions,
#174), and integers among the terms are refused (#180).
"""

import re

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
NOT_01 = ("#174: the shortcuts of Count() without value do not check that the terms are 0/1 (an explicit error is expected); Exist() on one or "
          "two terms that are not 0/1 posts the term itself, or the disjunction of the terms")
ONE_TERM = "#172: Count() on a single term generates an element <count> with a list of one variable (XCSP3 requires at least two)"
INTEGERS = "#180: Count() and its shortcuts do not refuse integers among the terms with an explicit message"
INVALID = "#176: Count() does not detect explicitly some invalid arguments"
REIFIED_LOST = ("#178: Exist() with reified_by, when used in an expression, is replaced by its reification variable, the constraint "
                "element reified by this variable being lost")
REIFIED_NOT_01 = ("#179: Exist() with reified_by on a single variable that is not 0/1 posts r = x (an explicit error is expected, as decided "
                  "in #174)")
REIFIED_EMPTY = "#179: Exist() with reified_by on no term posts the constraint false, instead of forcing the reification variable to 0"
REIFIED_INVALID = "#179: Exist() with reified_by checks it with an assert without message"
KNOWN = ("#193: a count of values that no term can take is posted as an element <count> (to be evaluated when compiling), on which ACE fails "
         "(empty scope) and that cosoco refuses")
REPEATED = ("#192: a variable repeated among the terms gives an element <count> with a repeated variable (to be posted as a sum), on which "
            "ACE gives wrong solutions and that cosoco refuses")
CHOCO_REIFIED = ("chocoteam/choco-solver#1248 (section 10): CHOCO gives wrong solutions for an element (member) constraint with the attribute "
                 "reifiedBy (the reification is ignored)")
PARSER_REIFIED = ("xcsp3team/XCSP3-Java-Tools#22: ACE fails on an element (member) constraint with the attribute reifiedBy whose value is a "
                  "variable (the parser, CtrLoaderInteger.element(), casts the value into Long: ClassCastException)")
EMPTY_SUPPORTS = ("(to be reported) ACE and CHOCO fail on a table with an empty set of supports, recognized as false by the parser "
                  "(buildCtrFalse(): RuntimeException: Constraint with only conflicts)")

# The cases that a solver says it does not handle (not reported)
COSOCO_REIFIED = "cosoco does not handle the constraint element with the attribute reifiedBy (s UNSUPPORTED)"

# Each function, with the condition on the number c of counted terms among n terms, and whether it has the parameter value
FUNCTIONS = {
    "Exist": (lambda c, n: c >= 1, True),
    "AtLeastOne": (lambda c, n: c >= 1, True),
    "AnyHold": (lambda c, n: c >= 1, False),
    "NotExist": (lambda c, n: c == 0, True),
    "NoneHold": (lambda c, n: c == 0, False),
    "ExactlyOne": (lambda c, n: c == 1, True),
    "AtMostOne": (lambda c, n: c <= 1, True),
    "AllHold": (lambda c, n: c == n, False),
}
WITH_VALUE = [f for f, (_, v) in FUNCTIONS.items() if v]
EXISTS = ("Exist", "AtLeastOne", "AnyHold")


def holds(f, terms, value=1):
    """Returns True if the specified function holds for the specified values of the terms."""
    return FUNCTIONS[f][0](sum(t == value for t in terms), len(terms))


def n_terms(text):
    """Returns the number of terms of the specified list of an XCSP3 file, a compact form x[i..j] standing for j - i + 1 variables, and x[] for 4."""
    m = [re.fullmatch(r"\w+\[(\d+)\.\.(\d+)\]", t) for t in text.split()]
    return sum(int(r.group(2)) - int(r.group(1)) + 1 if r else 4 if t.endswith("[]") else 1 for r, t in zip(m, text.split()))


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


B4 = "b = VarArray(size=4, dom={0, 1})\n"
DB4 = [(0, 1)] * 4
X4 = "x = VarArray(size=4, dom=range(3))\n"
D4 = [range(3)] * 4


# ------------------------------------------------------------------------------------------------------------ terms

@pytest.mark.parametrize("f", FUNCTIONS)
@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_on_01_variables(run, solver, f, n):
    terms = ", ".join(f"b[{i}]" for i in range(n))
    check(run, solver, B4 + f"satisfy({f}({terms}))", DB4, lambda *t: holds(f, t[:n]))


@pytest.mark.parametrize("f", FUNCTIONS)
@pytest.mark.parametrize("terms", ["x[0]", "x[0], x[1]", "x[0], x[1], x[2]", "x", "b[0], x[1]", "b[:2], x[2]", "x[0] + 1, x[1], x[2]",
                                   "abs(x[0] - x[1]), x[2]", "Sum(x[:2]), x[2], x[3]", "b[0] + b[1], b[2]"])
@bug(NOT_01)
def test_on_terms_that_are_not_01_without_value(run, f, terms):
    # without value, the terms must be 0/1 (variables with domain {0, 1} or Boolean expressions): an explicit error otherwise (decision of #174)
    r = run(B4 + X4 + f"satisfy({f}({terms}))")
    assert_fails(r)
    assert "requires 0/1 terms" in r.stdout + r.stderr, r.report()


@pytest.mark.parametrize("f", FUNCTIONS)
@pytest.mark.parametrize("terms, values", [
    ("x[0] > 0", lambda a, b, c, d: [a > 0]),
    ("x[0] > 0, x[1] == 2", lambda a, b, c, d: [a > 0, b == 2]),
    ("x[0] > 0, x[1] == 2, x[2] != x[3]", lambda a, b, c, d: [a > 0, b == 2, c != d]),
    ("(x[i] < x[i + 1] for i in range(3))", lambda *t: [t[i] < t[i + 1] for i in range(3)]),
    ("[x[0] == 1, x[1] + x[2] == 2]", lambda a, b, c, d: [a == 1, b + c == 2]),
    ("both(x[0] == 1, x[1] == 1), x[2] == 0, x[3] == 2", lambda a, b, c, d: [a == 1 and b == 1, c == 0, d == 2]),
])
def test_on_boolean_expressions(run, solver, f, terms, values):
    check(run, solver, X4 + f"satisfy({f}({terms}))", D4, lambda *t: holds(f, values(*t)))


@pytest.mark.parametrize("f", WITH_VALUE)
@pytest.mark.parametrize("terms, values", [
    ("x[0] + 1, x[1], x[2]", lambda a, b, c, d: [a + 1, b, c]),
    ("abs(x[0] - x[1]), x[2]", lambda a, b, c, d: [abs(a - b), c]),
    ("Sum(x[:2]), x[2], x[3]", lambda a, b, c, d: [a + b, c, d]),
])
@pytest.mark.parametrize("value", [1, 2])
def test_on_integer_expressions_with_a_value(run, solver, f, terms, values, value):
    check(run, solver, X4 + f"satisfy({f}({terms}, value={value}))", D4, lambda *t: holds(f, values(*t), value))


@pytest.mark.parametrize("f", FUNCTIONS)
@pytest.mark.parametrize("terms", ["b", "b[:]", "b[0], b[1], b[2], b[3]", "[b[0], b[1]], b[2:]", "(b[i] for i in range(4))", "[b[0], None, b[1], b[2], b[3]]",
                                   "{b[0], b[1], b[2], b[3]}"])
def test_forms(run, solver, f, terms):
    check(run, solver, B4 + f"satisfy({f}({terms}))", DB4, lambda *t: holds(f, t))


def test_on_a_matrix(run, solver):
    check(run, solver, "m = VarArray(size=[2, 2], dom={0, 1})\nsatisfy(ExactlyOne(m), AtLeastOne(m[0]), NotExist(m[:, 1]))", DB4,
          lambda a, b, c, d: a + b + c + d == 1 and a + b >= 1 and b + d == 0)


# ------------------------------------------------------------------------------------------------------------ value

@pytest.mark.parametrize("f", WITH_VALUE)
@pytest.mark.parametrize("n", [1, 2, 3, 4])
@pytest.mark.parametrize("value", [0, 1, 2])
def test_with_a_value(run, solver, request, f, n, value):
    if n == 1 and value != 0 and f in EXISTS:
        bug_for(request, "COSOCO", ONE_TERM)  # cosoco gives an invalid solution for a count of one variable with the condition (ge,1)
    terms = ", ".join(f"x[{i}]" for i in range(n))
    check(run, solver, X4 + f"satisfy({f}({terms}, value={value}))", D4, lambda *t: holds(f, t[:n], value))


@pytest.mark.parametrize("f", WITH_VALUE)
@pytest.mark.parametrize("n", [1, 2, 3])
@pytest.mark.parametrize("value, v", [("x[3]", lambda d: d), ("x[3] + 1", lambda d: d + 1), ("abs(x[3] - 1)", lambda d: abs(d - 1))])
def test_with_a_variable_or_an_expression_as_value(run, solver, f, n, value, v):
    terms = ", ".join(f"x[{i}]" for i in range(n))
    check(run, solver, X4 + f"satisfy({f}({terms}, value={value}))", D4, lambda *t: holds(f, t[:n], v(t[3])))


@pytest.mark.parametrize("f", WITH_VALUE)
@pytest.mark.parametrize("value", [7, -1])
def test_with_a_value_out_of_the_domains(run, solver, request, f, value):
    # no term can take the value, so that no term is counted
    bug_for(request, "ACE", KNOWN)  # ACE: A constraint Count is posted with an empty scope
    if f in ("Exist", "AtLeastOne", "AtMostOne"):
        bug_for(request, "COSOCO", KNOWN)  # cosoco: AtLeast (AtMost), all variables must contain value
    check(run, solver, X4 + f"satisfy({f}(x[:3], value={value}), x[3] != 1)", D4, lambda *t: holds(f, t[:3], value) and t[3] != 1)


# ------------------------------------------------------------------------------------------------------------ degenerated cases

EMPTY = {"Exist": False, "AtLeastOne": False, "AnyHold": False, "NotExist": True, "NoneHold": True, "ExactlyOne": False, "AtMostOne": True, "AllHold": True}


@pytest.mark.parametrize("f", FUNCTIONS)
@pytest.mark.parametrize("terms", ["[]", "()", "(x for x in [])"])
def test_on_no_term(run, solver, request, f, terms):
    if not EMPTY[f]:
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)  # the constraint false, posted by a table with an empty set of supports
    check(run, solver, B4 + f"satisfy({f}({terms}), b[3] == 0)", DB4, lambda *t: EMPTY[f] and t[3] == 0)


@pytest.mark.parametrize("f", FUNCTIONS)
@pytest.mark.parametrize("context, predicate", [
    ("{} | (b[3] == 1)", lambda e, t: e or t[3] == 1),
    ("{} | (b[2] + b[3] == 1)", lambda e, t: e or t[2] + t[3] == 1),
    ("{} & (b[3] == 1)", lambda e, t: e and t[3] == 1),
    ("~{}", lambda e, t: not e),
    ("[{}, b[3] == 1]", lambda e, t: e and t[3] == 1),
    ("imply(b[3] == 1, {})", lambda e, t: t[3] != 1 or e),
])
def test_on_no_term_in_expressions(run, solver, request, f, context, predicate):
    # another constraint (b[0] != b[1]) is posted, the model having no constraint when the expression always holds
    e = EMPTY[f]
    if not any(predicate(e, t) for t in brute_force(DB4, lambda *t: True)):
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)  # the constraint false, posted by a table with an empty set of supports
    check(run, solver, B4 + f"satisfy({context.format(f + '([])')}, b[0] != b[1])", DB4, lambda *t: predicate(e, t) and t[0] != t[1])


@pytest.mark.parametrize("f", FUNCTIONS)
@pytest.mark.parametrize("terms, values", [
    ("b[0], b[0], b[1]", lambda a, b, c, d: [a, a, b]),
    ("b[0], b[0]", lambda a, b, c, d: [a, a]),
    ("b[0], b[1], b[0], b[2]", lambda a, b, c, d: [a, b, a, c]),
])
def test_with_a_repeated_variable(run, solver, request, f, terms, values):
    # a variable repeated among the terms is counted as many times as it appears (or(b[0],b[0]) is b[0], #194)
    if not (f in EXISTS and terms == "b[0], b[0]"):
        bug_for(request, "COSOCO", REPEATED)  # cosoco: scope contains variable b[0] many times
        if f not in ("NotExist", "NoneHold", "AllHold"):  # ACE is right for (eq,0) and (eq,|X|)
            bug_for(request, "ACE", REPEATED)
    check(run, solver, B4 + f"satisfy({f}({terms}))", DB4, lambda *t: holds(f, values(*t)))


@pytest.mark.parametrize("f", FUNCTIONS)
@pytest.mark.parametrize("terms", ["b[0], 1", "b[0], 0", "b[0], 0, b[1]", "b[0], 1, b[1]", "b[:3], 1"])
@bug(INTEGERS)
def test_with_integers(run, f, terms):
    # integers among the terms are refused with an explicit error (decision of #180)
    r = run(B4 + f"satisfy({f}({terms}))")
    assert_fails(r)
    assert "does not accept integers among the terms" in r.stdout + r.stderr, r.report()


@pytest.mark.parametrize("f", FUNCTIONS)
@pytest.mark.parametrize("n", [1, 2, 3])
def test_xcsp3_count_has_at_least_two_terms(run, request, f, n):
    # XCSP3-core requires |X| >= 2 for count
    if f not in EXISTS or (n == 1 and FUNCTIONS[f][1]):  # without value, the shortcuts of Exist() return a single term (here, x[3] == 1) itself
        request.applymarker(bug(ONE_TERM))
    terms = ", ".join(f"x[{i}]" for i in range(n)) + ", value=2" if FUNCTIONS[f][1] else ", ".join(f"b[{i}]" for i in range(n))
    r = run(B4 + X4 + f"satisfy({f}({terms}), {f}(x[3] == 1))")
    assert r.ok, r.report()
    for c in r.xml.iter("count"):
        assert n_terms(c.find("list").text) >= 2, r.report()


# ------------------------------------------------------------------------------------------------ logical contexts

@pytest.mark.parametrize("f", FUNCTIONS)
@pytest.mark.parametrize("n", [1, 2, 3])
@pytest.mark.parametrize("context, predicate", [
    ("{} | (b[3] == 1)", lambda e, t: e or t[3] == 1),
    ("{} & (b[3] == 0)", lambda e, t: e and t[3] == 0),
    ("~{}", lambda e, t: not e),
    ("imply(b[3] == 1, {})", lambda e, t: t[3] != 1 or e),
    ("iff(b[3] == 1, {})", lambda e, t: (t[3] == 1) == e),
    ("b[3] == {}", lambda e, t: t[3] == e),
    ("Sum({}, b[3]) == 1", lambda e, t: e + t[3] == 1),
    ("If(b[3] == 1, Then={})", lambda e, t: t[3] != 1 or e),
])
def test_in_logical_expressions(run, solver, f, n, context, predicate):
    terms = ", ".join(f"b[{i}]" for i in range(n))
    check(run, solver, B4 + f"satisfy({context.format(f + '(' + terms + ')')})", DB4, lambda *t: predicate(holds(f, t[:n]), t))


@pytest.mark.parametrize("f", FUNCTIONS)
@pytest.mark.parametrize("context", ["{} | (x[3] == 2)", "~{}", "iff(x[3] == 2, {})"])
@bug(NOT_01)
def test_on_integer_variables_without_value_in_logical_expressions(run, f, context):
    # without value, the terms must be 0/1: an explicit error otherwise (decision of #174)
    r = run(X4 + f"satisfy({context.format(f + '(x[0], x[1])')})")
    assert_fails(r)
    assert "requires 0/1 terms" in r.stdout + r.stderr, r.report()


# ---------------------------------------------------------------------------------------------------------- groups

@pytest.mark.parametrize("f", FUNCTIONS)
def test_in_groups(run, solver, f):
    check(run, solver, B4 + f"satisfy([{f}(b[i:i + 2]) for i in range(3)])", DB4, lambda *t: all(holds(f, t[i:i + 2]) for i in range(3)))


@pytest.mark.parametrize("f", WITH_VALUE)
def test_in_groups_with_a_value(run, solver, f):
    check(run, solver, X4 + f"satisfy([{f}(x[i:i + 3], value=i) for i in range(2)])", D4, lambda *t: all(holds(f, t[i:i + 3], i) for i in range(2)))


# ------------------------------------------------------------------------------------------------------------ reified_by

REIFIED = "r = Var(dom={0, 1})\n"


@pytest.mark.parametrize("arguments, counted", [
    ("b[:3]", lambda t: [v == 1 for v in t[:3]]),
    ("b[0], b[1]", lambda t: [v == 1 for v in t[:2]]),
    ("b[0]", lambda t: [t[0] == 1]),
    ("b[:3], value=0", lambda t: [v == 0 for v in t[:3]]),
    ("b[0], value=0", lambda t: [t[0] == 0]),
    ("b[:3], value=b[3]", lambda t: [v == t[3] for v in t[:3]]),
])
def test_exist_reified(run, solver, request, arguments, counted):
    if "b[0]" not in arguments or "b[0], b[1]" in arguments:  # an element constraint is posted
        bug_for(request, "CHOCO", CHOCO_REIFIED)
        if "value=b" in arguments:
            bug_for(request, "ACE", PARSER_REIFIED)
        if solver == "COSOCO":
            pytest.skip(COSOCO_REIFIED)
    check(run, solver, B4 + REIFIED + f"satisfy(Exist({arguments}, reified_by=r))", DB4 + [(0, 1)], lambda *t: t[4] == any(counted(t)))


@pytest.mark.parametrize("arguments, counted", [
    ("x[:3], value=1", lambda t: [v == 1 for v in t[:3]]),
    ("x[:3], value=2", lambda t: [v == 2 for v in t[:3]]),
    ("x[0], value=2", lambda t: [t[0] == 2]),
    ("x[:3], value=x[3]", lambda t: [v == t[3] for v in t[:3]]),
    ("x[0], value=x[3]", lambda t: [t[0] == t[3]]),
])
def test_exist_reified_on_integer_variables(run, solver, request, arguments, counted):
    if not arguments.startswith("x[0]"):  # an element constraint is posted
        bug_for(request, "CHOCO", CHOCO_REIFIED)
        if "value=x" in arguments:
            bug_for(request, "ACE", PARSER_REIFIED)
        if solver == "COSOCO":
            pytest.skip(COSOCO_REIFIED)
    check(run, solver, X4 + REIFIED + f"satisfy(Exist({arguments}, reified_by=r))", D4 + [(0, 1)], lambda *t: t[4] == any(counted(t)))


@pytest.mark.parametrize("arguments, reason", [("x[:3]", NOT_01), ("x[0], x[1]", NOT_01), ("x[0]", REIFIED_NOT_01)])
def test_exist_reified_on_integer_variables_without_value(run, request, arguments, reason):
    # without value, the terms must be 0/1: an explicit error otherwise (decision of #174)
    request.applymarker(bug(reason))
    r = run(X4 + REIFIED + f"satisfy(Exist({arguments}, reified_by=r))")
    assert_fails(r)
    assert "requires 0/1 terms" in r.stdout + r.stderr, r.report()


@pytest.mark.parametrize("terms", ["b[:3]", "b[0]"])
def test_exist_reified_by_a_negation(run, solver, request, terms):
    # with ~r, r is 1 iff no term is counted
    n = 3 if terms == "b[:3]" else 1
    if n == 3:
        bug_for(request, "CHOCO", CHOCO_REIFIED)
        if solver == "COSOCO":
            pytest.skip(COSOCO_REIFIED)
    check(run, solver, B4 + REIFIED + f"satisfy(Exist({terms}, reified_by=~r))", DB4 + [(0, 1)], lambda *t: t[4] == (1 not in t[:n]))


@bug(REIFIED_EMPTY)
def test_exist_reified_on_no_term(run, solver):
    check(run, solver, B4 + REIFIED + "satisfy(Exist([], reified_by=r))", DB4 + [(0, 1)], lambda *t: t[4] == 0)


@pytest.mark.parametrize("context, predicate", [
    ("{} | (b[3] == 1)", lambda r, t: r == 1 or t[3] == 1),
    ("{} & (b[3] == 1)", lambda r, t: r == 1 and t[3] == 1),
    ("~{}", lambda r, t: r == 0),
    ("imply(b[3] == 1, {})", lambda r, t: t[3] != 1 or r == 1),
])
@pytest.mark.parametrize("terms", ["b[:3]", "b[0], b[1]"])
@bug(REIFIED_LOST)
def test_exist_reified_in_logical_expressions(run, solver, context, predicate, terms):
    # the constraint Exist (r is 1 iff a term is 1) holds, and r is then used in the expression
    n = 3 if terms == "b[:3]" else 2
    check(run, solver, B4 + REIFIED + f"satisfy({context.format('Exist(' + terms + ', reified_by=r)')})", DB4 + [(0, 1)],
          lambda *t: t[4] == (1 in t[:n]) and predicate(t[4], t))


@pytest.mark.parametrize("constraint", ["Exist(b, reified_by=x[0])", "Exist(b, reified_by=1)", "Exist(b, reified_by=b[0] + b[1])"])
@bug(REIFIED_INVALID)
def test_exist_reified_by_an_invalid_argument(run, constraint):
    r = run(B4 + X4 + f"satisfy({constraint})")
    assert not r.ok and r.error is not None and "reified_by" in r.error, r.report()


# ------------------------------------------------------------------------------------------------------------ options

@pytest.mark.parametrize("f", FUNCTIONS)
@pytest.mark.parametrize("n", [2, 4])
def test_with_mini(run, solver, f, n):
    terms = ", ".join(f"b[{i}]" for i in range(n))
    check(run, solver, B4 + f"satisfy({f}({terms}))", DB4, lambda *t: holds(f, t[:n]), args=("-mini",))


@pytest.mark.parametrize("f", FUNCTIONS)
def test_xcsp3_with_mini(run, f):
    # in the mini-tracks, the 0/1 variables are summed (and not counted)
    r = run(B4 + f"satisfy({f}(b))", args=("-mini",))
    assert r.ok, r.report()
    assert r.xml.find("constraints/count") is None, r.report()


@pytest.mark.parametrize("constraint, predicate", [
    ("Exist(b)", lambda *t: 1 in t),
    ("Exist(b[0], b[1])", lambda *t: 1 in t[:2]),
    ("Exist(b[0])", lambda *t: t[0] == 1),
    ("AtLeastOne(b, value=0)", lambda *t: 0 in t),
    ("AnyHold(b[:3])", lambda *t: 1 in t[:3]),
    ("Exist(b[:3]) | (b[3] == 1)", lambda *t: 1 in t),
    ("~Exist(b[:3])", lambda *t: 1 not in t[:3]),
    ("[Exist(b[i:i + 2]) for i in range(0, 4, 2)]", lambda *t: 1 in t[:2] and 1 in t[2:]),
])
def test_exist_by_element(run, solver, request, constraint, predicate):
    # with the option -exist_by_element, Exist() posts an element constraint reified by a new variable, which must be 1
    if constraint not in ("Exist(b[0], b[1])", "Exist(b[0])", "[Exist(b[i:i + 2]) for i in range(0, 4, 2)]"):
        bug_for(request, "CHOCO", CHOCO_REIFIED)
        if solver == "COSOCO":
            pytest.skip(COSOCO_REIFIED)
    check(run, solver, B4 + f"satisfy({constraint})", DB4, predicate, args=("-exist_by_element",))


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("f, expected", [
    ("Exist", ("1", "(ge,1)")),
    ("AtLeastOne", ("1", "(ge,1)")),
    ("AnyHold", ("1", "(ge,1)")),
    ("NotExist", ("1", "(eq,0)")),
    ("NoneHold", ("1", "(eq,0)")),
    ("ExactlyOne", ("1", "(eq,1)")),
    ("AtMostOne", ("1", "(le,1)")),
    ("AllHold", ("1", "(eq,4)")),
])
def test_xcsp3(run, f, expected):
    r = run(B4 + f"satisfy({f}(b))")
    assert r.ok, r.report()
    c = r.xml.find("constraints/count")
    assert c is not None and " ".join(c.find("list").text.split()) == "b[]", r.report()
    assert (" ".join(c.find("values").text.split()), c.find("condition").text.strip()) == expected, r.report()


@pytest.mark.parametrize("f", WITH_VALUE)
def test_xcsp3_with_a_value(run, f):
    r = run(X4 + f"satisfy({f}(x[:3], value=x[3]))")
    assert r.ok, r.report()
    assert " ".join(r.xml.find("constraints/count/values").text.split()) == "x[3]", r.report()


# ------------------------------------------------------------------------------------------------ examples of the doc

def test_exist_example(run, solver):
    neighbours = [[0, 1, 2], [0, 1, 3], [0, 2, 4], [1, 3, 5], [2, 4, 5], [3, 4, 5]]
    check(run, solver, f"b = VarArray(size=6, dom={{0, 1}})\nsatisfy(Sum(b) == 2, [Exist(b[j] for j in {neighbours}[i]) for i in range(6)])",
          [(0, 1)] * 6, lambda *t: sum(t) == 2 and all(any(t[j] for j in neighbours[i]) for i in range(6)))


def test_exist_example_with_reified_by(run, solver, request):
    bug_for(request, "CHOCO", CHOCO_REIFIED)
    if solver == "COSOCO":
        pytest.skip(COSOCO_REIFIED)
    check(run, solver, "b = VarArray(size=5, dom={0, 1})\nr = Var(dom={0, 1})\nsatisfy(Sum(b) == 1, Exist(b[0], b[1], reified_by=r))",
          [(0, 1)] * 6, lambda *t: sum(t[:5]) == 1 and t[5] == (t[0] or t[1]))


def test_notexist_example(run, solver):
    check(run, solver, "x = VarArray(size=7, dom=range(3))\nsatisfy(Count(x, value=2) == 2, NotExist([x[5] == 2, x[6] == 2]))", [range(3)] * 7,
          lambda *t: t.count(2) == 2 and t[5] != 2 and t[6] != 2)


def test_exactlyone_example(run, solver):
    check(run, solver, "b = VarArray(size=[4, 3], dom={0, 1})\nsatisfy([ExactlyOne(b[i]) for i in range(4)])", [(0, 1)] * 12,
          lambda *t: all(sum(t[3 * i:3 * i + 3]) == 1 for i in range(4)))


def test_atleastone_example(run, solver):
    covers = [[0, 2], [1, 3], [0, 4], [2, 3, 4]]
    check(run, solver, f"b = VarArray(size=5, dom={{0, 1}})\nsatisfy([AtLeastOne(b[i] for i in c) for c in {covers}])", [(0, 1)] * 5,
          lambda *t: all(any(t[i] for i in c) for c in covers))


def test_atmostone_example(run, solver):
    incompatible = [(0, 1, 2), (2, 3), (3, 4)]
    check(run, solver, f"b = VarArray(size=5, dom={{0, 1}})\nsatisfy(Sum(b) == 2, [AtMostOne(b[i] for i in g) for g in {incompatible}])",
          [(0, 1)] * 5, lambda *t: sum(t) == 2 and all(sum(t[i] for i in g) <= 1 for g in incompatible))


def test_anyhold_example(run, solver):
    check(run, solver, "x = VarArray(size=4, dom=range(5))\nsatisfy(AllDifferent(x), AnyHold(x[i] == 0 for i in range(4)))", [range(5)] * 4,
          lambda *t: len(set(t)) == 4 and 0 in t)


def test_nonehold_example(run, solver):
    check(run, solver, "x = VarArray(size=5, dom=range(3))\nsatisfy(Count(x, value=1) == 2, NoneHold(both(x[i] == 1, x[i + 1] == 1) for i in range(4)))",
          [range(3)] * 5, lambda *t: t.count(1) == 2 and not any(t[i] == 1 and t[i + 1] == 1 for i in range(4)))


def test_allhold_example(run, solver):
    precedences = [(0, 1), (0, 2), (1, 3), (2, 3)]
    check(run, solver, f"s = VarArray(size=4, dom=range(8))\nsatisfy(AllHold(s[i] + 3 <= s[j] for (i, j) in {precedences}))", [range(8)] * 4,
          lambda *t: all(t[i] + 3 <= t[j] for (i, j) in precedences))


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("f", WITH_VALUE)
@pytest.mark.parametrize("value, message", [
    ("True", "Count() does not accept Booleans as values"),
    ("1.5", "Count() requires an integer, a variable or an expression as value"),
    ("'a'", "Count() requires an integer, a variable or an expression as value"),
    ("[1, 2]", "Count() requires an integer, a variable or an expression as value"),
])
@bug(INVALID)
def test_invalid_value(run, f, value, message):
    r = run(X4 + f"satisfy({f}(x, value={value}))")
    assert_fails(r)
    assert message in r.stdout + r.stderr, r.report()


@pytest.mark.parametrize("f", FUNCTIONS)
def test_invalid_parameter_values(run, f):
    # only Count() has the parameter values
    assert_fails(run(X4 + f"satisfy({f}(x, values=[1, 2]))"))


@pytest.mark.parametrize("f", ["AnyHold", "NoneHold", "AllHold"])
def test_invalid_parameter_value(run, f):
    assert_fails(run(X4 + f"satisfy({f}(x, value=1))"))


@pytest.mark.parametrize("f", FUNCTIONS)
@bug(INVALID)
def test_invalid_symbolic_variables(run, f):
    r = run(f"s = VarArray(size=3, dom={{'a', 'b'}})\nsatisfy({f}(s{', value=' + repr('a') if FUNCTIONS[f][1] else ''}))")
    assert_fails(r)
    assert "Count() requires integer variables" in r.stdout + r.stderr or "requires 0/1 terms" in r.stdout + r.stderr, r.report()
