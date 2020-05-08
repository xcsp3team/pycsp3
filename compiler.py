import datetime
import json
import lzma
import os
import os.path
import sys  # for DataVisitor import ast, inspect
from collections import OrderedDict
from importlib import util

from lxml import etree

from pycsp3.dashboard import options
from pycsp3.problems.data import parsing
from pycsp3.tools.aggregator import build_similar_constraints
from pycsp3.tools.compactor import build_compact_forms
from pycsp3.tools.curser import OpOverrider, convert_to_namedtuples, is_namedtuple
from pycsp3.tools.slider import handle_slides
from pycsp3.tools.utilities import Stopwatch
from pycsp3.tools.xcsp import build_document

None_Values = ['None', '', 'null']  # adding 'none'?


class Compilation:
    string_model = None
    string_data = None
    model = None
    data = None
    solve = None
    stopwatch = None
    stopwatch2 = None
    done = False

    @staticmethod
    def load(console=False):
        _load(console=console)

    @staticmethod
    def compile():
        return _compile()


def _load_options():
    options.set_values("data", "dataparser", "dataexport", "variant", "checker", "solver")
    options.set_flags("dataexport", "compress", "ev", "display", "time", "noComments", "recognizeSlides", "solve")
    if options.checker is None:
        options.checker = "fast"
    assert options.checker in {"complete", "fast", "none"}
    options.parse(sys.argv[1:])


def _load_model():
    try:
        name = sys.argv[0]
        assert name.strip().endswith(".py"), "The first argument has to be a python file." + str(name)
        model_string = name[name.rfind(os.sep) + 1:name.rfind(".")]
        specification = util.spec_from_file_location("", name)
        model = util.module_from_spec(specification)
        return model, model_string
    except:
        usage("It was not possible to read the file: " + sys.argv[0])
        raise


def _load_data():
    def _load_data_sequence(raw_data):
        od = [None if v in None_Values else int(v) if v and v.isdigit() else v for v in raw_data]
        return OrderedDict([("f" + str(i), od[i]) for i, v in enumerate(raw_data)]), od
        # return DataVisitor(raw_data).visit(ast.parse(inspect.getsource(Compilation.model)))

    data = options.data
    compilation_data = OrderedDict()  # the object used for recording the data, available in the model
    if data is None:
        return compilation_data, ""
    if data.endswith(".json"):
        assert os.path.exists(data), "The file " + data + " does not exist (in the specified directory)."
        with open(data) as f:
            compilation_data = json.loads(f.read(), object_pairs_hook=OrderedDict)
            string_data = "-" + data.split(os.sep)[-1:][0].split(".")[:1][0]
    else:
        #  if '{' in data and '}' in data:
        #    compilation_data = json.loads(data, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()), object_pairs_hook=OrderedDict)
        #    for k, v in compilation_data.items(): setattr(compilation_data, k, v)  ordered_data = list(compilation_data.values())
        if data[0] == '[' and data[-1] == ']' or data[0] == '(' and data[-1] == ')':  # NB: these characters may be needed to be escaped as in \[2,3\]
            args = data[1:-1].split(",")
            if '=' in data:
                assert data.count('=') == data.count(',') + 1, "badly formed string of data " + data
                ordered_data = []
                for arg in args:
                    t = arg.split('=')
                    value = None if t[1] in None_Values else int(t[1]) if t[1].isdigit() else t[1]
                    compilation_data[t[0]] = value
                    ordered_data.append(value)
            else:
                compilation_data, ordered_data = _load_data_sequence(args)
        else:
            compilation_data, ordered_data = _load_data_sequence([data])
        string_data = "-" + "-".join(str(v) for v in ordered_data)
    return compilation_data, string_data


def _load_dataparser(parser_file, data_file):
    try:
        compilation_data = parsing.register_fields(data_file)  # the object used for recording data is returned, available in the model
        specification = util.spec_from_file_location("", parser_file)
        specification.loader.exec_module(util.module_from_spec(specification))
        string_data = "-" + options.data.split(os.sep)[-1:][0].split(".")[:1][0] if options.data else None
        if string_data is None:
            string_data = Compilation.string_data if Compilation.string_data else ""  # in case data are recorded through the dataparser (after asking the user)
        return compilation_data, string_data
    except:
        usage("It was not possible to correctly read the file: " + parser_file)
        raise


def _load(*, console=False):
    Compilation.stopwatch = Stopwatch()
    _load_options()
    if console is False:
        Compilation.model, Compilation.string_model = _load_model()
        if options.dataparser:
            Compilation.data, Compilation.string_data = _load_dataparser(options.dataparser, options.data)
        else:
            Compilation.data, Compilation.string_data = _load_data()
        Compilation.data = convert_to_namedtuples(Compilation.data)
        if len(Compilation.data) == 0:
            Compilation.data = None
        elif len(Compilation.data) == 1:
            Compilation.data = Compilation.data[0]  # the value instead of a tuple of size 1
    else:
        Compilation.string_model = "Console"
        Compilation.string_data = ""
    OpOverrider.enable()
    options.time and print("\tWCK for loading model and data:", Compilation.stopwatch.elapsed_time(), "seconds")


def default_data(filename):
    fn = os.path.dirname(os.path.realpath(__file__)) + os.sep + "problems" + os.sep + "data" + os.sep + "json" + os.sep + filename
    assert fn.endswith(".json")
    assert os.path.exists(fn), "The file " + fn + " does not exist (in the specified directory)."
    with open(fn) as f:
        Compilation.data = convert_to_namedtuples(json.loads(f.read(), object_pairs_hook=OrderedDict))
        Compilation.string_data = "-" + filename.split(os.sep)[-1:][0].split(".")[:1][0]
    if len(Compilation.data) == 1:
        Compilation.data = Compilation.data[0]  # the value instead of a tuple of size 1
    return Compilation.data


def _compile():
    # used to save data in jSON
    def prepare_for_json(obj):
        if is_namedtuple(obj):
            r = obj._asdict()
            for k in r:
                r[k] = prepare_for_json(r[k])
            return r
        if isinstance(obj, list):
            for i in range(len(obj)):
                obj[i] = prepare_for_json(obj[i])
            return obj
        return str(obj) if isinstance(obj, datetime.time) else obj

    OpOverrider.disable()
    if options.display:
        # print("\n", sys.argv, "\n")
        if sys.argv[1].endswith(".json"):
            with open(sys.argv[1], 'r') as f:
                print(f.read())

    stopwatch = Stopwatch()
    build_similar_constraints()
    options.time and print("\tWCK for generating groups:", stopwatch.elapsed_time(reset=True), "seconds")
    handle_slides()
    options.time and print("\tWCK for handling slides:", stopwatch.elapsed_time(reset=True), "seconds")
    build_compact_forms()
    options.time and print("\tWCK for compacting forms:", stopwatch.elapsed_time(reset=True), "seconds")

    filename_prefix = Compilation.string_model + ("-" + options.variant if options.variant else "") + Compilation.string_data

    filename = filename_prefix + ".xml"
    root = build_document()
    if root is not None:
        pretty_text = etree.tostring(root, pretty_print=True, xml_declaration=False).decode("UTF-8")
        with open(filename, "w") as f:
            f.write(pretty_text)
            print("  Generation of the file " + filename + " completed.")
        if options.compress:
            with lzma.open(filename + ".lzma", "w") as f:
                f.write(bytes(pretty_text, 'utf-8'))
                print("\tGeneration of the file " + filename + ".lzma completed.")
        if options.display:
            print("\n", pretty_text)
        options.time and print("\tWCK for generating files:", stopwatch.elapsed_time(reset=True), "seconds")

    if options.dataexport:
        if isinstance(options.dataexport, bool):
            json_prefix = options.data.split("/")[-1:][0].split(".")[:1][0] if options.dataparser else filename_prefix
            # TODO if data are given with name as e.g., in [k=3,l=9,b=0,r=0,v=9] for Bibd, maybe we should sort them
        else:
            json_prefix = str(options.dataexport)
        with open(json_prefix + '.json', 'w') as f:
            json.dump(prepare_for_json(Compilation.data), f)
        print("  Generation for data saving of the file " + json_prefix + '.json' + " completed.")

    print("\tTotal wall clock time:", Compilation.stopwatch.elapsed_time(), "seconds")

    Compilation.done = True

    if options.solve or options.solver:
        if options.solver == "choco":
            from pycsp3.solvers.chocosolver import ChocoProcess
            solution = ChocoProcess().solve(filename)
        else:  # Fallback case => options.solver == "abscon":
            from pycsp3.solvers.abscon import AbsConProcess
            solution = AbsConProcess().solve(filename)

        print()
        print(solution)

    return filename


def usage(message):
    print(message)
    print("\nThe PyCSP3 Compiler allows us to generate XCSP3 files.")
    print("\n\nUsage: python3.5 <model> <data>")
    print("  - <model> is the name of a Python file containing a PyCSP3 model (i.e., a Python file with code posting variables/constraints/objectives)")
    print("  - <data> is either a fixed list of elementary data or the name of a JSON file")
