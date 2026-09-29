"""
Tests of the constraints LexIncreasing and LexDecreasing of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#LexIncreasing and https://pycsp.org/documentation/api/constraints-global/#LexDecreasing):
the functions LexIncreasing() and LexDecreasing(), which post a constraint lex (lists lexicographically ordered, with the operator le, lt, ge or gt,
strict=True giving lt and gt), on lists of variables, on a list and a tuple of values, and on matrices (matrix=True: both the rows and the
columns are ordered), in groups of constraints and in logical expressions (where the constraint is decomposed).

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
According to XCSP3-core, lex requires at least two lists, of the same length, at least 2.
"""

import operator

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
ONE_VARIABLE = "#144: LexIncreasing() and LexDecreasing() on lists of one variable generate lex on lists of one variable, instead of ordered"
SINGLE_LIST = "#145: LexIncreasing() and LexDecreasing() on a single list of variables take each variable as a list, instead of reporting an error"
REPEATED = "#147: a list given several times to LexIncreasing() or LexDecreasing() is accepted (ACE fails on x[0] x[0], and CHOCO accepts x[0] <lex x[0])"
ACE_SHARED = ("xcsp3team/ACE#20: ACE fails on lex when, once removed the positions where the same variable is in both lists, "
              "a single position remains (control(1 < half) in LexicographicVar)")
COSOCO_ROWS = "xcsp3team/cosoco#82: cosoco fails on a matrix given by explicit rows (Matrix variable (x does not exist)"
CHOCO_MATRIX = ("chocoteam/choco-solver#1248: CHOCO loses solutions of lex-matrix with ge or gt (the columns of the matrix whose rows are reversed are ordered, "
                "instead of the reversed sequence of columns)")

# The cases that a solver says it does not handle, and the symbolic variables (not reported)
SYMBOLIC = "lex on symbolic variables is not part of XCSP3-core"
CHOCO_LIMIT = "CHOCO does not handle lex with a list of values (RuntimeException: UNSUPPORTED)"

OPERATORS = {"le": operator.le, "lt": operator.lt, "ge": operator.ge, "gt": operator.gt}

# the four orderings: the function, the argument strict (as written in the call) and the operator of the element <lex>
ORDERINGS = [("LexIncreasing", "", "le"), ("LexIncreasing", ", strict=True", "lt"), ("LexDecreasing", "", "ge"), ("LexDecreasing", ", strict=True", "gt")]
IDS = ["LexIncreasing", "LexIncreasing-strict", "LexDecreasing", "LexDecreasing-strict"]
FUNCTIONS = ["LexIncreasing", "LexDecreasing"]


def lex(lists, op):
    """Returns True if the lists (tuples) are lexicographically ordered according to the operator (the comparison of tuples in Python is lexicographic)."""
    return all(OPERATORS[op](tuple(lists[i]), tuple(lists[i + 1])) for i in range(len(lists) - 1))


def rows(t, n, m):
    """Returns the n rows of size m of the flat tuple t."""
    return [t[i * m:(i + 1) * m] for i in range(n)]


def columns_of(t, n, m):
    return [tuple(t[i * m + j] for i in range(n)) for j in range(m)]


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


X32 = "x = VarArray(size=[3, 2], dom=range(3))\n"  # x[i] is the ith row
D32 = [range(3)] * 6
X33 = "x = VarArray(size=[3, 3], dom=range(3))\n"


# ------------------------------------------------------------------------------------------------------------ forms

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("constraint", [
    "{f}(x{s})",
    "{f}(x[0], x[1], x[2]{s})",
    "{f}([x[0], x[1], x[2]]{s})",
    "{f}((x[i] for i in range(3)){s})",
    "{f}(tuple(x){s})",
    "{f}([[x[i][0], x[i][1]] for i in range(3)]{s})",
])
def test_lex_forms(run, solver, function, strict, op, constraint):
    check(run, solver, X32 + "satisfy(" + constraint.format(f=function, s=strict) + ")", D32, lambda *t: lex(rows(t, 3, 2), op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_lex_on_columns(run, solver, function, strict, op):
    check(run, solver, X32 + f"satisfy({function}(columns(x){strict}))", D32, lambda *t: lex(columns_of(t, 3, 2), op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_lex_on_two_lists(run, solver, function, strict, op):
    code = "x = VarArray(size=3, dom=range(3))\ny = VarArray(size=3, dom=range(3))\n" + f"satisfy({function}(x, y{strict}))"
    check(run, solver, code, [range(3)] * 6, lambda *t: lex([t[:3], t[3:]], op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("n, m, d", [(2, 2, 3), (2, 4, 2), (4, 2, 2), (3, 3, 2)])
def test_lex_sizes(run, solver, function, strict, op, n, m, d):
    check(run, solver, f"x = VarArray(size=[{n}, {m}], dom=range({d}))\nsatisfy({function}(x{strict}))", [range(d)] * (n * m),
          lambda *t: lex(rows(t, n, m), op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_lex_on_different_domains(run, solver, function, strict, op):
    code = "x = VarArray(size=[2, 3], dom=lambda i, j: range(i + j, i + j + 2))\n" + f"satisfy({function}(x{strict}))"
    domains = [range(i + j, i + j + 2) for i in range(2) for j in range(3)]
    check(run, solver, code, domains, lambda *t: lex(rows(t, 2, 3), op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_lex_on_negative_values(run, solver, function, strict, op):
    check(run, solver, f"x = VarArray(size=[3, 2], dom=range(-2, 1))\nsatisfy({function}(x{strict}))", [range(-2, 1)] * 6, lambda *t: lex(rows(t, 3, 2), op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_lex_on_symbolic_variables(run, solver, function, strict, op):
    pytest.skip(SYMBOLIC)


# ------------------------------------------------------------------------------------------------ examples of the doc

def test_lexincreasing_example(run, solver):
    # the first example of the documentation of LexIncreasing (with smaller rows)
    check(run, solver, X33 + "satisfy([Sum(row) == 3 for row in x], LexIncreasing(x))", [range(3)] * 9,
          lambda *t: all(sum(r) == 3 for r in rows(t, 3, 3)) and lex(rows(t, 3, 3), "le"))


def test_lexincreasing_example_with_matrix(run, solver):
    # the second example of the documentation of LexIncreasing (with smaller rows)
    check(run, solver, X33 + "satisfy([Sum(row) == 3 for row in x], LexIncreasing(x, matrix=True))", [range(3)] * 9,
          lambda *t: all(sum(r) == 3 for r in rows(t, 3, 3)) and lex(rows(t, 3, 3), "le") and lex(columns_of(t, 3, 3), "le"))


def test_lexincreasing_example_with_strict(run, solver):
    # the third example of the documentation of LexIncreasing
    check(run, solver, "x = VarArray(size=[3, 4], dom=range(2))\nsatisfy(LexIncreasing(x, strict=True))", [range(2)] * 12, lambda *t: lex(rows(t, 3, 4), "lt"))


def test_lexdecreasing_example(run, solver):
    # the first example of the documentation of LexDecreasing
    check(run, solver, "x = VarArray(size=[3, 4], dom=range(2))\nsatisfy([Sum(row) == 2 for row in x], LexDecreasing(x))", [range(2)] * 12,
          lambda *t: all(sum(r) == 2 for r in rows(t, 3, 4)) and lex(rows(t, 3, 4), "ge"))


def test_lexdecreasing_example_with_matrix(run, solver, request):
    # the second example of the documentation of LexDecreasing
    bug_for(request, "CHOCO", CHOCO_MATRIX)
    check(run, solver, "x = VarArray(size=[3, 3], dom=range(2))\nsatisfy([Sum(row) == 1 for row in x], LexDecreasing(x, matrix=True))", [range(2)] * 9,
          lambda *t: all(sum(r) == 1 for r in rows(t, 3, 3)) and lex(rows(t, 3, 3), "ge") and lex(columns_of(t, 3, 3), "ge"))


# ------------------------------------------------------------------------------------------------------------- matrix

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("n, m", [(2, 2), (2, 3), (3, 2), (3, 3)])
def test_lex_matrix(run, solver, request, function, strict, op, n, m):
    # both the rows and the columns are lexicographically ordered
    if function == "LexDecreasing":
        bug_for(request, "CHOCO", CHOCO_MATRIX)
    check(run, solver, f"x = VarArray(size=[{n}, {m}], dom=range(2))\nsatisfy({function}(x{strict}, matrix=True))", [range(2)] * (n * m),
          lambda *t: lex(rows(t, n, m), op) and lex(columns_of(t, n, m), op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_lex_matrix_given_by_rows(run, solver, request, function, strict, op):
    if function == "LexDecreasing":
        bug_for(request, "CHOCO", CHOCO_MATRIX)
    check(run, solver, f"x = VarArray(size=[2, 3], dom=range(2))\nsatisfy({function}(x[0], x[1]{strict}, matrix=True))", [range(2)] * 6,
          lambda *t: lex(rows(t, 2, 3), op) and lex(columns_of(t, 2, 3), op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_lex_matrix_with_a_single_row(run, solver, function, strict, op):
    # with matrix=True, the columns of a single row (lists of one variable) are ordered
    check(run, solver, f"x = VarArray(size=[1, 3], dom=range(3))\nsatisfy({function}(x{strict}, matrix=True))", [range(3)] * 3,
          lambda *t: all(OPERATORS[op](a, b) for a, b in zip(t, t[1:])))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("rows_of, lists", [
    ("x[0], x[2]", lambda t: [t[0:3], t[6:9]]),
    ("[[x[0][0], x[1][1]], [x[2][2], x[0][1]]]", lambda t: [(t[0], t[4]), (t[8], t[1])]),
], ids=["two rows", "any variables"])
def test_lex_matrix_given_by_explicit_rows(run, solver, request, function, strict, op, rows_of, lists):
    # the rows are not contiguous in the array: the matrix is written with explicit rows
    bug_for(request, "COSOCO", COSOCO_ROWS)
    if function == "LexDecreasing":
        bug_for(request, "CHOCO", CHOCO_MATRIX)
    check(run, solver, f"x = VarArray(size=[3, 3], dom=range(2))\nsatisfy({function}({rows_of}{strict}, matrix=True))", [range(2)] * 9,
          lambda *t: lex(lists(t), op) and lex(list(zip(*lists(t))), op))


# ------------------------------------------------------------------------------------------------------------- limits

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("limit", [[1, 0, 2], [0, 0, 0], [2, 2, 2], [3, -1, 0], [-1, 5, 5]])
def test_lex_with_a_limit(run, solver, function, strict, op, limit):
    # a list of variables compared with a tuple of values
    if solver == "CHOCO":
        pytest.skip(CHOCO_LIMIT)
    check(run, solver, f"x = VarArray(size=3, dom=range(3))\nsatisfy({function}(x, {limit}{strict}))", [range(3)] * 3, lambda *t: lex([t, limit], op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_lex_with_a_limit_given_by_a_tuple(run, solver, function, strict, op):
    # a tuple of values is accepted, as a list
    if solver == "CHOCO":
        pytest.skip(CHOCO_LIMIT)
    check(run, solver, f"x = VarArray(size=3, dom=range(3))\nsatisfy({function}(x, (1, 0, 2){strict}))", [range(3)] * 3, lambda *t: lex([t, (1, 0, 2)], op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_lex_with_a_limit_of_one_value(run, solver, request, function, strict, op):
    # a list of one variable compared with a list of one value: an intensional constraint is posted
    bug_for(request, "CHOCO", ONE_VARIABLE)
    check(run, solver, f"x = VarArray(size=2, dom=range(3))\nsatisfy({function}([x[0]], [1]{strict}))", [range(3)] * 2, lambda a, b: OPERATORS[op](a, 1))


# -------------------------------------------------------------------------------------------------- repeated lists

@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize("lists", ["x[0], x[0]", "x[0], x[1], x[0]", "[x[0], x[1], x[0]]"])
@bug(REPEATED)
def test_lex_with_a_repeated_list(run, function, lists):
    # a list given several times is forbidden (on x[0] x[0], ACE fails, and CHOCO accepts x[0] <lex x[0])
    assert_fails(run(X32 + f"satisfy({function}({lists}))"))


# ----------------------------------------------------------------------------------------------- degenerated cases

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("lists", ["[x[0]]", "[]"])
def test_lex_trivially_true(run, solver, function, strict, op, lists):
    # with less than two lists, the constraint always holds
    check(run, solver, X32 + f"satisfy({function}({lists}{strict}), x[1][0] == 1)", D32, lambda *t: t[2] == 1)


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize("lists", ["[x[0]]", "[]"])
def test_xcsp3_lex_with_less_than_two_lists(run, function, lists):
    # with less than two lists, no element <lex> is generated (the syntax requires at least two lists)
    r = run(X32 + f"satisfy({function}({lists}), x[1][0] == 1)")
    assert r.ok, r.report()
    assert r.xml.find("constraints//lex") is None, r.report()


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("lists, values", [
    ("[x[0][0]], [x[1][0]]", lambda t: (t[0], t[2])),
    ("x[0][0], x[1][0], x[2][0]", lambda t: (t[0], t[2], t[4])),
], ids=["two lists", "three variables"])
def test_lex_on_lists_of_one_variable(run, solver, function, strict, op, lists, values):
    check(run, solver, X32 + f"satisfy({function}({lists}{strict}))", D32, lambda *t: all(OPERATORS[op](a, b) for a, b in zip(values(t), values(t)[1:])))


@pytest.mark.parametrize("function, op", [("LexIncreasing", "le"), ("LexDecreasing", "ge")])
@pytest.mark.parametrize("lists, variables", [("[x[0][0]], [x[1][0]]", "x[0][0] x[1][0]"), ("x[0][0], x[1][0], x[2][0]", "x[][0]")])
@bug(ONE_VARIABLE)
def test_xcsp3_lex_on_lists_of_one_variable(run, function, op, lists, variables):
    # the syntax of lex requires lists of at least two variables: the constraint ordered is posted instead (as for Increasing() and Decreasing())
    r = run(X32 + f"satisfy({function}({lists}))")
    assert r.ok, r.report()
    assert r.xml.find("constraints//lex") is None, r.report()
    c = r.xml.find("constraints/ordered")
    assert c is not None and " ".join(c.find("list").text.split()) == variables and c.find("operator").text.strip() == op, r.report()


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize("arguments", ["x", "x[0], strict=True", "(v for v in x)"])
@bug(SINGLE_LIST)
def test_lex_on_a_single_list(run, function, arguments):
    # a single list of variables (and not a list of lists) is an error
    assert_fails(run("x = VarArray(size=3, dom=range(3))\n" + f"satisfy({function}({arguments}))"))


# ------------------------------------------------------------------------------------------------ shared variables

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("lists, predicate", [
    ("[x[0], x[0]], [x[1], x[2]]", lambda a, b, c: [(a, a), (b, c)]),
    ("[x[0], x[1]], [x[1], x[0]]", lambda a, b, c: [(a, b), (b, a)]),
    ("[x[0], x[1]], [x[1], x[2]], [x[2], x[0]]", lambda a, b, c: [(a, b), (b, c), (c, a)]),
    ("[x[0], x[1]], [x[0], x[2]]", lambda a, b, c: [(a, b), (a, c)]),
    ("[x[0], x[1], x[2]], [x[0], x[2], x[1]]", lambda a, b, c: [(a, b, c), (a, c, b)]),
], ids=["within a list", "across lists", "across three lists", "at the same position", "at the same position among three"])
def test_lex_with_a_shared_variable(run, solver, request, function, strict, op, lists, predicate):
    # a variable may appear several times in a list, or in different lists (only a list given several times is forbidden)
    if lists == "[x[0], x[1]], [x[0], x[2]]":  # once x[0] removed (at the same position), a single position remains
        bug_for(request, "ACE", ACE_SHARED)
    check(run, solver, "x = VarArray(size=3, dom=range(3))\n" + f"satisfy({function}({lists}{strict}))", [range(3)] * 3, lambda *t: lex(predicate(*t), op))


# ---------------------------------------------------------------------------------------------------------- groups

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_lex_on_consecutive_rows(run, solver, function, strict, op):
    check(run, solver, X32 + f"satisfy([{function}(x[i], x[i + 1]{strict}) for i in range(2)])", D32, lambda *t: lex(rows(t, 3, 2), op))


# ------------------------------------------------------------------------------------------------ logical contexts

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("constraint, predicate", [
    ("~{f}(x[0], x[1]{s})", lambda op: lambda *t: not lex(rows(t, 3, 2)[:2], op)),
    ("{f}(x[0], x[1]{s}) | (x[2][0] == 0)", lambda op: lambda *t: lex(rows(t, 3, 2)[:2], op) or t[4] == 0),
    ("{f}(x[0], x[1]{s}) & (x[2][0] == 0)", lambda op: lambda *t: lex(rows(t, 3, 2)[:2], op) and t[4] == 0),
    ("imply(x[2][0] == 0, {f}(x[0], x[1]{s}))", lambda op: lambda *t: t[4] != 0 or lex(rows(t, 3, 2)[:2], op)),
    ("{f}(x[0], [1, 2]{s}) | (x[2][0] == 0)", lambda op: lambda *t: lex([t[0:2], (1, 2)], op) or t[4] == 0),
], ids=["not", "or", "and", "imply", "or with a limit"])
def test_lex_in_logical_expressions(run, solver, function, strict, op, constraint, predicate):
    # the constraint is decomposed (as for Increasing() and Decreasing())
    check(run, solver, X32 + "satisfy(" + constraint.format(f=function, s=strict) + ")", D32, predicate(op))


@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
def test_lex_matrix_in_logical_expressions(run, solver, function, strict, op):
    check(run, solver, f"x = VarArray(size=[2, 2], dom=range(2))\nsatisfy(~{function}(x{strict}, matrix=True) | (x[0][0] == 1))", [range(2)] * 4,
          lambda *t: not (lex(rows(t, 2, 2), op) and lex(columns_of(t, 2, 2), op)) or t[0] == 1)


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("function, strict, op", ORDERINGS, ids=IDS)
@pytest.mark.parametrize("arguments, expected", [
    ("x", ("list", ["x[0][]", "x[1][]", "x[2][]"])),
    ("x[0], x[2]", ("list", ["x[0][]", "x[2][]"])),
    ("x[0], [1, 0, 2]", ("list", ["x[0][]", "1 0 2"])),
    ("x[0], (1, 0, 2)", ("list", ["x[0][]", "1 0 2"])),
    ("x, matrix=True", ("matrix", ["x[][]"])),
])
def test_xcsp3_lex(run, function, strict, op, arguments, expected):
    r = run(X33 + f"satisfy({function}({arguments}{strict}))")
    assert r.ok, r.report()
    c = r.xml.find("constraints/lex")
    assert c is not None, r.report()
    tag, texts = expected
    assert [" ".join(e.text.split()) for e in c.findall(tag)] == texts and c.find("operator").text.strip() == op, r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize("arguments", [
    "None",
    "x[0], None",
    "x, 'a'",
    "x[0], x[1][:2]",
    "[x[0], x[1][:2]]",
    "x[0], [1, 0]",
    "x[0], [1, x[1][0], 2]",
    "x[0], [1, 0, 2], matrix=True",
    "x[0], range(3)",
    "x[0], [x[1][0] + 1, x[1][1], x[1][2]]",
    "[x[0][0] + 1, x[0][1], x[0][2]], x[1]",
])
def test_invalid_lex(run, function, arguments):
    assert_fails(run(X33 + f"satisfy({function}({arguments}))"))


@pytest.mark.parametrize("function", FUNCTIONS)
def test_lex_on_an_array_with_holes(run, function):
    # the rows of an array with holes may have different lengths: an error is reported
    assert_fails(run(f"x = VarArray(size=[2, 3], dom=lambda i, j: None if (i, j) == (1, 2) else range(2))\nsatisfy({function}(x))"))


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize("arguments, message", [
    ("None", "{f}() requires lists of variables, which is not the case of None"),
    ("x[0], range(3)", "{f}() does not accept a range as a list of values (a list or a tuple is expected), which is the case of range(0, 3)"),
    ("x[0]", "{f}() requires several lists, or a list of lists (for instance, a two-dimensional array), which is not the case of [x[0][0], x[0][1], x[0][2]]"),
    ("x[0], [1, x[1][0], 2]", "{f}() requires lists of variables (the second of two lists being possibly a list of values), which is not the case of [1, x[1][0], 2]"),
    ("x[0], [1, 0, 2], matrix=True", "With matrix=True, {f}() requires lists of variables, which is not the case of [1, 0, 2]"),
    ("x[0], x[1][:2]", "{f}() requires lists of the same length"),
    ("x[0], x[1], x[0]", "A list cannot be given several times to {f}(), which is the case of [x[0][0], x[0][1], x[0][2]]"),
])
def test_invalid_lex_message(run, request, function, arguments, message):
    if arguments in ("x[0]", "x[0], x[1], x[0]"):
        request.applymarker(bug(SINGLE_LIST if arguments == "x[0]" else REPEATED))
    r = run(X33 + f"satisfy({function}({arguments}))")
    assert not r.ok and message.format(f=function) in r.stdout, r.report()
