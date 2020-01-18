import atexit, os, sys
from itertools import combinations, product, permutations

from pycsp3.functions import *  # keep it at first position (before Compilation)
from pycsp3.compiler import Compilation
from pycsp3.tools.utilities import value_in_base


def _pycharm_security():
    _ = (combinations, product, permutations)


__version__ = open(os.path.join(os.path.dirname(__file__), 'version.txt'), encoding='utf-8').read()

if sys.argv:
    if len(sys.argv) == 1 and sys.argv[0] == "-m":
        from shutil import copytree, ignore_patterns
        import os
        if os.name == 'nt':
            separator = "\\"
        else: 
            separator = "/"
        print("pycsp3 ", __version__)
        problems = separator.join(pycsp3.__file__.split(separator)[:-1]) + separator + "problems" + separator
        target = os.getcwd() + separator + "problems" + separator
        print("Source of files found: ", problems)
        copytree(problems, target, ignore=ignore_patterns('g7_todo', 'tests', '__init__.py', '__pycache__*'))
        print("Successfully created the directory " + target + " containing the problems !")
        exit(0)
    elif sys.argv[0] == '':
        Compilation.load(console=True)
        data = None
    elif 'tests' not in sys.argv[0].split("/"):  #  Import from tests are not models ; didn't understand the comment (chriss)
        Compilation.load()
        data = Compilation.data
    else:
        Compilation.done = True


@atexit.register
def end():
    if not Compilation.done:
        Compilation.compile()


def compile():
    return Compilation.compile()
