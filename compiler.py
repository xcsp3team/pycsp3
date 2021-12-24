import datetime
import json
import lzma
import os
import os.path
import platform
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
from pycsp3.tools.utilities import Stopwatch, GREEN, WHITE, Error
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
    user_filename = None

    @staticmethod
    def load(console=False):
        _load(console=console)

    @staticmethod
    def set_filename(_user_filename):
        if _user_filename is None:
            Compilation.user_filename = None
        else:
            Compilation.user_filename = _user_filename if _user_filename.endswith(".xml") else _user_filename + ".xml"

    @staticmethod
    def compile(filename=None, disabling_opoverrider=False, verbose=1):
        Compilation.set_filename(filename)
        return _compile(disabling_opoverrider, verbose=verbose)


def _load_options():
    options.set_values("data", "dataparser", "dataexport", "dataformat", "variant", "checker", "solver", "output")
    options.set_flags("dataexport", "solve", "display", "verbose", "lzma", "sober", "ev", "safe", "recognizeSlides", "keepSmartConditions",
                      "keepSmartTransitions", "restrictTablesWrtDomains", "dontcompactValues", "usemeta", "debug")
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
    except Exception:
        usage("It was not possible to read the file: " + sys.argv[0])
        raise


def _load_data():
    def _load_data_sequence(raw_data):
        od = [None if v in None_Values else int(v) if v and v.isdigit() else v for v in raw_data]
        return OrderedDict([("f" + str(i), od[i]) for i, v in enumerate(raw_data)]), od
        # return DataVisitor(raw_data).visit(ast.parse(inspect.getsource(Compilation.model)))

    def _arg_value(s):
        return None if s in None_Values else int(s) if s.isdigit() else s

    def _load_multiple_data_pieces():  # formatting instructions not possible in that case
        s = ""
        for arg in args:
            if "=" in arg:
                t = arg.split('=')
                value = _arg_value(t[1])
                compilation_data[t[0]] = value
                s += "-" + str(value)
            else:
                assert arg.endswith("json")
                assert os.path.exists(arg), "The file " + arg + " does not exist (in the specified directory)." + str(os.path)
                with open(arg) as f:
                    compilation_data.update(json.loads(f.read(), object_pairs_hook=OrderedDict))
                    s += "-" + arg.split(os.sep)[-1:][0].split(".")[:1][0]
        return compilation_data, s

    data = options.data
    if data is None:
        return OrderedDict(), ""
    if data.endswith(".json"):  # a single json file
        if data.startswith("http"):
            from urllib.request import urlopen
            # example: python Nonogram.py -data=https://www.cril.univ-artois.fr/~lecoutre/heart.json
            return json.loads(urlopen(data).read(), object_pairs_hook=OrderedDict), "-" + data.split(os.sep)[-1:][0].split(".")[:1][0]
        assert os.path.exists(data), "The file " + data + " does not exist (in the specified directory)."
        with open(data) as f:
            return json.loads(f.read(), object_pairs_hook=OrderedDict), "-" + data.split(os.sep)[-1:][0].split(".")[:1][0]
    compilation_data = OrderedDict()  # the object used for recording the data, available in the model
    # if '{' in data and '}' in data:
    #    compilation_data = json.loads(data, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()), object_pairs_hook=OrderedDict)
    #    for k, v in compilation_data.items(): setattr(compilation_data, k, v)  ordered_data = list(compilation_data.values())
    if (data[0], data[-1]) in [('[', ']'), ('(', ')')]:  # NB: these characters may be needed to be escaped as in \[2,3\]
        args = data[1:-1].split(",")
        if "json" in data:
            return _load_multiple_data_pieces()
        if '=' in data:
            assert data.count('=') == data.count(',') + 1, "badly formed string of data " + data
            ordered_data = []
            for arg in args:
                t = arg.split('=')
                value = _arg_value(t[1])
                compilation_data[t[0]] = value
                ordered_data.append(value)
        else:
            compilation_data, ordered_data = _load_data_sequence(args)
    else:
        compilation_data, ordered_data = _load_data_sequence([data])
    df = options.dataformat
    if df:
        assert df[0] == '{' and df[-1] == '}'
        if len(ordered_data) > 1 and df.count("{") == 1:
            df = "-".join(df for _ in range(len(ordered_data)))
        ss = df.format(*ordered_data)
    else:
        ss = "-".join(str(v) for v in ordered_data)
    string_data = "-" + ss
    return compilation_data, string_data


def _load_dataparser(parser_file, data_value):
    try:
        compilation_data = parsing.register_fields(data_value)  # the object used for recording data is returned, available in the model
        specification = util.spec_from_file_location("", parser_file)
        specification.loader.exec_module(util.module_from_spec(specification))
        string_data = "-" + options.data.split(os.sep)[-1:][0].split(".")[:1][0] if options.data else None
        if string_data is None:
            string_data = Compilation.string_data if Compilation.string_data else ""  # in case data are recorded through the dataparser (after asking the user)
        return compilation_data, string_data
    except Exception:
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
        Compilation.string_data = Compilation.string_data.replace("/", "-")
        if len(Compilation.data) == 0:
            Compilation.data = None
        elif len(Compilation.data) == 1:
            Compilation.data = Compilation.data[0]  # the value instead of a tuple of size 1
    else:
        Compilation.string_model = "Console"
        Compilation.string_data = ""
    OpOverrider.enable()
    options.verbose and print("\tWCK for loading model and data:", Compilation.stopwatch.elapsed_time(), "seconds")


def load_json_data(filename, *, storing=False):
    """
    Loads and returns the data from the specified JSON file (possibly given by an URL)

    :param filename: name (possibly ULR) of a JSON file
    :return: the loaded data
    """
    assert filename.endswith(".json")
    if filename.startswith("http"):
        from urllib.request import urlopen
        data = json.loads(urlopen(filename).read(), object_pairs_hook=OrderedDict)
    else:
        if os.path.exists(filename):
            fn = filename
        elif filename[0] == '.':
            fn = os.path.abspath('.') + filename[1:]
        else:
            fn = os.path.dirname(os.path.realpath(__file__)) + os.sep + "problems" + os.sep + "data" + os.sep + "json" + os.sep + filename
        assert os.path.exists(fn), "The file " + fn + " does not exist (in the specified directory)."
        with open(fn) as f:
            data = json.loads(f.read(), object_pairs_hook=OrderedDict)
    data = convert_to_namedtuples(data)
    if len(data) == 0:
        data = None
    elif len(data) == 1:
        data = data[0]  # the value instead of a tuple of size 1
    if storing:
        Compilation.data = data
        Compilation.string_data = "-" + filename.split(os.sep)[-1:][0].split(".")[:1][0]
    return data


def default_data(filename):
    """
    Loads data from the specified JSON file (possibly given by an URL)

    :param filename: mane (possibly ULR) of a JSON file
    :return: the loaded data
    """
    return load_json_data(filename, storing=True)


def _compile(disabling_opoverrider=False, verbose=1):
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

    if Error.errorOccurrence:
        return None

    if disabling_opoverrider:
        OpOverrider.disable()

    if Compilation.user_filename is None and options.output is not None:
        Compilation.set_filename(options.output)
    if Compilation.user_filename is not None:
        if options.output is None and options.verbose:
            print("  * User-defined XML file name:", Compilation.user_filename)
        filename = Compilation.user_filename
        if filename.endswith(".xml"):
            filename_prefix = filename[:-4]  # can be useful if data are exported
    else:
        same_prefix = Compilation.string_data.startswith("-" + Compilation.string_model)
        suffix = Compilation.string_data if not same_prefix else Compilation.string_data[1 + len(Compilation.string_model):]
        filename_prefix = Compilation.string_model + ("-" + options.variant if options.variant else "") + suffix
        filename = filename_prefix + ".xml"

    stopwatch = Stopwatch()
    if options.verbose:
        print("  PyCSP3 (Python:" + platform.python_version() + ", Path:" + os.path.abspath(__file__) + ")\n")
    build_similar_constraints()
    options.verbose and print("\tWCK for generating groups:", stopwatch.elapsed_time(reset=True), "seconds")
    handle_slides()
    options.verbose and print("\tWCK for handling slides:", stopwatch.elapsed_time(reset=True), "seconds")
    build_compact_forms()
    options.verbose and print("\tWCK for compacting forms:", stopwatch.elapsed_time(reset=True), "seconds")

    root = build_document()
    if root is not None:
        pretty_text = etree.tostring(root, pretty_print=True, xml_declaration=False, encoding='UTF-8').decode("UTF-8")
        if options.display:
            print("\n", pretty_text)
        else:
            with open(filename, "w") as f:
                f.write(pretty_text)
                if verbose > 0:
                    print("  * Generating the file " + filename + " completed in " + GREEN + Compilation.stopwatch.elapsed_time() + WHITE + " seconds.")
        if options.lzma:
            with lzma.open(filename + ".lzma", "w") as f:
                f.write(bytes(pretty_text, 'utf-8'))
                print("\tGeneration of the file " + filename + ".lzma completed.\n")
        options.verbose and print("\tWCK for generating files:", stopwatch.elapsed_time(reset=True), "seconds")

    if options.dataexport:
        if isinstance(options.dataexport, bool):
            json_prefix = options.data.split("/")[-1:][0].split(".")[:1][0] if options.dataparser else filename_prefix
            # TODO if data are given with name as e.g., in [k=3,l=9,b=0,r=0,v=9] for Bibd, maybe we should sort them
        else:
            json_prefix = str(options.dataexport)
        with open(json_prefix + '.json', 'w') as f:
            json.dump(prepare_for_json(Compilation.data), f)
        print("  Saving data in the file " + json_prefix + '.json' + " completed.")

    Compilation.done = True
    cop = root is not None and root.attrib and root.attrib["type"] == "COP"
    return filename, cop


def usage(message):
    print(message)
    print("\nThe PyCSP3 Compiler allows us to generate XCSP3 files.")
    print("\n\nUsage: python3.5 <model> <data>")
    print("  - <model> is the name of a Python file containing a PyCSP3 model (i.e., a Python file with code posting variables/constraints/objectives)")
    print("  - <data> is either a fixed list of elementary data or the name of a JSON file")

# solver = s if s[0] not in {'[', '('} else s[1:re.search("[,)\]]", s).start()]
