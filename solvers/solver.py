import os
import subprocess
import time
from io import IOBase

from lxml import etree
from py4j.java_gateway import JavaGateway, Py4JNetworkError

from pycsp3.classes.main.variables import VariableInteger
from pycsp3.classes.entities import VarEntities, EVarArray, EVar
from pycsp3.tools.utilities import Stopwatch, flatten
from pycsp3.dashboard import options


def directory_of_solver(name):
    # assert name == "abscon", "for the moment, only one embedded solver (abscon)"
    return os.sep.join(__file__.split(os.sep)[:-1]) + os.sep + name + os.sep


def class_path_abscon():
    d = directory_of_solver("abscon")
    return d + "AbsCon-20-01.jar" + os.pathsep + d + "xcsp3-tools-1.1.1-SNAPSHOT.jar" + os.pathsep + d + "javax.json-1.0.4.jar"


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

    def solve(self, model, time_limit=0, n_restarts=0):
        stopwatch = Stopwatch()
        print("\nSolving by " + self.name + " in progress ... ")
        if time_limit != 0:
            model += " -t=" + str(time_limit) + "s"
        if n_restarts != 0:
            model += " -r_n=" + str(n_restarts)
        model += " -cm -valh=Last"
        print("  command: ", self.command + " " + model)
        result = self.execute(self.command + " " + model)
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
        if self.stdout.find("<instantiation") == -1 or self.stdout.find("</instantiation>") == -1:
            print("  actually, the instance was not solved (add the option -ev to have more details")
            if options.ev:
                print("\n", self.stdout)
            return None
        left, right = self.stdout.find("<instantiation"), self.stdout.find("</instantiation>")
        root = etree.fromstring(self.stdout[left:right + len("</instantiation>")], etree.XMLParser(remove_blank_text=True))
        variables = []
        for token in root[0].text.split():
            r = VarEntities.get_item_with_name(token)
            if isinstance(r, VariableInteger):
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
