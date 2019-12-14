import subprocess
from lxml import etree
from pycsp3.tools.utilities import Stopwatch
from pycsp3.classes.entities import VarEntities
from py4j.java_gateway import JavaGateway, Py4JNetworkError
import time
from io import IOBase

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
        cptConnect = 0
        gateway = None
        process = subprocess.Popen(command.split())
        while connect is False:
            time.sleep(0.1)
            cptConnect += 1
            print("Py4J Connection " + str(cptConnect) + " ...")
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
        self.stdout = None
        self.stderr = None
        self.command = command

    def solve(self, model, time=0, restarts=0):
        etime = Stopwatch()
        print(self.command)
        print("Resolution with " + self.name + " in progress ... ")
        print("Command: ", self.command + " " + model)
        if time != 0:
            model += " -t=" + str(time) + "s"
        if restarts != 0:
            model += " -r_n=" + str(restarts)

        model += " -cm -valh=Last"
        result = self.execute(self.command + " " + model)

        print("Solve with " + self.name + " in %.3f" % etime.elapsed_time() + " seconds.")
        return self.solution() if result is True else None

    def execute(self, command):
        try:
            proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, error = proc.communicate()
            self.stdout, self.stderr = out.decode('utf-8'), error.decode('utf-8')
            return True
        except KeyboardInterrupt:
            out, error = proc.communicate()
            self.stdout, self.stderr = out.decode('utf-8'), error.decode('utf-8')
            print(self.stdout)
            return False

    def solution(self):
        parser = etree.XMLParser(remove_blank_text=True)
        posStart = self.stdout.find("<instantiation")
        posEnd = self.stdout.find("</instantiation>")
        solutionXML = self.stdout[posStart:posEnd + len("</instantiation>")]
        rootXML = etree.fromstring(solutionXML, parser)
        variableXML = rootXML[0].text.split()
        valuesXML = rootXML[1].text.split()
        variableWithOrder = [var for element in variableXML for varEntitie in VarEntities.items
                             for var in varEntitie.flatVars if varEntitie.name in element]
        for index, value in enumerate(valuesXML):
            variableWithOrder[index].solution = str(value)
        solutionXML = etree.tostring(rootXML, pretty_print=True, xml_declaration=False).decode("UTF-8")
        return Instantiation(solutionXML[:-1], variableWithOrder, valuesXML)
