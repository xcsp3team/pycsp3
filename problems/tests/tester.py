import os
import shutil
import subprocess
import sys
from pathlib import Path

from pycsp3.solvers.ace import Ace
from pycsp3.tools.utilities import is_windows, BLUE, GREEN, ORANGE, RED, WHITE, WHITE_BOLD, warning

COLOR_PY, COLOR_JV = BLUE, ORANGE

PYTHON_VERSIONS = ["python3"]
waiting = False
solver = Ace()


def run(xcsp, diff=None, same=None):
    global waiting
    global PYTHON_VERSIONS

    # Load parameters
    # TODO: regular expression for extracting the versions?
    mode = "-xcsp"
    for arg in sys.argv:
        if arg.startswith("-version"):
            PYTHON_VERSIONS = [python_exec.replace("[", "").replace("]", "") for python_exec in arg.split("=")[1].split(",")]
        if arg == "-xcsp" or arg == "-same" or arg == "-diff":
            mode = arg
        if arg == "-waiting":
            waiting = True

    # Get versions
    for i, python_exec in enumerate(PYTHON_VERSIONS):
        cmd = [python_exec, "--version"]
        out, _ = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=is_windows()).communicate()
        version = out.decode('utf-8').strip()
        PYTHON_VERSIONS[i] = (python_exec, version)

    # Launch the set of instances
    if mode == "-xcsp":
        xcsp.load(mode=2)
    elif mode == "-same":
        same.load()
    elif mode == "-diff":
        diff.load()


class Tester:
    @staticmethod
    def system_command(command, origin, target):
        assert command in {"mv", "cp"}
        print(os.getcwd())
        if is_windows():
            command = "move" if command == 'mv' else command
            command = "copy" if command == 'cp' else command
        print(command, origin, target)
        if not os.path.isfile(origin):
            warning("file not found: " + origin)
            exit(0)
        subprocess.call([command, origin, target], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=is_windows())

    @staticmethod
    def xml_indent(file):
        cmd = ["pycsp3" + os.sep + "libs" + os.sep + "xmlindent" + os.sep + "xmlindent", '-i', '2', '-w', file]
        print(cmd)
        out, error = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=is_windows()).communicate()
        if error.decode('utf-8') != "":
            print("XmlIndent stderr : ")

    @staticmethod
    def execute_compiler(title, command):
        if len(sys.argv) == 2:
            if sys.argv[1] == "-choco":
                command += " -solver=[choco,limit=2s]"
            elif sys.argv[1] == "-ace":
                command += " -solver=[ace,limit=2s]"
        print(BLUE + "Command:" + WHITE, command)
        out, error = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=is_windows()).communicate()
        # print(title + " stdout:")
        print(out.decode('utf-8'))
        if error.decode('utf-8') != "":
            print(title + " stderr : ")
            print(error.decode('utf-8'))

    @staticmethod
    def diff_files(file1, file2, tmp):
        command = "diff " + file1 + " " + file2
        with open(tmp, "wb") as out:
            subprocess.Popen(command.split(), stdout=out, stderr=None, shell=is_windows()).communicate()
        with open(tmp, "r") as out:
            lines = out.readlines()
        os.remove(tmp)
        return lines

    def data_path(self):
        return self.main_dir + "data" + os.sep

    def __init__(self, name=None, *, dir_pbs_py=None, dir_pbs_jv=None, dir_tmp=None, dir_prs_py=None, dir_prs_jv=None):
        # we assume that testing files (e.g., cop_academic.py) are in a subdirectory of problems
        base_dir = ".." if str(Path(sys.argv[0]).parent) == '.' else Path(sys.argv[0]).parent.parent
        self.main_dir = str(base_dir) + os.sep

        if name is None:
            assert dir_pbs_py and dir_pbs_jv and dir_tmp
        else:
            dir_pbs_py = self.main_dir + name + os.sep
            dir_pbs_jv = "problems." + name + "."
            dir_tmp = self.main_dir + "tests" + os.sep + "tmp" + os.sep + name
            dir_prs_py = self.main_dir + "data" + os.sep + "parsers" + os.sep
            dir_prs_jv = "problems.generators."
            self.dir_xcsp = self.main_dir + "tests" + os.sep + "xcsp" + os.sep + name + os.sep

        self.tmpDiff = dir_tmp + os.sep + "tmpDiff.txt"
        if not os.path.exists(dir_tmp):
            os.makedirs(dir_tmp)
        else:
            shutil.rmtree(dir_tmp)
            os.makedirs(dir_tmp)
        self.dir_xml_py = dir_tmp + os.sep + "PyCSP" + os.sep
        self.dir_xml_jv = dir_tmp + os.sep + "JvCSP" + os.sep
        os.makedirs(self.dir_xml_py)
        os.makedirs(self.dir_xml_jv)

        self.dir_pbs_py = dir_pbs_py  # for problems (models)
        self.dir_pbs_jv = dir_pbs_jv  # for problems (models)

        self.dir_prs_py = dir_prs_py  # for data parsers
        self.dir_prs_jv = dir_prs_jv  # for data parsers

        self.name_xml = None

        self.counters = {"total": 0, "diff": 0, "err": 0}

        self.instances = []

    def xml_name(self, model, data, variant, prs_py, prs_jv, nameXML):
        s = model + (("-" + variant) if variant else "")
        if nameXML:
            s += nameXML + ".xml"
        else:
            if data:
                sep = "-" if not data.startswith(model) else ""  # because if same prefix between model and data, one is removed
                data = data if sep else data[len(model):]
                if prs_py is None and prs_jv is None:
                    if data.endswith(".json"):
                        s += sep + data[:-5] + ".xml"
                    else:
                        if "," in data and "[" in data and "]" in data:
                            s += sep + "-".join(data[1:-1].split(",")) + ".xml"
                        elif "[" in data and "]" in data:
                            s += sep + data[1:-1] + ".xml"
                        else:
                            s += sep + data + ".xml"
                else:
                    s += sep + data.split(".")[0] + ".xml"
            else:
                s += ".xml"
        return s

    def xml_path_py(self):
        return self.dir_xml_py + self.name_xml

    def xml_path_jv(self):
        return self.dir_xml_jv + self.name_xml

    def xml_path_xcsp(self):
        return self.dir_xcsp + self.name_xml

    def data_py(self, data):
        return None if data is None else self.data_path() + "json" + os.sep + data if data.endswith(".json") else data

    def data_jv(self, data):
        return None if data is None else self.data_path() + "json" + os.sep + data if data.endswith(".json") else data

    def _command_py(self, model, data, variant, prs_py, options_py, python_exec="python3"):
        cmd = python_exec + " " + self.dir_pbs_py + model + ".py"
        if self.data_py(data):
            cmd += " -data=" + ("" if prs_py is None else self.data_path() + "raw" + os.sep) + self.data_py(data)
        if prs_py:
            cmd += " -dataparser=" + self.dir_prs_py + prs_py
        if variant:
            cmd += " -variant=" + variant
        if options_py:
            cmd += " " + options_py
        # cmd += " -restrictTablesWrtDomains"
        return cmd

    def _command_jv(self, model, data, variant, prs_jv, special, dataSpecial):
        print()

        cmd = "java -cp " + solver.cp + (" ace " if special else " org.xcsp.modeler.Compiler ")
        cmd += "problems.generators." + prs_jv if prs_jv else self.dir_pbs_jv + model
        if self.data_jv(data):
            if dataSpecial:
                cmd += " " + str(dataSpecial)
            cmd += " " + (self.data_path() + "raw" + os.sep if prs_jv else " -data=") + self.data_jv(data)
        if special:
            cmd += " -ic=false -export=file"
        if variant:
            cmd += " -variant=" + variant
        return cmd

    def add(self, model, *, data=None, variant=None, prs_py=None, prs_jv=None, special=None, dataSpecial=None, nameXML=None, options_py=None):
        if isinstance(model, list):
            assert data == variant == prs_py == prs_jv == special == dataSpecial == nameXML == options_py is None
            for m in model:
                self.instances.append(m)
        else:
            self.instances.append((model, data, variant, prs_py, prs_jv, special, dataSpecial, nameXML, options_py))
        return self

    def load(self, *, mode=1):
        for model, data, variant, prs_py, prs_jv, special, dataSpecial, nameXML, options_py in self.instances:
            for python_exec in PYTHON_VERSIONS:
                assert self.dir_pbs_py, "Call the __init__() function of g6_testing (constructor) before execute()"
                assert self.dir_pbs_jv, "Call the __init__() function of g6_testing (constructor) before execute()"
                assert self.dir_xml_py, "Call the __init__() function of g6_testing (constructor) before execute()"

                self.name_xml = self.xml_name(model, data, variant, prs_py, prs_jv, nameXML)  # name of the XML file that will be generated
                if os.path.isfile(self.xml_path_py()):
                    os.remove(self.xml_path_py())
                if os.path.isfile(self.xml_path_jv()):
                    os.remove(self.xml_path_jv())
                self.print_information(model, data, variant, prs_py, prs_jv, python_exec)

                self.execute_compiler("PyCSP", self._command_py(model, data, variant, prs_py if not prs_py or prs_py[-1] == 'y' else prs_py + ".py", options_py,
                                                                python_exec[0]))
                if not os.path.isfile(self.name_xml):
                    warning("file not found " + self.name_xml)
                    self.counters["err"] += 1
                    continue
                shutil.move(self.name_xml, self.xml_path_py())
                if mode == 1:  # comparison with jv
                    self.execute_compiler("JvCSP", self._command_jv(model, data, variant, prs_jv, special, dataSpecial))
                    if not is_windows():
                        self.xml_indent(self.name_xml)
                    shutil.move(self.name_xml, self.xml_path_jv())
                    if not is_windows():
                        self.check()
                elif mode == 2:  # comparison with recorded XCSP files
                    # if not is_windows():
                    # shutil.copy(self.dir_xcsp + self.name_xml, self.xml_path_jv())  # we copy the xcsp file in the java dir to simulate a comparison with JvCSP
                    print("  Comparing PyCSP outcome with the XCSP3 file stored in " + self.dir_xcsp)
                    self.check(True)
                else:
                    with open(self.xml_path_py(), "r") as f:
                        for line in f.readlines():
                            print(COLOR_PY + line[0:-1])
                # TODO replace rm -rf by os.remove() and check all system commands
                if not is_windows():
                    os.system("rm -rf *.*~")  # for removing the temporary files

    def check(self, xcsp=False):
        xml_to_compare = self.xml_path_xcsp() if xcsp else self.xml_path_jv()
        self.counters["total"] += 1

        # LZMA decompress
        xml_lzma = None
        if os.path.isfile(xml_to_compare + ".lzma"):
            if is_windows():
                print("  Not comparing because of LZMA on windows")
                return None
            xml_lzma = xml_to_compare + ".lzma"
            import lzma
            with lzma.open(xml_lzma) as f:
                data = f.read()
                fp = open(xml_to_compare, "wb")
                fp.write(data)
                fp.close()

            print("Decompress " + xml_lzma + " done.")

        # Show differences    
        if not os.path.isfile(self.xml_path_py()) or not os.path.isfile(xml_to_compare):
            warning("at least 1 file not found among " + self.xml_path_py() + " and " + xml_to_compare)
            self.counters["err"] += 1
            if waiting:
                input("Press Enter to continue...")
        else:
            lines = self.diff_files(self.xml_path_py(), xml_to_compare, self.tmpDiff)
            if len(lines) == 0:
                print("  => No difference for " + self.name_xml)
            else:
                print("  => Several differences (" + str(len(lines)) + ") in " + self.name_xml)
                self.counters["diff"] += 1
                self.print_differences(lines, limit=20 if len(lines) > 200 else None, xcsp=xcsp)
                if waiting:
                    input("Press Enter to continue...")

        # LZMA delete the decompress file
        if xml_lzma is not None:
            os.remove(xml_to_compare)

        # Count differences
        n_diffs, n_errs, n_tests = self.counters["diff"], self.counters["err"], self.counters["total"]
        n_diffs_colored, n_errs_colored = (RED if n_diffs > 0 else GREEN) + str(n_diffs), (RED if n_errs > 0 else GREEN) + str(n_errs)
        print("\n" + WHITE_BOLD + "Currently: " + n_diffs_colored + WHITE + (" differences" if n_diffs > 0 else " difference") + " on " + str(
            n_tests) + (" tests" if n_tests > 0 else " test") + " (and " + n_errs_colored + WHITE + (" errors" if n_errs > 0 else " error") + ")\n")

    def print_differences(self, lines, limit, xcsp=False):
        print(COLOR_PY + "PyCSP" + WHITE + " vs. " + COLOR_JV + ("JvCSP" if not xcsp else "XCSP") + WHITE + " differences:\n")
        if limit is None:
            for line in lines:
                if line[0] in {'>', '<'}:
                    print(COLOR_JV + line[2:-1] if line[0] == '>' else COLOR_PY + line[2:-1])
        else:
            cnt = 0
            for line in lines:
                if line[0] == '>':
                    print(COLOR_JV + line[2:-1])
                    cnt += 1
                    if cnt > limit:
                        break
            cnt = 0
            for line in lines:
                if line[0] == '<':
                    print(COLOR_PY + line[2:-1])
                    cnt += 1
                    if cnt > limit:
                        break
            print(WHITE + "Too many differences (" + str(len(lines)) + ") in " + self.name_xml + ": only " + str(limit) + " displayed lines")
        print(WHITE)

    def print_information(self, model, data, variant, prs_py, prs_jv, python_exec):
        print("\n" + RED + "|================================================================|" + WHITE)
        print("  Python: " + python_exec[0] + " (" + python_exec[1] + ")")

        print("  Name: " + model + ("    Variant: " + variant if variant else ""))
        if data:
            print("  Data: " + data)
        print("  Name XML: " + self.name_xml)
        if prs_py:
            print("  parser py: " + prs_py)
        if prs_jv:
            print("  parser jv: " + prs_jv)
        print(RED + "|================================================================|" + WHITE)
