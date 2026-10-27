import hashlib
import re
import shutil
from itertools import count
from pathlib import Path

import pytest

from harness import COSOCO_UNAVAILABLE, SOLVERS, build_java_archives, run_console, run_model

# The files of each test (models, XCSP3 files, solver logs, outputs) are kept in output/<test file>/<test>,
# this directory being emptied at the start of each session.
OUTPUT = Path(__file__).resolve().parent / "output"


def pytest_configure(config):
    if not hasattr(config, "workerinput"):  # not in a worker of pytest-xdist, so only once per session
        shutil.rmtree(OUTPUT, ignore_errors=True)
        build_java_archives(OUTPUT / "java")  # the Java solvers start faster with an archive of their classes (see harness)


@pytest.fixture(params=SOLVERS)
def solver(request):
    """The name of each solver in turn: a test using this fixture is run with ACE, CHOCO and COSOCO."""
    return request.param


def _directory(request):
    """The directory of the files of the test, emptied."""
    name = re.sub(r"[^\w\-\[\].,=+]", "_", request.node.name)
    if name != request.node.name or len(name) > 120:  # a digest keeps distinct the names differing only by replaced characters (e.g., < and >)
        name = name[:120] + "-" + hashlib.sha1(request.node.name.encode()).hexdigest()[:8]
    directory = OUTPUT / request.node.path.stem / name
    shutil.rmtree(directory, ignore_errors=True)
    directory.mkdir(parents=True)
    return directory


@pytest.fixture
def run(request):
    """Runs a model in a new process, in its own subdirectory run<i> of the directory of the test (see harness.run_model)."""
    directory = _directory(request)
    numbers = count()

    def _run(code, **kwargs):
        subdirectory = directory / ("run" + str(next(numbers)))
        subdirectory.mkdir()
        return run_model(code, subdirectory, **kwargs)

    return _run


@pytest.fixture
def console(request):
    """Types lines in an interactive interpreter of Python, in its own subdirectory console<i> of the directory of the test (see harness.run_console)."""
    directory = _directory(request)
    numbers = count()

    def _console(lines, **kwargs):
        subdirectory = directory / ("console" + str(next(numbers)))
        subdirectory.mkdir()
        return run_console(lines, subdirectory, **kwargs)

    return _console


def pytest_collection_modifyitems(items):
    for item in items:
        if "solver" in getattr(item, "fixturenames", ()):
            item.add_marker(pytest.mark.solving)
            if COSOCO_UNAVAILABLE and item.callspec.params.get("solver") == "COSOCO":
                item.add_marker(pytest.mark.skip(reason="cosoco is not available on Windows (no package on PyPI)"))
