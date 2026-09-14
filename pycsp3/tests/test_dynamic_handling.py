"""
Tests of the section Dynamic Handling of the API (https://pycsp.org/documentation/api/dynamic-handling/):
clear(), posted(), objective(), unpost(), value(), values(), solve(), status(), solution(), n_solutions(), bound(), ...
"""

from harness import assert_solutions, brute_force, bug


@bug("#80: solving a model without constraints fails: pycsp3 raises AttributeError with choco and cosoco, and ace gives UNKNOWN")
def test_solve_model_without_constraints(run, solver):
    r = run("x = VarArray(size=2, dom=range(2))", solver=solver)
    assert_solutions(r, brute_force([range(2)] * 2, lambda a, b: True))


@bug("#84: the error of the solver is not displayed: solve() only gives UNKNOWN")
def test_solver_error_is_reported(run):
    r = run("""
        x = VarArray(size=3, dom={"red", "green", "blue"})  # symbolic variables, not handled by cosoco
        satisfy(AllDifferent(x))
        print("status", solve(solver=COSOCO))
    """)
    assert 'expected type="integer"' in r.stdout + r.stderr, r.report()
