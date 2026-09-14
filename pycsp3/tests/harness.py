"""
The test harness: each test runs a PyCSP3 model as a user does, that is to say by writing it in a
Python file and executing this file (python model.py [args]) in a new process.

The pytest process never imports pycsp3, so that no state is shared between two tests.
When a solver is specified, a few lines are appended to the model: they solve it and print the result in
JSON, which is read back here. All the solutions are always sought, so as to detect a bug in any of the
solvers (a missing solution, a wrong solution, a solution found twice):
 - for a CSP, all the solutions;
 - for a COP, all the solutions satisfying the constraints (the objective being discarded), and then,
   in another process, an optimal solution.
"""

import json
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path

import pytest
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]  # the root of the repository, containing the package pycsp3

SOLVERS = ("ACE", "CHOCO", "COSOCO")

TIMEOUT = 60  # in seconds, for running a model (solving included)

MARKER = "@@PYCSP3-TEST@@"

ANSI_CODES = re.compile(r"\x1b\[[0-9;]*m")

# A value is None in a solution when the solver gives '*' (ACE) or no value (CHOCO, COSOCO) for a variable
# involved in no constraint: any value of its domain is possible.
SOLVING = """
# ---- appended by the test harness ----
import builtins as _builtins  # the model imports min, max, abs, ... from pycsp3
import json as _json
from pycsp3.classes.entities import VarEntities as _VarEntities, ObjEntities as _ObjEntities, EVar as _EVar

_cop = len(_ObjEntities.items) > 0
if {enumerating}:
    _ObjEntities.items = []  # all the solutions satisfying the constraints are sought, whatever the objective
_status = solve(solver={solver}, sols=ALL if {enumerating} else None)
_variables = [x for e in _VarEntities.items if not e.id.startswith("aux_gb") for x in ([e.variable] if isinstance(e, _EVar) else e.flatVars)]
_histories = [getattr(x, "values", None) or [] for x in _variables]
_solutions = [[h[k] if k < len(h) else None for h in _histories] for k in range(_builtins.max((len(h) for h in _histories), default=0))]
print({marker!r} + _json.dumps({{
    "status": None if _status is None else _status.name,
    "cop": _cop,
    "variables": [x.id for x in _variables],
    "domains": [list(x.dom.all_values()) for x in _variables],
    "solutions": [[None if v is None or v is ANY else v if isinstance(v, int) else str(v) for v in s] for s in _solutions],
    "n_solutions": n_solutions(),
    "bound": bound(),
}}))
"""


@dataclass
class Run:
    """The result of running a model."""
    returncode: int
    stdout: str
    stderr: str
    directory: Path
    status: str | None = None  # "SAT", "UNSAT", "OPTIMUM", ..., or None if the model was not solved
    cop: bool = False  # True if the model has an objective
    variables: list = field(default_factory=list)  # the ids of the variables of the model, in the order of declaration
    domains: list = field(default_factory=list)  # the values of the domains of the variables (same order)
    raw_solutions: list = field(default_factory=list)  # the solutions as given by the solver, None meaning any value
    n_solutions: int | None = None
    bound: int | None = None
    optimization: "Run | None" = None  # for a COP, the run seeking an optimal solution

    @property
    def ok(self):
        return self.returncode == 0

    @property
    def solutions(self):
        """The solutions found, each one a tuple of values (same order as variables), None being replaced by each value of the domain."""
        return [t for s in self.raw_solutions for t in product(*([v] if v is not None else dom for v, dom in zip(s, self.domains)))]

    @property
    def lines(self):
        """The lines displayed by the model (and by PyCSP3), stripped."""
        return [line.strip() for line in self.stdout.splitlines()]

    @property
    def error(self):
        """The message displayed by the function error() of PyCSP3, or None."""
        m = re.search(r"ERROR:\s*(.*)", self.stdout)
        return m.group(1).strip() if m else None

    @property
    def exception(self):
        """The name of the class of the uncaught exception, or None."""
        if "Traceback (most recent call last)" not in self.stderr:
            return None
        last = [line for line in self.stderr.splitlines() if line.strip()][-1]
        m = re.match(r"([A-Za-z_][\w.]*)(:|$)", last)
        return m.group(1).rpartition(".")[2] if m else last

    @property
    def xml(self):
        """The root element of the generated XCSP3 file, or None if no file was generated."""
        files = sorted(self.directory.glob("*.xml"))
        assert len(files) <= 1, "several XCSP3 files: " + str(files)
        return etree.parse(str(files[0])).getroot() if files else None

    def report(self):
        return "\n".join(["return code: " + str(self.returncode), "directory: " + str(self.directory),
                          "---- stdout ----", self.stdout, "---- stderr ----", self.stderr])


def _execute(code, directory, args, files, timeout):
    (directory / "model.py").write_text(code)
    for name, content in (files or {}).items():
        (directory / name).parent.mkdir(parents=True, exist_ok=True)  # the name may contain subdirectories, as in "instances/a.txt"
        (directory / name).write_text(content)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    try:
        process = subprocess.run([sys.executable, "model.py", *args], cwd=directory, env=env, stdin=subprocess.DEVNULL,  # input() never waits
                                 capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        pytest.fail("the model has not been run in " + str(timeout) + " seconds (directory: " + str(directory) + ")")

    r = Run(process.returncode, ANSI_CODES.sub("", process.stdout), ANSI_CODES.sub("", process.stderr), directory)
    (directory / "stdout.txt").write_text(r.stdout)
    (directory / "stderr.txt").write_text(r.stderr)
    lines =[line for line in r.stdout.splitlines() if line.startswith(MARKER)]
    if lines:
        result = json.loads(lines[-1][len(MARKER):])
        r.status, r.cop, r.variables, r.domains = result["status"], result["cop"], result["variables"], result["domains"]
        r.raw_solutions = [tuple(s) for s in result["solutions"]]
        r.n_solutions, r.bound = result["n_solutions"], result["bound"]
    return r


def run_model(code, directory, *, solver=None, args=(), files=None, header=True, timeout=TIMEOUT):
    """
    Writes the specified code in the file model.py of the specified directory, and executes it.

    :param code: the code of the model (dedented, so that it can be written as an indented triple-quoted string)
    :param directory: the directory where the model is written and executed
    :param solver: "ACE", "CHOCO" or "COSOCO" for solving the model, or None for only executing it
    :param args: the arguments of the command line, as in ["-data=[3,4]", "-variant=table"]
    :param files: other files to be written in the directory (e.g., JSON data), as a dict name -> content
    :param header: True if the line "from pycsp3 import *" must be inserted at the top of the model
    :param timeout: the maximal time (in seconds) for running the model
    """
    assert solver is None or solver in SOLVERS, solver
    code = textwrap.dedent(code).strip("\n") + "\n"
    if header:
        code = "from pycsp3 import *\n\n" + code
    if solver is None:
        return _execute(code, directory, args, files, timeout)
    r = _execute(code + SOLVING.format(solver=solver, marker=MARKER, enumerating=True), directory, args, files, timeout)
    if r.cop:
        (directory / "optimization").mkdir()
        r.optimization = _execute(code + SOLVING.format(solver=solver, marker=MARKER, enumerating=False),
                                  directory / "optimization", args, files, timeout)
    return r


def bug(reason):
    """
    Marks a test, or a parameter of a test, failing because of a bug of PyCSP3 (or of a solver).
    The mark is strict: once the bug is fixed, the test fails, so as to remove the mark.
    """
    return pytest.mark.xfail(strict=True, reason="bug: " + reason)


def bug_for(request, solvers, reason):
    """
    Marks the running test as failing because of a bug, when it is run with one of the specified solvers
    (a name, or a tuple of names). To be called at the start of a test using the fixture solver.
    """
    solvers = (solvers,) if isinstance(solvers, str) else solvers
    if request.node.callspec.params.get("solver") in solvers:
        request.applymarker(bug(reason))


def assert_fails(r):
    """
    Checks that running the model has failed with an explicit message, that is to say:
     - an error reported by PyCSP3 (function error()),
     - or an exception raised by an assert or a raise statement with a message,
     - or an exception raised by Python on a line of the model itself (e.g., a missing argument), or an IndexError/KeyError.
    An assert without message, or an exception raised by Python inside PyCSP3 (e.g., TypeError: '<' not supported
    between instances of 'str' and 'int'), is not explicit.
    """
    assert not r.ok, "the model should fail\n" + r.report()
    if r.error is not None:
        return
    assert r.exception is not None, "the model fails without any message\n" + r.report()
    lines = [line for line in r.stderr.splitlines() if line.strip()]
    frames = [i for i, line in enumerate(lines) if line.lstrip().startswith("File ")]
    location = lines[frames[-1]] if frames else ""
    statement = lines[frames[-1] + 1].strip() if frames and frames[-1] + 1 < len(lines) else ""
    message = lines[-1].partition(":")[2].strip()
    explicit = ((statement.startswith("assert") and r.exception == "AssertionError" or statement.startswith("raise")) and message) \
               or '/model.py", line' in location or r.exception in ("IndexError", "KeyError")
    assert explicit, "the error is not explicit: " + lines[-1] + " (raised by: " + statement + ")\n" + r.report()


def _domain_values(text):
    values = []
    for token in text.split():
        bounds = re.fullmatch(r"(-?\d+)\.\.(-?\d+)", token)
        if bounds and int(bounds.group(2)) - int(bounds.group(1)) < 100000:
            values.extend(range(int(bounds.group(1)), int(bounds.group(2)) + 1))
        elif re.fullmatch(r"-?\d+", token):
            values.append(int(token))
        else:
            values.append(token)  # a symbol, or an interval too large for being expanded
    return values


def _expand(token, name, sizes):
    brackets = re.findall(r"\[([^\]]*)\]", token)
    indexes = [range(sizes[k]) if b == "" else range(int(b.split("..")[0]), int(b.split("..")[1]) + 1) if ".." in b else [int(b)]
               for k, b in enumerate(brackets)]
    return [name + "".join("[" + str(i) + "]" for i in t) for t in product(*indexes)]


def declared_variables(r):
    """
    Returns the variables declared in the generated XCSP3 file, as a dict mapping the id of each variable
    (e.g., x or y[1][2]) to the list of the values of its domain.
    """
    assert r.ok, r.report()
    assert r.xml is not None, "no XCSP3 file has been generated\n" + r.report()
    variables = {}
    for element in r.xml.find("variables"):
        name = element.get("id")
        if element.tag == "var":
            variables[name] = _domain_values(element.text)
            continue
        sizes = [int(s) for s in re.findall(r"\[(\d+)\]", element.get("size"))]
        cells = [name + "".join("[" + str(i) + "]" for i in t) for t in product(*(range(s) for s in sizes))]
        domains = element.findall("domain")
        if len(domains) == 0:
            variables.update((cell, _domain_values(element.text)) for cell in cells)
        for domain in domains:
            tokens = domain.get("for").split()
            names = [c for c in cells if c not in variables] if tokens == ["others"] else [v for token in tokens for v in _expand(token, name, sizes)]
            variables.update((v, _domain_values(domain.text)) for v in names)
    return variables


def brute_force(domains, predicate):
    """
    Returns the set of tuples of the Cartesian product of the specified domains satisfying the predicate.
    The predicate receives the values of a tuple as arguments, as in lambda x, y: x < y or lambda *x: len(set(x)) == len(x).
    """
    return {t for t in product(*domains) if predicate(*t)}


def assert_solutions(r, expected):
    """
    Checks that the solutions found are exactly the expected ones (a set of tuples), each one being found only once.
    For a COP, the solutions are those satisfying the constraints, whatever the objective.
    """
    assert r.ok, r.report()
    assert r.status in ("SAT", "UNSAT"), "unexpected status " + str(r.status) + "\n" + r.report()
    solutions = r.solutions
    found = set(solutions)
    duplicates = sorted({t for t in solutions if solutions.count(t) > 1})
    assert not duplicates, "solutions found several times: " + str(duplicates) + "\n" + r.report()
    missing, wrong = set(expected) - found, found - set(expected)
    assert not missing and not wrong, "missing solutions: " + str(sorted(missing)) + "\nwrong solutions: " + str(sorted(wrong))
    assert (r.status == "UNSAT") == (len(expected) == 0), "status " + r.status + " with " + str(len(expected)) + " expected solutions"
    if r.status == "SAT" and r.n_solutions is not None:
        assert r.n_solutions == len(r.raw_solutions), \
            "n_solutions() gives " + str(r.n_solutions) + " but " + str(len(r.raw_solutions)) + " solutions are recorded\n" + r.report()


def assert_optimum(r, expected, objective, *, maximize=False):
    """
    Checks a COP: its solutions (whatever the objective) must be exactly the expected ones (a set of tuples),
    and the optimal solution found must be one of them, with the best value of the objective.

    :param objective: the objective as a Python function, receiving the values of a tuple as arguments
    """
    assert_solutions(r, expected)
    assert r.cop, "the model has no objective"
    o = r.optimization
    assert o.ok, o.report()
    if len(expected) == 0:
        assert o.status == "UNSAT", "unexpected status " + str(o.status) + "\n" + o.report()
        return
    best = (max if maximize else min)(objective(*t) for t in expected)
    assert o.status == "OPTIMUM", "unexpected status " + str(o.status) + "\n" + o.report()
    assert o.bound == best, "bound " + str(o.bound) + " instead of " + str(best)
    assert len(o.raw_solutions) > 0, "no optimal solution recorded\n" + o.report()
    for t in product(*([v] if v is not None else dom for v, dom in zip(o.raw_solutions[-1], o.domains))):
        assert t in expected, "the optimal solution " + str(t) + " does not satisfy the constraints"
        assert objective(*t) == best, "the optimal solution " + str(t) + " has value " + str(objective(*t)) + " instead of " + str(best)
