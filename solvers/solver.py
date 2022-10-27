import os
import signal
import subprocess
import sys
import uuid
import re

from lxml import etree

from pycsp3.classes.auxiliary.ptypes import TypeStatus
from pycsp3.classes.entities import VarEntities, EVar, EVarArray
from pycsp3.classes.main.variables import Variable, VariableInteger
from pycsp3.dashboard import options
from pycsp3.tools.utilities import Stopwatch, flatten, GREEN, WHITE, is_windows, ANY
from pycsp3.compiler import Compilation

# from py4j.java_gateway import JavaGateway, Py4JNetworkError


def process_options(solving):
    def option_parsing(s, recursive=False):
        if s is None:
            return None
        if s[0] != '[':
            assert "," not in s and "]" not in s, s
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
        assert "," not in solving and "]" not in solving, solving
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


class Logger:
    def __init__(self, prefix_end="", verbose=0, path=None):
        mac, pid = hex(uuid.getnode()), str(os.getpid())
        filename = "solver_" + mac + "_" + pid + "_" + (str(prefix_end) if prefix_end else "") + ".log"
        self.log_file = (path if path else os.getcwd()) + os.sep + filename
        # self.log_file = os.path.dirname(os.path.realpath(__file__)) + os.sep + filename  # old code
        if verbose > 0:
            print("    - logfile:", self.log_file)
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        self.log = open(self.log_file, "a")

    def write(self, message):
        self.log = open(self.log_file, "a")
        self.log.write(message)
        self.log.flush()

    def read(self):
        o = open(self.log_file, "r")
        r = o.read()
        o.close()
        return r

    def close(self):
        self.log.close()


class Instantiation:
    def __init__(self, root, variables, values, pretty_solution):
        self.root = root
        self.variables = variables
        self.values = values
        self.pretty_solution = pretty_solution

    def __repr__(self):
        return self.variables, self.values

    def __str__(self):
        return str(self.pretty_solution)


class SolverProcess:
    automatic_call = False

    def __init__(self, *, name, command, cp):
        self.name = name
        self.command = command
        self.cp = cp
        self.options = ""
        self.stdout = None
        self.stderr = None
        self.last_command_wck = None
        self.log_filename_suffix = None
        self.n_executions = 0
        self.last_log = None
        # concerning the last execution:
        self.last_solution = None
        self.n_solutions = None
        self.bound = None
        self.status = None
        # concerning extraction:
        self.core = None

    def command(self, _command):
        self.command = _command

    def get_logger(self):
        return self.last_log

    def setting(self, value):
        if value is not None:
            value = str(value).strip()
            self.options = " " + value if self.options != "" else value

    def log_suffix(self, _extend_filename_logger):
        self.log_filename_suffix = _extend_filename_logger

    def parse_general_options(self, string_options, dict_options, dict_simplified_options):  # specific options via args are managed automatically
        raise NotImplementedError("Must be overridden")

    def _solve(self, instance, string_options="", dict_options=dict(), dict_simplified_options=dict(), compiler=False, *, verbose=0, automatic=False,
               extraction=False):
        model, cop = instance
        if extraction:
            self.switch_to_extraction()

        def _int_from(s, left):
            right = left + s[left:].find("\n")
            left = right - 1
            while s[left].isdigit():
                left -= 1
            return int(s[left + 1:right])

        def _record_solution(roots, i):
            variables = []
            for token in roots[i][0].text.split():
                r = VarEntities.get_item_with_name(token)
                if isinstance(r, EVar):
                    variables.append(r.variable)
                elif isinstance(r, Variable):
                    variables.append(r)
                else:
                    for x in flatten(r.variables, keep_none=True):
                        variables.append(x)
            if i == 0:  # reset the history in that case
                for x in variables:
                    if x:
                        x.values = []
            values = []
            for tok in roots[i][1].text.split():
                if 'x' in tok:  # in order to handle compact forms in solutions
                    vk = tok.split('x')
                    assert len(vk) == 2
                    for _ in range(int(vk[1])):
                        values.append(vk[0])
                else:
                    values.append(tok)
            # values is a list with all values given as strings (possibly '*')
            assert len(variables) == len(values)
            for i, _ in enumerate(values):
                if variables[i]:
                    if isinstance(variables[i], VariableInteger):
                        values[i] = int(values[i]) if values[i] != "*" else ANY
                    variables[i].value = values[i]  # we record the last found solution value
                    variables[i].values.append(values[i])  # we record it in the history
            return variables, values

        def extract_result_and_solution(stdout):
            if extraction:
                left = stdout.rfind("c CORE")
                if left == -1:
                    return TypeStatus.UNKNOWN
                right = left + stdout[left:].find("\n")
                self.core = stdout[left:right]
                return TypeStatus.CORE

            if stdout.find("<unsatisfiable") != -1 or stdout.find("s UNSATISFIABLE") != -1:
                return TypeStatus.UNSAT
            if stdout.find("<instantiation") == -1 or stdout.find("</instantiation>") == -1:
                print("  Actually, the instance was not solved")
                return TypeStatus.UNKNOWN

            if "limit=no" in string_options or ("limit_sols" in dict_simplified_options and int(dict_simplified_options["limit_sols"]) > 1):
                # TODo findall does not seem to work with the output of Choco. why?
                roots = [etree.fromstring(("<instantiation" + tok + "</instantiation>").replace("\nv", ""), etree.XMLParser(remove_blank_text=True))
                         for tok in re.findall(r"<instantiation(.*?)</instantiation>", stdout)]
            else:
                left, right = stdout.rfind("<instantiation"), stdout.rfind("</instantiation>")
                roots = [etree.fromstring(stdout[left:right + len("</instantiation>")].replace("\nv", ""), etree.XMLParser(remove_blank_text=True))]

            for i in range(len(roots) - 1):  # all roots except the last one to record the history
                _record_solution(roots, i)

            root = roots[-1]
            variables, values = _record_solution(roots, len(roots) - 1)
            optimal = stdout.find("s OPTIMUM") != -1
            if cop:
                root.attrib['type'] = "optimum" if optimal else "solution"
                if "cost" not in root.attrib:
                    root.attrib['cost'] = _int_from(stdout, stdout.rfind("o ") + 2)
                self.bound = int(root.attrib['cost'])
                if "id" in root.attrib:
                    del root.attrib['id']

            def _array_values(t):
                if t is None:
                    return None
                if isinstance(t, Variable):
                    return t.value
                t.values = [_array_values(v) for v in t]
                return t.values

            for array in Variable.arrays:
                _array_values(array)  # we set the value of the field 'values'
                # (currently, the recursive mode does not work; superficial copy when getting an item)

            pretty_solution = etree.tostring(root, pretty_print=True, xml_declaration=False).decode("UTF-8").strip()
            self.last_solution = Instantiation(root, variables, values, pretty_solution)
            j = stdout.find("d FOUND SOLUTIONS")
            if j != -1:
                self.n_solutions = _int_from(stdout, j)
            return TypeStatus.OPTIMUM if optimal else TypeStatus.SAT

        def execute(command):
            if not is_windows():
                p = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, preexec_fn=os.setsid)
            else:
                p = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stopped = False
            handler = signal.getsignal(signal.SIGINT)

            def new_handler(frame, signum):
                global stopped
                stopped = True
                os.killpg(os.getpgid(p.pid), signal.SIGINT)

            signal.signal(signal.SIGINT, new_handler)
            end_prefix = self.log_filename_suffix if self.log_filename_suffix is not None else str(self.n_executions)
            log = Logger(end_prefix, verbose, Compilation.pathname)  # To record the output of the solver
            self.last_log = log.log_file
            for line in p.stdout:
                if verbose == 2:
                    sys.stdout.write(line)
                log.write(line)
            p.wait()
            p.terminate()
            log.close()
            signal.signal(signal.SIGINT, handler)  # Reset the right SIGINT
            return log.read(), stopped

        if model is not None and len(VarEntities.items) == 0:
            print("\n The instance has no variable, so the solver is not run.")
            print("Did you forget to indicate the variant of the model?")
            return None

        if automatic is False and SolverProcess.automatic_call:
            print("\n You attempt to solve the instance with both -solve and the function solve().")
            return None

        SolverProcess.automatic_call = automatic
        if compiler is False:  # To get options from the model
            if len(string_options) == 0 or string_options[0] != "[":
                string_options = "[" + self.name.lower() + ("," + string_options if len(string_options) > 0 else "") + "]"
            solver, tmp_dict_options, tmp_dict_simplified_options = process_options(string_options)
            dict_simplified_options.update(tmp_dict_simplified_options)
            dict_options.update(tmp_dict_options)

        stopwatch = Stopwatch()
        solver_args = self.parse_general_options(string_options, dict_options, dict_simplified_options)
        solver_args += " " + dict_options["args"] if "args" in dict_options else ""
        solver_args += " " + self.options

        verbose = 2 if options.solve or "verbose" in dict_simplified_options else verbose
        command = self.command + " " + (model if model is not None else "") + " " + solver_args

        if verbose > 0:
            print("\n  * Solving by " + self.name + " in progress ... ")
            print("    - command:", command)
        out_err, stopped = execute(command)

        missing = out_err is not None and out_err.find("Missing Implementation") != -1
        self.last_command_wck = stopwatch.elapsed_time()
        if verbose > 0:
            if stopped:
                print("  * Solving process stopped (SIGINT) by " + self.name + " after " + GREEN + self.last_command_wck + WHITE + " seconds")
            else:
                print("\n  * Solved by " + self.name + " in " + GREEN + self.last_command_wck + WHITE + " seconds")
            if missing:
                print("\n   This is due to a missing implementation")
            if automatic and verbose < 2:
                print("\n  NB: use the solver option v, as in -solver=[choco,v] or -solver=[ace,v] to see directly the output of the solver.")
            else:
                print()
        self.n_executions += 1
        return extract_result_and_solution(out_err) if out_err else TypeStatus.UNKNOWN

    def solve(self, instance, string_options="", dict_options=dict(), dict_simplified_options=dict(), compiler=False, *, verbose=0, automatic=False,
              extraction=False):
        self.status = self._solve(instance, string_options, dict_options, dict_simplified_options, compiler, verbose=verbose, automatic=automatic,
                                  extraction=extraction)
        return self.status

    def switch_to_extraction(self):
        pass

# class SolverPy4J(SolverProcess):  # TODO in progress
#     gateways = []
#     processes = []
#
#     def __init__(self, *, name, command, cp):
#         self.gateway, self.process = SolverPy4J.connexion(command)
#         SolverPy4J.gateways.append(self.gateway)
#         SolverPy4J.processes.append(self.process)
#         self.solver = self.gateway.entry_point.getSolver()
#         super().__init__(name=name, command=command, cp=cp)
#
#     @staticmethod
#     def connexion(command):
#         process = subprocess.Popen(command.split())
#         cnt = 0
#         while True:
#             time.sleep(0.1)
#             cnt += 1
#             print("Py4J Connection " + str(cnt) + " ...")
#             try:
#                 gateway = JavaGateway(eager_load=True)
#             except Py4JNetworkError:
#                 print("Py4J Connection failed: No JVM listening ...")
#             else:
#                 print("Py4J Successfully connected to the JVM")
#                 return gateway, process
#         return gateway, process
#
#     @staticmethod
#     def close():
#         for element in SolverPy4J.gateways:
#             element.close()
#
#     def loadXCSP3(self, arg):
#         if isinstance(arg, str):
#             self.solver.loadXCSP3(arg)
#         elif isinstance(arg, IOBase):
#             self.solver.loadXCSP3(arg.name)
