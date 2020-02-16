import os

from pycsp3.solvers.solver import SolverProcess, SolverPy4J, directory_of_solver, class_path_abscon


class AbsConProcess(SolverProcess):
    def __init__(self):
        c = class_path_abscon()
        super().__init__(name="AbsCon", command="java -cp " + c + " AbsCon")


class AbsconPy4J(SolverPy4J):
    def __init__(self):
        d = directory_of_solver("abscon")
        c = class_path_abscon()
        super().__init__(name="AbsCon", command="java -cp " + c + os.pathsep + d + "py4j0.10.8.1.jar" + os.pathsep + d + " AbsConPy4J")

# command="java -cp /usr/local/share/py4j/py4j0.10.8.1.jar:.:./pyAbsCon/ StackEntryPoint"
