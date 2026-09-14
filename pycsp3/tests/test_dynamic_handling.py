"""
Tests of the section Dynamic Handling of the API (https://pycsp.org/documentation/api/dynamic-handling/):
clear(), posted(), objective(), unpost(), value(), values(), solve(), status(), solution(), n_solutions(), bound(), ...
"""

import pytest

from harness import assert_fails


@pytest.mark.parametrize("model", [
    pytest.param("x = VarArray(size=2, dom=range(2))\ny = Var(dom={3, 5})", id="no constraint"),
    pytest.param("x = Var(dom=range(3))\nsatisfy(x.among(range(3)))", id="constraints simplified into true"),
    pytest.param("x = VarArray(size=2, dom=range(2))\nminimize(Sum(x))", id="objective without constraint"),
])
def test_solve_model_without_constraints(run, solver, model):
    r = run(model, solver=solver)
    assert_fails(r)
    assert "The instance has no constraint, so the solver is not run" in r.stderr, r.report()


def test_solver_error_is_reported(run):
    r = run("""
        x = VarArray(size=3, dom={"red", "green", "blue"})  # symbolic variables, not handled by cosoco
        satisfy(AllDifferent(x))
        print("status", solve(solver=COSOCO))
    """)
    assert 'expected type="integer"' in r.stdout + r.stderr, r.report()
