# Unit tests of PyCSP3

Each test runs a model as a user does: the model is written in a file `model.py`, in a temporary
directory, and executed in a new process (`python model.py [args]`). The pytest process never imports
pycsp3, so nothing is shared between two tests.

The solutions are checked with the three solvers ACE, CHOCO and COSOCO, against the solutions
computed by brute force in Python. All the solutions are always sought, so that a bug in any of the
solvers is detected (a missing solution, a wrong solution, a solution found twice): for a COP, all the
solutions satisfying the constraints are compared (the objective being discarded), and then the optimal
solution found is checked in another process.

## Installation

```bash
python3 -m venv .venv
.venv/bin/pip install lxml "cosoco>=2.6.1" pytest pytest-xdist pytest-timeout
```

Java is required by ACE and CHOCO.

## Running the tests

From the root of the repository:

```bash
.venv/bin/python -m pytest pycsp3/tests -n auto          # all tests, on all cores
.venv/bin/python -m pytest pycsp3/tests -m "not solving"  # only the tests that do not run the solvers
.venv/bin/python -m pytest pycsp3/tests -k CHOCO          # only the tests run with CHOCO
```

## Files of the tests

The files of each test are kept in `pycsp3/tests/output/<test file>/<test>/`, emptied at the start of
each session (so, only the files of the last session are available):

```
output/test_harness/test_optimum[CHOCO]/
  run0/                     # one directory per call to run() in the test
    model.py                # the model, as executed (with the lines appended by the harness)
    model.xml               # the generated XCSP3 file
    solver_<id>.log         # the output of the solver
    stdout.txt, stderr.txt  # the outputs of the process
    optimization/           # for a COP: the run seeking an optimal solution (same files)
```

To run a model again by hand: `cd <directory> && PYTHONPATH=<root of the repository> python model.py`.

## Writing a test

```python
from itertools import permutations

from harness import brute_force, assert_solutions, assert_optimum


def test_all_different(run, solver):  # run with ACE, CHOCO and COSOCO
    r = run("""
        x = VarArray(size=3, dom=range(3))
        satisfy(AllDifferent(x))
    """, solver=solver)
    assert_solutions(r, set(permutations(range(3))))


def test_minimize(run, solver):  # all the solutions satisfying the constraints, then the optimum
    r = run("""
        x = VarArray(size=2, dom=range(4))
        satisfy(x[0] != x[1])
        minimize(x[0] + 2 * x[1])
    """, solver=solver)
    assert_optimum(r, brute_force([range(4)] * 2, lambda a, b: a != b), lambda a, b: a + 2 * b)


def test_size_zero(run):  # no solver: the model is only executed (and compiled at exit)
    r = run("x = VarArray(size=0, dom=range(3))")
    assert not r.ok and "dimension" in r.error
```

- `run(code, solver=None, args=(), files=None, header=True)` executes the model; the line
  `from pycsp3 import *` is inserted at its top (unless `header=False`).
- The result gives `ok`, `stdout`, `stderr`, `error` (message of PyCSP3), `exception` (name of an uncaught
  exception), `xml` (the generated XCSP3 file) and, when a solver is specified, `status`, `variables`,
  `solutions`, `n_solutions` and `bound`.
- `brute_force(domains, predicate)` gives the expected solutions; `assert_solutions` and `assert_optimum`
  compare them with the ones found.

- `assert_fails(r)` checks that the model fails (error of PyCSP3 or uncaught exception), and
  `declared_variables(r)` gives the variables declared in the XCSP3 file with the values of their domains.

Models must be tiny (a few variables, small domains): the time of a test is mainly the time to launch
the solvers.

## Known bugs

A test failing because of a bug of PyCSP3 or of a solver expresses the correct behaviour, and is marked
as an expected failure, with the reason (displayed in the summary of pytest, as `xfail`). Each bug is
reported in a GitHub issue (labels `bug` and `unit-tests`), whose number starts the reason:

```python
@bug("#78: var() returns a Python list for an array, which cannot be indexed by a variable")
def test_var_function_array_indexed_by_variable(run, solver): ...

pytest.param("x = Var(dom=True)", [1], marks=bug("#67: the domain True gives an invalid XCSP3 file"))

def test_vararray_symbolic_solutions(run, solver, request):
    bug_for(request, "COSOCO", "xcsp3team/cosoco#71: cosoco does not handle symbolic variables")  # only for this solver
```

The marks are strict: once a bug is fixed, the test fails (`XPASS`), so as to remove its mark. A fix is
thus a commit that corrects the bug, removes the mark, and closes the issue with `Fixes #N` in its message.

## Continuous integration

The workflows of `.github/workflows` run for each pull request and each push on master (their status is
displayed by the badges of the main README):

- `tests-linux.yml` and `tests-macos.yml` run the tests on Linux and macOS; when a test fails, the files of
  the tests are kept as an artifact of the run (`files-of-the-tests-<os>`);
- `build-linux.yml` and `build-macos.yml` build the package, install it in a new environment and solve a model with it.

Both kinds of workflows are defined once, in `reusable-tests.yml` and `reusable-build.yml`.

## Organization

The test files follow the sections of the API of the web site (https://pycsp.org/documentation/api/):

| File                            | Section                 |
|---------------------------------|-------------------------|
| `test_structuration.py`         | Structuration           |
| `test_data.py`                  | Data                    |
| `test_variables.py`             | Variables               |
| `test_constraints_intension.py` | Constraints (Intension) |
| `test_constraints_global_*.py`  | Constraints (Global)    |
| `test_utilities.py`             | Utilities               |
| `test_dynamic_handling.py`      | Dynamic Handling        |
| `test_miscellaneous.py`         | Miscellaneous           |

`test_harness.py` checks the harness itself.
