"""
Tests of the section Dynamic Handling of the API (https://pycsp.org/documentation/api/dynamic-handling/):
clear(), posted(), objective(), unpost(), value(), values(), solve(), status(), solution(), n_solutions(), bound(), ...
"""

from harness import assert_solutions, brute_force, bug


def test_solve_model_without_constraints(run, solver):
    r = run("""
        x = VarArray(size=2, dom=range(2))
        y = Var(dom={3, 5})
        z = VarArray(size=3, dom=lambda i: None if i == 1 else range(i + 1))
    """, solver=solver)
    assert r.n_solutions == 1 and r.raw_solutions == [(None, None, None, None, None)], r.report()
    assert_solutions(r, brute_force([range(2), range(2), [3, 5], range(1), range(3)], lambda *t: True))


def test_solve_model_whose_constraints_are_true(run, solver):
    r = run("""
        x = Var(dom=range(3))
        satisfy(x.among(range(3)))
    """, solver=solver)
    assert_solutions(r, {(0,), (1,), (2,)})


@bug("#84: the error of the solver is not displayed: solve() only gives UNKNOWN")
def test_solver_error_is_reported(run):
    r = run("""
        x = VarArray(size=3, dom={"red", "green", "blue"})  # symbolic variables, not handled by cosoco
        satisfy(AllDifferent(x))
        print("status", solve(solver=COSOCO))
    """)
    assert 'expected type="integer"' in r.stdout + r.stderr, r.report()
