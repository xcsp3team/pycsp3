import hashlib
import re
import shutil
from itertools import count
from pathlib import Path

import pytest

from harness import SOLVERS, run_model

# The files of each test (models, XCSP3 files, solver logs, outputs) are kept in output/<test file>/<test>,
# this directory being emptied at the start of each session.
OUTPUT = Path(__file__).resolve().parent / "output"


def pytest_configure(config):
    if not hasattr(config, "workerinput"):  # not in a worker of pytest-xdist, so only once per session
        shutil.rmtree(OUTPUT, ignore_errors=True)


@pytest.fixture(params=SOLVERS)
def solver(request):
    """The name of each solver in turn: a test using this fixture is run with ACE, CHOCO and COSOCO."""
    return request.param


@pytest.fixture
def run(request):
    """Runs a model in a new process, in its own subdirectory run<i> of the directory of the test (see harness.run_model)."""
    name = re.sub(r"[^\w\-\[\].,=+]", "_", request.node.name)
    if name != request.node.name or len(name) > 120:  # a digest keeps distinct the names differing only by replaced characters (e.g., < and >)
        name = name[:120] + "-" + hashlib.sha1(request.node.name.encode()).hexdigest()[:8]
    directory = OUTPUT / request.node.path.stem / name
    shutil.rmtree(directory, ignore_errors=True)
    directory.mkdir(parents=True)
    numbers = count()

    def _run(code, **kwargs):
        subdirectory = directory / ("run" + str(next(numbers)))
        subdirectory.mkdir()
        return run_model(code, subdirectory, **kwargs)

    return _run


def pytest_collection_modifyitems(items):
    for item in items:
        if "solver" in getattr(item, "fixturenames", ()):
            item.add_marker(pytest.mark.solving)
