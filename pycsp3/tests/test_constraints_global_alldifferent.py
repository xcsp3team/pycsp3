"""
Tests of the constraint AllDifferent of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#AllDifferent): the function AllDifferent(), on variables and on expressions,
with the parameters excepting and matrix, and in groups of constraints.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
"""

from itertools import product

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

COSOCO_SYMBOLIC = "xcsp3team/cosoco#71: cosoco does not handle symbolic variables (XCSP3Core expected type=integer)"
COSOCO_HOLES = "xcsp3team/cosoco#72: cosoco gives individually the values of the variables involved in no constraint, and pycsp3 fails when recording those of holes"
MATRIX_LISTS = "#116: a matrix given by lists (or a one-dimensional list) is written as a one-dimensional array in the XCSP3 file"
EXCEPTING = "#117: excepting=[] generates an empty element <except>, and excepting cannot be a range"
INVALID = "#118: invalid arguments of AllDifferent() are accepted, or reported without explicit message"
REPEATED = "#119: a variable given several times to AllDifferent() is not reported"
ACE_NON_SQUARE = "xcsp3team/ACE#16: ACE fails on allDifferent-matrix with a non-square matrix"
COSOCO_MATRIX_EXCEPT = "xcsp3team/cosoco#78: cosoco loses solutions of allDifferent-matrix with except"
COSOCO_EXCEPT_EXPRESSIONS = "xcsp3team/cosoco#78: cosoco stops with a segmentation fault on allDifferent with expressions and except"
CHOCO_MATRIX_EXCEPT = "chocoteam/choco-solver#1248: CHOCO loses solutions of allDifferent-matrix with except"
CHOCO_EXCEPT_EXPRESSIONS = "CHOCO does not handle allDifferent with expressions and except (Other forms not implemented)"
ACE_SINGLE_VALUE = "xcsp3team/ACE#11: ace fails (ArrayIndexOutOfBoundsException in STR0a) on AllDifferent with a variable whose domain is a single value"


def different(values, excepting=()):
    """Returns True if the values are all different, the values in excepting being ignored."""
    kept = [v for v in values if v not in excepting]
    return len(set(kept)) == len(kept)


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


X3 = "x = VarArray(size=3, dom=range(3))\n"
X4 = "x = VarArray(size=4, dom=range(4))\n"


# ------------------------------------------------------------------------------------------------------------ forms

@pytest.mark.parametrize("constraint", [
    "AllDifferent(x)",
    "AllDifferent(x[0], x[1], x[2], x[3])",
    "AllDifferent([x[0], x[1]], x[2], [x[3]])",
    "AllDifferent(x[:2], x[2:])",
    "AllDifferent(x[i] for i in range(4))",
    "AllDifferent(tuple(x))",
    "AllDifferent([[x[0], x[1]], [x[2], x[3]]])",
    "AllDifferent(x[::-1])",
])
def test_alldifferent_forms(run, solver, constraint):
    check(run, solver, "x = VarArray(size=4, dom=range(5))\n" + f"satisfy({constraint})", [range(5)] * 4, lambda *t: different(t))


@pytest.mark.parametrize("n, d", [(2, 2), (3, 3), (4, 3), (3, 5), (5, 5)], ids=["2 variables 2 values", "3 variables 3 values", "pigeonhole", "3 variables 5 values", "5 variables 5 values"])
def test_alldifferent_sizes(run, solver, n, d):
    check(run, solver, f"x = VarArray(size={n}, dom=range({d}))\nsatisfy(AllDifferent(x))", [range(d)] * n, lambda *t: different(t))


def test_alldifferent_on_a_matrix_flattened(run, solver):
    check(run, solver, "x = VarArray(size=[2, 3], dom=range(6))\nsatisfy(AllDifferent(x), x[0][0] == 0, x[0][1] == 1)", [range(6)] * 6,
          lambda *t: different(t) and t[0] == 0 and t[1] == 1)


def test_alldifferent_on_different_domains(run, solver):
    check(run, solver, "x = VarArray(size=4, dom=lambda i: {i, i + 1, 5})\nsatisfy(AllDifferent(x))", [{i, i + 1, 5} for i in range(4)], lambda *t: different(t))


def test_alldifferent_with_a_single_value_domain(run, solver, request):
    bug_for(request, "ACE", ACE_SINGLE_VALUE)
    check(run, solver, "x = VarArray(size=3, dom=lambda i: range(i + 1))\nsatisfy(AllDifferent(x))", [range(1), range(2), range(3)], lambda *t: different(t))


def test_alldifferent_on_negative_values(run, solver):
    check(run, solver, "x = VarArray(size=3, dom=range(-2, 1))\nsatisfy(AllDifferent(x))", [range(-2, 1)] * 3, lambda *t: different(t))


def test_alldifferent_on_an_array_with_holes(run, solver, request):
    bug_for(request, "COSOCO", COSOCO_HOLES)
    r = run("x = VarArray(size=4, dom=lambda i: None if i == 1 else range(3))\nsatisfy(AllDifferent(x))", solver=solver)
    assert r.variables == ["x[0]", "x[2]", "x[3]"]
    assert_solutions(r, brute_force([range(3)] * 3, lambda *t: different(t)))


def test_alldifferent_on_symbolic_variables(run, solver, request):
    bug_for(request, "COSOCO", COSOCO_SYMBOLIC)
    check(run, solver, "x = VarArray(size=3, dom={'a', 'b', 'c', 'd'})\nsatisfy(AllDifferent(x))", [["a", "b", "c", "d"]] * 3, lambda *t: different(t))


def test_alldifferent_with_other_constraints(run, solver):
    check(run, solver, X4 + "satisfy(AllDifferent(x), x[0] < x[1], x[2] + x[3] == 3)", [range(4)] * 4,
          lambda a, b, c, d: different((a, b, c, d)) and a < b and c + d == 3)


# ----------------------------------------------------------------------------------------------- degenerated cases

@pytest.mark.parametrize("constraint", ["AllDifferent(x[0])", "AllDifferent([x[0]])", "AllDifferent([])", "AllDifferent(x[0], [])"])
def test_alldifferent_trivially_true(run, solver, constraint):
    # with less than two terms, the constraint always holds
    check(run, solver, X3 + f"satisfy({constraint}, x[1] == 1, x[2] == 2)", [range(3)] * 3, lambda a, b, c: (b, c) == (1, 2))


@pytest.mark.parametrize("constraint", ["AllDifferent(x[0], x[0])", "AllDifferent(x[0], x[1], x[0])", "AllDifferent(x + [x[1]])"])
def test_alldifferent_with_a_repeated_variable(run, solver, request, constraint):
    bug_for(request, "ACE" if constraint == "AllDifferent(x[0], x[0])" else ("ACE", "COSOCO"), REPEATED)
    # a variable cannot be different from itself: either the model is unsatisfiable, or an error is reported
    r = run(X3 + f"satisfy({constraint})", solver=solver)
    if r.ok:
        assert_solutions(r, set())
    else:
        assert_fails(r)


# ----------------------------------------------------------------------------------------------------- expressions

EXPRESSIONS = [
    ("AllDifferent(x[0] + 1, x[1], x[2] - 1)", lambda a, b, c, *_: different((a + 1, b, c - 1))),
    ("AllDifferent(abs(x[0] - x[1]), abs(x[1] - x[2]), abs(x[2] - x[3]))", lambda a, b, c, d: different((abs(a - b), abs(b - c), abs(c - d)))),
    ("AllDifferent(x[0] + x[1], x[1] + x[2], x[0] + x[2])", lambda a, b, c, *_: different((a + b, b + c, a + c))),
    ("AllDifferent(x[0] * 2, x[1], x[2] % 2)", lambda a, b, c, *_: different((a * 2, b, c % 2))),
    ("AllDifferent(x[0], x[1] + 0, x[2] * 1)", lambda a, b, c, *_: different((a, b, c))),
    ("AllDifferent([x[i] + i for i in range(4)])", lambda *t: different([v + i for i, v in enumerate(t)])),
    ("AllDifferent(x[0] > 1, x[1] > 1, x[2] == 0)", lambda a, b, c, *_: different((a > 1, b > 1, c == 0))),
    ("AllDifferent(max(x[0], x[1]), min(x[2], x[3]), x[0])", lambda a, b, c, d: different((max(a, b), min(c, d), a))),
    ("AllDifferent(Sum(x[0], x[1]), x[2], x[3])", lambda a, b, c, d: different((a + b, c, d))),
]


@pytest.mark.parametrize("constraint, predicate", EXPRESSIONS)
def test_alldifferent_on_expressions(run, solver, constraint, predicate):
    check(run, solver, X4 + f"satisfy({constraint})", [range(4)] * 4, lambda *t: predicate(*t[:4]))


@pytest.mark.parametrize("constraint, predicate", EXPRESSIONS)
def test_alldifferent_on_expressions_with_option_mini(run, solver, constraint, predicate):
    # with the option -mini, the expressions are replaced by auxiliary variables (which are not part of the solutions recorded by the harness)
    check(run, solver, X4 + f"satisfy({constraint})", [range(4)] * 4, lambda *t: predicate(*t[:4]), args=["-mini"])


# ------------------------------------------------------------------------------------------------------- excepting

@pytest.mark.parametrize("excepting, values", [
    ("0", {0}),
    ("[0]", {0}),
    ("(0,)", {0}),
    ("{0}", {0}),
    ("[0, 3]", {0, 3}),
    ("{3, 0}", {0, 3}),
    ("range(2)", {0, 1}),
    ("9", {9}),
    ("[]", set()),
    ("None", set()),
])
def test_alldifferent_excepting(run, solver, request, excepting, values):
    if excepting == "[]":
        bug_for(request, ("ACE", "CHOCO"), EXCEPTING)
    if excepting == "range(2)":
        bug_for(request, ("ACE", "CHOCO", "COSOCO"), EXCEPTING)
    check(run, solver, X4 + f"satisfy(AllDifferent(x, excepting={excepting}))", [range(4)] * 4, lambda *t: different(t, values))


def test_alldifferent_excepting_negative_value(run, solver):
    check(run, solver, "x = VarArray(size=3, dom=range(-1, 2))\nsatisfy(AllDifferent(x, excepting=-1))", [range(-1, 2)] * 3, lambda *t: different(t, {-1}))


def test_alldifferent_excepting_with_other_constraints(run, solver):
    # the example of the documentation (with fewer jobs)
    check(run, solver, "y = VarArray(size=5, dom=range(4))\nsatisfy(Count(y, value=0) == 2, AllDifferent(y, excepting=0))", [range(4)] * 5,
          lambda *t: t.count(0) == 2 and different(t, {0}))


def test_alldifferent_excepting_on_expressions(run, solver, request):
    if solver == "CHOCO":
        pytest.skip(CHOCO_EXCEPT_EXPRESSIONS)
    bug_for(request, "COSOCO", COSOCO_EXCEPT_EXPRESSIONS)
    check(run, solver, X4 + "satisfy(AllDifferent(x[0] + 1, x[1], x[2], excepting=1))", [range(4)] * 4, lambda a, b, c, d: different((a + 1, b, c), {1}))


# ---------------------------------------------------------------------------------------------------------- matrix

def _matrix_different(rows, excepting=()):
    return all(different(row, excepting) for row in rows) and all(different(col, excepting) for col in zip(*rows))


@pytest.mark.parametrize("size, dom, excepting", [
    ("[3, 3]", 3, None),
    ("[2, 3]", 3, None),
    ("[3, 2]", 3, None),
    ("[2, 3]", 3, 0),
    ("[2, 2]", 3, [0, 2]),
], ids=["latin square", "2 rows 3 columns", "3 rows 2 columns", "excepting 0", "excepting 0 and 2"])
def test_alldifferent_matrix(run, solver, request, size, dom, excepting):
    if size in ("[2, 3]", "[3, 2]"):
        bug_for(request, "ACE", ACE_NON_SQUARE)
    if excepting is not None:
        bug_for(request, "CHOCO", CHOCO_MATRIX_EXCEPT)
        bug_for(request, "COSOCO", COSOCO_MATRIX_EXCEPT)
    n, m = eval(size)
    code = f"x = VarArray(size={size}, dom=range({dom}))\nsatisfy(AllDifferent(x, matrix=True{'' if excepting is None else ', excepting=' + repr(excepting)}))"
    E = () if excepting is None else ({excepting} if isinstance(excepting, int) else set(excepting))
    check(run, solver, code, [range(dom)] * (n * m), lambda *t: _matrix_different([t[i * m:(i + 1) * m] for i in range(n)], E))


def test_alldifferent_matrix_given_as_lists(run, solver, request):
    bug_for(request, ("ACE", "CHOCO", "COSOCO"), MATRIX_LISTS)
    check(run, solver, "x = VarArray(size=4, dom=range(2))\nsatisfy(AllDifferent([[x[0], x[1]], [x[2], x[3]]], matrix=True))", [range(2)] * 4,
          lambda a, b, c, d: _matrix_different([(a, b), (c, d)]))


def test_alldifferent_matrix_with_option_mini(run, solver):
    check(run, solver, "x = VarArray(size=[3, 3], dom=range(3))\nsatisfy(AllDifferent(x, matrix=True))", [range(3)] * 9,
          lambda *t: _matrix_different([t[0:3], t[3:6], t[6:9]]), args=["-mini"])


# ---------------------------------------------------------------------------------------------------------- groups

def test_alldifferent_on_rows_and_columns(run, solver):
    # as for a Sudoku, the constraints are grouped in the XCSP3 file
    check(run, solver, "x = VarArray(size=[3, 3], dom=range(3))\nsatisfy([AllDifferent(row) for row in x], [AllDifferent(col) for col in columns(x)])",
          [range(3)] * 9, lambda *t: _matrix_different([t[0:3], t[3:6], t[6:9]]))


def test_alldifferent_on_sliding_windows(run, solver):
    check(run, solver, "x = VarArray(size=5, dom=range(3))\nsatisfy([AllDifferent(x[i:i + 3]) for i in range(3)])", [range(3)] * 5,
          lambda *t: all(different(t[i:i + 3]) for i in range(3)))


def test_alldifferent_on_blocks(run, solver):
    check(run, solver, "x = VarArray(size=[2, 4], dom=range(4))\nsatisfy([AllDifferent(x[:, j:j + 2]) for j in (0, 2)], AllDifferent(x[0]))",
          [range(4)] * 8, lambda *t: different((t[0], t[1], t[4], t[5])) and different((t[2], t[3], t[6], t[7])) and different(t[0:4]))


def test_alldifferent_with_excepting_in_a_group(run, solver):
    check(run, solver, "x = VarArray(size=[2, 3], dom=range(3))\nsatisfy([AllDifferent(row, excepting=0) for row in x])", [range(3)] * 6,
          lambda *t: different(t[0:3], {0}) and different(t[3:6], {0}))


# ----------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, expected", [
    ("AllDifferent(x)", ("allDifferent", "x[]", None)),
    ("AllDifferent(x, excepting=0)", ("allDifferent", "x[]", "0")),
    ("AllDifferent(x[0], x[2])", ("allDifferent", "x[0] x[2]", None)),
    ("AllDifferent(x[0] + 1, x[1])", ("allDifferent", "add(x[0],1) x[1]", None)),
])
def test_xcsp3_alldifferent(run, constraint, expected):
    r = run(X3 + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints")[0]
    lst = c.find("list")
    text = (lst.text if lst is not None else c.text).strip()
    exc = c.find("except")
    assert (c.tag, " ".join(text.split()), None if exc is None else exc.text.strip()) == expected, r.report()


def test_xcsp3_alldifferent_matrix(run):
    r = run("x = VarArray(size=[2, 2], dom=range(2))\nsatisfy(AllDifferent(x, matrix=True))")
    assert r.ok, r.report()
    c = r.xml.find("constraints/allDifferent")
    assert c is not None and c.find("matrix") is not None, r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("constraint", [
    "AllDifferent(x, 2)",
    "AllDifferent(x[0], 'a')",
    pytest.param("AllDifferent(None)", marks=bug(INVALID)),
    pytest.param("AllDifferent(5)", marks=bug(INVALID)),
    "AllDifferent(x, excepting='a')",
    "AllDifferent(x, excepting=2.5)",
    "AllDifferent(x, excepting=[0, 'a'])",
    "AllDifferent(x, excepting=x[0])",
    pytest.param("AllDifferent(x, x, matrix=True)", marks=bug(INVALID)),
    pytest.param("AllDifferent(x, matrix=True)", marks=bug(MATRIX_LISTS)),
    "AllDifferent([[x[0], x[1]], [x[2]]], matrix=True)",
    "AllDifferent([[x[0] + 1, x[1]], [x[2], x[0]]], matrix=True)",
])
def test_invalid_alldifferent(run, constraint):
    assert_fails(run(X3 + f"satisfy({constraint})"))
