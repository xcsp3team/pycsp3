import atexit
import sys
import os
from itertools import combinations, product, permutations

from pycsp3.functions import *
from pycsp3.compiler import Compilation
from pycsp3.tools.utilities import value_in_base


def _pycharm_security():
    _ = combinations
    _ = product
    _ = permutations


__version__ = open(os.path.join(os.path.dirname(__file__), 'version.txt'), encoding='utf-8').read()

if sys.argv:
    if len(sys.argv) == 1 and sys.argv[0] == "-m":
        from shutil import copytree, ignore_patterns
        import os

        print("pycsp3 ", __version__)
        problems = "/".join(pycsp3.__file__.split("/")[:-1]) + "/problems/"
        target = os.getcwd() + "/problems/"
        print("Source of files found: ", problems)
        copytree(problems, target, ignore=ignore_patterns('g7_todo', 'tests', '__init__.py', '__pycache__*'))
        print("Successfully created the directory " + target + " containing the problems !")
        exit(0)
    elif sys.argv[0] == '':
        Compilation.load(console=True)
        data = None
    else:
        directories = sys.argv[0].split("/")
        if 'tests' not in directories:
            #  Import from tests are not models
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
