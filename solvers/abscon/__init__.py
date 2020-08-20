import os

from pycsp3.solvers.solver import SolverProcess, SolverPy4J

class AbsConProcess(SolverProcess):
    def __init__(self):
        super().__init__(
            name="AbsCon", 
            command="java -cp " + self.class_path() + " AbsCon"
        )
    
    def class_path(self):
        d = self.directory_of_solver("abscon")
        return d + "AbsCon-20-08.jar" + os.pathsep + d + "xcsp3-tools-1.2.2-SNAPSHOT.jar" + os.pathsep + d + "javax.json-1.0.4.jar"

    def parse_options(self, string_options, dict_options, dict_simplified_options):
        args_solver = ""
        if "limit_time" in dict_simplified_options:
            args_solver += " -t=" + dict_simplified_options["limit_time"] + "s"
        if "limit_runs" in dict_simplified_options:
            args_solver += " -r_n=" + dict_simplified_options["limit_runs"]
        if "limit_sols" in dict_simplified_options:
            args_solver += " -s=" + dict_simplified_options["limit_sols"]
        if "nolimit" in dict_simplified_options:
            args_solver += " -s=all"
        if "varheuristic" in dict_simplified_options:
            dict_simplified_options["varh"] = dict_simplified_options["varHeuristic"]
        if "varh" in dict_simplified_options:
            v = dict_simplified_options["varh"]
            if v == "input":
                va = "Lexico"
            elif v == "dom":
                va = "Dom"
            elif v == "rand":
                va = "Rand"
            elif v == "impact":
                va = "Impact"
            elif v == "activity":
                va = "Activity"
            elif v == "dom/ddeg":
                va = "DDegOnDom"
            elif v == "dom/wdeg":
                va = "WDegOnDom"
            else:
                va = None
                print("heuristic " + v + " not implemented in AbsCon")
            if va:
                args_solver += " -varh=" + va
        if "valheuristic" in dict_simplified_options:
            dict_simplified_options["valh"] = dict_simplified_options["valHeuristic"]
        if "valh" in dict_simplified_options:
            v = dict_simplified_options["valh"]
            if v == "min":
                va = "First"
            elif v == "max":
                va = "Last"
            elif v == "rand":
                va = "Rand"
            else:
                va = None
                print("heuristic " + v + " not implemented in AbsCon")
            if va:
                args_solver += " -valh=" + va
        if "lastConflict" in dict_simplified_options:
            dict_simplified_options["lc"] = dict_simplified_options["lastConflict"]
        if "lc" in dict_simplified_options:
            args_solver += " -lc" + ("=" + dict_simplified_options["lc"] if dict_simplified_options["lc"] else "")
        if "cos" in dict_simplified_options:
            args_solver += " -varh=Memory"
        if "last" in dict_simplified_options:
            print("Technique 'last' not implemented in AbsCon")
        if "restarts_type" in dict_simplified_options:
            v = dict_simplified_options["restarts_type"]
            if v != "geometric":
                print("Restarts Type " + v + " not implemented in AbsCon")
        if "restarts_cutoff" in dict_simplified_options:
            args_solver += " -r_c=" + dict_simplified_options["restarts_cutoff"]
        if "restarts_factor" in dict_simplified_options:
            args_solver += " -r_f=" + dict_simplified_options["restarts_factor"]
        if "lb" in dict_simplified_options:
            args_solver += " -lb=" + dict_simplified_options["lb"]
        if "ub" in dict_simplified_options:
            args_solver += " -ub=" + dict_simplified_options["ub"]
        if "seed" in dict_simplified_options:
            args_solver += " -seed=" + dict_simplified_options["seed"]
        if "verbose" in dict_simplified_options:
            args_solver += " -v=" + dict_simplified_options["verbose"]
        if "trace" in dict_simplified_options:
            if dict_simplified_options["trace"]:
                print("Saving trace into a file not implemented in AbsCon")
            else:
                args_solver += " -trace"
        return args_solver        

class AbsconPy4J(SolverPy4J):

    def class_path(self):
        d = self.directory_of_solver("abscon")
        return d + "AbsCon-20-08.jar" + os.pathsep + d + "xcsp3-tools-1.2.2-SNAPSHOT.jar" + os.pathsep + d + "javax.json-1.0.4.jar"

    def __init__(self):
        d = self.directory_of_solver("abscon")
        c = self.class_path()
        super().__init__(name="AbsCon", command="java -cp " + c + os.pathsep + d + "py4j0.10.8.1.jar" + os.pathsep + d + " AbsConPy4J")

# command="java -cp /usr/local/share/py4j/py4j0.10.8.1.jar:.:./pyAbsCon/ StackEntryPoint"
