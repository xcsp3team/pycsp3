"""
Tests of the console mode: PyCSP3 is used in the interactive interpreter of Python, the lines being typed one by one as a user does, in the
basic interpreter and in the new interpreter of Python 3.13+, which give other names to the typed code ("<stdin>-1", "<python-input-1>", ...).
"""

import re
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="the console mode is not available on Windows (no module readline)")


@pytest.fixture(params=["basic", pytest.param("new", marks=pytest.mark.skipif(sys.version_info < (3, 13), reason="new interpreter of Python 3.13+"))])
def repl(request):
    """The basic interactive interpreter, and the new one of Python 3.13+."""
    return request.param


def test_interpreter(console, repl):  # the expected interpreter is run, as shown by the name of the typed code
    r = console(["import sys", "print('NAME', sys._getframe().f_code.co_filename)"], repl=repl)
    name = re.search(r"^NAME (\S+)\s*$", r.output, re.M)
    assert name is not None, r.report()
    assert name.group(1).startswith("<python-input-" if repl == "new" else "<stdin"), r.report()


def test_names_of_variables(console, repl):
    r = console(["from pycsp3 import *",
                 "x = Var(range(10))",
                 "y = VarArray(size=2, dom={0, 1})",
                 "z = VarArray(",
                 "   size=[2, 3],",
                 "   dom=range(3)",
                 ")",
                 "satisfy(x > y[0], AllDifferent(z[0]))",
                 "compile()"], repl=repl)
    assert r.xml is not None, r.report()
    variables = [(e.tag, e.get("id"), e.get("size")) for e in r.xml.find("variables")]
    assert variables == [("var", "x", None), ("array", "y", "[2]"), ("array", "z", "[2][3]")], r.report()


def test_comments_become_notes(console, repl):  # the comment of an array, and the comment of a constraint (the quoted name replaced by its value)
    r = console(["from pycsp3 import *",
                 "n = 15",
                 "# x[i] is the ith value",
                 "x = VarArray(size=2, dom=range(10))",
                 "satisfy(",
                 "   # the sum is more than 'n'",
                 "   x[0] + x[1] > n",
                 ")",
                 "compile()"], repl=repl)
    assert r.xml is not None, r.report()
    assert r.xml.find("variables/array").get("note") == "x[i] is the ith value", r.report()
    assert r.xml.find("constraints/intension").get("note") == "the sum is more than 15", r.report()


def test_example_of_the_readme(console, repl):  # Example 1 of the README
    r = console(["from pycsp3 import *",
                 "x = Var(range(10))",
                 "y = Var(range(10))",
                 "satisfy(",
                 "   x < y,",
                 "   x + y > 15",
                 ")",
                 "compile()",
                 "if solve() is SAT:",
                 "   print(value(x), value(y))",
                 ""], repl=repl)
    values = re.findall(r"^(\d+) (\d+)\s*$", r.output, re.M)
    assert len(values) == 1, r.report()
    x, y = map(int, values[0])
    assert x < y and x + y > 15, r.report()
