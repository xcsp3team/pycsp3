"""
Tests of the constraint Cardinality of the section Constraints (Global) of the API (https://pycsp.org/documentation/api/constraints-global/#Cardinality):
the function Cardinality(), with occurrences given by integers, ranges and variables, values given by integers and variables, the parameter
closed, on variables and on expressions, in groups of constraints and in logical expressions.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
According to XCSP3-core, cardinality(X, V, O) holds iff, for each j, the number of variables of X assigned the value v[j] is o[j] (an integer, a
variable, or an interval of integers), and with closed="true", each variable of X must also be assigned a value of V; X is a list of (at least two)
variables, V is a list of integers or a list of variables, O is a list of integers, of variables or of intervals, with |V| = |O| >= 1.
As decided in #226, a number of occurrences given by a range or a collection must be a non-empty set of contiguous integers (A), the integers mixed
with variables are replaced by auxiliary variables (B), the numbers of occurrences known when compiling are evaluated by PyCSP3 (C), and a variable
cannot be given several times in the list (D).
"""

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
RANGES = ("#227: a number of occurrences given by an empty range is written 0, and by a range with a step as an interval (the step "
          "being ignored), instead of an explicit error (decision A of #226)")
COLLECTIONS = ("#228: a number of occurrences given by a collection of integers (list, tuple, set) is written as in Python (e.g. [1, 3]) in the "
               "element <occurs>, unless it is a sorted list of contiguous integers; an empty or non-contiguous collection must be refused (decision A "
               "of #226)")
EXPRESSIONS = ("#229: a number of occurrences given by an expression is written as such in the element <occurs>, and a value given by an "
               "expression is refused by an assert without message, instead of being replaced by an auxiliary variable")
MIXED = ("#230: occurrences mixing variables with integers or intervals, and values mixing variables and integers, are not XCSP3-core: ACE "
         "and CHOCO fail (Pb, ClassCastException), cosoco crashes or ignores the variables")
SINGLE_TERM = "#231: a constraint cardinality is written on a single term, whereas XCSP3-core requires at least two"
NO_TERM = "#232: Cardinality() on no term fails with an assert without message, unless each number of occurrences can be 0"
NO_VALUE = "#233: Cardinality() without value writes empty elements <values> and <occurs>, whereas XCSP3-core requires at least one value"
INVALID = "#234: invalid arguments of Cardinality() refused by an assert without message, or accepted and written as such in the XCSP3 file"
LOGICAL = ("#235: Cardinality() in a logical expression gives a meta-constraint (or, and, iff, xor), an assert without message or a TypeError, "
           "and is silently discarded by both(), either(), conjunction() and disjunction()")
ACE_ALL = ("xcsp3team/ACE#29: ACE finds wrong solutions when the number of occurrences of a value is the number of variables, the value not being the "
           "smallest one of the domains")
ACE_ALLDIFFERENT = ("xcsp3team/ACE#30: ACE posts allDifferent when each value can be assigned at most once (with closed, or domains included in the "
                    "values), ignoring that some values must be assigned")
KNOWN = ("#237: numbers of occurrences known when compiling (negative, greater than the number of terms, values that no term can take) are written as "
         "such: ACE fails without message, cosoco crashes on values greater than the values of the domains")
REPEATED = "#238: a variable given several times in the list of Cardinality() is accepted (ACE gives wrong solutions), instead of an explicit error"
ACE_FAILS = ("(to be reported) ACE fails without message when the number of occurrences is 0 for all the values, or when a value in no domain has a "
             "variable as number of occurrences")
ACE_RANGE = "xcsp3team/ACE#31: ACE excludes the upper bound of an interval of occurrences when the values are variables (Range is half-open)"
COSOCO_CLOSED = "(to be reported) cosoco ignores closed=\"true\""
COSOCO_OUTSIDE = ("(to be reported) cosoco crashes (heap overflow: malloc(): corrupted top size) when a value greater than the values of the domains "
                  "has a variable as number of occurrences")
CHOCO_VALUES_CLOSED = ("(to be reported) CHOCO 4.10.15-beta (embedded in PyCSP3) finds solutions several times with variables as values and closed, "
                       "and CHOCO 6.0.2 fails (ClassCastException: SetVarImpl cannot be cast to IntVar)")

# The cases that a solver says it does not handle, and the symbolic variables (not reported)
ACE_VALUES_CLOSED = "ACE does not handle cardinality with variables as values and closed (unimplemented case for the moment)"
COSOCO_VALUES = "cosoco does not handle cardinality with variables as values (not yet supported, s UNSUPPORTED)"
SYMBOLIC = "cardinality on symbolic variables is not part of XCSP3-core"
ALL = ("ACE", "CHOCO", "COSOCO")


def card(t, occurrences, closed=False):
    """
    Returns True if the tuple t satisfies the constraint cardinality with the specified occurrences, a list of pairs (v, o), where v is a value and o
    the number of occurrences of v (an integer), or the collection of the possible numbers of occurrences of v; with closed, each value of t is one of v.
    """
    return all(t.count(v) == o if isinstance(o, int) else t.count(v) in o for v, o in occurrences) and (not closed or all(
        w in [v for v, _ in occurrences] for w in t))


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


X4 = "x = VarArray(size=4, dom=range(3))\n"
D4 = [range(3)] * 4
XZ = X4 + "z = Var(dom=range(5))\n"  # z is a possible number of occurrences
DZ = D4 + [range(5)]
XV = "x = VarArray(size=3, dom=range(3))\nv = VarArray(size=2, dom=range(3))\n"  # v[0] and v[1] are possible values
DV = [range(3)] * 5


# ------------------------------------------------------------------------------------------------------------ occurrences

@pytest.mark.parametrize("occurrences, expected", [
    ("{0: 1, 1: 2}", [(0, 1), (1, 2)]),
    ("{0: 1, 1: 2, 2: 1}", [(0, 1), (1, 2), (2, 1)]),
    ("{0: 2}", [(0, 2)]),
    ("{2: 4}", [(2, 4)]),
    ("{0: 0}", [(0, 0)]),
    ("{0: 0, 1: 0}", [(0, 0), (1, 0)]),
    ("{1: 0, 2: 3}", [(1, 0), (2, 3)]),
    ("{0: range(1, 3), 1: 2}", [(0, range(1, 3)), (1, 2)]),
    ("{0: range(1, 3), 1: range(0, 2)}", [(0, range(1, 3)), (1, range(0, 2))]),
    ("{0: range(2, 5)}", [(0, range(2, 5))]),
    ("{0: range(1, 2)}", [(0, 1)]),
    ("{0: range(0, 5)}", [(0, range(0, 5))]),
    ("{0: range(0, 2), 1: range(0, 2), 2: range(0, 2)}", [(0, range(0, 2)), (1, range(0, 2)), (2, range(0, 2))]),
    ("{0: 1, 1: range(1, 3)}", [(0, 1), (1, range(1, 3))]),
    ("{-1: 0, 0: 1}", [(-1, 0), (0, 1)]),
    ("{0: 1, 7: 0}", [(0, 1), (7, 0)]),
    ("{2: 1, 0: 2}", [(2, 1), (0, 2)]),
    ("[1, 2, 1]", [(0, 1), (1, 2), (2, 1)]),
    ("(2, 2)", [(0, 2), (1, 2)]),
    ("[range(1, 3), 2]", [(0, range(1, 3)), (1, 2)]),
    ("{v: 1 for v in range(2)}", [(0, 1), (1, 1)]),
])
def test_cardinality_occurrences(run, solver, request, occurrences, expected):
    if occurrences in ("{0: 0}", "{0: 0, 1: 0}"):
        bug_for(request, "ACE", ACE_FAILS)
    if occurrences == "{0: 1, 7: 0}":
        bug_for(request, "COSOCO", KNOWN)
    check(run, solver, X4 + f"satisfy(Cardinality(x, occurrences={occurrences}))", D4, lambda *t: card(t, expected))


@pytest.mark.parametrize("occurrences, expected", [
    ("{0: 1, 1: 2}", [(0, 1), (1, 2)]),
    ("{0: 2, 1: 2}", [(0, 2), (1, 2)]),
    ("{0: range(1, 3), 1: range(1, 3)}", [(0, range(1, 3)), (1, range(1, 3))]),
    ("{0: range(0, 5)}", [(0, range(0, 5))]),
    ("{1: range(0, 5), 2: range(0, 5)}", [(1, range(0, 5)), (2, range(0, 5))]),
    ("{0: 4}", [(0, 4)]),
    ("{0: 0, 1: 4}", [(0, 0), (1, 4)]),
    ("{0: 1, 1: 1, 2: 2}", [(0, 1), (1, 1), (2, 2)]),
    ("{0: 1, 1: 1, 2: 1}", [(0, 1), (1, 1), (2, 1)]),
    ("{0: 1, 7: 3}", [(0, 1), (7, 3)]),
])
def test_cardinality_closed(run, solver, request, occurrences, expected):
    if occurrences == "{0: 1, 7: 3}":
        bug_for(request, ("ACE", "COSOCO"), KNOWN)
    if occurrences in ("{0: 1, 1: 2}", "{0: range(1, 3), 1: range(1, 3)}", "{0: range(0, 5)}", "{1: range(0, 5), 2: range(0, 5)}"):
        bug_for(request, "COSOCO", COSOCO_CLOSED)
    check(run, solver, X4 + f"satisfy(Cardinality(x, occurrences={occurrences}, closed=True))", D4, lambda *t: card(t, expected, closed=True))


@pytest.mark.parametrize("closed", ["False", "None"])
def test_cardinality_not_closed(run, solver, closed):
    check(run, solver, X4 + f"satisfy(Cardinality(x, occurrences={{0: 1, 1: 2}}, closed={closed}))", D4, lambda *t: card(t, [(0, 1), (1, 2)]))


@pytest.mark.parametrize("n, occurrences, closed, expected", [
    (2, "{0: 1, 1: 1, 2: 1}", False, [(0, 1), (1, 1), (2, 1)]),
    (2, "{0: 1, 1: 1, 2: 1}", True, [(0, 1), (1, 1), (2, 1)]),
    (3, "{0: 1, 1: 1, 2: 1}", True, [(0, 1), (1, 1), (2, 1)]),
    (2, "{0: range(0, 2), 1: range(0, 2), 2: 1}", True, [(0, range(0, 2)), (1, range(0, 2)), (2, 1)]),
    (2, "{0: range(0, 2), 1: range(0, 2), 2: 1}", False, [(0, range(0, 2)), (1, range(0, 2)), (2, 1)]),
    (3, "{0: 1, 1: 1}", True, [(0, 1), (1, 1)]),
    (2, "{0: 1, 1: 1}", True, [(0, 1), (1, 1)]),
    (2, "{0: 1, 1: range(0, 2)}", True, [(0, 1), (1, range(0, 2))]),
], ids=["2 vars 3 values once", "2 vars 3 values once closed", "3 vars 3 values once closed", "2 vars one value required closed",
        "2 vars one value required", "3 vars 2 values once closed", "2 vars 2 values once closed", "2 vars 0 required closed"])
def test_cardinality_with_values_at_most_once(run, solver, request, n, occurrences, closed, expected):
    # each value can be assigned at most once, which looks like an allDifferent, but the occurrences must still be respected
    if n == 2 and occurrences in ("{0: 1, 1: 1, 2: 1}", "{0: range(0, 2), 1: range(0, 2), 2: 1}"):
        bug_for(request, "ACE", ACE_ALLDIFFERENT)
    if closed and (n, occurrences) in ((3, "{0: 1, 1: 1}"), (2, "{0: 1, 1: range(0, 2)}")):
        bug_for(request, "COSOCO", COSOCO_CLOSED)
    check(run, solver, f"x = VarArray(size={n}, dom=range(3))\nsatisfy(Cardinality(x, occurrences={occurrences}, closed={closed}))", [range(3)] * n,
          lambda *t: card(t, expected, closed=closed))


# ------------------------------------------------------------------------------------------ occurrences given by variables

@pytest.mark.parametrize("occurrences, predicate", [
    ("{0: z}", lambda *t: card(t[:4], [(0, t[4])])),
    ("{2: z}", lambda *t: card(t[:4], [(2, t[4])])),
    ("{0: z, 1: z}", lambda *t: card(t[:4], [(0, t[4]), (1, t[4])])),
    ("{0: z, 1: 2}", lambda *t: card(t[:4], [(0, t[4]), (1, 2)])),
    ("{0: 1, 1: z}", lambda *t: card(t[:4], [(0, 1), (1, t[4])])),
    ("{0: z, 1: range(1, 3)}", lambda *t: card(t[:4], [(0, t[4]), (1, range(1, 3))])),
    ("[range(0, 2), z, 1]", lambda *t: card(t[:4], [(0, range(0, 2)), (1, t[4]), (2, 1)])),
    ("{7: z}", lambda *t: t[4] == 0),
    ("{0: z, 7: z}", lambda *t: t[4] == 0 and card(t[:4], [(0, 0)])),
])
def test_cardinality_occurrences_given_by_variables(run, solver, request, occurrences, predicate):
    if occurrences in ("{0: z, 1: 2}", "{0: 1, 1: z}", "{0: z, 1: range(1, 3)}", "[range(0, 2), z, 1]"):
        bug_for(request, ALL, MIXED)
    if "7" in occurrences:
        bug_for(request, "ACE", ACE_FAILS)
    if occurrences == "{0: z, 7: z}":
        bug_for(request, "COSOCO", COSOCO_OUTSIDE)
    check(run, solver, XZ + f"satisfy(Cardinality(x, occurrences={occurrences}))", DZ, predicate)


def test_cardinality_occurrences_given_by_a_variable_with_negative_values(run, solver):
    check(run, solver, X4 + "w = Var(dom=range(-2, 3))\nsatisfy(Cardinality(x, occurrences={0: w, 1: w}))", D4 + [range(-2, 3)],
          lambda *t: card(t[:4], [(0, t[4]), (1, t[4])]))


@pytest.mark.parametrize("occurrences, predicate", [
    ("{0: z}", lambda *t: card(t[:4], [(0, t[4])], closed=True)),
    ("{0: z, 1: z}", lambda *t: card(t[:4], [(0, t[4]), (1, t[4])], closed=True)),
    ("{0: z, 1: 2}", lambda *t: card(t[:4], [(0, t[4]), (1, 2)], closed=True)),
])
def test_cardinality_occurrences_given_by_variables_closed(run, solver, request, occurrences, predicate):
    bug_for(request, ALL if occurrences == "{0: z, 1: 2}" else "COSOCO", MIXED if occurrences == "{0: z, 1: 2}" else COSOCO_CLOSED)
    check(run, solver, XZ + f"satisfy(Cardinality(x, occurrences={occurrences}, closed=True))", DZ, predicate)


@pytest.mark.parametrize("constraint, predicate", [
    ("Cardinality(x[:3], occurrences={0: x[3]})", lambda *t: card(t[:3], [(0, t[3])])),
    ("Cardinality(x[:3], occurrences={0: x[3], 1: x[3]})", lambda *t: card(t[:3], [(0, t[3]), (1, t[3])])),
    ("Cardinality(x, occurrences={0: x[0]})", lambda *t: card(t, [(0, t[0])])),
    ("Cardinality(x, occurrences={1: x[0], 2: x[1]})", lambda *t: card(t, [(1, t[0]), (2, t[1])])),
])
def test_cardinality_occurrences_given_by_variables_of_the_list(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


@pytest.mark.parametrize("occurrences, predicate", [
    ("{0: z + 1}", lambda *t: card(t[:4], [(0, t[4] + 1)])),
    ("{0: abs(z - 2)}", lambda *t: card(t[:4], [(0, abs(t[4] - 2))])),
    ("{0: z, 1: z - 1}", lambda *t: card(t[:4], [(0, t[4]), (1, t[4] - 1)])),
    ("{0: Sum(x[:2])}", lambda *t: card(t[:4], [(0, t[0] + t[1])])),
])
def test_cardinality_occurrences_given_by_expressions(run, solver, request, occurrences, predicate):
    bug_for(request, ALL, EXPRESSIONS)
    check(run, solver, XZ + f"satisfy(Cardinality(x, occurrences={occurrences}))", DZ, predicate)


# ------------------------------------------------------------------------------------------ values given by variables

@pytest.mark.parametrize("occurrences, predicate", [
    ("{v[0]: 1}", lambda *t: card(t[:3], [(t[3], 1)])),
    ("{v[0]: 2}", lambda *t: card(t[:3], [(t[3], 2)])),
    ("{v[0]: 0}", lambda *t: card(t[:3], [(t[3], 0)])),
    ("{v[0]: 1, v[1]: 2}", lambda *t: card(t[:3], [(t[3], 1), (t[4], 2)])),
    ("{v[0]: range(1, 3)}", lambda *t: card(t[:3], [(t[3], range(1, 3))])),
    ("{v[0]: range(0, 2), v[1]: range(2, 4)}", lambda *t: card(t[:3], [(t[3], range(0, 2)), (t[4], range(2, 4))])),
    ("{v[0]: v[1]}", lambda *t: card(t[:3], [(t[3], t[4])])),
    ("{v[0]: 1, 2: 2}", lambda *t: card(t[:3], [(t[3], 1), (2, 2)])),
    ("{2: 1, v[0]: 1}", lambda *t: card(t[:3], [(2, 1), (t[3], 1)])),
])
def test_cardinality_values_given_by_variables(run, solver, request, occurrences, predicate):
    if occurrences in ("{v[0]: 1, 2: 2}", "{2: 1, v[0]: 1}"):
        bug_for(request, ALL, MIXED)
    elif solver == "COSOCO":
        pytest.skip(COSOCO_VALUES)
    if "range" in occurrences:
        bug_for(request, "ACE", ACE_RANGE)
    check(run, solver, XV + f"satisfy(Cardinality(x, occurrences={occurrences}))", DV, predicate)


@pytest.mark.parametrize("occurrences, predicate", [
    ("{v[0]: 1, v[1]: 1}", lambda *t: card(t[:3], [(t[3], 1), (t[4], 1)])),
    ("{v[0]: 0, v[1]: 1}", lambda *t: card(t[:3], [(t[3], 0), (t[4], 1)])),
    ("{v[0]: 2, v[1]: 1}", lambda *t: card(t[:3], [(t[3], 2), (t[4], 1)])),
])
def test_cardinality_values_given_by_variables_possibly_equal(run, solver, occurrences, predicate):
    # two variables of values may be assigned the same value: the numbers of occurrences of this value must then be both respected
    if solver == "COSOCO":
        pytest.skip(COSOCO_VALUES)
    check(run, solver, XV + f"satisfy(Cardinality(x, occurrences={occurrences}))", DV, predicate)


@pytest.mark.parametrize("occurrences, predicate", [
    ("{v[0]: 1, v[1]: 2}", lambda *t: card(t[:3], [(t[3], 1), (t[4], 2)], closed=True)),
    ("{v[0]: 3}", lambda *t: card(t[:3], [(t[3], 3)], closed=True)),
    ("{v[0]: range(1, 4), v[1]: range(0, 3)}", lambda *t: card(t[:3], [(t[3], range(1, 4)), (t[4], range(0, 3))], closed=True)),
])
def test_cardinality_values_given_by_variables_closed(run, solver, request, occurrences, predicate):
    if solver in ("ACE", "COSOCO"):
        pytest.skip(ACE_VALUES_CLOSED if solver == "ACE" else COSOCO_VALUES)
    bug_for(request, "CHOCO", CHOCO_VALUES_CLOSED)
    check(run, solver, XV + f"satisfy(Cardinality(x, occurrences={occurrences}, closed=True))", DV, predicate)


@pytest.mark.parametrize("occurrences, predicate", [
    ("{v[0] + 1: 1}", lambda *t: card(t[:3], [(t[3] + 1, 1)])),
    ("{abs(v[0] - v[1]): 2}", lambda *t: card(t[:3], [(abs(t[3] - t[4]), 2)])),
])
def test_cardinality_values_given_by_expressions(run, solver, request, occurrences, predicate):
    if solver == "COSOCO":
        pytest.skip(COSOCO_VALUES)
    bug_for(request, ("ACE", "CHOCO"), EXPRESSIONS)
    check(run, solver, XV + f"satisfy(Cardinality(x, occurrences={occurrences}))", DV, predicate)


def test_cardinality_values_given_by_variables_of_the_list(run, solver):
    if solver == "COSOCO":
        pytest.skip(COSOCO_VALUES)
    check(run, solver, X4 + "satisfy(Cardinality(x, occurrences={x[0]: 2}))", D4, lambda *t: t.count(t[0]) == 2)


# ------------------------------------------------------------------------------------------------- unusual occurrences

@pytest.mark.parametrize("occurrences, expected", [
    ("{0: 5}", [(0, 5)]),
    ("{0: -1}", [(0, -1)]),
    ("{0: 1, 1: -1}", [(0, 1), (1, -1)]),
    ("{7: 2}", [(7, 2)]),
    ("{0: 3, 1: 3}", [(0, 3), (1, 3)]),
    ("{0: range(5, 8)}", [(0, range(5, 8))]),
    ("{0: range(-2, 1)}", [(0, range(-2, 1))]),
    ("{0: range(-2, 2), 1: 2}", [(0, range(-2, 2)), (1, 2)]),
    ("{0: range(0, 9)}", [(0, range(0, 9))]),
])
def test_cardinality_with_unreachable_occurrences(run, solver, request, occurrences, expected):
    # numbers of occurrences that cannot be reached (negative, greater than the number of terms) or always reached
    if "-" in occurrences or "7" in occurrences:
        bug_for(request, "ACE", KNOWN)
    check(run, solver, X4 + f"satisfy(Cardinality(x, occurrences={occurrences}), x[3] != 1)", D4, lambda *t: card(t, expected) and t[3] != 1)


@pytest.mark.parametrize("occurrences, written", [
    ("{0: -1}", None),
    ("{0: 5}", None),
    ("{7: 2}", None),
    ("{0: range(5, 8)}", None),
    ("{0: range(-2, 1)}", ("0", "0")),
    ("{0: range(-2, 2), 1: 2}", ("0 1", "0..1 2")),
    ("{0: range(0, 9)}", ("0", "0..4")),
    ("{0: 1, 7: 0}", ("0", "1")),
    ("{0: 1, 7: range(0, 2)}", ("0", "1")),
])
@bug(KNOWN)
def test_xcsp3_cardinality_known_when_compiling(run, occurrences, written):
    # the numbers of occurrences are between 0 and the number of terms, and a value that no term can take has 0 occurrences: the constraint is false
    # (None), or written with intervals restricted to 0..len(X) and without the values that no term can take (decision C of #226)
    r = run(X4 + f"satisfy(Cardinality(x, occurrences={occurrences}), x[3] != 1)")
    assert r.ok, r.report()
    c = r.xml.find("constraints/cardinality")
    if written is None:
        assert c is None and "trivially false" in r.stdout, r.report()
    else:
        assert c is not None and (" ".join(c.find("values").text.split()), " ".join(c.find("occurs").text.split())) == written, r.report()


@pytest.mark.parametrize("occurrences", [
    pytest.param("{0: range(0)}", marks=bug(RANGES)),
    pytest.param("{0: range(3, 1)}", marks=bug(RANGES)),
    pytest.param("{0: range(1, 3), 1: range(2, 2)}", marks=bug(RANGES)),
    pytest.param("{0: range(0, 5, 2)}", marks=bug(RANGES)),
    pytest.param("{0: range(1, 4, 2), 1: 1}", marks=bug(RANGES)),
    pytest.param("{0: []}", marks=bug(COLLECTIONS)),
    pytest.param("{0: set()}", marks=bug(COLLECTIONS)),
    pytest.param("{0: ()}", marks=bug(COLLECTIONS)),
    pytest.param("{0: [1, 3]}", marks=bug(COLLECTIONS)),
    pytest.param("{0: [3, 1]}", marks=bug(COLLECTIONS)),
    pytest.param("{0: {1, 3}}", marks=bug(COLLECTIONS)),
    pytest.param("{0: (1, 3)}", marks=bug(COLLECTIONS)),
    pytest.param("{0: {0, 2}, 1: [1, 2]}", marks=bug(COLLECTIONS)),
])
def test_cardinality_with_empty_or_non_contiguous_occurrences(run, occurrences):
    # an empty range or collection, or integers that are not contiguous, are refused with an explicit error (decision A of #226)
    assert_fails(run(X4 + f"satisfy(Cardinality(x, occurrences={occurrences}))"))


@pytest.mark.parametrize("occurrences, expected", [
    ("{0: range(3, 0, -1)}", [(0, range(3, 0, -1))]),
    ("{0: range(1, 3, 1)}", [(0, range(1, 3))]),
    ("{0: [1, 2]}", [(0, [1, 2])]),
    ("{0: [1, 2, 3]}", [(0, [1, 2, 3])]),
    ("{0: [2]}", [(0, [2])]),
    pytest.param("{0: [3, 2]}", [(0, [2, 3])], marks=bug(COLLECTIONS)),
    pytest.param("{0: (1, 2)}", [(0, [1, 2])], marks=bug(COLLECTIONS)),
    pytest.param("{0: {1, 2}}", [(0, [1, 2])], marks=bug(COLLECTIONS)),
    pytest.param("{0: frozenset({0, 1}), 1: (2,)}", [(0, [0, 1]), (1, [2])], marks=bug(COLLECTIONS)),
])
def test_cardinality_with_contiguous_occurrences(run, solver, occurrences, expected):
    # a range or a collection of contiguous integers gives the possible numbers of occurrences (an interval)
    check(run, solver, X4 + f"satisfy(Cardinality(x, occurrences={occurrences}))", D4, lambda *t: card(t, expected))


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
    "x, None",
    "[x[0], None, x[1]], x[2:]",
])
def test_cardinality_forms(run, solver, terms):
    check(run, solver, X4 + f"satisfy(Cardinality({terms}, occurrences={{0: 1, 1: range(1, 3)}}))", D4, lambda *t: card(t, [(0, 1), (1, range(1, 3))]))


@pytest.mark.parametrize("n, d, occurrences, expected", [
    (2, 2, "{0: 1}", [(0, 1)]),
    (2, 3, "{0: 1, 1: 1}", [(0, 1), (1, 1)]),
    (3, 3, "{0: 1, 1: 1, 2: 1}", [(0, 1), (1, 1), (2, 1)]),
    (5, 2, "{0: range(2, 4)}", [(0, range(2, 4))]),
    (2, 5, "{4: 2}", [(4, 2)]),
    (6, 3, "{0: 2, 1: 2, 2: 2}", [(0, 2), (1, 2), (2, 2)]),
])
def test_cardinality_sizes(run, solver, request, n, d, occurrences, expected):
    if occurrences == "{4: 2}":
        bug_for(request, "ACE", ACE_ALL)
    check(run, solver, f"x = VarArray(size={n}, dom=range({d}))\nsatisfy(Cardinality(x, occurrences={occurrences}))", [range(d)] * n,
          lambda *t: card(t, expected))


@pytest.mark.parametrize("occurrences, expected", [
    ("{0: 500}", [(0, 0)]),
    ("{0: range(499, 501)}", [(0, 0), (0, 1), (1, 0)]),
    ("{0: 500, 1: 501}", [(0, 0)]),
    ("{1: 503}", [(1, 1)]),
])
def test_cardinality_on_many_variables(run, solver, occurrences, expected):
    # more than 1000 variables, all fixed except x[0] and x[1] (498 variables are fixed to 0, and 501 to 1)
    r = run("x = VarArray(size=1001, dom={0, 1})\n"
            f"satisfy(Cardinality(x, occurrences={occurrences}), [x[i] == (0 if i < 500 else 1) for i in range(2, 1001)])", solver=solver)
    assert_solutions(r, {t + tuple(0 if i < 500 else 1 for i in range(2, 1001)) for t in expected})


def test_cardinality_on_a_matrix(run, solver):
    check(run, solver, "m = VarArray(size=[2, 2], dom=range(3))\nsatisfy(Cardinality(m, occurrences={0: 2, 2: 1}))", [range(3)] * 4,
          lambda *t: card(t, [(0, 2), (2, 1)]))


def test_cardinality_on_an_array_with_holes(run, solver):
    r = run("x = VarArray(size=4, dom=lambda i: None if i == 1 else range(3))\nsatisfy(Cardinality(x, occurrences={0: 1, 1: 1}))", solver=solver)
    assert r.variables == ["x[0]", "x[2]", "x[3]"]
    assert_solutions(r, brute_force([range(3)] * 3, lambda *t: card(t, [(0, 1), (1, 1)])))


def test_cardinality_on_variables_of_arrays_and_simple_variables(run, solver):
    check(run, solver, "x = VarArray(size=2, dom=range(3))\nw = Var(range(3))\ny = VarArray(size=2, dom=range(3))\n"
                       "satisfy(Cardinality(x, w, y, occurrences={0: 2, 1: 2}))", [range(3)] * 5, lambda *t: card(t, [(0, 2), (1, 2)]))


@pytest.mark.parametrize("dom, domains, occurrences, expected", [
    ("lambda i: {i, 2}", [{0, 2}, {1, 2}, {2}], "{2: 2}", [(2, 2)]),
    ("lambda i: range(i, 3)", [range(0, 3), range(1, 3), range(2, 3)], "{1: 1, 2: range(1, 3)}", [(1, 1), (2, range(1, 3))]),
    ("lambda i: {i}", [{0}, {1}, {2}], "{0: 1, 1: 1}", [(0, 1), (1, 1)]),
    ("lambda i: {0, 5} if i == 0 else range(3)", [{0, 5}, range(3), range(3)], "{5: 1, 0: range(0, 2)}", [(5, 1), (0, range(0, 2))]),
    ("lambda i: {i, 2}", [{0, 2}, {1, 2}, {2}], "{0: 1, 2: 2}", [(0, 1), (2, 2)]),
], ids=["a common value", "intervals", "no common value", "a value out of the others", "a value of a single variable"])
def test_cardinality_on_different_domains(run, solver, dom, domains, occurrences, expected):
    check(run, solver, f"x = VarArray(size=3, dom={dom})\nsatisfy(Cardinality(x, occurrences={occurrences}))", domains, lambda *t: card(t, expected))


@pytest.mark.parametrize("dom, domains, occurrences, expected", [
    ("lambda i: {i, 2}", [{0, 2}, {1, 2}, {2}], "{2: 2}", [(2, 2)]),
    ("lambda i: range(i, 3)", [range(0, 3), range(1, 3), range(2, 3)], "{1: 1, 2: range(1, 3)}", [(1, 1), (2, range(1, 3))]),
    ("lambda i: {0, 5} if i == 0 else range(3)", [{0, 5}, range(3), range(3)], "{5: 1, 0: range(0, 2), 1: 1}", [(5, 1), (0, range(0, 2)), (1, 1)]),
], ids=["a common value", "intervals", "a value out of the others"])
def test_cardinality_on_different_domains_closed(run, solver, request, dom, domains, occurrences, expected):
    bug_for(request, "COSOCO", COSOCO_CLOSED)
    check(run, solver, f"x = VarArray(size=3, dom={dom})\nsatisfy(Cardinality(x, occurrences={occurrences}, closed=True))", domains,
          lambda *t: card(t, expected, closed=True))


def test_cardinality_on_negative_values(run, solver):
    check(run, solver, "x = VarArray(size=3, dom=range(-2, 1))\nsatisfy(Cardinality(x, occurrences={-1: 1, -2: range(1, 3)}))", [range(-2, 1)] * 3,
          lambda *t: card(t, [(-1, 1), (-2, range(1, 3))]))


def test_cardinality_on_symbolic_variables(run, solver):
    pytest.skip(SYMBOLIC)
    check(run, solver, "x = VarArray(size=3, dom={'a', 'b'})\nsatisfy(Cardinality(x, occurrences={'a': 2}))", [["a", "b"]] * 3, lambda *t: card(t, [("a", 2)]))


# ------------------------------------------------------------------------------------------------------------ expressions

@pytest.mark.parametrize("terms, occurrences, predicate", [
    ("x[0] + 1, x[1] + 1, x[2] + 1", "{1: 2}", lambda a, b, c, d: card((a + 1, b + 1, c + 1), [(1, 2)])),
    ("x[0], x[1] + 1, x[2]", "{1: 2, 2: 1}", lambda a, b, c, d: card((a, b + 1, c), [(1, 2), (2, 1)])),
    ("x[0] > 0, x[1] > 1, x[2] == 2", "{1: 1}", lambda a, b, c, d: card((a > 0, b > 1, c == 2), [(1, 1)])),
    ("[x[i] + i for i in range(4)]", "{2: range(2, 4)}", lambda *t: card([v + i for i, v in enumerate(t)], [(2, range(2, 4))])),
    ("x[0] * 2, x[1], abs(x[2] - x[3])", "{0: 1, 2: 1}", lambda a, b, c, d: card((a * 2, b, abs(c - d)), [(0, 1), (2, 1)])),
    ("x[0] + x[1], x[2] + x[3]", "{2: 2}", lambda a, b, c, d: a + b == 2 and c + d == 2),
    ("x[0] + 1, x[1] + 1, x[2] + 1", "{1: 1, 2: 1, 3: 1}", lambda a, b, c, d: sorted((a, b, c)) == [0, 1, 2]),
])
def test_cardinality_on_expressions(run, solver, request, terms, occurrences, predicate):
    if terms == "x[0] + x[1], x[2] + x[3]":
        bug_for(request, "ACE", ACE_ALL)
    check(run, solver, X4 + f"satisfy(Cardinality({terms}, occurrences={occurrences}))", D4, predicate)


def test_cardinality_on_expressions_closed(run, solver):
    check(run, solver, X4 + "satisfy(Cardinality(x[0] + 1, x[1] + 1, x[2], occurrences={1: 2, 2: 1}, closed=True))", D4,
          lambda a, b, c, d: card((a + 1, b + 1, c), [(1, 2), (2, 1)], closed=True))


@pytest.mark.parametrize("terms, occurrences, predicate", [
    ("Sum(x[:2]), x[2], x[3]", "{2: 2}", lambda a, b, c, d: card((a + b, c, d), [(2, 2)])),
    ("Maximum(x[:2]), Minimum(x[2:]), x[0]", "{1: 3}", lambda a, b, c, d: card((max(a, b), min(c, d), a), [(1, 3)])),
    ("Count(x, value=0), x[0], x[1]", "{1: 2}", lambda a, b, c, d: card(([a, b, c, d].count(0), a, b), [(1, 2)])),
    ("NValues(x[:2]), x[2], x[3]", "{2: 3}", lambda a, b, c, d: card((len({a, b}), c, d), [(2, 3)])),
])
def test_cardinality_on_components(run, solver, request, terms, occurrences, predicate):
    # a component (Sum, Maximum, Count, ...) among the terms is replaced by an auxiliary variable
    if terms.startswith("Maximum"):
        bug_for(request, "ACE", ACE_ALL)
    check(run, solver, X4 + f"satisfy(Cardinality({terms}, occurrences={occurrences}))", D4, predicate)


@pytest.mark.parametrize("terms, occurrences, predicate", [
    ("~b[0], b[1], b[2]", "{1: 2}", lambda a, b, c: card((1 - a, b, c), [(1, 2)])),
    ("~b[0], ~b[1], b[2]", "{0: 1, 1: 2}", lambda a, b, c: card((1 - a, 1 - b, c), [(0, 1), (1, 2)])),
    ("b[0], ~b[0], b[1]", "{1: 2}", lambda a, b, c: card((a, 1 - a, b), [(1, 2)])),
])
def test_cardinality_on_negated_variables(run, solver, terms, occurrences, predicate):
    check(run, solver, f"b = VarArray(size=3, dom={{0, 1}})\nsatisfy(Cardinality({terms}, occurrences={occurrences}))", [range(2)] * 3, predicate)


# ------------------------------------------------------------------------------------------------ degenerated cases

@pytest.mark.parametrize("constraint, predicate", [
    ("Cardinality(x[0], occurrences={0: 1})", lambda a: a == 0),
    ("Cardinality(x[0], occurrences={0: 0})", lambda a: a != 0),
    ("Cardinality([x[0]], occurrences={0: 1, 1: 0})", lambda a: a == 0),
    ("Cardinality(x[0], occurrences={0: 1, 1: 1})", lambda a: False),
    ("Cardinality(x[0], occurrences={0: range(0, 2), 1: range(0, 2)})", lambda a: True),
    ("Cardinality(x[0], occurrences={0: range(0, 2), 1: range(0, 2)}, closed=True)", lambda a: a in (0, 1)),
    ("Cardinality(x[0], occurrences={0: 2})", lambda a: False),
    ("Cardinality(x[0], occurrences={0: z})", lambda a: True),
    ("Cardinality(x[0] + 1, occurrences={1: 1})", lambda a: a == 0),
])
def test_cardinality_on_a_single_term(run, solver, request, constraint, predicate):
    # with a single term t, the number of occurrences of a value v is 1 if t = v, and 0 otherwise
    if constraint in ("Cardinality(x[0], occurrences={0: 0})", "Cardinality(x[0], occurrences={0: 1, 1: 1})", "Cardinality(x[0], occurrences={0: 2})",
                      "Cardinality(x[0], occurrences={0: range(0, 2), 1: range(0, 2)})"):
        bug_for(request, "ACE", SINGLE_TERM)
    if "closed" in constraint:
        bug_for(request, "COSOCO", SINGLE_TERM)
    if "z" in constraint:
        check(run, solver, XZ + f"satisfy({constraint}, x[3] != 1)", DZ, lambda *t: t[4] == int(t[0] == 0) and t[3] != 1)
        return
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: predicate(t[0]) and t[3] != 1)


@pytest.mark.parametrize("constraint", [
    pytest.param("Cardinality(x[0], occurrences={0: 1})", marks=bug(SINGLE_TERM)),
    pytest.param("Cardinality([x[0]], occurrences={0: range(0, 2), 1: 0})", marks=bug(SINGLE_TERM)),
    pytest.param("Cardinality(x[0], occurrences={0: z})", marks=bug(SINGLE_TERM)),
])
def test_xcsp3_cardinality_has_at_least_two_terms(run, constraint):
    # XCSP3-core requires |X| >= 2
    r = run(XZ + f"satisfy({constraint}, x[3] != 1)")
    assert r.ok, r.report()
    for c in r.xml.iter("cardinality"):
        assert len(c.find("list").text.split()) >= 2 or "[]" in c.find("list").text, constraint + "\n" + r.report()


@pytest.mark.parametrize("constraint, predicate", [
    ("Cardinality([], occurrences={0: 0})", lambda *t: True),
    ("Cardinality([], occurrences={0: range(0, 2)})", lambda *t: True),
    ("Cardinality([], occurrences={})", lambda *t: True),
    ("Cardinality([], occurrences={0: 1})", lambda *t: False),
    ("Cardinality([], occurrences={0: 0, 1: range(1, 3)})", lambda *t: False),
    ("Cardinality([], occurrences={0: z})", lambda *t: t[4] == 0),
    ("Cardinality([], occurrences={0: 0}, closed=True)", lambda *t: True),
])
def test_cardinality_on_no_term(run, solver, request, constraint, predicate):
    # the number of occurrences of any value in no term is 0
    if "{0: 1}" in constraint or "z" in constraint or "range(1, 3)" in constraint:
        bug_for(request, ALL, NO_TERM)
    check(run, solver, XZ + f"satisfy({constraint}, x[3] != 1)", DZ, lambda *t: predicate(*t) and t[3] != 1)


@pytest.mark.parametrize("occurrences, closed, predicate", [
    ("{}", False, lambda *t: True),
    ("[]", False, lambda *t: True),
    ("{}", True, lambda *t: False),
])
def test_cardinality_with_no_value(run, solver, request, occurrences, closed, predicate):
    # no value: nothing is required, except with closed (no term can be assigned a value)
    bug_for(request, ALL if closed else ("ACE", "CHOCO"), NO_VALUE)
    check(run, solver, X4 + f"satisfy(Cardinality(x, occurrences={occurrences}, closed={closed}), x[3] != 1)", D4, lambda *t: predicate(*t) and t[3] != 1)


@pytest.mark.parametrize("constraint", [
    "Cardinality(x[0], x[1], x[0], occurrences={0: 2})",
    "Cardinality(x[0], x[0], occurrences={0: 2})",
    "Cardinality(x, x[0], occurrences={0: 2, 1: 2})",
    "Cardinality(x[0], [x[0], x[1]], occurrences={1: range(1, 3)}, closed=True)",
    "Cardinality(x[:2], x[1:], occurrences={0: z})",
    "Cardinality(Sum(x[:2]), Sum(x[:2]), x[2], occurrences={1: 2})",
])
@bug(REPEATED)
def test_cardinality_with_a_repeated_variable(run, constraint):
    # a variable given several times in the list is refused with an explicit error (decision D of #226), also when it replaces a component given
    # several times
    r = run(XZ + f"satisfy({constraint}, x[3] != 1)")
    assert_fails(r)
    assert "several times" in r.stdout, r.report()


@pytest.mark.parametrize("constraint, predicate", [
    ("Cardinality(x[0] + 1, x[0] + 1, x[1], occurrences={1: 2})", lambda a, b, c, d: card((a + 1, a + 1, b), [(1, 2)])),
    ("Cardinality(x[0] + 1, 1 + x[0], x[1], occurrences={1: 1})", lambda a, b, c, d: card((a + 1, a + 1, b), [(1, 1)])),
])
def test_cardinality_with_a_repeated_expression(run, solver, constraint, predicate):
    # an expression given several times is replaced by distinct auxiliary variables, and counted as many times as it is given
    check(run, solver, X4 + f"satisfy({constraint}, x[3] != 1)", D4, lambda *t: predicate(*t) and t[3] != 1)


# ---------------------------------------------------------------------------------------------------------- groups

M32 = "m = VarArray(size=[3, 2], dom=range(3))\n"
D32 = [range(3)] * 6


@pytest.mark.parametrize("constraints, predicate", [
    ("[Cardinality(m[i], occurrences={0: 1}) for i in range(3)]", lambda *t: all(card(t[2 * i:2 * i + 2], [(0, 1)]) for i in range(3))),
    ("[Cardinality(m[i], occurrences={i: 1}) for i in range(3)]", lambda *t: all(card(t[2 * i:2 * i + 2], [(i, 1)]) for i in range(3))),
    ("[Cardinality(m[i], occurrences={0: i}) for i in range(3)]", lambda *t: all(card(t[2 * i:2 * i + 2], [(0, i)]) for i in range(3))),
    ("[Cardinality(m[:, j], occurrences={0: 1, 1: range(1, 3)}) for j in range(2)]",
     lambda *t: all(card(t[j::2], [(0, 1), (1, range(1, 3))]) for j in range(2))),
    ("[Cardinality(m[i], occurrences={0: 1, 1: 1}, closed=True) for i in range(3)]",
     lambda *t: all(card(t[2 * i:2 * i + 2], [(0, 1), (1, 1)], closed=True) for i in range(3))),
    ("[Cardinality(m[i], occurrences={i: range(1, 3)}) for i in range(3)]", lambda *t: all(card(t[2 * i:2 * i + 2], [(i, range(1, 3))]) for i in range(3))),
])
def test_cardinality_in_groups(run, solver, request, constraints, predicate):
    if constraints == "[Cardinality(m[i], occurrences={0: i}) for i in range(3)]":
        bug_for(request, "ACE", ACE_FAILS)  # Cardinality(m[0], occurrences={0: 0})
    check(run, solver, M32 + f"satisfy({constraints})", D32, predicate)


def test_cardinality_in_a_slide(run, solver):
    check(run, solver, X4 + "satisfy(Slide(Cardinality(x[i:i + 2], occurrences={0: 1}) for i in range(3)))", D4,
          lambda *t: all(card(t[i:i + 2], [(0, 1)]) for i in range(3)))


def test_cardinality_on_sliding_windows(run, solver):
    check(run, solver, "x = VarArray(size=5, dom=range(3))\nsatisfy([Cardinality(x[i:i + 3], occurrences={0: 1, 1: 1}) for i in range(3)])",
          [range(3)] * 5, lambda *t: all(card(t[i:i + 3], [(0, 1), (1, 1)]) for i in range(3)))


def test_cardinality_with_occurrences_given_by_variables_in_groups(run, solver):
    check(run, solver, "x = VarArray(size=4, dom=range(2))\nk = VarArray(size=2, dom=range(3))\n"
                       "satisfy([Cardinality(x[2 * i:2 * i + 2], occurrences={0: k[i]}) for i in range(2)])", [range(2)] * 4 + [range(3)] * 2,
          lambda *t: card(t[0:2], [(0, t[4])]) and card(t[2:4], [(0, t[5])]))


# ------------------------------------------------------------------------------------------------ logical contexts

@pytest.mark.parametrize("constraint, predicate", [
    ("Cardinality(x, occurrences={0: 1}) | (x[0] == 2)", lambda *t: card(t, [(0, 1)]) or t[0] == 2),
    ("Cardinality(x, occurrences={0: 1}) & (x[0] == 2)", lambda *t: card(t, [(0, 1)]) and t[0] == 2),
    ("~Cardinality(x, occurrences={0: 1, 1: 1})", lambda *t: not card(t, [(0, 1), (1, 1)])),
    ("imply(x[0] == 2, Cardinality(x, occurrences={0: 2}))", lambda *t: t[0] != 2 or card(t, [(0, 2)])),
    ("iff(x[0] == 2, Cardinality(x, occurrences={0: 2}))", lambda *t: (t[0] == 2) == card(t, [(0, 2)])),
    ("xor(x[0] == 2, Cardinality(x, occurrences={0: 2}))", lambda *t: (t[0] == 2) != card(t, [(0, 2)])),
    ("If(x[0] == 2, Then=Cardinality(x[1:], occurrences={0: 1}))", lambda *t: t[0] != 2 or card(t[1:], [(0, 1)])),
    ("Cardinality(x, occurrences={0: range(1, 3)}) | (x[0] == 2)", lambda *t: card(t, [(0, range(1, 3))]) or t[0] == 2),
    ("Cardinality(x, occurrences={0: 1, 1: 1}, closed=True) | (x[0] == 2)", lambda *t: card(t, [(0, 1), (1, 1)], closed=True) or t[0] == 2),
    ("Cardinality(x[1:], occurrences={0: x[0]}) | (x[0] == 2)", lambda *t: card(t[1:], [(0, t[0])]) or t[0] == 2),
    ("either(Cardinality(x[:2], occurrences={0: 2}), Cardinality(x[2:], occurrences={1: 2}))", lambda *t: t[0] == t[1] == 0 or t[2] == t[3] == 1),
    ("both(Cardinality(x[:3], occurrences={0: 1}), Cardinality(x[1:], occurrences={1: 1}))", lambda *t: card(t[:3], [(0, 1)]) and card(t[1:], [(1, 1)])),
    ("disjunction(Cardinality(x, occurrences={0: 2}), x[0] == 1)", lambda *t: card(t, [(0, 2)]) or t[0] == 1),
    ("conjunction(Cardinality(x, occurrences={0: 2}), x[0] == 1)", lambda *t: card(t, [(0, 2)]) and t[0] == 1),
])
def test_cardinality_in_logical_expressions(run, solver, request, constraint, predicate):
    bug_for(request, ("CHOCO", "COSOCO") if constraint.startswith("Cardinality(x, occurrences={0: 1}) &") else ALL, LOGICAL)
    check(run, solver, X4 + f"satisfy({constraint})", D4, predicate)


# ------------------------------------------------------------------------------------------------ examples of the doc

def test_cardinality_example(run, solver):
    # the first example of the documentation (employees and shifts), with less employees and shifts
    check(run, solver, "x = VarArray(size=6, dom=range(3))\nsatisfy(Cardinality(x, occurrences={0: 2, 1: range(1, 3), 2: range(1, 4)}))",
          [range(3)] * 6, lambda *t: card(t, [(0, 2), (1, range(1, 3)), (2, range(1, 4))]))


def test_cardinality_example_closed(run, solver, request):
    # the second example of the documentation (closed), with less variables and values
    bug_for(request, "COSOCO", COSOCO_CLOSED)
    check(run, solver, "y = VarArray(size=4, dom=range(6))\nsatisfy(Cardinality(y, occurrences={2: range(3), 3: range(3), 5: range(3)}, closed=True))",
          [range(6)] * 4, lambda *t: card(t, [(2, range(3)), (3, range(3)), (5, range(3))], closed=True))


def test_cardinality_example_with_a_variable(run, solver, request):
    # the third example of the documentation (a variable as number of occurrences), with less employees
    bug_for(request, ALL, MIXED)
    check(run, solver, "x = VarArray(size=5, dom=range(3))\nz = Var(dom=range(2, 5))\n"
                       "satisfy(Cardinality(x, occurrences={0: z, 1: range(1, 3), 2: range(1, 3)}))", [range(3)] * 5 + [range(2, 5)],
          lambda *t: card(t[:5], [(0, t[5]), (1, range(1, 3)), (2, range(1, 3))]))


@pytest.mark.parametrize("code, solution", [
    ("x = VarArray(size=12, dom=range(4))\nsatisfy(Cardinality(x, occurrences={0: 3, 1: 3, 2: range(2, 5), 3: range(1, 4)}))",
     [0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3]),
    ("y = VarArray(size=6, dom=range(10))\nsatisfy(Cardinality(y, occurrences={2: range(4), 3: range(4), 5: range(4)}, closed=True))", [2, 2, 2, 3, 3, 3]),
], ids=["Cardinality 1", "Cardinality 2"])
def test_solutions_given_in_the_doc(run, solver, code, solution):
    # the solution given by the documentation satisfies the constraints of the example
    name = code[0]
    r = run(code + f"\nsatisfy({name} == {solution})", solver=solver)
    assert r.ok and r.status == "SAT" and len(r.raw_solutions) == 1, r.report()


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, expected", [
    ("Cardinality(x, occurrences={0: 1, 1: 2})", ("x[]", "0 1", None, "1 2")),
    ("Cardinality(x, occurrences={0: 1, 1: 2}, closed=True)", ("x[]", "0 1", "true", "1 2")),
    ("Cardinality(x, occurrences={0: 1, 1: 2}, closed=False)", ("x[]", "0 1", None, "1 2")),
    ("Cardinality(x, occurrences={2: range(1, 3), 0: range(0, 2)})", ("x[]", "2 0", None, "1..2 0..1")),
    ("Cardinality(x, occurrences=[1, 0, 3])", ("x[]", "0 1 2", None, "1 0 3")),
    ("Cardinality(x[:3], occurrences={0: x[3], 1: x[3]})", ("x[0..2]", "0 1", None, "x[3] x[3]")),
    ("Cardinality(x[1:], occurrences={x[0]: 2})", ("x[1..3]", "x[0]", None, "2")),
    ("Cardinality(x, occurrences={0: range(1, 2)})", ("x[]", "0", None, "1")),
])
def test_xcsp3_cardinality(run, constraint, expected):
    r = run(X4 + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/cardinality")
    values = c.find("values")
    got = (" ".join(c.find("list").text.split()), " ".join(values.text.split()), values.get("closed"), " ".join(c.find("occurs").text.split()))
    assert got == expected, r.report()


@pytest.mark.parametrize("occurrences", [
    pytest.param("{0: z, 1: 2}", marks=bug(MIXED)),
    pytest.param("{0: z, 1: range(1, 3)}", marks=bug(MIXED)),
    pytest.param("[range(0, 2), z, 1]", marks=bug(MIXED)),
    "{0: z, 1: z}",
])
def test_xcsp3_cardinality_occurrences_of_a_single_kind(run, occurrences):
    # XCSP3-core: the occurrences are all integers, all variables, or all intervals (a variable cannot be mixed with integers or intervals)
    r = run(XZ + f"satisfy(Cardinality(x, occurrences={occurrences}))")
    assert r.ok, r.report()
    for c in r.xml.iter("cardinality"):
        tokens = c.find("occurs").text.split()
        kinds = {"variable" if t[0].isalpha() else "integer" for t in tokens}
        assert len(kinds) == 1, r.report()


@pytest.mark.parametrize("occurrences", [pytest.param("{v[0]: 1, 2: 2}", marks=bug(MIXED)), pytest.param("{2: 1, v[0]: 1}", marks=bug(MIXED)),
                                         "{v[0]: 1, v[1]: 2}"])
def test_xcsp3_cardinality_values_of_a_single_kind(run, occurrences):
    # XCSP3-core: the values are all integers, or all variables
    r = run(XV + f"satisfy(Cardinality(x, occurrences={occurrences}))")
    assert r.ok, r.report()
    for c in r.xml.iter("cardinality"):
        tokens = c.find("values").text.split()
        assert len({t[0].isalpha() for t in tokens}) == 1, r.report()


def test_xcsp3_cardinality_in_a_group(run):
    r = run("x = VarArray(size=4, dom=range(3))\nsatisfy([Cardinality(x[i:i + 2], occurrences={i: 1}) for i in range(3)])")
    assert r.ok, r.report()
    group = r.xml.find("constraints/group")
    assert group is not None and group.find("cardinality") is not None, r.report()
    assert [" ".join(a.text.split()) for a in group.findall("args")] == ["x[0] x[1] 0", "x[1] x[2] 1", "x[2] x[3] 2"], r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("arguments", [
    "x",
    "occurrences={0: 1}",
    "x, {0: 1}",
    "None, occurrences={0: 1}",
    "x, occurrences=None",
    "x, occurrences=3",
    "x, occurrences='a'",
    "x, occurrences={0: None}",
    "x, occurrences={0: 'a'}",
    "x, occurrences={0: 1.5}",
    "x, occurrences={0: True}",
    "x, occurrences={0: [1, 'a']}",
    "x, occurrences={0: [x[0], 1]}",
    "x, occurrences={0: {'a': 1}}",
    "x, occurrences={'a': 1}",
    "x, occurrences={1.5: 1}",
    "x, occurrences={True: 1}",
    "x, occurrences={(0, 1): 1}",
    "x, occurrences={None: 1}",
    "x, occurrences={0: 1}, closed=1",
    "x, occurrences={0: 1}, closed='yes'",
    "x, occurrences={0: 1}, foo=2",
    "x[0], 'a', occurrences={0: 1}",
    "x[0], 2.5, occurrences={0: 1}",
    "x[0], True, occurrences={0: 1}",
    "x[0], {'a': x[1]}, occurrences={0: 1}",
])
def test_invalid_cardinality(run, request, arguments):
    if arguments not in ("x", "occurrences={0: 1}", "x, {0: 1}", "x, occurrences={0: 1}, closed=1", "x, occurrences={0: 1}, closed='yes'",
                         "x, occurrences={0: 1}, foo=2", "x[0], 'a', occurrences={0: 1}", "x[0], 2.5, occurrences={0: 1}", "x[0], True, occurrences={0: 1}",
                         "x[0], {'a': x[1]}, occurrences={0: 1}"):
        request.applymarker(bug(INVALID))
    assert_fails(run(X4 + f"satisfy(Cardinality({arguments}))"))


@pytest.mark.parametrize("code", [
    "minimize(Cardinality(x, occurrences={0: 1}))",
    "satisfy(Cardinality(x, occurrences={0: 1}) == 1)",
    "satisfy(Cardinality(x, occurrences={0: 1}) + 1 == 2)",
])
def test_cardinality_is_not_a_term(run, code):
    # Cardinality() is a constraint, not a term of an expression or an objective
    assert_fails(run(X4 + code))
