import os
import shutil
import subprocess
import sys

from pycsp3.solvers.solver import class_path_abscon
from pycsp3.tools.utilities import BLUE, GREEN, ORANGE, RED, WHITE, WHITE_BOLD

COLOR_PY, COLOR_JV = BLUE, ORANGE

DATA_PATH = "pycsp3" + os.sep + "problems" + os.sep + "data" + os.sep
XCSP_PATH = "pycsp3" + os.sep + "problems" + os.sep + "tests" + os.sep + "xcsp" + os.sep


def run(xcsp, diff=None, same=None):
    if len(sys.argv) == 1 or sys.argv[1] == "-xcsp":
        xcsp.load(mode=2)
    elif sys.argv[1] == "-same":
        same.load()
    elif sys.argv[1] == "-diff":
        diff.load()


waiting = False


class Tester:
    @staticmethod
    def system_command(command, origin, target):
        assert command in {"mv", "cp"}
        print(os.getcwd())
        if os.name == 'nt':
            command = "move" if command == 'mv' else command
            command = "copy" if command == 'cp' else command
        print(command, origin, target)
        if not os.path.isfile(origin):
            print("error: do not found the file " + origin)
            exit(0)
        subprocess.call([command, origin, target], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @staticmethod
    def xml_indent(file):
        cmd = ["pycsp3" + os.sep + "libs" + os.sep + "xmlindent" + os.sep + "xmlindent", '-i', '2', '-w', file]
        print(cmd)
        out, error = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if error.decode('utf-8') != "":
            print("XmlIndent stderr : ")

    @staticmethod
    def execute_compiler(title, command):
        print(BLUE + "Command:" + WHITE, command)
        out, error = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        # print(title + " stdout:")
        print(out.decode('utf-8'))
        if error.decode('utf-8') != "":
            print(title + " stderr : ")
            print(error.decode('utf-8'))

    @staticmethod
    def diff_files(file1, file2, tmp):
        command = "diff " + file1 + " " + file2
        with open(tmp, "wb") as out:
            subprocess.Popen(command.split(), stdout=out, stderr=None).communicate()
        with open(tmp, "r") as out:
            lines = out.readlines()
        os.remove(tmp)
        return lines

    def __init__(self, name=None, *, dir_pbs_py=None, dir_pbs_jv=None, dir_tmp=None, dir_prs_py=None, dir_prs_jv=None):
        if name is None:
            assert dir_pbs_py and dir_pbs_jv and dir_tmp
        else:
            dir_pbs_py = "pycsp3" + os.sep + "problems" + os.sep + name + os.sep
            dir_pbs_jv = "problems." + name + "."
            dir_tmp = "pycsp3" + os.sep + "problems" + os.sep + "tests" + os.sep + "tmp" + os.sep + name
            dir_prs_py = "pycsp3" + os.sep + "problems" + os.sep + "data" + os.sep + "parsers" + os.sep
            dir_prs_jv = "problems.generators."
            self.dir_xcsp = XCSP_PATH + name + os.sep

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
        s = model + ("-" + variant if variant else "")
        if nameXML:
            s += nameXML + ".xml"
        else:
            if data:
                if prs_py is None and prs_jv is None:
                    if data.endswith(".json"):
                        s += "-" + data[:-5] + ".xml"
                    else:
                        if "," in data and "[" in data and "]" in data:
                            s += "-" + "-".join(data[1:-1].split(",")) + ".xml"
                        elif "[" in data and "]" in data:
                            s += "-" + data[1:-1] + ".xml"
                        else:
                            s += "-" + data + ".xml"
                else:
                    s += "-" + data.split(".")[0] + ".xml"
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
        return None if data is None else DATA_PATH + "json" + os.sep + data if data.endswith(".json") else data

    def data_jv(self, data):
        return None if data is None else DATA_PATH + "json" + os.sep + data if data.endswith(".json") else data

    def _command_py(self, model, data, variant, prs_py, options_py):
        cmd = "python3 " + self.dir_pbs_py + model + ".py"
        if self.data_py(data):
            cmd += " -data=" + ("" if prs_py is None else DATA_PATH + "raw" + os.sep) + self.data_py(data)
        if prs_py:
            cmd += " -dataparser=" + self.dir_prs_py + prs_py
        if variant:
            cmd += " -variant=" + variant
        if options_py:
            cmd += " " + options_py
        return cmd

    def _command_jv(self, model, data, variant, prs_jv, special, dataSpecial):
        print()
        cmd = "java -cp " + class_path_abscon() + (" AbsCon " if special else " org.xcsp.modeler.Compiler ")
        cmd += "problems.generators." + prs_jv if prs_jv else self.dir_pbs_jv + model
        if self.data_jv(data):
            if dataSpecial:
                cmd += " " + str(dataSpecial)
            cmd += " " + (DATA_PATH + "raw" + os.sep if prs_jv else " -data=") + self.data_jv(data)
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
            assert self.dir_pbs_py, "Call the __init__() function of g6_testing (constructor) before execute()"
            assert self.dir_pbs_jv, "Call the __init__() function of g6_testing (constructor) before execute()"
            assert self.dir_xml_py, "Call the __init__() function of g6_testing (constructor) before execute()"

            self.name_xml = self.xml_name(model, data, variant, prs_py, prs_jv, nameXML)  # name of the XML file that will be generated
            if os.path.isfile(self.xml_path_py()):
                os.remove(self.xml_path_py())
            if os.path.isfile(self.xml_path_jv()):
                os.remove(self.xml_path_jv())
            self.print_information(model, data, variant, prs_py, prs_jv)

            self.execute_compiler("PyCSP", self._command_py(model, data, variant, prs_py if not prs_py or prs_py[-1] == 'y' else prs_py + ".py", options_py))
            shutil.move(self.name_xml, self.xml_path_py())
            if mode == 1:  # comparison with jv
                self.execute_compiler("JvCSP", self._command_jv(model, data, variant, prs_jv, special, dataSpecial))
                if os.name != 'nt':
                    self.xml_indent(self.name_xml)
                shutil.move(self.name_xml, self.xml_path_jv())
                if os.name != 'nt':
                    self.check()
            elif mode == 2:  # comparison with recorded XCSP files
                if os.name != 'nt':
                    # shutil.copy(self.dir_xcsp + self.name_xml, self.xml_path_jv())  # we copy the xcsp file in the java dir to simualte a comparison with JvCSP
                    print("  Comparing PyCSP outcome with the XCSP3 file stored in " + self.dir_xcsp)
                    self.check(True)
            else:
                with open(self.xml_path_py(), "r") as f:
                    for line in f.readlines():
                        print(COLOR_PY + line[0:-1])
            if os.name != 'nt':
                os.system("rm -rf *.*~")  # for removing the temporary files

    def check(self, xcsp=False):
        f = self.xml_path_xcsp() if xcsp else self.xml_path_jv()
        self.counters["total"] += 1
        if not os.path.isfile(self.xml_path_py()) or not os.path.isfile(f):
            print("error: files not found " + self.xml_path_py() + " or " + f)
            self.counters["err"] += 1
            if waiting:
                input("Press Enter to continue...")
        else:
            lines = self.diff_files(self.xml_path_py(), f, self.tmpDiff)
            if len(lines) == 0:
                print("  => No difference for " + self.name_xml)
            else:
                print("  => Several differences (" + str(len(lines)) + ") in " + self.name_xml)
                self.counters["diff"] += 1
                self.print_differences(lines, limit=20 if len(lines) > 200 else None, xcsp=xcsp)
                if waiting:
                    input("Press Enter to continue...")
        diff = (RED if self.counters["diff"] > 0 else GREEN) + str(self.counters["diff"])
        err = (RED if self.counters["err"] > 0 else GREEN) + str(self.counters["err"])
        print("\n" + WHITE_BOLD + "[Currently] " + diff + WHITE + " difference(s) on " + str(
            self.counters["total"]) + " test(s) (" + err + WHITE + " error(s))\n")

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

    def print_information(self, model, data, variant, prs_py, prs_jv):
        print("\n" + RED + "|================================================================|" + WHITE)
        print("  Name: " + model + ("    Variant: " + variant if variant else ""))
        if data:
            print("  Data: " + data)
        print("  Name XML: " + self.name_xml)
        if prs_py:
            print("  parser py: " + prs_py)
        if prs_jv:
            print("  parser jv: " + prs_jv)
        print(RED + "|================================================================|" + WHITE)
