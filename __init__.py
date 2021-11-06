import atexit
import math
import os
import sys
import types
from collections import namedtuple
from itertools import product, permutations

__python_version__ = str(sys.version).split(os.linesep)[0].split(' ')[0]

if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    __message_version__ = os.linesep + " Python should be at least 3.6" + os.linesep + " Your version is Python " + __python_version__
    raise Exception(__message_version__)

from pycsp3.classes.auxiliary.conditions import lt, le, ge, gt, ne, eq, complement
from pycsp3.classes.auxiliary.ptypes import TypeStatus, TypeSolver
from pycsp3.tools.utilities import ANY, flatten, transpose, alphabet_positions, all_primes, integer_scaling, to_ordinary_table
from pycsp3.functions import (
    combinations, Automaton, MDD, clear, default_data, options, columns, protect, variant, subvariant)
from pycsp3.functions import (
    Var, VarArray, And, Or, Not, Xor, IfThen, IfThenElse, Iff, Slide, satisfy, col, abs, min, max, xor, iff, imply, ift, belong, not_belong, expr, conjunction,
    disjunction)
from pycsp3.functions import (
    AllDifferent, AllDifferentList, AllEqual, Increasing, Decreasing, LexIncreasing, LexDecreasing, Sum, Count, NValues, Cardinality, Maximum, Minimum, Channel,
    NoOverlap, Cumulative, BinPacking, Circuit, Clause, minimize, maximize, annotate)
from pycsp3.functions import (
    diagonal_down, diagonals_down, diagonal_up, diagonals_up, different_values, cp_array, posted, objective, unpost, value, values)

# from pycsp3.compiler import Compilation  # keep it after other imports
# from pycsp3.solvers.ace import Ace
# from pycsp3.solvers.choco import Choco

UNSAT, SAT, OPTIMUM, UNKNOWN = [s for s in TypeStatus]
ACE, CHOCO = [s for s in TypeSolver]
ALL = "all"

__version__ = open(os.path.join(os.path.dirname(__file__), 'version.txt'), encoding='utf-8').read()

if sys.argv:
    if len(sys.argv) == 1 and sys.argv[0] == "-m":  # copy of models
        import shutil
        import pycsp3

        print("Python version: ", __python_version__)
        print("PyCSP3 version: ", __version__)
        problems = os.sep.join(pycsp3.__file__.split(os.sep)[:-1]) + os.sep + "problems" + os.sep
        target = os.getcwd() + os.sep + "problems" + os.sep
        print("Source of files found: ", problems)
        shutil.copytree(problems, target, ignore=shutil.ignore_patterns('g6_testing', 'g7_todo', 'tests', '__init__.py', '__pycache__*'))
        print("Successfully created the directory " + target + " containing the problems !")
        exit(0)
    from pycsp3.compiler import Compilation

    if sys.argv[-1] == '-debug':  # debug mode
        try:
            Compilation.load()
            data = Compilation.data
            with open(sys.argv[0]) as f:
                code = compile(f.read(), sys.argv[0], 'exec')
                exec(code)
        except Exception as e:
            import traceback

            print("Error: ", e)
            # TODO analysing cases and displaying information (most modeling mistakes)
            print("\n")
            print(traceback.format_exc())
            exit(1)
    elif sys.argv[0] == '':  # console mode
        Compilation.load(console=True)
        data = None
    elif "pycsp3/problems/tests/" in sys.argv[0]:  # test mode
        # TODO is it correct (for avoiding compiling two times)?
        #  analysing if we have to compile (e..g, when running the tester, we should not try to do that);
        #  Trying to replace this with the inspector?
        Compilation.done = True
    else:
        Compilation.load()
        data = Compilation.data

_solver = None  # current solver


def _set_solver(name):
    global _solver
    if name == CHOCO:
        from pycsp3.solvers.choco import Choco
        _solver = Choco()
    else:  # Fallback case => ace
        from pycsp3.solvers.ace import Ace
        _solver = Ace()
    return _solver


def solver(name=None):
    return _solver if name is None else _set_solver(name)


def compile(filename=None, *, disabling_opoverrider=False, verbose=1):
    global _solver
    from pycsp3.compiler import Compilation
    filename, cop = Compilation.compile(filename, disabling_opoverrider, verbose=verbose)
    solving = ACE.name if options.solve else options.solver
    if solving:
        if options.display:
            print("Warning: options -display and -solve should not be used together.")
            return filename
        from pycsp3.solvers.solver import process_options
        solver_name, args, args_recursive = process_options(solving)
        solver_name = next(ss for ss in TypeSolver if ss.name.lower() == solver_name.lower())
        _solver = _set_solver(solver_name)
        result = _solver.solve((filename, cop), solving, args, args_recursive, compiler=True, verbose=verbose, automatic=True)
        print("\nResult: ", result)
        if solution():
            print(solution())
    return filename, cop


def solution():
    return None if _solver is None else _solver.last_solution


def n_solutions():
    return None if _solver is None else _solver.n_solutions


def bound():
    return None if _solver is None else _solver.bound


def solve(*, solver=ACE, options=None, filename=None, disabling_opoverrider=False, verbose=0, sols=None):
    global _solver
    instance = compile(filename, disabling_opoverrider=disabling_opoverrider, verbose=verbose)
    if instance is None:
        print("Problem when compiling")
    else:
        _solver = _set_solver(solver)
        # we cannot call the function solver there is a conflict with the parameter of same name
        if solver == ACE and (sols == ALL or isinstance(sols, int) and sols > 1):
            options = "-xe -xc=false" if options is None else options + " -xe -xc=false"
        _solver.setting(options)
        limit = "limit=no" if sols == ALL else "limit=" + str(sols) + "sols" if isinstance(sols, int) else ""
        return _solver.solve(instance, string_options=limit, dict_options=dict(), dict_simplified_options=dict(), verbose=verbose)


def _pycharm_security():  # for avoiding that imports are removed when reformatting code
    _ = (math, types, namedtuple, product, permutations)


@atexit.register
def end():
    from pycsp3.tools.utilities import Error
    if not Compilation.done and not Error.errorOccurrence:
        compile(disabling_opoverrider=True)
