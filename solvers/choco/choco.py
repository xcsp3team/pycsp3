import os

from pycsp3.solvers.solver import SolverProcess  #, SolverPy4J

CHOCO_DIR = os.sep.join(__file__.split(os.sep)[:-1]) + os.sep
CHOCO_CP = CHOCO_DIR + "choco-parsers-4.10.15-beta.jar"


class Choco(SolverProcess):
    def __init__(self):
        super().__init__(
            name="Choco-solver",
            command="java -cp " + CHOCO_CP + " org.chocosolver.parser.xcsp.ChocoXCSP", cp=CHOCO_CP
        )

    def parse_general_options(self, string_options, dict_options, dict_simplified_options):
        free, all = False, False
        args_solver = ""
        if "nolimit" in dict_simplified_options:
            all = True
        else:
            tl = -1
            if "limit_time" in dict_simplified_options:
                tl = dict_simplified_options["limit_time"]
            args_solver += " -limit=[" + str(tl) + ("s" if tl != -1 else "")
            if "limit_runs" in dict_simplified_options:
                args_solver += "," + dict_simplified_options["limit_runs"] + "runs"
                free = True
            if "limit_sols" in dict_simplified_options:
                args_solver += "," + dict_simplified_options["limit_sols"] + "sols"
                free = all = True
            args_solver += "]"

        if "varheuristic" in dict_simplified_options:
            dict_simplified_options["varh"] = dict_simplified_options["varHeuristic"]
        if "varh" in dict_simplified_options:
            v = dict_simplified_options["varh"]
            if v == "dom/wdeg":
                v = "domwdeg"
            if v not in ["input", "dom", "rand", "ibs", "impact", "abs", "activity", "chs", "domwdeg"]:
                print("heuristic " + v + " not implemented in Choco")
            else:
                args_solver += " -varh=" + v
                free = True
        if "valheuristic" in dict_simplified_options:
            dict_simplified_options["valh"] = dict_simplified_options["valHeuristic"]
        if "valh" in dict_simplified_options:
            v = dict_simplified_options["valh"]
            if v not in ["min", "med", "max", "rand", "best", ]:
                print("heuristic " + v + " not implemented in Choco")
            else:
                args_solver += " -valh=" + v
                free = True
        if "lastConflict" in dict_simplified_options:
            dict_simplified_options["lc"] = dict_simplified_options["lastConflict"]
        if "lc" in dict_simplified_options:
            args_solver += " -lc=" + (dict_simplified_options["lc"] if dict_simplified_options["lc"] else "1")
            free = True
        if "cos" in dict_simplified_options:
            args_solver += " -cos"
            free = True
        if "last" in dict_simplified_options:
            args_solver += " -last"
            free = True
        if "restarts_type" in dict_simplified_options:
            rt = dict_simplified_options["restarts_type"]
            args_solver += " -restarts=[" + rt + ","
            if "restarts_cutoff" in dict_simplified_options:
                args_solver += dict_simplified_options["restarts_cutoff"] + ","
            else:
                print("Choco needs 'restarts_cutoff' to be set when 'restarts_type' is set.")
            if rt == "geometric":
                if "restarts_factor" in dict_simplified_options:
                    args_solver += dict_simplified_options["restarts_gfactor"] + ","
                else:
                    print("Choco needs 'restarts_gfactor' to be set when 'geometric' is declared.")
            if "restarts_factor" in dict_simplified_options:
                args_solver += dict_simplified_options["restarts_factor"] + ","
            else:
                print("Choco needs 'restarts_factor' to be set when 'restarts_type' is set.")
            free = True
        else:
            if "restarts_cutoff" in dict_simplified_options \
                    or "restarts_factor" in dict_simplified_options \
                    or "restarts_gfactor" in dict_simplified_options:
                print("Choco needs 'restarts_type' to be set when 'restarts_cutoff' "
                      "or 'restarts_factor' or 'restarts_gfactor' is set.")
        if "lb" in dict_simplified_options or "ub" in dict_simplified_options:
            print("  Bounding objective not implemented in Choco")
        if free:  # required when some solving options are defined
            args_solver += " -f"
        if all:
            args_solver += " -a"
        if "seed" in dict_simplified_options:
            args_solver += " -seed=" + dict_simplified_options["seed"]
        if "verbose" in dict_simplified_options:
            print("  Verbose log not implemented in Choco")
        if "trace" in dict_simplified_options:
            print("  Saving trace into a file not implemented in Choco")
        return args_solver + " -flt"


# class ChocoPy4J(SolverPy4J):  # TODO in progress
#     def __init__(self):
#         cp = CHOCO_CP + os.pathsep + CHOCO_DIR + "../py4j0.10.8.1.jar" + os.pathsep + CHOCO_DIR + " ChocoSolverPy4J"
#         super().__init__(name="Choco-solver", command="java -cp " + cp, cp=CHOCO_CP)

