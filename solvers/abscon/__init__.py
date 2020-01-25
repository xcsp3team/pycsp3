from pycsp3.solvers.solver import SolverProcess, SolverPy4J
import pycsp3
import os

directoryAbsCon = os.sep.join(pycsp3.__file__.split(os.sep)[:-1]) + os.sep + "solvers"+os.sep+"abscon"+os.sep
jarAbsCon = directoryAbsCon + "AbsCon-19-08.jar"+os.pathsep+ directoryAbsCon + "xcsp3-tools-1.1.1-SNAPSHOT.jar"+os.pathsep + directoryAbsCon + "javax.json-1.0.4.jar"


class AbsConProcess(SolverProcess):
    def __init__(self):
        super().__init__(
            name="AbsCon",
            command="java -cp " + jarAbsCon + " abscon.Resolution"
        )


class AbsconPy4J(SolverPy4J):
    def __init__(self):
        super().__init__(
            name="AbsCon",
            command="java -cp " + jarAbsCon + os.pathsep + directoryAbsCon + "py4j0.10.8.1.jar" + os.pathsep + directoryAbsCon + " AbsConPy4J"
           # command="java -cp /usr/local/share/py4j/py4j0.10.8.1.jar:.:./pyAbsCon/ StackEntryPoint"
        )
