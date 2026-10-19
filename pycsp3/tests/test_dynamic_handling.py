"""
Tests of the section Dynamic Handling of the API (https://pycsp.org/documentation/api/dynamic-handling/):
clear(), posted(), objective(), unpost(), value(), values(), solve(), status(), solution(), n_solutions(), bound(), ...
"""

import pytest

from harness import COSOCO_UNAVAILABLE, assert_fails


@pytest.mark.parametrize("model", [
    pytest.param("x = VarArray(size=2, dom=range(2))\ny = Var(dom={3, 5})", id="no constraint"),
    pytest.param("x = Var(dom=range(3))\nsatisfy(x.among(range(3)))", id="constraints simplified into true"),
    pytest.param("x = VarArray(size=2, dom=range(2))\nminimize(Sum(x))", id="objective without constraint"),
])
def test_solve_model_without_constraints(run, solver, model):
    r = run(model, solver=solver)
    assert_fails(r)
    assert "The instance has no constraint, so the solver is not run" in r.stderr, r.report()


@pytest.mark.skipif(COSOCO_UNAVAILABLE, reason="cosoco is not available on Windows (no package on PyPI)")
def test_solver_error_is_reported(run):
    r = run("""
        x = VarArray(size=3, dom={"red", "green", "blue"})  # symbolic variables, not handled by cosoco
        satisfy(AllDifferent(x))
        print("status", solve(solver=COSOCO))
    """)
    assert 'expected type="integer"' in r.stdout + r.stderr, r.report()


@pytest.mark.skipif(not COSOCO_UNAVAILABLE, reason="only on Windows, where cosoco is not available")
def test_cosoco_not_available_on_windows(run):  # the package cosoco has no version for Windows, so it is not installed automatically
    r = run("""
        x = VarArray(size=2, dom=range(2))
        satisfy(x[0] != x[1])
        solve(solver=COSOCO)
    """)
    assert_fails(r)
    assert r.exception == "ImportError" and "cosoco is not available on Windows" in r.stderr, r.report()
    assert "installing it now" not in r.stderr, r.report()
