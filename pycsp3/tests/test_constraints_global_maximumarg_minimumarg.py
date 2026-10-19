"""
Tests of the constraints MaximumArg and MinimumArg of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#MaximumArg): the functions MaximumArg() and MinimumArg(), with or without rank, on
variables, integers and expressions, with conditions given by operators or by the parameter condition, as terms of expressions, in groups of
constraints, in logical expressions and in objectives.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force; each test is run
for MaximumArg() (compared with max()) and for MinimumArg() (compared with min()).
According to XCSP3 (Specifications 3.2, Section 4.1.5), maximumArg(X, (op, k)) holds iff there is an index i (starting at 0) of a maximum
variable of X (i.e., a variable with a maximal value) such that i op k; with rank="first" (resp. "last"), i must be the first (resp. last) such
index; rank="any" by default. The same for minimumArg with the minimal value. X is a list of (at least two) integer variables, or of integer
expressions (generalized form).
"""

import re

import pytest

from harness import assert_fails, assert_optimum, assert_solutions, brute_force, bug, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
CONDITION_PARAMETER = "#253: the parameter condition of MaximumArg() and MinimumArg() is not built: a tuple is written as it is (eq 1)"
SINGLE_TERM = "#254: MaximumArg() and MinimumArg() of a single term give a constraint on one term"
NO_TERM = "#255: MaximumArg() and MinimumArg() of no term give a constraint with an empty list"
INVALID_TERMS = "#256: MaximumArg() and MinimumArg() accept Booleans and symbolic variables among the terms"
INTEGERS = ("#257: the integers among the terms of MaximumArg() and MinimumArg() are written in the list: the parser of ACE and CHOCO "
            "fails (ClassCastException in CtrLoaderInteger.minimumMaximumArg()), and cosoco crashes")
SEVERAL_INDEXES = ("#259: with rank any, the auxiliary variable replacing MaximumArg() or MinimumArg() in an expression can take several "
                   "values (the indexes of all the extrema): a solution is found several times")
OBJECTIVE = "#258: an objective MaximumArg() or MinimumArg() is written with the type maximumArg (not in XCSP3), its rank being lost"
EMPTY_SUPPORTS = ("(to be reported) ACE and CHOCO fail on a table with an empty set of supports, recognized as false by the parser "
                  "(buildCtrFalse(): RuntimeException: Constraint with only conflicts)")
ACE_INDEX = ("(to be reported) ACE fails without message on maximumArg and minimumArg with (eq,y) when the domain of y is not the range of the "
             "indexes, or when y is in the list (controls in the constructor of ExtremumArgVar)")
COSOCO_INDEX = ("(to be reported) cosoco crashes (segmentation fault) on maximumArg with (eq,y) when y has a value that is not an index, and finds "
                "wrong solutions when an index is not in the domain of y, when y is in the list, or when a variable is given several times")
CHOCO_ANY = ("(to be reported) CHOCO handles maximumArg and minimumArg with rank any as with rank first (model.argmax and model.argmin give the "
             "first index), also in the develop version (859fdde)")
CHOCO_LAST = ("(to be reported) CHOCO finds wrong solutions for maximumArg and minimumArg with rank last (on the reversed list, the view -i + n "
              "instead of -i + n - 1), also in the develop version (859fdde)")
CHOCO_REPEATED = ("CHOCO 4.10.15-beta (embedded in PyCSP3) finds a wrong solution for minimumArg with rank first on [x[0] x[1] x[1]], fixed in the "
                  "develop version of CHOCO (859fdde, not reported)")
CHOCO_INTERVAL = ("CHOCO 4.10.15-beta (embedded in PyCSP3) and CHOCO 6.0.2 find wrong solutions for maximumArg and minimumArg with (in,a..b) and "
                  "(notin,a..b), fixed in the develop version of CHOCO (859fdde, not reported)")

# The cases that a solver says it does not handle (not reported)
ACE_UNIMPLEMENTED = "ACE handles maximumArg and minimumArg only with (eq,y) (unimplemented case for maximumArg)"
ACE_REPEATED = "ACE does not accept a variable given several times in the list of maximumArg and minimumArg (vector length = 3 list=...)"
COSOCO_UNSUPPORTED = "cosoco handles maximumArg only with (eq,y), and does not handle minimumArg (s UNSUPPORTED)"

FUNCTIONS = [pytest.param("MaximumArg", max, id="MaximumArg"), pytest.param("MinimumArg", min, id="MinimumArg")]
RANKS = [pytest.param("", "any", id="no rank"), pytest.param(", rank=TypeRank.FIRST", "first", id="FIRST"),
         pytest.param(", rank=TypeRank.LAST", "last", id="LAST")]

X3 = "x = VarArray(size=3, dom=range(3))\n"
D3 = [range(3)] * 3
XY = X3 + "y = Var(dom=range(3))\n"  # y has the range of the indexes as domain
DY = D3 + [range(3)]


def indexes(f, values, rank="any"):
    """
    The indexes of the terms taking the largest value (f=max) or the smallest one (f=min), all of them or only the first or the last one.
    The rank "choco-last" gives the index that CHOCO uses for the rank last (the last index plus 1, see CHOCO_LAST).
    """
    best = f(values)
    s = [i for i, v in enumerate(values) if v == best]
    return s if rank == "any" else s[:1] if rank == "first" else s[-1:] if rank == "last" else [s[-1] + 1]


def holds(f, values, rank, test):
    """True iff the test holds for an index of an extremum (any one, the first one or the last one)."""
    return any(test(i) for i in indexes(f, values, rank))


def code_of(code, name, rank=""):
    """The code with F( replaced by MaximumArg( or MinimumArg(, and the rank (if any) added to the first argument F(x)."""
    code = code.replace("F(x)", "F(x" + rank + ")")
    return re.sub(r"(?<![A-Za-z_])F\(", name + "(", code)


def differ(domains, predicate, rank1, rank2):
    """True iff the predicate (of the brute force, receiving the rank as first argument) gives different solutions with the two ranks."""
    return brute_force(domains, lambda *t: predicate(rank1, *t)) != brute_force(domains, lambda *t: predicate(rank2, *t))


def mark(request, name, rank, domains, predicate, eq_var=True, index=True, repeated=False, several=False, cosoco_ok=False):
    """
    Marks the running test (using the fixture solver) according to the cases of maximumArg/minimumArg that the solvers do not handle or get wrong:
    eq_var for a condition (eq,y), index for a variable y whose domain is the range of the indexes (and which is not in the list), repeated for a
    variable given several times in the list (cosoco_ok when cosoco handles it), and several when the index (rank any) is given by an auxiliary
    variable that can take several values for the same solution. The predicate (of the brute force) receives the rank as first argument.
    """
    solver = request.node.callspec.params["solver"]
    if solver == "ACE":
        if not eq_var:
            pytest.skip(ACE_UNIMPLEMENTED)
        if repeated:
            pytest.skip(ACE_REPEATED)
        if not index:
            request.applymarker(bug(ACE_INDEX))
    elif solver == "COSOCO":
        if name == "MinimumArg" or not eq_var:
            pytest.skip(COSOCO_UNSUPPORTED)
        if not index or (repeated and not cosoco_ok):
            request.applymarker(bug(COSOCO_INDEX))
    elif rank == "last" and differ(domains, predicate, "last", "choco-last"):
        request.applymarker(bug(CHOCO_LAST))
    elif rank == "any" and differ(domains, predicate, "any", "first"):
        request.applymarker(bug(CHOCO_ANY))  # CHOCO gives the solutions of rank first
    if several and rank == "any" and solver in ("ACE", "COSOCO"):
        request.applymarker(bug(SEVERAL_INDEXES))


def several_indexes(f, domains, test):
    """True iff, for a tuple of the domains (the three first values being the terms), several indexes of an extremum satisfy the test."""
    return any(sum(1 for i in indexes(f, t[:3]) if test(i, t)) > 1 for t in brute_force(domains, lambda *t: True))


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


# ------------------------------------------------------------------------------------------------------------ conditions

@pytest.mark.parametrize("constraint, test", [
    ("F(x) == y", lambda i, y: i == y),
    ("y == F(x)", lambda i, y: i == y),
    ("F(x) == 1", lambda i, y: i == 1),
    ("1 == F(x)", lambda i, y: i == 1),
    ("F(x) != 1", lambda i, y: i != 1),
    ("F(x) != y", lambda i, y: i != y),
    ("F(x) < 1", lambda i, y: i < 1),
    ("F(x) < y", lambda i, y: i < y),
    ("F(x) <= 1", lambda i, y: i <= 1),
    ("F(x) > 1", lambda i, y: i > 1),
    ("1 < F(x)", lambda i, y: i > 1),
    ("F(x) >= y", lambda i, y: i >= y),
    ("F(x) in {0, 2}", lambda i, y: i in (0, 2)),
    ("F(x) in range(1, 3)", lambda i, y: i in (1, 2)),
    ("F(x) in [0, 1]", lambda i, y: i in (0, 1)),
    ("F(x) not in {0, 2}", lambda i, y: i not in (0, 2)),
    ("F(x) not in range(1, 3)", lambda i, y: i not in (1, 2)),
    ("F(x) == 3", lambda i, y: i == 3),  # never, 3 not being an index
    ("F(x) == -1", lambda i, y: i == -1),  # never
    ("F(x) >= 0", lambda i, y: True),
])
@pytest.mark.parametrize("rank, r", RANKS)
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_conditions(run, solver, request, name, f, rank, r, constraint, test):
    predicate = lambda rk, *t: holds(f, t[:3], rk, lambda i: test(i, t[3]))
    mark(request, name, r, DY, predicate, eq_var=constraint in ("F(x) == y", "y == F(x)"))
    if "range(1, 3)" in constraint:
        bug_for(request, "CHOCO", CHOCO_INTERVAL)
    check(run, solver, XY + "satisfy(" + code_of(constraint, name, rank) + ")", DY, lambda *t: predicate(r, *t))


@pytest.mark.parametrize("constraint, predicate", [
    ("F(x) in set()", lambda *t: False),
    ("F(x) in range(1, 1)", lambda *t: False),
    ("F(x) not in set()", lambda *t: True),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_with_an_empty_set_of_values(run, solver, request, name, f, constraint, predicate):
    # never in an empty set: the constraint is false with 'in' (a table without support), and always true with 'not in'
    if "not in" not in constraint:
        bug_for(request, ("ACE", "CHOCO"), EMPTY_SUPPORTS)
    check(run, solver, X3 + "satisfy(" + code_of(constraint, name) + ", x[0] != 2)", D3, lambda *t: predicate(*t) and t[0] != 2)


@pytest.mark.parametrize("condition, test", [
    ("('eq', y)", lambda i, y: i == y),
    ("('eq', 1)", lambda i, y: i == 1),
    ("('ne', 1)", lambda i, y: i != 1),
    ("('le', y)", lambda i, y: i <= y),
    ("['gt', 0]", lambda i, y: i > 0),
    ("('in', {0, 2})", lambda i, y: i in (0, 2)),
])
@pytest.mark.parametrize("rank, r", RANKS)
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_with_the_parameter_condition(run, solver, request, name, f, rank, r, condition, test):
    predicate = lambda rk, *t: holds(f, t[:3], rk, lambda i: test(i, t[3]))
    request.applymarker(bug(CONDITION_PARAMETER))
    mark(request, name, r, DY, predicate, eq_var=condition == "('eq', y)")
    check(run, solver, XY + f"satisfy({name}(x{rank}, condition={condition}))", DY, lambda *t: predicate(r, *t))


# ------------------------------------------------------------------------------------------------------------ forms

@pytest.mark.parametrize("terms", [
    "x", "x[0], x[1], x[2]", "[x[0], x[1], x[2]]", "(x[0], x[1], x[2])", "x[i] for i in range(3)", "[x[i] for i in range(3)]",
    "x[:2], x[2]", "x[0], x[1:]", "[x[:1], [x[1], [x[2]]]]", "(x[i] for i in range(2)), x[2]",
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_forms(run, solver, name, f, terms):
    # with rank FIRST, handled by the three solvers (except minimumArg by cosoco)
    if solver == "COSOCO" and name == "MinimumArg":
        pytest.skip(COSOCO_UNSUPPORTED)
    terms = "(" + terms + ")" if terms.startswith("x[i]") else terms  # a generator followed by an argument must be parenthesized
    check(run, solver, XY + f"satisfy({name}({terms}, rank=TypeRank.FIRST) == y)", DY, lambda *t: indexes(f, t[:3], "first") == [t[3]])


@pytest.mark.parametrize("n, d", [(2, 2), (2, 4), (4, 2), (5, 2), (3, 4)])
@pytest.mark.parametrize("rank, r", RANKS)
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_sizes(run, solver, request, name, f, rank, r, n, d):
    predicate = lambda rk, *t: holds(f, t[:n], rk, lambda i: i == t[n])
    domains = [range(d)] * n + [range(n)]
    mark(request, name, r, domains, predicate)
    check(run, solver, f"x = VarArray(size={n}, dom=range({d}))\ny = Var(dom=range({n}))\nsatisfy({name}(x{rank}) == y)", domains,
          lambda *t: predicate(r, *t))


@pytest.mark.parametrize("dom, domain", [("{0, 2, 5}", [0, 2, 5]), ("range(-3, 0)", range(-3, 0)), ("{-5, 0, 5}", [-5, 0, 5]), ("{0, 1}", [0, 1]),
                                         ("{7}", [7])])
@pytest.mark.parametrize("rank, r", RANKS)
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_on_different_domains(run, solver, request, name, f, rank, r, dom, domain):
    # the indexes do not depend on the values of the domains
    predicate = lambda rk, *t: holds(f, t[:3], rk, lambda i: i == t[3])
    domains = [domain] * 3 + [range(3)]
    mark(request, name, r, domains, predicate)
    check(run, solver, f"x = VarArray(size=3, dom={dom})\ny = Var(dom=range(3))\nsatisfy({name}(x{rank}) == y)", domains, lambda *t: predicate(r, *t))


@pytest.mark.parametrize("rank, r", RANKS)
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_on_variables_with_different_domains(run, solver, request, name, f, rank, r):
    predicate = lambda rk, *t: holds(f, t[:3], rk, lambda i: i == t[3])
    domains = [range(3), [1, 4], range(-2, 1), range(3)]
    mark(request, name, r, domains, predicate)
    check(run, solver, "x = Var(dom=range(3))\ny = Var(dom={1, 4})\nz = Var(dom=range(-2, 1))\nw = Var(dom=range(3))\n"
                       f"satisfy({name}([x, y, z]{rank}) == w)", domains, lambda *t: predicate(r, *t))


@pytest.mark.parametrize("dom, domain", [("range(4)", range(4)), ("range(1, 3)", range(1, 3)), ("range(-1, 3)", range(-1, 3)), ("{0, 2}", [0, 2])])
@pytest.mark.parametrize("rank, r", RANKS)
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_with_an_index_variable_of_any_domain(run, solver, request, name, f, rank, r, dom, domain):
    # the domain of the variable equal to the index is not necessarily the range of the indexes
    predicate = lambda rk, *t: holds(f, t[:3], rk, lambda i: i == t[3])
    domains = D3 + [domain]
    mark(request, name, r, domains, predicate, index=False)
    check(run, solver, X3 + f"y = Var(dom={dom})\nsatisfy({name}(x{rank}) == y)", domains, lambda *t: predicate(r, *t))


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_on_a_matrix(run, solver, name, f):
    if solver == "COSOCO" and name == "MinimumArg":
        pytest.skip(COSOCO_UNSUPPORTED)
    check(run, solver, "x = VarArray(size=[2, 2], dom=range(3))\ny = Var(dom=range(4))\n"
                       f"satisfy({name}(x, rank=TypeRank.FIRST) == y, x[0][0] != x[1][1])", [range(3)] * 4 + [range(4)],
          lambda *t: indexes(f, t[:4], "first") == [t[4]] and t[0] != t[3])


# ------------------------------------------------------------------------------------------------------------ terms

@pytest.mark.parametrize("terms, values", [
    ("x[0] + 1, x[1], x[2]", lambda t: (t[0] + 1, t[1], t[2])),
    ("x[0] * 2, x[1] - 1, x[2]", lambda t: (t[0] * 2, t[1] - 1, t[2])),
    ("abs(x[0] - 1), x[1], x[2]", lambda t: (abs(t[0] - 1), t[1], t[2])),
    ("x[0] == 1, x[1], x[2]", lambda t: (int(t[0] == 1), t[1], t[2])),
    ("-x[0], -x[1], -x[2]", lambda t: (-t[0], -t[1], -t[2])),
    ("x[i] + i for i in range(3)", lambda t: tuple(t[i] + i for i in range(3))),
    ("x[0], x[1] * [2], x[2]", lambda t: (t[0], t[1] * 2, t[2])),
])
@pytest.mark.parametrize("rank, r", RANKS)
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_on_expressions(run, solver, request, name, f, rank, r, terms, values):
    # the generalized form (view): a list of expressions
    predicate = lambda rk, *t: holds(f, values(t), rk, lambda i: i == t[3])
    mark(request, name, r, DY, predicate)
    terms = "(" + terms + ")" if " for " in terms and rank else terms  # a generator followed by an argument must be parenthesized
    check(run, solver, XY + f"satisfy({name}({terms}{rank}) == y)", DY, lambda *t: predicate(r, *t))


@pytest.mark.parametrize("terms, values", [
    ("x[0], 1, x[1]", lambda t: (t[0], 1, t[1])),
    ("2, x[0], x[1]", lambda t: (2, t[0], t[1])),
    ("x[0], x[1], 0", lambda t: (t[0], t[1], 0)),
    ("x[0], 1, 1", lambda t: (t[0], 1, 1)),
    ("x[0], x[1], x[1] >= x[1]", lambda t: (t[0], t[1], 1)),
])
@pytest.mark.parametrize("rank, r", RANKS)
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_with_integers(run, solver, request, name, f, rank, r, terms, values):
    # each integer has an index, like the other terms
    predicate = lambda rk, *t: holds(f, values(t), rk, lambda i: i == t[3])
    request.applymarker(bug(INTEGERS))
    mark(request, name, r, DY, predicate)
    check(run, solver, XY + f"satisfy({name}({terms}{rank}) == y)", DY, lambda *t: predicate(r, *t))


@pytest.mark.parametrize("terms", ["3, 1", "1, 3, 2", "2, 2, 0", "-2, 0"])
@pytest.mark.parametrize("rank, r", RANKS)
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_of_integers(run, solver, request, name, f, rank, r, terms):
    request.applymarker(bug(INTEGERS))
    if solver == "COSOCO" and name == "MinimumArg":
        pytest.skip(COSOCO_UNSUPPORTED)
    values = eval("(" + terms + ")")
    check(run, solver, f"y = Var(dom=range({len(values)}))\nsatisfy({name}({terms}{rank}) == y)", [range(len(values))],
          lambda v: v in indexes(f, values, r))


@pytest.mark.parametrize("terms, values", [
    ("Sum(x[:2]), x[2], x[0]", lambda t: (t[0] + t[1], t[2], t[0])),
    ("x[0], Count(x[1:], value=1), x[2]", lambda t: (t[0], t[1:3].count(1), t[2])),
    ("x[2], x[:2] * [1, 2], x[1]", lambda t: (t[2], t[0] + 2 * t[1], t[1])),
    ("Maximum(x[:2]), x[2], x[1]", lambda t: (max(t[:2]), t[2], t[1])),
    ("NValues(x), x[0], x[1]", lambda t: (len(set(t[:3])), t[0], t[1])),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_on_components(run, solver, name, f, terms, values):
    # the components (Sum, Count, ...) among the terms are replaced by auxiliary variables
    if solver == "COSOCO" and name == "MinimumArg":
        pytest.skip(COSOCO_UNSUPPORTED)
    check(run, solver, XY + f"satisfy({name}({terms}, rank=TypeRank.FIRST) == y)", DY, lambda *t: indexes(f, values(t), "first") == [t[3]])


# ------------------------------------------------------------------------------------------------ degenerated cases

@pytest.mark.parametrize("constraint, predicate", [
    ("F(x[0]) == 0", lambda *t: True),
    ("F([x[0]]) == 1", lambda *t: False),
    ("F(x[0] + 1) == y", lambda *t: t[3] == 0),
    ("F(x[0], None) != 0", lambda *t: False),
    ("F(x[0]) in {0, 2}", lambda *t: True),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_on_a_single_term(run, solver, request, name, f, constraint, predicate):
    # the index of a single term is 0 (CHOCO handles a list of one term, but not ACE and cosoco)
    bug_for(request, ("ACE", "COSOCO"), SINGLE_TERM)
    check(run, solver, XY + "satisfy(" + code_of(constraint, name) + ", x[1] == x[2])", DY, lambda *t: predicate(*t) and t[1] == t[2])


@pytest.mark.parametrize("constraint", ["F(x[0]) == 0", "F(x[0]) == y", "F(x[0], condition=('eq', 0))", "F(x[0] + 1, rank=TypeRank.LAST) != 0"])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_xcsp3_extremum_arg_has_at_least_two_terms(run, request, name, f, constraint):
    # XCSP3 requires at least two terms
    request.applymarker(bug(SINGLE_TERM))
    r = run(XY + "satisfy(" + code_of(constraint, name) + ")")
    assert r.ok, r.report()
    assert r.xml.find("constraints/" + name[0].lower() + name[1:]) is None, r.report()


@pytest.mark.parametrize("terms, values", [
    ("x[0], x[0], x[1]", lambda t: (t[0], t[0], t[1])),
    ("x[0], x[1], x[0]", lambda t: (t[0], t[1], t[0])),
    ("x[0], x[1], x[1]", lambda t: (t[0], t[1], t[1])),
])
@pytest.mark.parametrize("rank, r", RANKS)
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_with_a_repeated_term(run, solver, request, name, f, rank, r, terms, values):
    # a term given several times has several indexes
    predicate = lambda rk, *t: holds(f, values(t), rk, lambda i: i == t[3])
    mark(request, name, r, DY, predicate, repeated=True, cosoco_ok=r == "first" and terms != "x[0], x[0], x[1]")
    if name == "MinimumArg" and r == "first" and terms == "x[0], x[1], x[1]":
        bug_for(request, "CHOCO", CHOCO_REPEATED)
    check(run, solver, XY + f"satisfy({name}({terms}{rank}) == y)", DY, lambda *t: predicate(r, *t))


# ------------------------------------------------------------------------------------------------ terms of expressions

@pytest.mark.parametrize("constraint, test", [
    ("F(x) + 1 == y", lambda i, t: i + 1 == t[3]),
    ("F(x) * 2 <= y", lambda i, t: i * 2 <= t[3]),
    ("y - F(x) == 1", lambda i, t: t[3] - i == 1),
    ("F(x) == x[0]", lambda i, t: i == t[0]),
    ("x[F(x)] == 2", lambda i, t: t[i] == 2),
    ("abs(F(x) - y) <= 1", lambda i, t: abs(i - t[3]) <= 1),
])
@pytest.mark.parametrize("rank, r", RANKS)
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_as_a_term(run, solver, request, name, f, rank, r, constraint, test):
    # the component is replaced by an auxiliary variable, equal to an index of an extremum (with rank any, the expression holds for one of them)
    predicate = lambda rk, *t: holds(f, t[:3], rk, lambda i: test(i, t))
    mark(request, name, r, DY, predicate, index=constraint != "F(x) == x[0]", several=several_indexes(f, DY, test))
    check(run, solver, XY + "satisfy(" + code_of(constraint, name, rank) + ")", DY, lambda *t: predicate(r, *t))


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_first_and_last(run, solver, request, name, f):
    # the first and the last indexes of an extremum are the same iff the extremum is taken by a single term
    if solver == "COSOCO" and name == "MinimumArg":
        pytest.skip(COSOCO_UNSUPPORTED)
    bug_for(request, "CHOCO", CHOCO_LAST)
    check(run, solver, X3 + f"satisfy({name}(x, rank=TypeRank.FIRST) == {name}(x, rank=TypeRank.LAST))", D3,
          lambda *t: len(indexes(f, t)) == 1)


# ---------------------------------------------------------------------------------------------------------- groups

@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_in_groups(run, solver, name, f):
    if solver == "COSOCO" and name == "MinimumArg":
        pytest.skip(COSOCO_UNSUPPORTED)
    z = "z = VarArray(size=2, dom=range(2))\n"
    check(run, solver, X3 + z + f"satisfy({name}(x[i], x[i + 1], rank=TypeRank.FIRST) == z[i] for i in range(2))", D3 + [range(2)] * 2,
          lambda *t: all(indexes(f, t[i:i + 2], "first") == [t[3 + i]] for i in range(2)))


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_in_a_function(run, solver, name, f):
    if solver == "COSOCO" and name == "MinimumArg":
        pytest.skip(COSOCO_UNSUPPORTED)
    z = "z = VarArray(size=2, dom=range(2))\n"
    check(run, solver, X3 + z + f"def c(i):\n    return {name}(x[i], x[i + 1], rank=TypeRank.FIRST) == z[i]\n\nsatisfy(c(i) for i in range(2))",
          D3 + [range(2)] * 2, lambda *t: all(indexes(f, t[i:i + 2], "first") == [t[3 + i]] for i in range(2)))


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_in_a_slide(run, solver, name, f):
    if solver == "COSOCO" and name == "MinimumArg":
        pytest.skip(COSOCO_UNSUPPORTED)
    z = "z = VarArray(size=2, dom=range(2))\n"
    check(run, solver, X3 + z + f"satisfy(Slide({name}(x[i], x[i + 1], rank=TypeRank.FIRST) == z[i] for i in range(2)))", D3 + [range(2)] * 2,
          lambda *t: all(indexes(f, t[i:i + 2], "first") == [t[3 + i]] for i in range(2)))


# ------------------------------------------------------------------------------------------------ logical contexts

@pytest.mark.parametrize("constraint, test", [
    ("(F(x) == 1) | (y == 0)", lambda i, t: i == 1 or t[3] == 0),
    ("(F(x) == 1) & (y == 0)", lambda i, t: i == 1 and t[3] == 0),
    ("~(F(x) == 1)", lambda i, t: i != 1),
    ("imply(F(x) == 1, y == 0)", lambda i, t: i != 1 or t[3] == 0),
    ("iff(F(x) == 1, y == 0)", lambda i, t: (i == 1) == (t[3] == 0)),
    ("If(y == 0, Then=F(x) == 2, Else=F(x) == 0)", lambda i, t: i == (2 if t[3] == 0 else 0)),
    ("(F(x) in {0, 2}) | (y == 0)", lambda i, t: i in (0, 2) or t[3] == 0),
    ("(F(x) == y) | (x[0] == 0)", lambda i, t: i == t[3] or t[0] == 0),
])
@pytest.mark.parametrize("rank, r", RANKS)
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_in_logical_expressions(run, solver, request, name, f, rank, r, constraint, test):
    # the component is replaced by an auxiliary variable, equal to an index of an extremum (with rank any, the expression holds for one of them)
    predicate = lambda rk, *t: holds(f, t[:3], rk, lambda i: test(i, t))
    mark(request, name, r, DY, predicate, several=several_indexes(f, DY, test))
    check(run, solver, XY + "satisfy(" + code_of(constraint, name, rank) + ")", DY, lambda *t: predicate(r, *t))


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_in_a_meta_constraint(run, name, f):
    # a meta-constraint explicitly asked for (not in XCSP3-core): the constraint is kept
    r = run(XY + f"satisfy(Or({name}(x) == 2, y == 1, meta=True))")
    assert r.ok, r.report()
    assert r.xml.find("constraints/or/" + name[0].lower() + name[1:]) is not None, r.report()


# ------------------------------------------------------------------------------------------------------------ objectives

@pytest.mark.parametrize("objective, function", [
    ("minimize(F(x))", lambda f, t: indexes(f, t)[0]),
    ("maximize(F(x))", lambda f, t: indexes(f, t)[-1]),
    ("minimize(F(x, rank=TypeRank.LAST))", lambda f, t: indexes(f, t, "last")[0]),
    ("maximize(F(x, rank=TypeRank.FIRST))", lambda f, t: indexes(f, t, "first")[0]),
    ("minimize(F(x[0] + 1, x[1], x[2]))", lambda f, t: indexes(f, (t[0] + 1, t[1], t[2]))[0]),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_as_objective(run, solver, request, name, f, objective, function):
    # with rank any, the index is chosen so as to optimize the objective
    request.applymarker(bug(OBJECTIVE))
    code = code_of(objective, name)
    r = run(X3 + "satisfy(x[0] != x[1])\n" + code, solver=solver)
    expected = brute_force(D3, lambda *t: t[0] != t[1])
    assert_optimum(r, expected, lambda *t: function(f, t), maximize=code.startswith("maximize"))


@pytest.mark.parametrize("objective", ["minimize(F(x[0]))", "maximize(F(3, 1))"])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_constant_as_objective(run, request, name, f, objective):
    # the index of a single term, or of an extremum of integers (with a rank), is a constant: there is nothing to optimize
    request.applymarker(bug(SINGLE_TERM if "x[0]" in objective else INTEGERS))
    r = run(X3 + "satisfy(x[0] != x[1])\n" + code_of(objective, name))
    assert not r.ok and "The objective is the constant" in r.stdout, r.report()


# ------------------------------------------------------------------------------------------------ examples of the doc

def test_maximumarg_example(run, solver):
    # the first example of the doc: the solution given is the only one when x is [0, 1, 2, 3]
    r = run("x = VarArray(size=4, dom=range(20))\ny = Var(dom=range(4))\nsatisfy(AllDifferent(x), MaximumArg(x) == y, x == [0, 1, 2, 3])",
            solver=solver)
    assert r.ok and r.status == "SAT" and r.raw_solutions == [(0, 1, 2, 3, 3)], r.report()


def test_maximumarg_example_with_rank(run, solver, request):
    # the second example of the doc: the last machine has the greatest load
    predicate = lambda rk, *t: holds(max, t, rk, lambda i: i == 3)
    mark(request, "MaximumArg", "last", [range(3)] * 4, predicate, eq_var=False)
    check(run, solver, "z = VarArray(size=4, dom=range(3))\nsatisfy(MaximumArg(z, rank=TypeRank.LAST) == 3)", [range(3)] * 4,
          lambda *t: predicate("last", *t))


def test_minimumarg_example(run, solver):
    # the first example of the doc: the solution given is the only one when x is [0, 3, 48, 49]
    if solver == "COSOCO":
        pytest.skip(COSOCO_UNSUPPORTED)
    r = run("x = VarArray(size=4, dom=range(50))\ny = Var(dom=range(4))\n"
            "satisfy(AllDifferent(x), Sum(x) == 100, MinimumArg(x) == y, x == [0, 3, 48, 49])", solver=solver)
    assert r.ok and r.status == "SAT" and r.raw_solutions == [(0, 3, 48, 49, 0)], r.report()


def test_minimumarg_example_with_rank(run, solver, request):
    # the second example of the doc: the last supplier proposes the smallest price
    predicate = lambda rk, *t: holds(min, t, rk, lambda i: i == 3)
    mark(request, "MinimumArg", "last", [range(3)] * 4, predicate, eq_var=False)
    check(run, solver, "x = VarArray(size=4, dom=range(3))\nsatisfy(MinimumArg(x, rank=TypeRank.LAST) == 3)", [range(3)] * 4,
          lambda *t: predicate("last", *t))


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, expected", [
    ("F(x) == y", (None, "x[]", "(eq,y)")),
    ("F(x, rank=TypeRank.ANY) == y", (None, "x[]", "(eq,y)")),
    ("F(x, rank=TypeRank.FIRST) == y", ("first", "x[]", "(eq,y)")),
    ("F(x, rank=TypeRank.LAST) != 1", ("last", "x[]", "(ne,1)")),
    ("F(x) in {0, 2}", (None, "x[]", "(in,{0,2})")),
    ("F(x) not in range(1, 3)", (None, "x[]", "(notin,1..2)")),
    ("2 > F(x)", (None, "x[]", "(lt,2)")),
    ("F(x[0] + 1, x[1]) == y", (None, "add(x[0],1) x[1]", "(eq,y)")),
    ("F(x[0], x[0], x[1]) == y", (None, "x[0] x[0..1]", "(eq,y)")),
    ("F(x, condition=('eq', 1))", (None, "x[]", "(eq,1)")),
    ("F(x, rank=TypeRank.LAST, condition=('in', range(1, 3)))", ("last", "x[]", "(in,1..2)")),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_xcsp3_extremum_arg(run, request, name, f, constraint, expected):
    if "condition=" in constraint:
        request.applymarker(bug(CONDITION_PARAMETER))
    r = run(XY + "satisfy(" + code_of(constraint, name) + ")")
    assert r.ok, r.report()
    c = r.xml.find("constraints/" + name[0].lower() + name[1:])
    assert c is not None, r.report()
    assert (c.get("rank"), c.find("list").text.strip(), c.find("condition").text.strip()) == expected, r.report()


@pytest.mark.parametrize("terms, expected", [("x[0], 1, x[1]", "x[0] aux_gb[0] x[1]"), ("x[0], x[1], x[1] >= x[1]", "x[0..1] aux_gb[0]")])
@pytest.mark.parametrize("name, f", FUNCTIONS)
@bug(INTEGERS)
def test_xcsp3_extremum_arg_with_integers(run, name, f, terms, expected):
    # an integer is replaced by an auxiliary variable (the parser of XCSP3 does not accept integers in the list)
    r = run(XY + f"satisfy({name}({terms}) == y)")
    assert r.ok, r.report()
    assert r.xml.find("constraints/" + name[0].lower() + name[1:] + "/list").text.strip() == expected, r.report()


@pytest.mark.parametrize("objective, rank", [("minimize(F(x))", None), ("maximize(F(x, rank=TypeRank.LAST))", "last")])
@pytest.mark.parametrize("name, f", FUNCTIONS)
@bug(OBJECTIVE)
def test_xcsp3_extremum_arg_as_objective(run, name, f, objective, rank):
    # the types of objectives are sum, minimum, maximum, nValues and lex: the index is given by an auxiliary variable
    r = run(X3 + code_of(objective, name))
    assert r.ok, r.report()
    o = r.xml.find("objectives/" + objective[:8])
    c = r.xml.find("constraints/" + name[0].lower() + name[1:])
    assert o is not None and o.get("type") is None and c is not None and c.get("rank") == rank, r.report()


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_xcsp3_extremum_arg_in_a_group(run, name, f):
    r = run(X3 + f"satisfy({name}(x[i], x[i + 1], rank=TypeRank.LAST) == 0 for i in range(2))")
    assert r.ok, r.report()
    tag = name[0].lower() + name[1:]
    assert r.xml.find("constraints/group/" + tag) is not None and r.xml.find("constraints/group/" + tag).get("rank") == "last", r.report()
    assert len(r.xml.findall("constraints/group/args")) == 2, r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("arguments", [
    "",
    "[]",
    "x[i] for i in range(0)",
    "None",
    "[None, None]",
    "x, 'a'",
    "x, 1.5",
    "x, {'a': 1}",
    "True, x[0]",
    "x[0], False",
    "s",
    "x[0], s[0]",
    "x, rank='first'",
    "x, rank=1",
    "x, rank=TypeRank.FOO",
    "x, condition='eq'",
    "x, condition=('eq',)",
    "x, condition=('foo', 2)",
    "x, condition=('eq', 'a')",
    "x, condition=('eq', True)",
    "x, condition=('in', 2)",
    "x, condition=('in', {y, 2})",
    "x, foo=2",
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_invalid_extremum_arg(run, request, name, f, arguments):
    if arguments in ("[]", "x[i] for i in range(0)", "None", "[None, None]"):
        request.applymarker(bug(NO_TERM))
    if arguments in ("True, x[0]", "x[0], False", "s", "x[0], s[0]"):
        request.applymarker(bug(INVALID_TERMS))
    if arguments in ("x, condition='eq'", "x, condition=('eq',)", "x, condition=('foo', 2)", "x, condition=('eq', 'a')", "x, condition=('eq', True)",
                     "x, condition=('in', 2)", "x, condition=('in', {y, 2})"):
        request.applymarker(bug(CONDITION_PARAMETER))
    code = XY + "s = VarArray(size=2, dom={'a', 'b'})\n" + f"satisfy({name}({arguments}) == 1)"
    if "condition=" in arguments:
        code = XY + f"satisfy({name}({arguments}))"
    assert_fails(run(code))


@pytest.mark.parametrize("operand", ["2.5", "'a'", "True", "None", "{1: 2}", "[y, 2]"])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_invalid_extremum_arg_operand(run, name, f, operand):
    constraint = f"{name}(x) in {operand}" if operand == "[y, 2]" else f"{name}(x) == {operand}"
    assert_fails(run(XY + f"satisfy({constraint})"))


@pytest.mark.parametrize("arguments, message", [
    ("[]", "() requires at least one term"),
    ("None", "() requires at least one term"),
    ("True, x[0]", "() does not accept Booleans as terms, which is the case of True"),
    ("s", "() requires integer variables (or expressions), which is not the case of s[0]"),
])
@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_invalid_extremum_arg_message(run, request, name, f, arguments, message):
    request.applymarker(bug(NO_TERM if arguments in ("[]", "None") else INVALID_TERMS))
    r = run(X3 + "s = VarArray(size=2, dom={'a', 'b'})\n" + f"satisfy({name}({arguments}) == 1)")
    assert not r.ok and name + message in r.stdout, r.report()


@pytest.mark.parametrize("name, f", FUNCTIONS)
def test_extremum_arg_without_condition(run, name, f):
    # a component MaximumArg (or MinimumArg) must be subject to a condition to be a constraint
    r = run(X3 + f"satisfy({name}(x))")
    assert not r.ok and "is not a constraint: it must be subject to a condition" in r.stdout, r.report()
