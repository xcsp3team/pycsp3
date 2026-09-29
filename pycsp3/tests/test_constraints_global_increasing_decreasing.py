"""
Tests of the constraints Increasing and Decreasing of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#Increasing and https://pycsp.org/documentation/api/constraints-global/#Decreasing):
the functions Increasing() and Decreasing(), which post a constraint ordered, with the parameters strict and lengths, on variables and on
expressions, in groups of constraints, and in logical expressions.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
According to XCSP3-core, ordered(X, L, op) holds iff x[i] + l[i] op x[i+1] for each i (op being <=, <, >= or >).
"""

import operator

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
REPEATED = "#140: a term given several times to Increasing() or Decreasing() is accepted (the solvers fail or are wrong on x[0] op x[0])"
CHOCO_LENGTHS = "chocoteam/choco-solver#1248: CHOCO orders the whole sequence x[0], x[0] + l[0], x[1], x[1] + l[1], ..., which is wrong for some lengths"

# The cases that a solver says it does not handle, and the symbolic variables (not reported)
SYMBOLIC = "ordered on symbolic variables is not part of XCSP3-core"

OPERATORS = {"le": operator.le, "lt": operator.lt, "ge": operator.ge, "gt": operator.gt}

# the four orderings: the function, the argument strict (as written in the call) and the operator of the element <ordered>
ORDERINGS = [("Increasing", "", "le"), ("Increasing", ", strict=True", "lt"), ("Decreasing", "", "ge"), ("Decreasing", ", strict=True", "gt")]
IDS = ["Increasing", "Increasing-strict", "Decreasing", "Decreasing-strict"]


def ordered(values, op, lengths=None):
    """Returns True if the values are ordered according to the operator (possibly with the lengths), as for the constraint ordered of XCSP3."""
    return all(OPERATORS[op](values[i] + (lengths[i] if lengths else 0), values[i + 1]) for i in range(len(values) - 1))


def ordered_by_choco(values, op, lengths):
    """Returns True if the sequence x[0], x[0] + l[0], x[1], x[1] + l[1], ..., x[n-1] is ordered (the decomposition of CHOCO)."""
    sequence = [v for i in range(len(values) - 1) for v in (values[i], values[i] + lengths[i])] + [values[-1]]
    return ordered(sequence, op)


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


X3 = "x = VarArray(size=3, dom=range(3))\n"
X4 = "x = VarArray(size=4, dom=range(3))\n"


# ------------------------------------------------------------------------------------------------------------ forms

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("constraint", [
    "{f}(x{s})",
    "{f}(x[0], x[1], x[2], x[3]{s})",
    "{f}([x[0], x[1]], x[2], [x[3]]{s})",
    "{f}(x[:2], x[2:]{s})",
    "{f}((x[i] for i in range(4)){s})",
    "{f}(tuple(x){s})",
    "{f}([[x[0], x[1]], [x[2], x[3]]]{s})",
])
def test_ordered_forms(run, solver, function, strict, op, constraint):
    check(run, solver, X4 + "satisfy(" + constraint.format(f=function, s=strict) + ")", [range(3)] * 4, lambda *t: ordered(t, op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_ordered_reversed(run, solver, function, strict, op):
    check(run, solver, X4 + f"satisfy({function}(x[::-1]{strict}))", [range(3)] * 4, lambda *t: ordered(t[::-1], op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("n, d", [(2, 2), (3, 3), (5, 2), (4, 5)])
def test_ordered_sizes(run, solver, function, strict, op, n, d):
    check(run, solver, f"x = VarArray(size={n}, dom=range({d}))\nsatisfy({function}(x{strict}))", [range(d)] * n, lambda *t: ordered(t, op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_ordered_on_a_matrix(run, solver, function, strict, op):
    # the matrix is flattened (row by row)
    check(run, solver, f"x = VarArray(size=[2, 2], dom=range(3))\nsatisfy({function}(x{strict}))", [range(3)] * 4, lambda *t: ordered(t, op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("dom, domains", [
    ("lambda i: range(i, i + 3)", [range(0, 3), range(1, 4), range(2, 5)]),
    ("lambda i: {2 - i, 4}", [{2, 4}, {1, 4}, {0, 4}]),
    ("lambda i: {i}", [{0}, {1}, {2}]),
], ids=["shifted intervals", "holes", "singletons"])
def test_ordered_on_different_domains(run, solver, function, strict, op, dom, domains):
    check(run, solver, f"x = VarArray(size=3, dom={dom})\nsatisfy({function}(x{strict}))", domains, lambda *t: ordered(t, op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_ordered_on_negative_values(run, solver, function, strict, op):
    check(run, solver, f"x = VarArray(size=3, dom=range(-2, 2))\nsatisfy({function}(x{strict}))", [range(-2, 2)] * 3, lambda *t: ordered(t, op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_ordered_on_an_array_with_holes(run, solver, function, strict, op):
    r = run(f"x = VarArray(size=4, dom=lambda i: None if i == 1 else range(3))\nsatisfy({function}(x{strict}))", solver=solver)
    assert r.variables == ["x[0]", "x[2]", "x[3]"]
    assert_solutions(r, brute_force([range(3)] * 3, lambda *t: ordered(t, op)))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_ordered_on_symbolic_variables(run, solver, function, strict, op):
    pytest.skip(SYMBOLIC)


@pytest.mark.parametrize("function", ["Increasing", "Decreasing"])
@pytest.mark.parametrize("terms", ["x[0], x[1], x[0]", "x[0], x[0]", "x[0], x, x[2]", "x[0] + 1, x[1], x[0] + 1"])
@bug(REPEATED)
def test_ordered_with_a_repeated_term(run, function, terms):
    # a term given several times is forbidden (on x[0] op x[0], ACE fails, CHOCO accepts x[0] < x[0], and cosoco reports its own solution
    # as invalid for x[0] <= x[0])
    assert_fails(run(X3 + f"satisfy({function}({terms}))"))


# ------------------------------------------------------------------------------------------------ examples of the doc

def test_increasing_example(run, solver):
    # the first example of the documentation of Increasing (with smaller domains)
    check(run, solver, "x = VarArray(size=4, dom=range(8))\nsatisfy(Sum(x) == 12, Increasing(x))", [range(8)] * 4, lambda *t: sum(t) == 12 and ordered(t, "le"))


def test_increasing_example_with_lengths(run, solver):
    # the second example of the documentation of Increasing (with smaller domains)
    check(run, solver, "p = VarArray(size=4, dom=range(14))\nsatisfy(Increasing(p, strict=True, lengths=[3, 2, 5]))", [range(14)] * 4,
          lambda *t: ordered(t, "lt", [3, 2, 5]))


def test_decreasing_example(run, solver):
    # the first example of the documentation of Decreasing (with smaller domains)
    check(run, solver, "x = VarArray(size=5, dom=range(8))\nsatisfy(Sum(x) == 9, Decreasing(x))", [range(8)] * 5, lambda *t: sum(t) == 9 and ordered(t, "ge"))


def test_decreasing_example_with_strict(run, solver):
    # the second example of the documentation of Decreasing (with smaller domains)
    check(run, solver, "x = VarArray(size=4, dom=range(8))\nsatisfy(Sum(x) == 14, Decreasing(x, strict=True))", [range(8)] * 4,
          lambda *t: sum(t) == 14 and ordered(t, "gt"))


# ------------------------------------------------------------------------------------------------------------ lengths

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("lengths, values", [
    ("1", [1, 1, 1]),
    ("[1, 0, 2]", [1, 0, 2]),
    ("(1, 0, 2)", [1, 0, 2]),
    ("range(3)", [0, 1, 2]),
    ("[0, 0, 0]", [0, 0, 0]),
    ("[-1, -1, -1]", [-1, -1, -1]),
    ("[-2, 1, 0]", [-2, 1, 0]),
    ("[1, 0, 2, 5]", [1, 0, 2]),  # as many lengths as terms: the last one is ignored
    ("None", None),
])
def test_ordered_with_lengths(run, solver, request, function, strict, op, lengths, values):
    domains = [range(5)] * 4
    if values is not None and brute_force(domains, lambda *t: ordered(t, op, values)) != brute_force(domains, lambda *t: ordered_by_choco(t, op, values)):
        bug_for(request, "CHOCO", CHOCO_LENGTHS)
    check(run, solver, f"x = VarArray(size=4, dom=range(5))\nsatisfy({function}(x{strict}, lengths={lengths}))", domains, lambda *t: ordered(t, op, values))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_ordered_with_lengths_given_by_variables(run, solver, request, function, strict, op):
    # the lengths are variables: x[0] + y[0] op x[1] and x[1] + y[1] op x[2]
    domains = [range(3)] * 3 + [range(2)] * 2
    if brute_force(domains, lambda a, b, c, u, v: ordered((a, b, c), op, (u, v))) != brute_force(domains, lambda a, b, c, u, v: ordered_by_choco((a, b, c), op, (u, v))):
        bug_for(request, "CHOCO", CHOCO_LENGTHS)
    code = "x = VarArray(size=3, dom=range(3))\ny = VarArray(size=2, dom=range(2))\n" + f"satisfy({function}(x{strict}, lengths=y))"
    check(run, solver, code, domains, lambda a, b, c, u, v: ordered((a, b, c), op, (u, v)))


@pytest.mark.parametrize("function", ["Increasing", "Decreasing"])
@pytest.mark.parametrize("lengths", ["[1, y]", "[y, 1]"])
def test_ordered_with_lengths_mixing_integers_and_variables(run, function, lengths):
    # the lengths are either all integers or all variables (syntax of XCSP3): mixing them is forbidden
    assert_fails(run("x = VarArray(size=3, dom=range(4))\ny = Var(dom=range(2))\n" + f"satisfy({function}(x, lengths={lengths}))"))


# -------------------------------------------------------------------------------------------------------- expressions

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("terms, values", [
    ("x[0] + 1, x[1], x[2] * 2", lambda a, b, c: (a + 1, b, c * 2)),
    ("abs(x[0] - x[1]), x[2]", lambda a, b, c: (abs(a - b), c)),
    ("x[0], x[1] + x[2]", lambda a, b, c: (a, b + c)),
    ("Sum(x[0], x[1]), x[2]", lambda a, b, c: (a + b, c)),
    ("x[0] > 0, x[1] > 1, x[2] == 2", lambda a, b, c: (int(a > 0), int(b > 1), int(c == 2))),
])
def test_ordered_on_expressions(run, solver, function, strict, op, terms, values):
    # the expressions are replaced by auxiliary variables (which are not part of the solutions recorded by the harness)
    check(run, solver, X3 + f"satisfy({function}({terms}{strict}))", [range(3)] * 3, lambda *t: ordered(values(*t), op))


# ----------------------------------------------------------------------------------------------------- option -mini

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("lengths, values", [("None", None), ("[1, 0, 2]", [1, 0, 2]), ("1", [1, 1, 1])])
def test_ordered_with_option_mini(run, solver, function, strict, op, lengths, values):
    # with the option -mini, the constraint is decomposed into intensional constraints
    r = check(run, solver, f"x = VarArray(size=4, dom=range(5))\nsatisfy({function}(x{strict}, lengths={lengths}))", [range(5)] * 4,
              lambda *t: ordered(t, op, values), args=["-mini"])
    assert r.xml.find("constraints//ordered") is None, r.report()


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_ordered_with_lengths_given_by_variables_and_option_mini(run, solver, function, strict, op):
    code = "x = VarArray(size=3, dom=range(3))\ny = VarArray(size=2, dom=range(2))\n" + f"satisfy({function}(x{strict}, lengths=y))"
    check(run, solver, code, [range(3)] * 3 + [range(2)] * 2, lambda a, b, c, u, v: ordered((a, b, c), op, (u, v)), args=["-mini"])


# ------------------------------------------------------------------------------------------------------------- groups

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_ordered_on_rows(run, solver, function, strict, op):
    check(run, solver, f"x = VarArray(size=[3, 2], dom=range(3))\nsatisfy([{function}(row{strict}) for row in x], AllDifferent(x[:, 0]))", [range(3)] * 6,
          lambda *t: all(ordered(t[2 * i:2 * i + 2], op) for i in range(3)) and len({t[0], t[2], t[4]}) == 3)


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_ordered_on_sliding_windows(run, solver, function, strict, op):
    check(run, solver, f"x = VarArray(size=5, dom=range(3))\nsatisfy([{function}(x[i], x[i + 2]{strict}) for i in range(3)])", [range(3)] * 5,
          lambda *t: all(ordered((t[i], t[i + 2]), op) for i in range(3)))


# --------------------------------------------------------------------------------------------------- logical contexts

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("constraint, predicate", [
    ("~{f}(x{s})", lambda op: lambda *t: not ordered(t, op)),
    ("{f}(x{s}) | (x[0] == 0)", lambda op: lambda *t: ordered(t, op) or t[0] == 0),
    ("{f}(x{s}) & (x[0] == 1)", lambda op: lambda *t: ordered(t, op) and t[0] == 1),
    ("imply(x[0] == 0, {f}(x{s}))", lambda op: lambda *t: t[0] != 0 or ordered(t, op)),
    ("either({f}(x[:2]{s}), {f}(x[1:]{s}))", lambda op: lambda *t: ordered(t[:2], op) or ordered(t[1:], op)),
    ("{f}(x{s}, lengths=1) | (x[0] == 0)", lambda op: lambda *t: ordered(t, op, [1, 1]) or t[0] == 0),
], ids=["not", "or", "and", "imply", "either", "or with lengths"])
def test_ordered_in_logical_expressions(run, solver, function, strict, op, constraint, predicate):
    check(run, solver, X3 + "satisfy(" + constraint.format(f=function, s=strict) + ")", [range(3)] * 3, predicate(op))


# -------------------------------------------------------------------------------------------------- degenerated cases

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("terms", ["x[0]", "[x[0]]", "[]", "x[0], []"])
def test_ordered_trivially_true(run, solver, function, strict, op, terms):
    # with less than two terms, the constraint always holds
    check(run, solver, X3 + f"satisfy({function}({terms}{strict}), x[1] == 1, x[2] == 2)", [range(3)] * 3, lambda a, b, c: (b, c) == (1, 2))


@pytest.mark.parametrize("function", ["Increasing", "Decreasing"])
@pytest.mark.parametrize("terms", ["x[0]", "[x[0]]", "x[0], []"])
def test_xcsp3_ordered_with_a_single_term(run, function, terms):
    # with a single term, no element <ordered> is generated (the syntax requires at least two variables)
    r = run(X3 + f"satisfy({function}({terms}), x[1] == 1, x[2] == 2)")
    assert r.ok, r.report()
    assert r.xml.find("constraints//ordered") is None, r.report()


# -------------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, expected", [
    ("Increasing(x)", ("x[]", None, "le")),
    ("Increasing(x, strict=True)", ("x[]", None, "lt")),
    ("Decreasing(x)", ("x[]", None, "ge")),
    ("Decreasing(x, strict=True)", ("x[]", None, "gt")),
    ("Increasing(x[0], x[2])", ("x[0] x[2]", None, "le")),
    ("Increasing(x, lengths=[1, 2, 3])", ("x[]", "1 2 3", "le")),
    ("Decreasing(x, lengths=[-1, 0, 2, 7])", ("x[]", "-1 0 2", "ge")),
    ("Increasing(x[:2], lengths=[x[2]])", ("x[0] x[1]", "x[2]", "le")),
])
def test_xcsp3_ordered(run, constraint, expected):
    r = run(X4 + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/ordered")
    assert c is not None, r.report()
    lengths = c.find("lengths")
    assert (" ".join(c.find("list").text.split()), None if lengths is None else " ".join(lengths.text.split()), c.find("operator").text.strip()) == expected, r.report()


@pytest.mark.parametrize("function", ["Increasing", "Decreasing"])
def test_xcsp3_ordered_on_expressions(run, function):
    # the expressions are replaced by auxiliary variables
    r = run(X3 + f"satisfy({function}(x[0] + 1, x[1], x[2] * 2))")
    assert r.ok, r.report()
    assert " ".join(r.xml.find("constraints/ordered/list").text.split()) == "aux_gb[0] x[1] aux_gb[1]", r.report()


# ------------------------------------------------------------------------------------------------------ invalid cases

@pytest.mark.parametrize("function", ["Increasing", "Decreasing"])
@pytest.mark.parametrize("arguments", [
    "x, 'a'",
    "x[0], 2.5",
    "x, lengths=2.5",
    "x, lengths='a'",
    "x, lengths=[1, 'a', 2]",
    "x, lengths=[1, 2]",
    "x, lengths=[1, 2, 3, 4, 5]",
    "x, lengths=[]",
    "x[:3], lengths=x[3:]",
    "None",
])
def test_invalid_ordered(run, function, arguments):
    assert_fails(run(X4 + f"satisfy({function}({arguments}))"))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_ordered_with_an_integer(run, solver, function, strict, op):
    # an integer among the terms: either it is taken into account, or an error is reported
    r = run(X3 + f"satisfy({function}(x[0], 1, x[1]{strict}))", solver=solver)
    if r.ok:
        assert_solutions(r, brute_force([range(3)] * 3, lambda a, b, c: ordered((a, 1, b), op)))
    else:
        assert_fails(r)


@pytest.mark.parametrize("constraint, message", [
    ("Increasing(None)", "Increasing() requires variables (or expressions), which is not the case of None"),
    ("Decreasing(x, lengths=[1])", "Decreasing() requires as many lengths as terms minus 1 (possibly as many lengths as terms, the last one being ignored), "
                                   "which is not the case of [1] for 4 terms"),
    ("Increasing(x[:3], lengths=[1, x[3]])", "The lengths of Increasing() must be either all integers or all variables, which is not the case of [1, x[3]]"),
])
def test_invalid_ordered_message(run, constraint, message):
    r = run(X4 + f"satisfy({constraint})")
    assert not r.ok and message in r.stdout, r.report()


@pytest.mark.parametrize("constraint, predicate", [
    ("Increasing(x[0]) | (x[1] == 1)", lambda a, b, c: True),
    ("(x[1] == 1) | Decreasing([x[0]])", lambda a, b, c: True),
    ("~Increasing(x[0]) | (x[1] == 1)", lambda a, b, c: b == 1),
])
def test_ordered_with_a_single_term_in_logical_expressions(run, solver, constraint, predicate):
    # a single term is always ordered, including in a logical expression
    check(run, solver, X3 + f"satisfy({constraint}, x[2] != 0)", [range(3)] * 3, lambda a, b, c: predicate(a, b, c) and c != 0)
