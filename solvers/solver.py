import subprocess
import time
from io import IOBase

from lxml import etree
from py4j.java_gateway import JavaGateway, Py4JNetworkError

from pycsp3.classes.entities import VarEntities
from pycsp3.tools.utilities import Stopwatch


class Instantiation:
    def __init__(self, xml, variables, values):
        self.xml = xml
        self.variables = variables
        self.values = values

    def __repr__(self):
        return self.variables, self.values

    def __str__(self):
        return str(self.xml)


class SolverPy4J:
    processes = []
    gateways = []

    def __init__(self, *, name, command):
        self.gateway, self.process = self.connexion(command)
        SolverPy4J.gateways.append(self.gateway)
        SolverPy4J.processes.append(self.process)
        self.solver = self.gateway.entry_point.getSolver()
        self.name = name

    @staticmethod
    def close():
        for element in SolverPy4J.gateways:
            element.close()

    def connexion(self, command):
        connect = False
        gateway = None
        process = subprocess.Popen(command.split())
        cnt = 0
        while connect is False:
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

    def loadXCSP3(self, arg):
        if isinstance(arg, str):
            self.solver.loadXCSP3(arg)
        elif isinstance(arg, IOBase):
            self.solver.loadXCSP3(arg.name)
        return self


class SolverProcess:
    def __init__(self, *, name, command):
        self.name = name
        self.command = command
        self.stdout = None
        self.stderr = None

    def solve(self, model, time=0, restarts=0):
        stopwatch = Stopwatch()
        print(self.command)
        print("Resolution with " + self.name + " in progress ... ")
        print("Command: ", self.command + " " + model)
        if time != 0:
            model += " -t=" + str(time) + "s"
        if restarts != 0:
            model += " -r_n=" + str(restarts)
        model += " -cm -valh=Last"
        result = self.execute(self.command + " " + model)
        print("Solve with " + self.name + " in %.3f" % stopwatch.elapsed_time() + " seconds.")
        return self.solution() if result is True else None

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
        left = self.stdout.find("<instantiation")
        right = self.stdout.find("</instantiation>")
        root = etree.fromstring(self.stdout[left:right + len("</instantiation>")], etree.XMLParser(remove_blank_text=True))
        xml_variables = root[0].text.split()
        xml_values = root[1].text.split()
        variableWithOrder = [var for element in xml_variables for item in VarEntities.items for var in item.flatVars if item.name in element]
        for i, v in enumerate(xml_values):
            variableWithOrder[i].solution = str(v)
        xml_solution = etree.tostring(root, pretty_print=True, xml_declaration=False).decode("UTF-8")
        return Instantiation(xml_solution[:-1], variableWithOrder, xml_values)
