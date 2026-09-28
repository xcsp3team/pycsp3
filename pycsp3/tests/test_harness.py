"""
Checks of the test harness itself (harness.py).
"""

from itertools import permutations

from harness import brute_force, assert_solutions, assert_optimum


def test_all_solutions(run, solver):
    r = run("""
        x = VarArray(size=3, dom=range(3))
        satisfy(AllDifferent(x))
    """, solver=solver)
    assert r.variables == ["x[0]", "x[1]", "x[2]"]
    assert_solutions(r, set(permutations(range(3))))


def test_unsatisfiable(run, solver):
    r = run("""
        x = VarArray(size=2, dom=range(3))
        satisfy(x[0] < x[1], x[1] < x[0])
    """, solver=solver)
    assert r.status == "UNSAT"
    assert_solutions(r, set())


def test_variable_not_involved_in_constraints(run, solver):
    r = run("""
        x = Var(dom=range(2))
        y = Var(dom=range(2))
        satisfy(x == 0)
    """, solver=solver)
    assert r.raw_solutions == [(0, None)]  # y may take any value: '*' for ACE, no value for CHOCO and COSOCO
    assert_solutions(r, brute_force([range(2), range(2)], lambda x, y: x == 0))


def test_optimum(run, solver):
    r = run("""
        x = VarArray(size=2, dom=range(4))
        satisfy(x[0] != x[1])
        maximize(x[0] - 2 * x[1])
    """, solver=solver)
    assert_optimum(r, brute_force([range(4)] * 2, lambda a, b: a != b), lambda a, b: a - 2 * b, maximize=True)
    assert r.optimization.bound == 3


def test_unsatisfiable_optimization(run, solver):
    r = run("""
        x = VarArray(size=2, dom=range(3))
        satisfy(x[0] < x[1], x[1] < x[0])
        minimize(x[0] + x[1])
    """, solver=solver)
    assert_optimum(r, set(), lambda a, b: a + b)


def test_each_run_is_a_new_process(run):
    code = "x = VarArray(size=2, dom=range(2))"
    assert run(code).ok
    assert run(code).ok  # declaring x again is possible, since nothing remains from the previous run


def test_pycsp3_error(run):
    r = run("x = VarArray(size=0, dom=range(3))")
    assert not r.ok
    assert r.error is not None and "dimension" in r.error


def test_uncaught_exception(run):
    r = run("raise ValueError('bad value')")
    assert not r.ok
    assert r.exception == "ValueError"


def test_compilation_without_solving(run):
    r = run("""
        x = VarArray(size=3, dom=range(5))
        satisfy(AllDifferent(x))
    """)
    assert r.ok and r.status is None
    array = r.xml.find("variables/array")
    assert array.get("id") == "x" and array.get("size") == "[3]"
    assert r.xml.find("constraints/allDifferent") is not None


def test_command_line_data(run):
    r = run("""
        n = data
        x = VarArray(size=n, dom=range(n))
    """, args=["-data=4"])
    assert r.ok, r.report()
    assert r.xml.find("variables/array").get("size") == "[4]"
