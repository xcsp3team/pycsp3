import os

from pycsp3.solvers.solver import SolverProcess, SolverPy4J, directory_of_solver, class_path_chocosolver


class ChocoProcess(SolverProcess):
    def __init__(self):
        c = class_path_chocosolver()
        super().__init__(name="Choco-solver", command="java -cp " + c + " org.chocosolver.parser.xcsp.ChocoXCSP")


class ChocoPy4J(SolverPy4J):
    def __init__(self):
        d = directory_of_solver("chocosolver")
        c = class_path_chocosolver()
        super().__init__(name="Choco-solver", command="java -cp " + c + os.pathsep + d + "py4j0.10.8.1.jar" + os.pathsep + d + " ChocoSolverPy4J")

# command="java -cp /usr/local/share/py4j/py4j0.10.8.1.jar:.:./pyAbsCon/ StackEntryPoint"
