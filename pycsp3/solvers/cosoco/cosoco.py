import os

from pycsp3.solvers.solver import SolverProcess  # , SolverPy4J

COSOCO_DIR = os.sep.join(__file__.split(os.sep)[:-1]) + os.sep
COSOCO_BIN = COSOCO_DIR + "cosoco"


class Cosoco(SolverProcess):
    def __init__(self):
        super().__init__(name="cosoco", command=COSOCO_BIN, cp=COSOCO_BIN)

    def parse_general_options(self, string_options, dict_options, dict_simplified_options):
        # cosoco prints solutions in a compact form by default; level 2 is the XCSP3
        # <instantiation> form that SolverProcess parses.
        args_solver = " -model=2"
        if "limit_time" in dict_simplified_options:
            args_solver += " -cpu_lim=" + dict_simplified_options["limit_time"]
        if "limit_sols" in dict_simplified_options:
            args_solver += " -nbsols=" + dict_simplified_options["limit_sols"]
        if "nolimit" in dict_simplified_options:
            args_solver += " -nbsols=0"
        if "limit_sols" in dict_simplified_options and dict_simplified_options["limit_sols"] != "1" \
                or "nolimit" in dict_simplified_options:
            # cosoco prints the last solution twice, once when it is found and once at the end,
            # so it is recorded twice in the history.
            print("  The last solution is reported twice by cosoco when several ones are asked")
        if "limit_runs" in dict_simplified_options:
            print("  Limiting the number of runs not implemented in cosoco")
        if "varheuristic" in dict_simplified_options:
            dict_simplified_options["varh"] = dict_simplified_options["varHeuristic"]
        if "varh" in dict_simplified_options:
            v = dict_simplified_options["varh"]
            if v == "dom/wdeg":
                va = "wdeg"
            elif v in ("cacd", "pick", "frba", "robin"):  # heuristics specific to cosoco
                va = v
            else:
                va = None
                print("heuristic " + v + " not implemented in cosoco")
            if va:
                args_solver += " -var=" + va
        if "valheuristic" in dict_simplified_options:
            dict_simplified_options["valh"] = dict_simplified_options["valHeuristic"]
        if "valh" in dict_simplified_options:
            v = dict_simplified_options["valh"]
            if v == "min":
                va = "first"
            elif v == "max":
                va = "last"
            elif v == "rand":
                va = "random"
            elif v in ("occs", "asgs", "pool", "robin"):  # heuristics specific to cosoco
                va = v
            else:
                va = None
                print("heuristic " + v + " not implemented in cosoco")
            if va:
                args_solver += " -val=" + va
        if "lastConflict" in dict_simplified_options:
            dict_simplified_options["lc"] = dict_simplified_options["lastConflict"]
        if "lc" in dict_simplified_options:
            args_solver += " -lc=" + (dict_simplified_options["lc"] if dict_simplified_options["lc"] else "1")
        if "cos" in dict_simplified_options:
            print("Technique 'cos' not implemented in cosoco")
        if "last" in dict_simplified_options:
            print("Technique 'last' not implemented in cosoco")
        if "restarts_type" in dict_simplified_options:
            v = dict_simplified_options["restarts_type"]
            if v == "geometric":
                args_solver += " -restarts=geo"
            elif v == "luby":
                args_solver += " -restarts=luby"
            else:
                print("Restarts Type " + v + " not implemented in cosoco")
        if "restarts_cutoff" in dict_simplified_options or "restarts_factor" in dict_simplified_options \
                or "restarts_gfactor" in dict_simplified_options:
            print("  Tuning restarts not implemented in cosoco")
        if "lb" in dict_simplified_options:
            print("  Bounding the objective from below not implemented in cosoco")
        if "ub" in dict_simplified_options:
            args_solver += " -bound=" + dict_simplified_options["ub"]
        if "seed" in dict_simplified_options:
            print("  Setting the seed not implemented in cosoco")
        if "verbose" in dict_simplified_options:
            args_solver += " -verb=" + dict_simplified_options["verbose"]
        if "trace" in dict_simplified_options:
            print("  Saving trace into a file not implemented in cosoco")
        return args_solver
