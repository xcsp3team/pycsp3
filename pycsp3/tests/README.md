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

Models must be tiny (a few variables, small domains): the time of a test is mainly the time to launch
the solvers.

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
