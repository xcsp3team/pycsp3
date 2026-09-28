"""
Tests of the section Constraints (Intension) of the API (https://pycsp.org/documentation/api/constraints-intension/):
the arithmetic, relational, logical and membership operators of Python redefined to build intensional constraints, and the
functions abs(), min(), max(), xor(), iff(), imply(), ift(), conjunction(), both(), disjunction(), either(), belong(),
not_belong() and expr().

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
"""

import pytest

from harness import assert_fails, assert_optimum, assert_solutions, brute_force, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
ALL = ("ACE", "CHOCO", "COSOCO")
PYTHON_DIVISION = "#95: // and % are translated into div and mod, which round towards 0 (and not towards negative infinity as in Python)"
ACE_NEGATIVE = "xcsp3team/ACE#12: ACE fails on abs, dist, mul, div and mod with negative values"
# The cases that a solver says it does not handle (not reported): for each constraint, the solvers and the reasons
SKIPPED = {"x ** z == y": {"ACE": "ACE does not implement pow with a variable exponent (not implemented)"}}
CHOCO_POW = "chocoteam/choco-solver#1248: CHOCO does not support pow in some intensional constraints"

# For each constraint (as written in the tests), the known bugs: pairs (solvers, reason)
KNOWN = {
    "x * y == -2": [("ACE", ACE_NEGATIVE)],
    "x // 2 == y": [("ACE", ACE_NEGATIVE), (("CHOCO", "COSOCO"), PYTHON_DIVISION)],
    "x // -2 == y": [("ACE", ACE_NEGATIVE), (("CHOCO", "COSOCO"), PYTHON_DIVISION)],
    "x // y == 1": [("ACE", ACE_NEGATIVE)],
    "7 // x == y": [(ALL, PYTHON_DIVISION)],
    "x % 3 == y": [("ACE", ACE_NEGATIVE), (("CHOCO", "COSOCO"), PYTHON_DIVISION)],
    "x % -3 == y": [("ACE", ACE_NEGATIVE), (("CHOCO", "COSOCO"), PYTHON_DIVISION)],
    "x % y == 1": [("ACE", ACE_NEGATIVE), (("CHOCO", "COSOCO"), PYTHON_DIVISION)],
    "7 % x == y": [(ALL, PYTHON_DIVISION)],
    "x ** 3 == y": [("CHOCO", CHOCO_POW)],
    "x % 3 == z": [("ACE", ACE_NEGATIVE), (("CHOCO", "COSOCO"), PYTHON_DIVISION)],
    "x ** z == y": [("CHOCO", CHOCO_POW)],
    "abs(x) == y": [("ACE", ACE_NEGATIVE)],
    "iff(x > 0, y > 0, b)": [("CHOCO", "chocoteam/choco-solver#1248: iff with more than two arguments is evaluated with associativity, instead of all the arguments being equivalent"),
                             ("COSOCO", "xcsp3team/cosoco#74: cosoco ignores the arguments of iff after the second one")],
    'expr("eq", y, expr("abs", x))': [("ACE", ACE_NEGATIVE)],
    'expr("eq", y, expr("dist", x, 1))': [("ACE", ACE_NEGATIVE)],
    'expr("eq", y, expr("div", x, 2))': [("ACE", ACE_NEGATIVE), (("CHOCO", "COSOCO"), PYTHON_DIVISION)],
    'expr("eq", y, expr("mod", x, 2))': [("ACE", ACE_NEGATIVE), (("CHOCO", "COSOCO"), PYTHON_DIVISION)],
    'expr("eq", y, expr("pow", x, 2))': [("CHOCO", CHOCO_POW)],
}

X = [("x", "range(-3, 4)")]
XY = [("x", "range(-3, 4)"), ("y", "range(-3, 4)")]
XYZ = [("x", "range(-3, 4)"), ("y", "range(-3, 4)"), ("z", "range(3)")]
XYB = [("x", "range(-3, 4)"), ("y", "range(-3, 4)"), ("b", "{0, 1}")]


def check(request, run, solver,constraints, variables, predicate, prefix=""):
    """
    Solves the model with the specified variables (pairs name, domain) and constraints (strings), and compares its
    solutions with the tuples of the Cartesian product of the domains satisfying the predicate.
    """
    for constraint in constraints:
        skipped = SKIPPED.get(constraint, {}).get(request.node.callspec.params.get("solver"))
        if skipped:
            pytest.skip(skipped)
        for solvers, reason in KNOWN.get(constraint, []):
            bug_for(request, solvers, reason)
    declarations = "\n".join(f"{name} = Var(dom={dom})" for name, dom in variables)
    code = prefix + declarations + "\nsatisfy(\n" + "".join("    " + c + ",\n" for c in constraints) + ")\n"
    r = run(code, solver=solver)
    assert_solutions(r, brute_force([list(eval(dom)) for _, dom in variables], predicate))
    return r


def _div(a, b):  # the integer division of Python
    return None if b == 0 else a // b


def _mod(a, b):  # the remainder of Python
    return None if b == 0 else a % b


# -------------------------------------------------------------------------------------------------- arithmetic operators

@pytest.mark.parametrize("constraint, predicate", [
    ("x + y == 1", lambda x, y: x + y == 1),
    ("x - y > 2", lambda x, y: x - y > 2),
    ("y - x - 1 >= 3", lambda x, y: y - x - 1 >= 3),
    ("x * y == -2", lambda x, y: x * y == -2),
    ("2 * x - 3 * y == 1", lambda x, y: 2 * x - 3 * y == 1),
    ("x * y * 2 == 4", lambda x, y: x * y * 2 == 4),
    ("-x == y", lambda x, y: -x == y),
    ("-(x + y) == 2", lambda x, y: -(x + y) == 2),
    ("5 - x == y", lambda x, y: 5 - x == y),
    ("0 - x == y", lambda x, y: -x == y),
    ("x + 0 == y", lambda x, y: x == y),
    ("x - 0 == y", lambda x, y: x == y),
    ("x * 1 == y", lambda x, y: x == y),
    ("x * 0 == y", lambda x, y: y == 0),
    ("1 + x + 2 == y", lambda x, y: x + 3 == y),
    ("x + 1 - 1 == y", lambda x, y: x == y),
    ("x - 2 + 2 == y", lambda x, y: x == y),
    ("x // 2 == y", lambda x, y: x // 2 == y),
    ("x // -2 == y", lambda x, y: x // -2 == y),
    ("x // 1 == y", lambda x, y: x == y),
    ("x // y == 1", lambda x, y: _div(x, y) == 1),
    ("7 // x == y", lambda x, y: _div(7, x) == y),
    ("x % 3 == y", lambda x, y: x % 3 == y),
    ("x % -3 == y", lambda x, y: x % -3 == y),
    ("x % y == 1", lambda x, y: _mod(x, y) == 1),
    ("7 % x == y", lambda x, y: _mod(7, x) == y),
    ("x ** 2 == y + 3", lambda x, y: x ** 2 == y + 3),
    ("x ** 3 == y", lambda x, y: x ** 3 == y),
    ("(x < 1) + (y > 0) == 1", lambda x, y: (x < 1) + (y > 0) == 1),  # Boolean expressions used as 0/1 values
    ("(x == y) * 3 == x + 3", lambda x, y: (x == y) * 3 == x + 3),
])
def test_arithmetic_operators(run, solver, request, constraint, predicate):
    check(request, run, solver,[constraint], XY, predicate)


@pytest.mark.parametrize("constraint, predicate", [
    ("x % 3 == z", lambda x, y, z: x % 3 == z),
    ("x ** z == y", lambda x, y, z: x ** z == y),
    ("2 ** z == y", lambda x, y, z: 2 ** z == y),
    ("z % 5 == x", lambda x, y, z: z == x),  # simplified, the domain of z being 0..2
])
def test_arithmetic_operators_with_small_domains(run, solver, request, constraint, predicate):
    check(request, run, solver,[constraint], XYZ, predicate)


def test_operators_on_shared_nodes(run, solver, request):
    # a node used in several expressions must not be modified by them
    r = run("""
        x = Var(dom=range(-3, 4))
        y = Var(dom=range(-3, 4))
        e = x + 1
        d = x - 1
        satisfy(
            e + 2 == y,
            d - 1 < y,
            e >= 0,
            d <= 0
        )
    """, solver=solver)
    assert_solutions(r, brute_force([range(-3, 4)] * 2, lambda x, y: x + 3 == y and x - 2 < y and x + 1 >= 0 and x - 1 <= 0))


def test_operators_on_shared_nodes_xcsp3(run):
    r = run("""
        x = Var(dom=range(-3, 4))
        y = Var(dom=range(-3, 4))
        e = x + 1
        d = x - 1
        f = x + y + 1
        satisfy(
            e + 2 == y,
            e >= 0,
            d - 1 < y,
            d <= 0,
            e - 1 == y,
            f + 1 == 0,
            f <= 3
        )
    """)
    assert r.ok, r.report()
    assert [c.text.strip() for c in r.xml.iter("intension")] == [
        "eq(add(x,3),y)", "ge(add(x,1),0)", "lt(sub(x,2),y)", "le(sub(x,1),0)", "eq(x,y)", "eq(add(x,y,2),0)", "le(add(x,y,1),3)"], r.report()


# -------------------------------------------------------------------------------------------------- relational operators

@pytest.mark.parametrize("constraint, predicate", [
    ("x < y", lambda x, y: x < y),
    ("x <= y", lambda x, y: x <= y),
    ("x > y", lambda x, y: x > y),
    ("x >= y", lambda x, y: x >= y),
    ("x == y", lambda x, y: x == y),
    ("x != y", lambda x, y: x != y),
    ("1 < x", lambda x, y: 1 < x),
    ("2 >= y", lambda x, y: 2 >= y),
    ("0 == x + y", lambda x, y: x + y == 0),
    ("-1 != x - y", lambda x, y: x - y != -1),
    ("x + 1 < y - 1", lambda x, y: x + 1 < y - 1),
    ("(x < y) == (y < 1)", lambda x, y: (x < y) == (y < 1)),
    ("(x == y) != (x > 0)", lambda x, y: (x == y) != (x > 0)),
    ("(x > 0) <= (y > 0)", lambda x, y: (x > 0) <= (y > 0)),
    ("(x > 0) < 1", lambda x, y: x <= 0),
    ("(x > 0) >= 1", lambda x, y: x > 0),
])
def test_relational_operators(run, solver, request, constraint, predicate):
    check(request, run, solver,[constraint, "y >= -2"], XY, lambda x, y: predicate(x, y) and y >= -2)


# ----------------------------------------------------------------------------------------------------- logical operators

@pytest.mark.parametrize("constraint, predicate", [
    ("(x > 0) | (y > 0)", lambda x, y: x > 0 or y > 0),
    ("(x > 0) & (y > 0)", lambda x, y: x > 0 and y > 0),
    ("(x > 0) ^ (y > 0)", lambda x, y: (x > 0) != (y > 0)),
    ("~(x > y)", lambda x, y: not x > y),
    ("~(x == y)", lambda x, y: x != y),
    ("~((x > 0) & (y > 0))", lambda x, y: not (x > 0 and y > 0)),
    ("~((x > 0) | (y < 0))", lambda x, y: not (x > 0 or y < 0)),
    ("(x > 0) >> (y > 0)", lambda x, y: x <= 0 or y > 0),
    ("((x > 0) | (y > 0)) & (x != y)", lambda x, y: (x > 0 or y > 0) and x != y),
    ("(x == 0) | (y == 0) | (x == y)", lambda x, y: x == 0 or y == 0 or x == y),
    ("((x > 0) ^ (y > 0)) ^ (x == y)", lambda x, y: ((x > 0) != (y > 0)) != (x == y)),
])
def test_logical_operators(run, solver, request, constraint, predicate):
    check(request, run, solver,[constraint], XY, predicate)


@pytest.mark.parametrize("constraint, predicate", [
    ("b", lambda x, y, b: b == 1),
    ("~b", lambda x, y, b: b == 0),
    ("b | (x > 0)", lambda x, y, b: b == 1 or x > 0),
    ("b & (x == y)", lambda x, y, b: b == 1 and x == y),
    ("b == (x < y)", lambda x, y, b: b == (x < y)),
    ("b != (x < y)", lambda x, y, b: b != (x < y)),
    ("b ^ (x < y)", lambda x, y, b: (b == 1) != (x < y)),
    ("(x > 0) >> b", lambda x, y, b: x <= 0 or b == 1),
    ("x + b == y", lambda x, y, b: x + b == y),
])
def test_logical_operators_with_binary_variables(run, solver, request, constraint, predicate):
    check(request, run, solver,[constraint], XYB, predicate)


# ---------------------------------------------------------------------------------------------------- membership operators

@pytest.mark.parametrize("constraint, predicate", [
    ("x in {1, 2}", lambda x, y: x in {1, 2}),
    ("x not in {1, 2}", lambda x, y: x not in {1, 2}),
    ("x in [-3, 0, 3]", lambda x, y: x in {-3, 0, 3}),
    ("x in range(2)", lambda x, y: x in range(2)),
    ("x not in range(-2, 3)", lambda x, y: x not in range(-2, 3)),
    ("x + y in {0, 1}", lambda x, y: x + y in {0, 1}),
    ("x * y not in {0, 1}", lambda x, y: x * y not in {0, 1}),
])
def test_membership_operators(run, solver, request, constraint, predicate):
    check(request, run, solver,[constraint, "y != 0"], XY, lambda x, y: predicate(x, y) and y != 0)


# ------------------------------------------------------------------------------------------------------ abs() min() max()

@pytest.mark.parametrize("constraint, predicate", [
    ("abs(x) == y", lambda x, y: abs(x) == y),
    ("abs(x - y) == 2", lambda x, y: abs(x - y) == 2),
    ("abs(y - x) > 4", lambda x, y: abs(x - y) > 4),
    ("abs(x - y) < 1", lambda x, y: abs(x - y) < 1),
    ("abs(x - y) <= 0", lambda x, y: abs(x - y) <= 0),
    ("abs(x - y) >= 1", lambda x, y: abs(x - y) >= 1),
    ("abs(x - y) > 0", lambda x, y: abs(x - y) > 0),
    ("abs(x - y) == 0", lambda x, y: abs(x - y) == 0),
    ("abs(x - y) != 0", lambda x, y: abs(x - y) != 0),
    ("abs(x + y) == 1", lambda x, y: abs(x + y) == 1),
    ("abs(-x) == 2", lambda x, y: abs(x) == 2),
    ("abs(x * y) == 2 * y", lambda x, y: abs(x * y) == 2 * y),
    ("abs(x) + abs(y) == 3", lambda x, y: abs(x) + abs(y) == 3),
    ("min(x, y) == 1", lambda x, y: min(x, y) == 1),
    ("max(x, y) == -2", lambda x, y: max(x, y) == -2),
    ("max(x, y, 0) == 2", lambda x, y: max(x, y, 0) == 2),
    ("min(x, 1) == y", lambda x, y: min(x, 1) == y),
    ("min([x, y]) == -3", lambda x, y: min(x, y) == -3),
    ("max((x, y)) == 3", lambda x, y: max(x, y) == 3),
    ("max(v for v in [x, y]) == 0", lambda x, y: max(x, y) == 0),
    ("min(x, y) + max(x, y) == 1", lambda x, y: min(x, y) + max(x, y) == 1),
    ("max(x - y, 2) == y", lambda x, y: max(x - y, 2) == y),
    ("min(abs(x), abs(y)) == 2", lambda x, y: min(abs(x), abs(y)) == 2),
    ("max([x]) == 2", lambda x, y: x == 2),
    ("min(x) == y", lambda x, y: x == y),
])
def test_abs_min_max(run, solver, request, constraint, predicate):
    check(request, run, solver,[constraint], XY, predicate)


def test_abs_min_max_on_integers(run):
    r = run('print("values", abs(-3), abs(2), min(3, 1, 2), max([4, 7]), min([5]), max(v for v in [2, 9]), min({3, 8}), max("a", "b"))')
    assert "values 3 2 1 7 5 9 3 b" in r.lines, r.report()


@pytest.mark.parametrize("call", ["min([])", "max()", "abs([1, 2])", "abs('a')"])
def test_abs_min_max_invalid_on_integers(run, call):
    r = run(f"v = {call}")
    assert not r.ok and r.exception == "TypeError", r.report()  # as with the functions of Python


def test_min_max_objective(run, solver):
    r = run("""
        x = Var(dom=range(-3, 4))
        y = Var(dom=range(-3, 4))
        satisfy(
            abs(x - y) == 3
        )
        minimize(
            max(x, y) - min(x, 0)
        )
    """, solver=solver)
    assert_optimum(r, brute_force([range(-3, 4)] * 2, lambda x, y: abs(x - y) == 3), lambda x, y: max(x, y) - min(x, 0))


# ------------------------------------------------------------------------------------------------------- xor() iff() imply()

@pytest.mark.parametrize("constraint, predicate", [
    ("xor(x > 0, y > 0)", lambda x, y, b: (x > 0) != (y > 0)),
    ("xor(x > 0, y > 0, b)", lambda x, y, b: ((x > 0) + (y > 0) + b) % 2 == 1),
    ("xor([x > 0, y > 0])", lambda x, y, b: (x > 0) != (y > 0)),
    ("xor(v > 0 for v in [x, y])", lambda x, y, b: (x > 0) != (y > 0)),
    ("xor(x > 0)", lambda x, y, b: x > 0),  # with only one argument, this argument is returned
    ("xor(x > 0, True)", lambda x, y, b: x <= 0),
    ("xor(False, x > 0)", lambda x, y, b: x > 0),
    ("xor(x > 0, True, y > 0)", lambda x, y, b: (x > 0) == (y > 0)),
    ("xor(x > 0, False, y > 0)", lambda x, y, b: (x > 0) != (y > 0)),
    ("xor(True, x > 0, True)", lambda x, y, b: x > 0),
    ("xor(x > 0, True, y > 0, True, b)", lambda x, y, b: ((x > 0) + (y > 0) + b) % 2 == 1),
    ("xor([x > 0, y > 0], True)", lambda x, y, b: not (x > 0 and y > 0)),
    ("iff(x > 0, y > 0)", lambda x, y, b: (x > 0) == (y > 0)),
    ("iff(x > 0, y > 0, b)", lambda x, y, b: (x > 0) == (y > 0) == (b == 1)),
    ("iff([x >= 0, y >= 0])", lambda x, y, b: (x >= 0) == (y >= 0)),
    ("iff(v < 1 for v in [x, y])", lambda x, y, b: (x < 1) == (y < 1)),
    ("iff(x > 0, True)", lambda x, y, b: x > 0),
    ("iff(x > 0, False)", lambda x, y, b: x <= 0),
    ("iff(True, x > 0)", lambda x, y, b: x > 0),
    ("iff(x > 0, False, y > 0)", lambda x, y, b: (x > 0) == False == (y > 0)),  # noqa: E712
    ("iff(x > 0, True, y > 0)", lambda x, y, b: x > 0 and y > 0),
    ("iff(True, x > 0, True, b)", lambda x, y, b: x > 0 and b == 1),
    ("iff(x > 0, True, False)", lambda x, y, b: False),
    ("iff([x > 0, y > 0], False)", lambda x, y, b: not (x > 0 and y > 0)),
    ("iff(b, x == y)", lambda x, y, b: (b == 1) == (x == y)),
    ("imply(x > 0, y > 0)", lambda x, y, b: x <= 0 or y > 0),
    ("imply(b, x == y)", lambda x, y, b: b == 0 or x == y),
    ("imply(x > 0, [y > 0, b])", lambda x, y, b: x <= 0 or (y > 0 and b == 1)),
    ("imply(x > 0, True)", lambda x, y, b: True),
    ("imply(False, x > 0)", lambda x, y, b: True),
    ("imply(True, x > 0)", lambda x, y, b: x > 0),
    ("imply(x > 0, False)", lambda x, y, b: x <= 0),
    ("imply(b, False)", lambda x, y, b: b == 0),
    ("imply((x > 0) & (y > 0), False)", lambda x, y, b: not (x > 0 and y > 0)),
    ("imply(x > y, imply(y > 0, b))", lambda x, y, b: x <= y or y <= 0 or b == 1),
])
def test_xor_iff_imply(run, solver, request, constraint, predicate):
    # the constraint b | (x != 2) is posted too, so that the model is not empty when the constraint is simplified into true
    check(request, run, solver,[constraint, "b | (x != 2)"], XYB, lambda x, y, b: predicate(x, y, b) and (b == 1 or x != 2))


@pytest.mark.parametrize("call", ["iff(x > 0)", "iff()", "iff([x > 0])", "imply(x > 0)", "imply()", "imply(x > 0, y > 0, x == y)", "xor()"])
def test_xor_iff_imply_invalid(run, call):
    assert_fails(run(f"x = Var(dom=range(3))\ny = Var(dom=range(3))\nsatisfy({call})"))


# ------------------------------------------------------------------------------------------------------------------ ift()

@pytest.mark.parametrize("constraint, predicate", [
    ("y == ift(x > 0, 2, -2)", lambda x, y, b: y == (2 if x > 0 else -2)),
    ("y == ift(b, x, -x)", lambda x, y, b: y == (x if b == 1 else -x)),
    ("y == ift(x > 0, x - 1, x + 1) + 1", lambda x, y, b: y == (x - 1 if x > 0 else x + 1) + 1),
    ("ift(x > 0, y > 0, y < 0)", lambda x, y, b: (y > 0) if x > 0 else (y < 0)),
    ("ift(b, x == y, x != y)", lambda x, y, b: (x == y) if b == 1 else (x != y)),
    ("ift(x > 0, y > 0, None)", lambda x, y, b: x <= 0 or y > 0),
    ("ift(x > 0, [y > 0, b], [y < 0])", lambda x, y, b: (y > 0 and b == 1) if x > 0 else y < 0),
    ("ift(x > 0, [y > 0], [y < 0, b])", lambda x, y, b: y > 0 if x > 0 else (y < 0 and b == 1)),
    ("y == ift(True, 2, -2)", lambda x, y, b: y == 2),
    ("y == ift(False, 2, -2)", lambda x, y, b: y == -2),
    ("y == ift(x > 0, ift(b, 1, 2), 3)", lambda x, y, b: y == ((1 if b == 1 else 2) if x > 0 else 3)),
])
def test_ift(run, solver, request, constraint, predicate):
    check(request, run, solver,[constraint, "b | (x != 2)"], XYB, lambda x, y, b: predicate(x, y, b) and (b == 1 or x != 2))


# --------------------------------------------------------------------------------------- conjunction() both() disjunction() either()

@pytest.mark.parametrize("constraint, predicate", [
    ("conjunction(x > 0, y > 0, x != y)", lambda x, y: x > 0 and y > 0 and x != y),
    ("conjunction([x > 0, y > 0])", lambda x, y: x > 0 and y > 0),
    ("conjunction(v != 0 for v in [x, y])", lambda x, y: x != 0 and y != 0),
    ("conjunction(x > 0)", lambda x, y: x > 0),
    ("conjunction([x > 0])", lambda x, y: x > 0),
    ("conjunction(x > 0, True)", lambda x, y: x > 0),
    ("conjunction(x > 0, False)", lambda x, y: False),
    ("conjunction()", lambda x, y: True),
    ("conjunction(x > 0, conjunction(y > 0, x < y))", lambda x, y: 0 < x < y and y > 0),
    ("both(x > 0, y > 0)", lambda x, y: x > 0 and y > 0),
    ("both(None, x > 0)", lambda x, y: x > 0),
    ("both(x > 0, None)", lambda x, y: x > 0),
    ("both(x > 0, True)", lambda x, y: x > 0),
    ("both(x > 0, False)", lambda x, y: False),
    ("disjunction(x > 1, y > 1, x == y)", lambda x, y: x > 1 or y > 1 or x == y),
    ("disjunction([x > 1, y > 1])", lambda x, y: x > 1 or y > 1),
    ("disjunction(x == v for v in [1, 3, -2])", lambda x, y: x in (1, 3, -2)),
    ("disjunction(x > 0)", lambda x, y: x > 0),
    ("disjunction(x > 0, False)", lambda x, y: x > 0),
    ("disjunction(x > 0, True)", lambda x, y: True),
    ("disjunction()", lambda x, y: False),
    ("disjunction(conjunction(x > 0, y > 0), conjunction(x < 0, y < 0))", lambda x, y: x * y > 0),
    ("either(x + 2 <= y, y + 3 <= x)", lambda x, y: x + 2 <= y or y + 3 <= x),
    ("either(None, x > 0)", lambda x, y: x > 0),
    ("either(x > 0, None)", lambda x, y: x > 0),
    ("either(x > 0, False)", lambda x, y: x > 0),
    ("either(x > 0, True)", lambda x, y: True),
])
def test_conjunction_disjunction(run, solver, request, constraint, predicate):
    check(request, run, solver,[constraint, "y != 1"], XY, lambda x, y: predicate(x, y) and y != 1)


# ---------------------------------------------------------------------------------------------- belong() not_belong()

@pytest.mark.parametrize("constraint, predicate", [
    ("belong(x, [1, 2])", lambda x, y, w: x in (1, 2)),
    ("belong(x, {-3, 0, 3})", lambda x, y, w: x in (-3, 0, 3)),
    ("belong(x, (1,))", lambda x, y, w: x == 1),
    ("belong(x, 2)", lambda x, y, w: x == 2),
    ("belong(x, range(-1, 2))", lambda x, y, w: x in range(-1, 2)),
    ("belong(x, range(-3, 4, 2))", lambda x, y, w: x in range(-3, 4, 2)),
    ("belong(x, [2, 3, 9])", lambda x, y, w: x in (2, 3)),  # the values outside the domain are discarded
    ("belong(x, range(-3, 4))", lambda x, y, w: True),
    ("belong(x, [10, 11])", lambda x, y, w: False),
    ("belong(x, [])", lambda x, y, w: False),
    ("belong(w, range(2, 12))", lambda x, y, w: w in range(2, 12)),
    ("belong(w, list(range(3, 13)))", lambda x, y, w: w in range(3, 13)),
    ("belong(w, range(5, 30))", lambda x, y, w: w in range(5, 30)),
    ("belong(w, {1, 3} | set(range(10, 18)))", lambda x, y, w: w in {1, 3} | set(range(10, 18))),
    ("belong(2, [x, y])", lambda x, y, w: 2 in (x, y)),
    ("belong(-3, [x, None, y])", lambda x, y, w: -3 in (x, y)),
    ("not_belong(-3, [x, None, y])", lambda x, y, w: -3 not in (x, y)),
    ("not_belong(x, [1, 2])", lambda x, y, w: x not in (1, 2)),
    ("not_belong(x, {-3, 0, 3})", lambda x, y, w: x not in (-3, 0, 3)),
    ("not_belong(x, 2)", lambda x, y, w: x != 2),
    ("not_belong(x, range(-1, 2))", lambda x, y, w: x not in range(-1, 2)),
    ("not_belong(x, [2, 3, 9])", lambda x, y, w: x not in (2, 3)),
    ("not_belong(x, range(-3, 4))", lambda x, y, w: False),
    ("not_belong(x, [])", lambda x, y, w: True),
    ("not_belong(w, range(2, 12))", lambda x, y, w: w not in range(2, 12)),
    ("not_belong(w, list(range(3, 13)))", lambda x, y, w: w not in range(3, 13)),
    ("not_belong(2, [x, y])", lambda x, y, w: 2 not in (x, y)),
])
def test_belong(run, solver, request, constraint, predicate):
    check(request, run, solver,[constraint, "y != 0"], XY + [("w", "range(15)")], lambda x, y, w: predicate(x, y, w) and y != 0)


@pytest.mark.parametrize("constraint, predicate", [
    ("belong(b, [1])", lambda b, c: b == 1),
    ("belong(b, [0])", lambda b, c: b == 0),
    ("not_belong(b, [0])", lambda b, c: b == 1),
    ("not_belong(b, [1])", lambda b, c: b == 0),
    ("belong(b, [0, 1])", lambda b, c: True),
])
def test_belong_binary_variables(run, solver, request, constraint, predicate):
    check(request, run, solver,[constraint, "c != 1"], [("b", "{0, 1}"), ("c", "range(3)")], lambda b, c: predicate(b, c) and c != 1)


@pytest.mark.parametrize("call", [
    "belong(x + 1, [1, 2])",
    "belong(x, ['a'])",
    "belong(2, [1, 2])",
    "belong(x, None)",
    "belong(x, [1.5])",
    "belong(x, 'ab')",
    "belong(2, None)",
    "not_belong(x + 1, [1, 2])",
    "not_belong(2, [1, 2])",
    "not_belong(x, {1.5})",
])
def test_belong_invalid(run, call):
    assert_fails(run(f"x = Var(dom=range(3))\ny = Var(dom=range(3))\nsatisfy({call}, y != 0)"))


# ---------------------------------------------------------------------------------------------------------------- expr()

@pytest.mark.parametrize("constraint, predicate", [
    ('expr("lt", x, y)', lambda x, y: x < y),
    ('expr("<", x, y)', lambda x, y: x < y),
    ('expr("le", x, y)', lambda x, y: x <= y),
    ('expr("<=", x, 1)', lambda x, y: x <= 1),
    ('expr("ge", x, y)', lambda x, y: x >= y),
    ('expr(">=", x, y)', lambda x, y: x >= y),
    ('expr("gt", x, 0)', lambda x, y: x > 0),
    ('expr(">", x, y)', lambda x, y: x > y),
    ('expr("eq", x, y)', lambda x, y: x == y),
    ('expr("==", x, y)', lambda x, y: x == y),
    ('expr("=", x, y)', lambda x, y: x == y),
    ('expr("ne", x, y)', lambda x, y: x != y),
    ('expr("!=", x, y)', lambda x, y: x != y),
    ('expr("<>", x, y)', lambda x, y: x != y),
    ('expr("eq", y, expr("add", x, 1))', lambda x, y: y == x + 1),
    ('expr("eq", y, expr("sub", x, 1))', lambda x, y: y == x - 1),
    ('expr("eq", y, expr("mul", x, -1))', lambda x, y: y == -x),
    ('expr("eq", y, expr("neg", x))', lambda x, y: y == -x),
    ('expr("eq", y, expr("abs", x))', lambda x, y: y == abs(x)),
    ('expr("eq", y, expr("dist", x, 1))', lambda x, y: y == abs(x - 1)),
    ('expr("eq", y, expr("min", x, 0))', lambda x, y: y == min(x, 0)),
    ('expr("eq", y, expr("max", x, 0, -y))', lambda x, y: y == max(x, 0, -y)),
    ('expr("eq", y, expr("div", x, 2))', lambda x, y: y == x // 2),
    ('expr("eq", y, expr("mod", x, 2))', lambda x, y: y == x % 2),
    ('expr("eq", y, expr("pow", x, 2))', lambda x, y: y == x ** 2),
    ('expr("eq", y, expr("sqr", x))', lambda x, y: y == x * x),
    ('expr("and", x > 0, y > 0)', lambda x, y: x > 0 and y > 0),
    ('expr("or", x > 0, y > 0, x == y)', lambda x, y: x > 0 or y > 0 or x == y),
    ('expr("xor", x > 0, y > 0)', lambda x, y: (x > 0) != (y > 0)),
    ('expr("iff", x > 0, y > 0)', lambda x, y: (x > 0) == (y > 0)),
    ('expr("imp", x > 0, y > 0)', lambda x, y: x <= 0 or y > 0),
    ('expr("not", x > 0)', lambda x, y: x <= 0),
    ('expr("eq", y, expr("if", x > 0, 1, -1))', lambda x, y: y == (1 if x > 0 else -1)),
    ('expr("in", x, {1, 2})', lambda x, y: x in (1, 2)),
    ('expr("notin", x, {1, 2})', lambda x, y: x not in (1, 2)),
    ('expr(TypeNode.LT, x, y)', lambda x, y: x < y),
    ('expr(TypeConditionOperator.GE, x, y)', lambda x, y: x >= y),
])
def test_expr(run, solver, request, constraint, predicate):
    check(request, run, solver,[constraint], XY, predicate,
          prefix="from pycsp3.classes.nodes import TypeNode\nfrom pycsp3.classes.auxiliary.enums import TypeConditionOperator\n")


@pytest.mark.parametrize("call", ['expr("foo", x, y)', 'expr("lt", x)', 'expr("lt", x, y, x)', 'expr("not", x, y)', 'expr(None, x, y)', 'expr(3, x, y)'])
def test_expr_invalid(run, call):
    assert_fails(run(f"x = Var(dom=range(3))\ny = Var(dom=range(3))\nsatisfy({call})"))


@pytest.mark.parametrize("call, message", [
    ("belong(x + 1, [1, 2])", "The first argument of belong() must be a variable or an integer, which is not the case of add(x,1) (for an expression, the operator in can be used)"),
    ("not_belong(2, [1, 2])", "When the first argument of not_belong() is an integer, the second argument must be a list of variables, which is not the case of [1, 2]"),
    ("belong(x, ['a'])", "The second argument of belong() must be an integer, a range or a collection of integers, which is not the case of ['a']"),
    ("iff(x > 0)", "iff() must have at least two arguments (possibly given in a list), which is not the case of 1"),
    ("imply(x > 0)", "imply() must have two arguments (a condition and a consequence), which is not the case of 1"),
    ("expr(None, x, y)", "The first argument of expr() must be an operator (a string such as \"lt\" or \"add\", or a TypeNode), which is not the case of None"),
    ('expr("foo", x, y)', "which is not the case of 'foo'"),
])
def test_intension_functions_invalid_messages(run, call, message):
    r = run(f"x = Var(dom=range(3))\ny = Var(dom=range(3))\nsatisfy({call})")
    assert not r.ok and message in r.stdout, r.report()


# ------------------------------------------------------------------------------------------------------------ XCSP3 files

@pytest.mark.parametrize("constraint, text", [
    ("x + y < 10", "lt(add(x,y),10)"),
    ("abs(x - y) > 2", "gt(dist(x,y),2)"),
    ("(x == 0) | (y > 1)", "or(eq(x,0),gt(y,1))"),
    ("imply(x > 0, y > 0)", "imp(gt(x,0),gt(y,1))".replace("1", "0")),
    ("iff(x > 0, y > 0, x == y)", "iff(gt(x,0),gt(y,0),eq(x,y))"),
    ("y == ift(x > 0, 2, 3)", "eq(y,if(gt(x,0),2,3))"),
    ("belong(x, {0, 2, 5})", "in(x,set(0,2,5))"),
    ("not_belong(x, {0, 2, 5})", "notin(x,set(0,2,5))"),
    ("belong(z, range(3, 15))", "and(ge(z,3),lt(z,15))"),
    ('expr("le", x, y)', "le(x,y)"),
])
def test_xcsp3_expressions(run, constraint, text):
    r = run(f"x = Var(dom=range(10))\ny = Var(dom=range(10))\nz = Var(dom=range(20))\nsatisfy({constraint})")
    assert r.ok, r.report()
    assert [c.text.strip() for c in r.xml.find("constraints")] == [text], r.report()
