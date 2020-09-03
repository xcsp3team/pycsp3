import subprocess
import time
from io import IOBase

from lxml import etree
from py4j.java_gateway import JavaGateway, Py4JNetworkError

from pycsp3.classes.entities import VarEntities, EVar
from pycsp3.classes.main.variables import Variable
from pycsp3.dashboard import options
from pycsp3.tools.utilities import Stopwatch, flatten


def process_options(solving):
    def option_parsing(s, recursive=False):
        if s is None:
            return None
        if s[0] != '[':
            assert "," not in s and "]" not in s
            return s
        assert s[-1] == ']'
        t = s[1:-1].split(",")
        curr = -1
        for i in range(len(t)):
            if curr != -1:
                t[curr] += "," + t[i]
                if ']' in t[i]:
                    curr = -1
                t[i] = ""
            elif '[' in t[i] and ']' not in t[i]:
                curr = i
        t = [v for v in t if v]  # we discard empty cells
        t = [(k, None) if j == -1 else (k[:j], k[j + 1:]) for (j, k) in [(s.find("="), s) for s in t]]
        return {k: v for (k, v) in [(k, option_parsing(v, recursive)) if recursive else (k, v) for (k, v) in t]}

    def simplify_args_recursive():
        if "limit" in args_recursive:
            def handle_limit(s):
                if s.endswith("sols"):  # keep it at this position (because ends with s)
                    args_recursive["limit_sols"] = s[:-4]
                elif s.endswith("runs"):
                    args_recursive["limit_runs"] = s[:-4]
                elif s.endswith("h"):
                    args_recursive["limit_time"] = str(int(s[:-1]) * 3600)
                elif s.endswith("m"):
                    args_recursive["limit_time"] = str(int(s[:-1]) * 60)
                elif s.endswith("s"):
                    args_recursive["limit_time"] = s[:-1]
                elif s.endswith("no"):
                    args_recursive["nolimit"] = True

            v = args_recursive["limit"]
            if isinstance(v, dict):
                for key in v:
                    handle_limit(key)
            else:
                handle_limit(v)
            del args_recursive["limit"]
        if "restarts" in args_recursive:
            v = args_recursive["restarts"]
            if isinstance(v, dict):
                for key in v:
                    if key in ["monotonic", "geometric", "luby"]:
                        args_recursive["restarts_type"] = key
                    elif key == "cutoff":
                        args_recursive["restarts_cutoff"] = v[key]
                    elif key == "factor":
                        args_recursive["restarts_factor"] = v[key]
                    elif key == "gfactor":
                        args_recursive["restarts_gfactor"] = v[key]
            else:
                args_recursive["restarts_type"] = v
            del args_recursive["restarts"]
        if "v" in args_recursive:
            args_recursive["verbose"] = "1"
            del args_recursive["v"]
        if "vv" in args_recursive:
            args_recursive["verbose"] = "2"
            del args_recursive["vv"]
        if "vvv" in args_recursive:
            args_recursive["verbose"] = "3"
            del args_recursive["vvv"]

    args = args_recursive = dict()
    if solving[0] != '[':
        assert "," not in solving and "]" not in solving
        solver = solving
    else:
        assert solving[-1] == "]"
        if "," not in solving:  # it means that only the name of the solver is between square brackets
            solver = solving[1:-1]
        else:
            i = solving.find(",")
            solver = solving[1:i]
            args = option_parsing("[" + solving[i + 1:])
            args_recursive = option_parsing("[" + solving[i + 1:], True)
            simplify_args_recursive()
    return solver, args, args_recursive


class Instantiation:
    def __init__(self, pretty_solution, variables, values):
        self.pretty_solution = pretty_solution
        self.variables = variables
        self.values = values

    def __repr__(self):
        return self.variables, self.values

    def __str__(self):
        return str(self.pretty_solution)


class SolverProcess:
    def __init__(self, *, name, command, cp):
        self.name = name
        self.command = command
        self.cp = cp
        self.stdout = None
        self.stderr = None

    def parse_general_options(self, string_options, dict_options, dict_simplified_options):  # specific options via args are managed automatically
        raise NotImplementedError("Must be overridden")

    def solve(self, model, string_options="", dict_options=dict(), dict_simplified_options=dict()):
        if string_options != "" and not dict_options and not dict_simplified_options:
            string_options = "[" + self.name.lower() + "," + string_options + "]"
            solver, dict_options, dict_simplified_options = process_options(string_options)
            dict_simplified_options = simplify_args_recursive(dict_simplified_options)
            
        stopwatch = Stopwatch()
        solver_args = self.parse_general_options(string_options, dict_options, dict_simplified_options)
        solver_args += " " + dict_options["args"] if "args" in dict_options else ""
        verbose = options.solve or "verbose" in dict_simplified_options
        command = self.command + " " + model + " " + solver_args
        if not verbose:
            print("\n  * Solving by " + self.name + " in progress ... ")
        if verbose:
            print("\n  command: ", command + "\n")
        else:
            print("    command: ", command)
        result = self.execute(command, verbose)
        if not verbose:
            print("  * Solved by " + self.name + " in " + stopwatch.elapsed_time()
                  + " seconds (use the solver option v to see directly the output of the solver).\n")
        return self.solution() if result else None

    def execute(self, command, verbose):
        try:
            if verbose:
                subprocess.Popen(command.split()).communicate()
                return False  # in verbose mode, the solution is ignored
            else:
                p = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, error = p.communicate()
                self.stdout, self.stderr = out.decode('utf-8'), error.decode('utf-8')
                return True
        except KeyboardInterrupt:
            return False

    def solution(self):
        if self.stdout.find("<unsatisfiable") != -1 or self.stdout.find("s UNSATISFIABLE") != -1:
            return Instantiation("unsatisfiable", None, None)
        if self.stdout.find("<instantiation") == -1 or self.stdout.find("</instantiation>") == -1:
            print("  actually, the instance was not solved (add the option -ev to have more details")
            return None
        left, right = self.stdout.rfind("<instantiation"), self.stdout.rfind("</instantiation>")
        s = self.stdout[left:right + len("</instantiation>")].replace("\nv", "")
        root = etree.fromstring(s, etree.XMLParser(remove_blank_text=True))
        variables = []
        for token in root[0].text.split():
            r = VarEntities.get_item_with_name(token)
            if isinstance(r, (EVar, Variable)):  # TODO why do we need these two classes of variables?
                variables.append(r)
            else:
                for x in flatten(r.variables, keep_none=True):
                    variables.append(x)
        values = root[1].text.split()  # a list with all values given as strings (possibly '*')
        assert len(variables) == len(values)
        for i, v in enumerate(values):
            if variables[i]:
                variables[i].value = v  # we add new field (may be useful)

        pretty_solution = etree.tostring(root, pretty_print=True, xml_declaration=False).decode("UTF-8").strip()
        return Instantiation(pretty_solution, variables, values)


class SolverPy4J(SolverProcess):  # TODO in progress
    gateways = []
    processes = []

    def __init__(self, *, name, command, cp):
        self.gateway, self.process = SolverPy4J.connexion(command)
        SolverPy4J.gateways.append(self.gateway)
        SolverPy4J.processes.append(self.process)
        self.solver = self.gateway.entry_point.getSolver()
        super().__init__(name=name, command=command, cp=cp)

    @staticmethod
    def connexion(command):
        process = subprocess.Popen(command.split())
        cnt = 0
        while True:
            time.sleep(0.1)
            cnt += 1
            print("Py4J Connection " + str(cnt) + " ...")
            try:
                gateway = JavaGateway(eager_load=True)
            except Py4JNetworkError:
                print("Py4J Connection failed: No JVM listening ...")
            else:
                print("Py4J Successfully connected to the JVM")
                return gateway, process
        return gateway, process

    @staticmethod
    def close():
        for element in SolverPy4J.gateways:
            element.close()

    def loadXCSP3(self, arg):
        if isinstance(arg, str):
            self.solver.loadXCSP3(arg)
        elif isinstance(arg, IOBase):
            self.solver.loadXCSP3(arg.name)
