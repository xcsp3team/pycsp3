import atexit
import os
import sys

__python_version__ = str(sys.version).split(os.linesep)[0].split(' ')[0]

if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    __message_version__ = os.linesep + " Python should be at least 3.5" + os.linesep + " Your version is Python " + __python_version__
    raise Exception(__message_version__)

from pycsp3.functions import *  # keep it at first position (before Compilation)
from pycsp3.compiler import Compilation
from pycsp3.solvers.ace.ace import Ace
from pycsp3.solvers.choco.choco import Choco
from pycsp3.solvers.solver import process_options
from pycsp3.classes.auxiliary.ptypes import TypeSolver
from pycsp3.tools.utilities import Error

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
    elif sys.argv[-1] == '-debug':  # debug mode
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

last_solver = None  # this is the last built solver


def compile(filename=None, *, disabling_opoverrider=False, verbose=1):
    global last_solver
    filename, cop = Compilation.compile(filename, disabling_opoverrider, verbose=verbose)
    solving = TypeSolver.ACE.name if options.solve else options.solver
    if solving:
        if options.display:
            print("Warning: options -display and -solve should not be used together.")
            return filename
        solver, args, args_recursive = process_options(solving)
        solver = next(ss for ss in TypeSolver if ss.name.lower() == solver.lower())
        if solver == TypeSolver.CHOCO:
            from pycsp3.solvers.choco import Choco
            last_solver = Choco()
            result = last_solver.solve((filename, cop), solving, args, args_recursive, compiler=True, verbose=verbose, automatic=True)
        else:  # Fallback case => options.solver == "ace":
            from pycsp3.solvers.ace import Ace
            last_solver = Ace()
            result = last_solver.solve((filename, cop), solving, args, args_recursive, compiler=True, verbose=verbose, automatic=True)
        print("\nResult: ", result)
        if solution():
            print(solution())

    return filename, cop


def solution():
    global last_solver
    return None if last_solver is None else last_solver.last_solution


def n_solutions():
    global last_solver
    return None if last_solver is None else last_solver.n_solutions


def bound():
    global last_solver
    return None if last_solver is None else last_solver.bound


def solve(*, solver=TypeSolver.ACE, options=None, filename=None, disabling_opoverrider=False, verbose=0, all_solutions=False):
    global last_solver
    instance = compile(filename, disabling_opoverrider=disabling_opoverrider, verbose=verbose)
    if instance is None:
        print("Problem when compiling")
    else:
        last_solver = Ace() if solver == TypeSolver.ACE else Choco()
        last_solver.setting(options)
        result = last_solver.solve(instance, dict_simplified_options={"nolimit": True} if all_solutions else {}, verbose=verbose)
        return result


@atexit.register
def end():
    if not Compilation.done and not Error.errorOccurrence:
        compile(disabling_opoverrider=True)
