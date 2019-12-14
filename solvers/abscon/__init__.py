from pycsp3.solvers.solver import SolverProcess, SolverPy4J
import pycsp3

directoryAbsCon = "/".join(pycsp3.__file__.split("/")[:-1]) + "/solvers/abscon/"
jarAbsCon = directoryAbsCon + "AbsCon-19-08.jar:" + directoryAbsCon + "xcsp3-tools-1.1.1-SNAPSHOT.jar:" + directoryAbsCon + "javax.json-1.0.4.jar"


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
            command="java -cp " + jarAbsCon + ":" + directoryAbsCon + "py4j0.10.8.1.jar:" + directoryAbsCon + " AbsConPy4J"
            # command="java -cp /usr/local/share/py4j/py4j0.10.8.1.jar:.:./pyAbsCon/ StackEntryPoint"
        )
