import os
import subprocess
import time
from io import IOBase

from lxml import etree
from py4j.java_gateway import JavaGateway, Py4JNetworkError

from pycsp3.classes.main.variables import Variable, VariableInteger
from pycsp3.classes.entities import VarEntities, EVarArray, EVar
from pycsp3.tools.utilities import Stopwatch, flatten
from pycsp3.dashboard import options
from pycsp3.compiler import ABSCON, CHOCO


def directory_of_solver(name):
    # assert name in {"abscon", "choco"}  #  for the moment, two embedded solvers"
    return os.sep.join(__file__.split(os.sep)[:-1]) + os.sep + name + os.sep


def class_path_abscon():
    d = directory_of_solver("abscon")
    return d + "AbsCon-20-07.jar" + os.pathsep + d + "xcsp3-tools-1.2.1-SNAPSHOT.jar" + os.pathsep + d + "javax.json-1.0.4.jar"


def class_path_chocosolver():
    d = directory_of_solver("chocosolver")
    return d + "choco-parsers-4.10.3-SNAPSHOT-jar-with-dependencies.jar"


class Instantiation:
    def __init__(self, pretty_solution, variables, values):
        self.pretty_solution = pretty_solution
        self.variables = variables
        self.values = values

    def __repr__(self):
        return self.variables, self.values

    def __str__(self):
        return str(self.pretty_solution)


class SolverPy4J:
    gateways = []
    processes = []

    def __init__(self, *, name, command):
        self.gateway, self.process = SolverPy4J.connexion(command)
        SolverPy4J.gateways.append(self.gateway)
        SolverPy4J.processes.append(self.process)
        self.solver = self.gateway.entry_point.getSolver()
        self.name = name

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


class SolverProcess:
    def __init__(self, *, name, command):
        self.name = name
        self.command = command
        self.stdout = None
        self.stderr = None

    def solve(self, model, string_options, dict_options, dict_simplified_options):
        stopwatch = Stopwatch()
        args_solver = ""
        if self.name == ABSCON:
            print(string_options, dict_options, dict_simplified_options)
            if "limit_time" in dict_simplified_options:
                args_solver += " -t=" + dict_simplified_options["limit_time"] + "s"
            if "limit_runs" in dict_simplified_options:
                args_solver += " -r_n=" + dict_simplified_options["limit_runs"]
            if "limit_sols" in dict_simplified_options:
                args_solver += " -s=" + dict_simplified_options["limit_sols"]
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
        elif self.name == CHOCO:
            if "v" in dict_options:
                pass
                # TODO
        print("\nSolving by " + self.name + " in progress ... ")
        print("  command: ", self.command + " " + model + " " + args_solver)
        result = self.execute(self.command + " " + model + " " + args_solver)
        print("Solved by " + self.name + " in " + stopwatch.elapsed_time() + " seconds (add the option -ev to see totally the output of the solver).")
        return self.solution() if result else None

    def execute(self, command):
        try:
            p = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, error = p.communicate()
            self.stdout, self.stderr = out.decode('utf-8'), error.decode('utf-8')
            return True
        except KeyboardInterrupt:
            out, error = p.communicate()
            self.stdout, self.stderr = out.decode('utf-8'), error.decode('utf-8')
            print(self.stdout)
            return False

    def solution(self):
        if self.stdout.find("<unsatisfiable") != -1 or self.stdout.find("s UNSATISFIABLE") != -1:
            return Instantiation("unsatisfiable", None, None)
        if options.ev:
            print("\n", self.stdout)
        if self.stdout.find("<instantiation") == -1 or self.stdout.find("</instantiation>") == -1:
            print("  actually, the instance was not solved (add the option -ev to have more details")
            return None
        left, right = self.stdout.find("<instantiation"), self.stdout.find("</instantiation>")
        root = etree.fromstring(self.stdout[left:right + len("</instantiation>")], etree.XMLParser(remove_blank_text=True))
        variables = []
        for token in root[0].text.split():
            r = VarEntities.get_item_with_name(token)
            if isinstance(r, (EVar, Variable)):  # TODO why do we need these two cases?
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
