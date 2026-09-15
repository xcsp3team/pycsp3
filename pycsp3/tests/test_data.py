"""
Tests of the section Data of the API (https://pycsp.org/documentation/api/data/):
the data given on the command line (option -data) and available in the variable data, default_data(), load_json_data(),
the structures Task and Item, and the data parsers (option -parser).
"""

import json
import textwrap

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

# Known bugs shared by several tests (each bug is reported in the issue given at the start of its reason)
PARSING_INVALID = "#94: invalid arguments of the data parsing functions are reported without explicit message"
# Displays the variable data, the named tuples built from data (nt0, nt1, ...) being displayed without their names
SHOW = r'print("data", __import__("re").sub(r"\bnt\d+\(", "(", repr(data)))'

PARSING = "from pycsp3.problems.data.parsing import *\n"


def xml_names(r):
    assert r.ok, r.report()
    return sorted(p.name for p in r.directory.glob("*.xml"))


# ---------------------------------------------------------------------------------------------- command line (-data)

@pytest.mark.parametrize("value, shown", [
    ("5", "5"),
    ("abc", "'abc'"),
    ("[7]", "7"),
    ("[3,4]", "(f0=3, f1=4)"),
    ("(3,4)", "(f0=3, f1=4)"),
    ("[3,abc,4]", "(f0=3, f1='abc', f2=4)"),
    ("[n=3,m=4]", "(n=3, m=4)"),
    ("(n=3,m=4)", "(n=3, m=4)"),
    ("[n=3]", "3"),
    ("[3,[1,2],4]", "(f0=3, f1=[1, 2], f2=4)"),
    ("[n=3,t=[1,2]]", "(n=3, t=[1, 2])"),
    ("[None,null,3]", "(f0=None, f1=None, f2=3)"),
    ("null", "None"),
    ("None", "None"),
])
def test_data_command_line(run, value, shown):
    r = run(SHOW, args=["-data=" + value])
    assert "data " + shown in r.lines, r.report()


def test_data_without_option(run):
    assert "data None" in run(SHOW).lines


@pytest.mark.parametrize("value, shown", [
    ("-3", "-3"),
    ("2.5", "2.5"),
    ("-2.5e-2", "-0.025"),
    ("True", "True"),
    ("False", "False"),
    ("true", "True"),
    ("false", "False"),
    ("[-3,4]", "(f0=-3, f1=4)"),
    ("[2.5,True]", "(f0=2.5, f1=True)"),
    ("[a=-3,b=2.5,c=False]", "(a=-3, b=2.5, c=False)"),
    ("[a=true,t=[-1,0.5,false]]", "(a=True, t=[-1, 0.5, False])"),
    ("[data.json,c=-5]", "(n=3, c=-5)"),
    ("[data.json,c=true]", "(n=3, c=True)"),
    ("nan", "'nan'"),
    ("inf", "'inf'"),
    ("[+3,1_000]", "(f0='+3', f1='1_000')"),
])
def test_data_command_line_elementary_values(run, value, shown):
    # an elementary value is an integer, a real, a string or a Boolean (https://pycsp.org/documentation/interface/Data/)
    r = run(SHOW, args=["-data=" + value], files={"data.json": '{"n": 3}'})
    assert "data " + shown in r.lines, r.report()


def test_data_command_line_unpacking(run):
    r = run("""
        n, m = data
        print("values", n, m, data.f0, data[1], len(data))
    """, args=["-data=[3,4]"])
    assert "values 3 4 3 4 2" in r.lines, r.report()


def test_data_command_line_solutions(run, solver):
    r = run("""
        n, k = data
        x = VarArray(size=n, dom=range(k))
        satisfy(AllDifferent(x))
    """, args=["-data=[3,4]"], solver=solver)
    assert_solutions(r, brute_force([range(4)] * 3, lambda *t: len(set(t)) == 3))


def test_data_command_line_named_solutions(run, solver):
    r = run("""
        x = VarArray(size=data.n, dom=range(data.k))
        satisfy(Sum(x) == data.s)
    """, args=["-data=[n=3,k=3,s=4]"], solver=solver)
    assert_solutions(r, brute_force([range(3)] * 3, lambda *t: sum(t) == 4))


@pytest.mark.parametrize("args, name", [
    ([], "model.xml"),
    (["-data=5"], "model-5.xml"),
    (["-data=abc"], "model-abc.xml"),
    (["-data=[3,4]"], "model-3-4.xml"),
    (["-data=[n=3,m=4]"], "model-3-4.xml"),
    (["-data=[03,4]"], "model-03-4.xml"),
    (["-data=007"], "model-007.xml"),
    (["-data=[3,4]", "-dataformat={:02d}"], "model-03-04.xml"),
    (["-data=[3,4]", "-dataformat={:02d}-{:03d}"], "model-03-004.xml"),
    (["-data=data.json"], "model-data.xml"),
    (["-data=[data.json,k=5]"], "model-data-5.xml"),
])
def test_data_filename(run, args, name):
    assert xml_names(run("x = Var(dom=range(2))", args=args, files={"data.json": '{"n": 3, "m": 4}'})) == [name]


def test_data_leading_zeros(run):
    assert "data (f0=3, f1=4)" in run(SHOW, args=["-data=[03,4]"]).lines


@pytest.mark.parametrize("args", [
    ["-data="],
    ["-data=missing.json"],
    ["-data=[missing.json,k=5]"],
])
def test_data_command_line_invalid(run, args):
    assert_fails(run(SHOW, args=args))


# -------------------------------------------------------------------------------------------------------- JSON files

@pytest.mark.parametrize("content, shown", [
    ('{"n": 3, "m": [1, 2]}', "(n=3, m=[1, 2])"),
    ('{"n": 3}', "3"),
    ('{"t": [1, 2]}', "[1, 2]"),
    ('{}', "None"),
    ('[1, 2, 3]', "[1, 2, 3]"),
    ('[5]', "5"),
    ('[]', "None"),
    ('{"f": 2.5, "b": true, "z": null, "s": "hi"}', "(f=2.5, b=True, z=None, s='hi')"),
    ('{"t": [1, "a"], "u": [[1], ["a"]], "e": []}', "(t=[1, 'a'], u=[[1], ['a']], e=[])"),
    ('{"jobs": [{"duration": 2, "succ": [1]}, {"duration": 5, "succ": []}], "n": 2}', "(jobs=[(duration=2, succ=[1]), (duration=5, succ=[])], n=2)"),
    ('{"p": {"x": 1, "y": {"z": [3]}}, "n": 2}', "(p=(x=1, y=(z=[3])), n=2)"),  # only the root object is replaced by its value when it has a single field
    ('[{"a": 1}, {"a": 2}]', "[(a=1), (a=2)]"),
])
def test_data_json(run, content, shown):
    r = run(SHOW, args=["-data=data.json"], files={"data.json": content})
    assert "data " + shown in r.lines, r.report()


def test_data_json_types(run):
    r = run("""
        print("types", type(data.m).__name__, type(data.m[0]).__name__, type(data.t).__name__, type(data.jobs).__name__)
        print("values", data.jobs[1].duration, data.m[1][0], data.t[-1])
    """, args=["-data=data.json"], files={"data.json": '{"m": [[1, 2], [3, 4]], "t": [5, 6], "jobs": [{"duration": 2}, {"duration": 5}]}'})
    assert "types ListInt ListInt ListInt list" in r.lines, r.report()
    assert "values 5 3 6" in r.lines


@pytest.mark.parametrize("value, shown", [
    ("[a.json,b.json]", "(n=3, m=4, k=5)"),
    ("[a.json,m=7]", "(n=3, m=7)"),
    ("[a.json,k=5]", "(n=3, m=4, k=5)"),
    ("[m=7,a.json]", "(m=4, n=3)"),  # the value given first is overridden by the JSON file
])
def test_data_json_combined(run, value, shown):
    r = run(SHOW, args=["-data=" + value], files={"a.json": '{"n": 3, "m": 4}', "b.json": '{"k": 5}'})
    assert "data " + shown in r.lines, r.report()


def test_data_json_solutions(run, solver):
    r = run("""
        x = VarArray(size=len(data.weights), dom=range(2))
        satisfy(x * data.weights <= data.capacity)
    """, args=["-data=data.json"], files={"data.json": '{"weights": [2, 3, 4], "capacity": 5}'}, solver=solver)
    assert_solutions(r, brute_force([range(2)] * 3, lambda a, b, c: 2 * a + 3 * b + 4 * c <= 5))


def test_data_json_non_identifier_keys(run):
    r = run('print("dict", dict(data), data["t"]["x-y"])', args=["-data=data.json"], files={"data.json": '{"my-key": 3, "t": {"x-y": 4}}'})
    assert "no conversion to named tuples is performed" in r.stdout, r.report()
    assert "dict {'my-key': 3, 't': OrderedDict({'x-y': 4})} 4" in r.lines


@pytest.mark.parametrize("content, shown", [
    ('{"my-key": 3}', "3"),
    ('{"class": 3}', "3"),
    ('{"my-key": [1, 2]}', "[1, 2]"),
    ('{"my-key": {"x-y": 4}}', "OrderedDict({'x-y': 4})"),
])
@pytest.mark.parametrize("code, args", [
    ('print("value", data)', ["-data=data.json"]),
    ('print("value", load_json_data("data.json"))', []),
])
def test_data_json_single_non_identifier_key(run, code, args, content, shown):
    # the root object has a single field: its value is given, even if the data are not converted into named tuples
    r = run(code, args=args, files={"data.json": content})
    assert "value " + shown in r.lines, r.report()


@pytest.mark.parametrize("key", ["class", "if", "None", "_x", "_"])
def test_data_json_keys_not_allowed_in_named_tuples(run, key):
    # as for any key that is not an identifier, the data are not converted into named tuples
    r = run(f'print("values", data["{key}"], data["b"])', args=["-data=data.json"], files={"data.json": json.dumps({key: 3, "b": 4})})
    assert "no conversion to named tuples is performed" in r.stdout, r.report()
    assert "values 3 4" in r.lines, r.report()


def test_data_json_nested_key_not_allowed_in_named_tuples(run):
    r = run('print("values", data["items"][1]["class"], data["n"])', args=["-data=data.json"],
            files={"data.json": '{"items": [{"class": 1}, {"class": 2}], "n": 0}'})
    assert "no conversion to named tuples is performed" in r.stdout, r.report()
    assert "values 2 0" in r.lines, r.report()


@pytest.mark.parametrize("key", ["type", "match", "case", "x_"])
def test_data_json_soft_keywords_in_named_tuples(run, key):
    # soft keywords are accepted as field names of named tuples
    r = run(f'print("values", data.{key}, data.b)', args=["-data=data.json"], files={"data.json": json.dumps({key: 3, "b": 4})})
    assert "no conversion to named tuples is performed" not in r.stdout, r.report()
    assert "values 3 4" in r.lines, r.report()


OBJECTS_ORDERS = '{"items": [{"a": 1, "b": 2}, {"b": 3, "a": 4}], "n": 0}'


@pytest.mark.parametrize("code, args", [
    ('print("items", [(item.a, item.b) for item in data.items], [tuple(item) for item in data.items])', ["-data=data.json"]),
    ('items = load_json_data("data.json").items\nprint("items", [(item.a, item.b) for item in items], [tuple(item) for item in items])', []),
])
def test_data_json_objects_with_keys_in_different_orders(run, code, args):
    # the values are given by name; the fields of all the objects are in the order of the keys of the first object
    r = run(code, args=args, files={"data.json": OBJECTS_ORDERS})
    assert "items [(1, 2), (4, 3)] [(1, 2), (4, 3)]" in r.lines, r.report()


def test_data_json_nested_objects_with_keys_in_different_orders(run):
    r = run('print("items", [(item.a, [(p.x, p.y) for p in item.t]) for item in data.items])', args=["-data=data.json"],
            files={"data.json": '{"items": [{"a": 1, "t": [{"x": 1, "y": 2}, {"y": 3, "x": 4}]}, {"t": [], "a": 2}], "n": 0}'})
    assert "items [(1, [(1, 2), (4, 3)]), (2, [])]" in r.lines, r.report()


@pytest.mark.parametrize("second", ['{"a": 3, "c": 4}', '{"a": 3}', '{"a": 3, "b": 4, "c": 5}'])
@pytest.mark.parametrize("code, args", [('print("items", data.items)', ["-data=data.json"]), ('print("items", load_json_data("data.json"))', [])])
def test_data_json_objects_with_different_keys(run, second, code, args):
    # an error is reported: a value is never given to another field
    r = run(code, args=args, files={"data.json": '{"items": [{"a": 1, "b": 2}, ' + second + '], "n": 0}'})
    assert_fails(r)
    assert "The objects of a list must have the same keys" in r.stdout, r.report()


@pytest.mark.parametrize("content", ["5", "-2.5", "true", "null", '"abc"'])
@pytest.mark.parametrize("code, args", [(SHOW, ["-data=data.json"]), ('data = load_json_data("data.json")\n' + SHOW, [])])
def test_data_json_scalar(run, content, code, args):
    # the root of the JSON file is given as such
    r = run(code, args=args, files={"data.json": content})
    assert "data " + repr(json.loads(content)) in r.lines, r.report()


def test_data_json_invalid(run):
    r = run(SHOW, args=["-data=data.json"], files={"data.json": '{"n": 3,'})
    assert not r.ok and r.exception == "JSONDecodeError", r.report()


# -------------------------------------------------------------------------------------- load_json_data() default_data()

def test_load_json_data(run):
    r = run('d = load_json_data("data.json")\nprint("loaded", d.n, d.m)\n' + SHOW, files={"data.json": '{"n": 3, "m": 4}'})
    assert "loaded 3 4" in r.lines, r.report()
    assert "data None" in r.lines  # the variable data is not modified


@pytest.mark.parametrize("path", ["data.json", "./data.json", "sub/data.json", "sub/../data.json"])
def test_load_json_data_paths(run, path):
    r = run(f'print("loaded", load_json_data("{path}"))', files={"data.json": '{"t": [1, 2]}', "sub/data.json": '{"t": [1, 2]}'})
    assert "loaded [1, 2]" in r.lines, r.report()


def test_load_json_data_in_directory_of_model(run):
    # the model models/m.py is run from another directory: the JSON file is looked for in the directory of the model
    r = run("""
        import subprocess, sys
        p = subprocess.run([sys.executable, "models/m.py"], capture_output=True, text=True)
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        sys.exit(p.returncode)
    """, header=False, files={"models/m.py": 'from pycsp3 import *\nprint("loaded", load_json_data("data.json"), default_data("data.json"))\n',
                              "models/data.json": '{"t": [1, 2]}'})
    assert "loaded [1, 2] [1, 2]" in r.lines, r.report()


@pytest.mark.parametrize("code, name", [
    ('d = load_json_data("data.json")', "model-data.xml"),
    ('d = load_json_data("sub/data.json")', "model-data.xml"),
    ('d = load_json_data("data.json", record_string_data=False)', "model.xml"),
    ('data = default_data("data.json")', "model-data.xml"),
])
def test_load_json_data_filename(run, code, name):
    r = run(code + "\nx = Var(dom=range(2))", files={"data.json": '{"n": 3, "m": 4}', "sub/data.json": '{"n": 3, "m": 4}'})
    assert xml_names(r) == [name]


def test_default_data_solutions(run, solver):
    r = run("""
        data = default_data("data.json")
        x = VarArray(size=data.n, dom=range(data.k))
        satisfy(AllDifferent(x))
    """, files={"data.json": '{"n": 3, "k": 4}'}, solver=solver)
    assert_solutions(r, brute_force([range(4)] * 3, lambda *t: len(set(t)) == 3))


@pytest.mark.parametrize("args, values", [([], "3 4"), (["-data=[5,6]"], "5 6")])
def test_default_data_when_no_data_given(run, args, values):
    # the idiom of the documentation: the default data are loaded only when no data are given on the command line
    r = run("""
        n, k = data or default_data("data.json")
        print("values", n, k)
    """, args=args, files={"data.json": '{"n": 3, "k": 4}'})
    assert "values " + values in r.lines, r.report()


@pytest.mark.parametrize("call", [
    'load_json_data("missing.json")',
    'load_json_data("sub/missing.json")',
    'default_data("missing.json")',
    'load_json_data("data.txt")',
    'load_json_data("")',
    'load_json_data("../missing.json")',
    'load_json_data("./missing.json")',
    'load_json_data(5)',
    'load_json_data(None)',
    'load_json_data(["data.json"])',
    'default_data(None)',
])
def test_load_json_data_invalid(run, call):
    assert_fails(run("d = " + call, files={"data.txt": '{"n": 3}'}))


@pytest.mark.parametrize("call, message", [
    ('load_json_data("data.txt")', "The name of a JSON file must end with .json, which is not the case of 'data.txt'"),
    ('load_json_data(5)', "The name of a JSON file must be a string (possibly a URL), which is not the case of 5"),
    ('load_json_data("../missing.json")', "missing.json does not exist"),
])
def test_load_json_data_invalid_messages(run, call, message):
    r = run("d = " + call, files={"data.txt": '{"n": 3}'})
    assert not r.ok and message in r.stdout + r.stderr, r.report()


def test_load_json_data_parent_directory(run):
    # the model sub/m.py is run from the directory sub: ../data.json is the file data.json of the parent directory
    r = run("""
        import subprocess, sys
        p = subprocess.run([sys.executable, "m.py"], capture_output=True, text=True, cwd="sub")
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        sys.exit(p.returncode)
    """, header=False, files={"sub/m.py": 'from pycsp3 import *\nprint("loaded", load_json_data("../data.json"))\n', "data.json": '{"t": [1, 2]}'})
    assert "loaded [1, 2]" in r.lines, r.report()


@pytest.mark.parametrize("args, files, name, content", [
    (["-data=[n=3,m=4]", "-dataexport"], {}, "model-3-4.json", {"n": 3, "m": 4}),
    (["-data=[n=3,m=4]", "-dataexport=out"], {}, "out.json", {"n": 3, "m": 4}),
    (["-data=data.json", "-dataexport=out"], {"data.json": '{"items": [{"a": 1, "b": [2]}, {"a": 3, "b": []}], "n": 5}'}, "out.json",
     {"items": [{"a": 1, "b": [2]}, {"a": 3, "b": []}], "n": 5}),
])
def test_dataexport(run, args, files, name, content):
    r = run("x = Var(dom=range(2))", args=args, files=files)
    assert r.ok, r.report()
    assert json.loads((r.directory / name).read_text()) == content


# ------------------------------------------------------------------------------------------------------ Task and Item

def test_task_and_item_fields(run):
    r = run("""
        t, u = Task(1, 2), Task(origin=3, length=4, height=5)
        i = Item(bin=0, size=3)
        print("task", t, u.origin, u.length, u.height, Task._fields)
        print("item", i, i.bin, i.size, Item(1, 2), Item._fields)
    """)
    assert "task Task(origin=1, length=2, height=None) 3 4 5 ('origin', 'length', 'height')" in r.lines, r.report()
    assert "item Item(bin=0, size=3) 0 3 Item(bin=1, size=2) ('bin', 'size')" in r.lines


@pytest.mark.parametrize("call", ["Task(1)", "Task()", "Task(1, 2, 3, 4)", "Task(1, 2, weight=3)", "Item(1)", "Item(1, 2, 3)", "Item(size=2)"])
def test_task_and_item_invalid(run, call):
    assert_fails(run("t = " + call))


def _cumulative(origins, lengths, heights, capacity):
    return all(sum(h for o, l, h in zip(origins, lengths, heights) if o <= t < o + l) <= capacity for t in range(10))


def test_task_cumulative_solutions(run, solver):
    r = run("""
        s = VarArray(size=3, dom=range(3))
        satisfy(Cumulative([Task(origin=s[i], length=2, height=1) for i in range(3)]) <= 2)
    """, solver=solver)
    assert_solutions(r, brute_force([range(3)] * 3, lambda *s: _cumulative(s, [2] * 3, [1] * 3, 2)))


def test_task_cumulative_with_variable_lengths_solutions(run, solver):
    r = run("""
        s = VarArray(size=2, dom=range(3))
        d = VarArray(size=2, dom=range(1, 3))
        satisfy(Cumulative([Task(s[i], d[i], i + 1) for i in range(2)]) <= 2)
    """, solver=solver)
    assert_solutions(r, brute_force([range(3)] * 2 + [range(1, 3)] * 2, lambda s0, s1, d0, d1: _cumulative([s0, s1], [d0, d1], [1, 2], 2)))


@pytest.mark.parametrize("tasks, message", [
    ("[Task(origin=s[i], length=2) for i in range(3)]", "The height of a task must be given in Cumulative()"),
    ("[Task(s[0], 2, 1), Task(s[1], 2), Task(s[2], 2, 1)]", "The height of a task must be given in Cumulative()"),
    ("[Task(s[0], 2)]", "The height of a task must be given in Cumulative()"),
    ("[(s[0], 2, None), (s[1], 2, 1), (s[2], 2, 1)]", "The height of a task must be given in Cumulative()"),
    ("[(s[0], None, 1), (s[1], 2, 1), (s[2], 2, 1)]", "The lengths of Cumulative() must be given, and cannot be None"),
    ("[(s[0], 2), (s[1], 2), (s[2], 2)]", "A task of Cumulative() must be (origin, length, height) or (origin, length, end, height)"),
    ("[(s[0], 2, 1), (s[1], 2, s[2], 1), (s[2], 2, 1)]", "The tasks of Cumulative() must all have the same size"),
])
def test_task_cumulative_without_height(run, tasks, message):
    # the height of a task is None by default, which is not possible in a constraint Cumulative
    r = run(f"""
        s = VarArray(size=3, dom=range(3))
        satisfy(Cumulative({tasks}) <= 2)
    """)
    assert_fails(r)
    assert message in r.stdout, r.report()


@pytest.mark.parametrize("parameters, message", [
    ("origins=s, lengths=[2, 2, 2]", "The heights of Cumulative() must be given, and cannot be None"),
    ("origins=s, lengths=[2, 2, 2], heights=[1, None, 1]", "The heights of Cumulative() must be given, and cannot be None"),
    ("origins=s, heights=[1, 1, 1]", "The lengths of Cumulative() must be given, and cannot be None"),
    ("origins=s, lengths=[2, None, 2], heights=[1, 1, 1]", "The lengths of Cumulative() must be given, and cannot be None"),
    ("origins=[s[0], None, s[2]], lengths=[2, 2, 2], heights=[1, 1, 1]", "The origins of Cumulative() must be given, and cannot be None"),
    ("origins=s, lengths=[2, 2, 2], heights=[1, 1]", "In Cumulative(), the number of heights (2) must be the number of origins (3)"),
    ("origins=s, lengths=[2, 2], heights=[1, 1, 1]", "In Cumulative(), the number of lengths (2) must be the number of origins (3)"),
    ("origins=s, lengths=[2, 2, 2], heights=[1, 1, 1], ends=s[:2]", "In Cumulative(), the number of ends (2) must be the number of origins (3)"),
])
def test_cumulative_invalid_heights_and_sizes(run, parameters, message):
    # found with #90 (tasks without height); to be moved into the tests of the constraint Cumulative
    r = run(f"""
        s = VarArray(size=3, dom=range(3))
        satisfy(Cumulative({parameters}) <= 2)
    """)
    assert_fails(r)
    assert message in r.stdout, r.report()


@pytest.mark.parametrize("parameters", ["origins=s, lengths=2, heights=1", "origins=s, lengths=[2, 2, 2], heights=[1, 1, 1], ends=s"])
def test_cumulative_valid_parameters(run, parameters):
    r = run(f"""
        s = VarArray(size=3, dom=range(3))
        satisfy(Cumulative({parameters}) <= 2)
    """)
    assert r.ok and r.xml.find("constraints/cumulative") is not None, r.report()


def test_task_nooverlap_solutions(run, solver, request):
    bug_for(request, "COSOCO", "xcsp3team/cosoco#73: cosoco enumerates the solutions of a constraint NoOverlap several times")
    r = run("""
        s = VarArray(size=3, dom=range(5))
        satisfy(NoOverlap([Task(origin=s[i], length=2) for i in range(3)]))
    """, solver=solver)
    assert_solutions(r, brute_force([range(5)] * 3, lambda *s: all(s[i] + 2 <= s[j] or s[j] + 2 <= s[i] for i in range(3) for j in range(i + 1, 3))))


def test_item_binpacking_solutions(run, solver):
    r = run("""
        b = VarArray(size=3, dom=range(2))
        items = [Item(bin=b[i], size=i + 1) for i in range(3)]
        satisfy(BinPacking([item.bin for item in items], sizes=[item.size for item in items]) <= 3)
    """, solver=solver)
    assert_solutions(r, brute_force([range(2)] * 3, lambda *b: all(sum(i + 1 for i in range(3) if b[i] == k) <= 3 for k in range(2))))


# ------------------------------------------------------------------------------------------------------- data parsers

def run_parser(run, parser, text, *args, model=SHOW, **kwargs):
    """Runs the model with the options -data=data.txt -parser=parser.py, the file data.txt containing the specified text."""
    files = {"parser.py": PARSING + textwrap.dedent(parser).strip("\n") + "\n", "data.txt": text}
    return run(model, args=["-data=data.txt", "-parser=parser.py", *args], files=files, **kwargs)


def test_parser_lines(run):
    r = run_parser(run, """
        data["a"] = line()
        data["b"] = next_line()
        data["c"] = next_line()
        data["d"] = line()
    """, "first\n\n   second  \nthird\n")
    assert "data (a='first', b='second', c='third', d='third')" in r.lines, r.report()  # empty lines discarded, lines stripped


def test_parser_next_line_repeat(run):
    r = run_parser(run, """
        data["a"] = next_line(repeat=1)
        data["b"] = next_line(repeat=0)
        data["c"] = next_line()
        data["d"] = line()
    """, "l0\nl1\nl2\nl3\n")
    assert "data (a='l2', b='l3', c=None, d=None)" in r.lines, r.report()
    assert "Warning: no more line" in r.lines


@pytest.mark.parametrize("call, text, current", [
    ('skip_empty_lines(or_prefixed_by="%")', "% c1\n%c2\nn = 5;\n% c3\n", "'n = 5;'"),
    ('skip_empty_lines(or_prefixed_by="#")', "# c1\nn = 5;\n", "'n = 5;'"),
    ('skip_empty_lines(or_prefixed_by="%")', "n = 5;\n% c1\n", "'n = 5;'"),
    ("skip_empty_lines()", "a\nb\n", "'a'"),
    ('skip_empty_lines(or_prefixed_by="%")', "% c1\n% c2\n", "None"),
])
def test_parser_skip_empty_lines(run, call, text, current):
    r = run_parser(run, call + '\ndata["a"] = line()\ndata["b"] = 0', text)
    assert "data (a=" + current + ", b=0)" in r.lines, r.report()


def test_parser_next_int(run):
    # a nonogram: its numbers of rows and columns, and then each pattern given by its number of blocks followed by their sizes
    r = run_parser(run, """
        nRows, nCols = next_int(), next_int()
        data["rows"] = [[next_int() for _ in range(next_int())] for _ in range(nRows)]
        data["cols"] = [[next_int() for _ in range(next_int())] for _ in range(nCols)]
    """, "2 3\n1 2\n2 1 1\n1 1\n1 2\n1 1\n")
    assert "data (rows=[[2], [1, 1]], cols=[[1], [2], [1]])" in r.lines, r.report()


def test_parser_next_str(run):
    r = run_parser(run, """
        data["items"] = [(next_str(), next_int()) for _ in range(2)]
        data["end"] = next_str()
    """, "apple 3 banana 5\nend\n")
    assert "data (items=[['apple', 3], ['banana', 5]], end='end')" in r.lines, r.report()


@pytest.mark.parametrize("parser, text, shown", [
    ('data["a"] = next_int()\ndata["l"] = line()\ndata["m"] = next_line()\ndata["b"] = next_int()', "1 2 3\n4 5\n", "(a=1, l='1 2 3', m='4 5', b=4)"),
    ('data["l"] = line()\ndata["a"] = next_int()\ndata["b"] = next_int()\ndata["c"] = next_int()', "1 2\n\n3\n", "(l='1 2', a=1, b=2, c=3)"),
    ('data["a"] = next_int()\ndata["b"] = next_int()', "-3 +4\n", "(a=-3, b=4)"),
    ('data["a"] = next_str()\ndata["b"] = next_int()', "x-1   7\n", "(a='x-1', b=7)"),
])
def test_parser_tokens_and_lines(run, parser, text, shown):
    assert "data " + shown in run_parser(run, parser, text).lines


@pytest.mark.parametrize("parser, text", [
    ('data["a"] = next_int()\ndata["b"] = next_int()', "1\n2\n"),
    ('data["a"] = next_int()\ndata["b"] = next_int()', "1 2\n"),
    ('data["a"] = next_str()\ndata["b"] = next_str()', "x\ny\n"),
])
def test_parser_last_token_without_warning(run, parser, text):
    # all the data are read, without going beyond: no warning must be displayed
    r = run_parser(run, parser, text)
    assert r.ok, r.report()
    assert "Warning: no more line" not in r.stdout, r.report()


@pytest.mark.parametrize("parser, shown", [
    ('data["n"] = number_in(line())\ndata["pre"] = [numbers_in(ln) for ln in remaining_lines(skip_curr=True)]\ndata["l"] = line()',
     "(n=9, pre=[[2, 0], [4, 1]], l='constraint prerequisite(2, 0);')"),
    ('data["r"] = remaining_lines()\ndata["l"] = line()', "(r=['n_courses = 9;', 'constraint prerequisite(2, 0);', 'constraint prerequisite(4, 1);'], l='n_courses = 9;')"),
    ('next_line(repeat=1)\ndata["r"] = remaining_lines()\ndata["l"] = line()', "(r=['constraint prerequisite(4, 1);'], l='constraint prerequisite(4, 1);')"),
    ('next_line(repeat=5)\ndata["r"] = remaining_lines()\ndata["l"] = line()', "(r=[], l=None)"),
])
def test_parser_remaining_lines(run, parser, shown):
    r = run_parser(run, parser, "n_courses = 9;\nconstraint prerequisite(2, 0);\nconstraint prerequisite(4, 1);\n")
    assert "data " + shown in r.lines, r.report()


@pytest.mark.parametrize("call, shown", [
    ('next_lines(skip_curr=True, prefix_stop="end")', "(e=['0 1', '1 2'], l='end')"),
    ('next_lines(prefix_stop="end")', "(e=['edges', '0 1', '1 2'], l='end')"),
    ('next_lines(prefix_stop="ed")', "(e=[], l='edges')"),
    ('next_lines(skip_curr=True, prefix_stop="1")', "(e=['0 1'], l='1 2')"),
])
def test_parser_next_lines(run, call, shown):
    r = run_parser(run, f'data["e"] = {call}\ndata["l"] = line()', "edges\n0 1\n1 2\nend\nafter\n")
    assert "data " + shown in r.lines, r.report()


@bug("#93: next_lines() silently drops the last line when no line starts with prefix_stop")
def test_parser_next_lines_without_stop(run):
    # the line starting with the prefix must exist
    assert_fails(run_parser(run, 'data["e"] = next_lines(skip_curr=True, prefix_stop="end")\ndata["l"] = line()', "edges\n0 1\n1 2\n"))


@pytest.mark.parametrize("text, costs, current", [
    ("costs = [\n4, 2, 7,\n3, 5];\nn = 5;\n", [4, 2, 7, 3, 5], "3, 5];"),
    ("costs = [\n1, 2];\n", [1, 2], "1, 2];"),
    ("costs = [1, 2];\n[3, 4];\n", [3, 4], "[3, 4];"),
    ("costs = [\n-4, 2,\n3];\n", [-4, 2, 3], "3];"),
    ("costs = [\n4 2 7\n3 5];\nn = 5;\n", [4, 2, 7, 3, 5], "3 5];"),
    ("costs = [\n4\n7\n5];\n", [4, 7, 5], "5];"),
    ("costs = [\n-4\n-2 1];\n", [-4, -2, 1], "-2 1];"),
])
def test_parser_numbers_in_lines_until(run, text, costs, current):
    r = run_parser(run, 'data["costs"] = numbers_in_lines_until(";")\ndata["l"] = line()', text)
    assert "data (costs=" + str(costs) + ", l=" + repr(current) + ")" in r.lines, r.report()


@pytest.mark.parametrize("text", ["costs = [\n1 2\n3\n", "costs = [1, 2];\n"])
def test_parser_numbers_in_lines_until_without_stop(run, text):
    # the line ending with the stop must exist (after the current line)
    r = run_parser(run, 'data["costs"] = numbers_in_lines_until(";")\ndata["l"] = line()', text)
    assert_fails(r)
    assert "numbers_in_lines_until(): no line ends with ';'" in r.stdout and "Warning: no more line" not in r.stdout, r.report()


@pytest.mark.parametrize("parser, text", [
    ('data["a"] = next_int()\ndata["b"] = next_int()', "1\n"),  # no more token
    ('data["a"] = next_int()\ndata["b"] = 0', "abc\n"),  # not an integer
    ('data["a"] = numbers_in_lines_until(";")\ndata["b"] = 0', "costs = [\n1 2\n3\n"),  # no line ending with ;
    ('data["a"] = number_in(line())\ndata["b"] = 0', "no number\n"),
    ('data["a"] = 1 / 0', "1\n"),
])
def test_parser_invalid_data(run, parser, text):
    assert_fails(run_parser(run, parser, text))


@pytest.mark.parametrize("parser, text", [
    ('data["a"] = next_int()\ndata["b"] = next_int()', "1\n"),
    ('data["a"] = next_str()\ndata["b"] = next_int()\ndata["c"] = next_str()', "x 2\n"),
    ('data["a"] = line()\nnext_line()\ndata["b"] = next_int()', "1\n"),
])
def test_parser_no_more_token(run, parser, text):
    # reading a token beyond the data is reported by an explicit error
    r = run_parser(run, parser, text)
    assert_fails(r)
    assert "No more token to read with next_int() or next_str()" in r.stdout, r.report()


@pytest.mark.parametrize("args", [
    ["-data=missing.txt", "-parser=parser.py"],
    ["-data=data.txt", "-parser=missing.py"],
    ["-parser=parser.py"],  # line() without data
])
def test_parser_invalid(run, args):
    assert_fails(run(SHOW, args=args, files={"parser.py": PARSING + 'data["a"] = line()\ndata["b"] = 0', "data.txt": "1\n"}))


@pytest.mark.parametrize("value, lines", [
    ("[a.txt,b.txt]", ["1 2", "3", "4"]),
    ("[b.txt,a.txt]", ["3", "4", "1 2"]),
    ("[a.txt,b.txt,10,3 5,partial]", ["1 2", "3", "4", "10", "3 5", "partial"]),
    ("instances", ["1 2", "3", "4"]),  # a directory: all its files, in the order of their names
])
def test_parser_several_sources(run, value, lines):
    r = run('print("lines", data.lines)', args=["-data=" + value, "-parser=parser.py"],
            files={"parser.py": PARSING + 'data["lines"] = remaining_lines()\ndata["b"] = 0', "a.txt": "1 2\n", "b.txt": "3\n\n4\n",
                   "instances/b.txt": "3\n\n4\n", "instances/a.txt": "1 2\n"})
    assert "lines " + str(lines) in r.lines, r.report()


@pytest.mark.parametrize("value, name", [
    ("data.txt", "model-data.xml"),
    ("[data.txt,b.txt]", "model-data-b.xml"),
    ("instances", "model-instances.xml"),
])
def test_parser_filename(run, value, name):
    r = run("x = Var(dom=range(2))", args=["-data=" + value, "-parser=parser.py"],
            files={"parser.py": PARSING + 'data["a"] = line()\ndata["b"] = 0', "data.txt": "1\n", "b.txt": "2\n", "instances/a.txt": "1\n"})
    assert xml_names(r) == [name]


def test_parser_structures(run):
    r = run_parser(run, """
        data["t"] = [1, 2]
        data["m"] = [[1, 2], [3, 4]]
        data["p"] = (1, 2)
    """, "1\n", model='print("types", type(data.t).__name__, type(data.m).__name__, type(data.m[0]).__name__, type(data.p).__name__)')
    assert "types ListInt ListInt ListInt ListInt" in r.lines, r.report()


def test_parser_single_field(run):
    assert "data 8" in run_parser(run, 'data["n"] = number_in(line())', "n = 8;\n").lines


def test_parser_solutions(run, solver):
    r = run_parser(run, """
        data["n"] = next_int()
        data["values"] = [next_int() for _ in range(next_int())]
    """, "2\n3 1 4 6\n", model="""
        x = VarArray(size=data.n, dom=data.values)
        satisfy(x[0] < x[1])
    """, solver=solver)
    assert_solutions(r, brute_force([[1, 4, 6]] * 2, lambda a, b: a < b))


def test_parser_dataexport(run):
    r = run_parser(run, 'data["a"] = next_int()\ndata["b"] = [next_int(), next_int()]', "1 2 3\n", "-dataexport", model="x = Var(dom=range(2))")
    assert r.ok, r.report()
    assert json.loads((r.directory / "data.json").read_text()) == {"a": 1, "b": [2, 3]}


def test_register_fields(run):
    r = run(PARSING + """
data = register_fields("[data.txt,more.txt]")
data["n"] = number_in(line())
data["m"] = numbers_in(next_line())
data["r"] = remaining_lines(skip_curr=True)
print("fields", dict(data))
""", files={"data.txt": "n = 8;\nm = [1, 2];\n", "more.txt": "end\n"})
    assert "fields {'n': 8, 'm': [1, 2], 'r': ['end']}" in r.lines, r.report()


@pytest.mark.parametrize("expression, value", [
    ('number_in("n_courses = 9;")', 9),
    ('number_in("first = 1;", offset=-1)', 0),
    ('number_in("x = -4")', -4),
    ('number_in("a1b22")', 1),
    ('number_in("  7  ", offset=3)', 10),
    ('numbers_in("course_load = [2, 3, 1, 3];")', [2, 3, 1, 3]),
    ('numbers_in("prerequisite(2, 1);", offset=-1)', [1, 0]),
    ('numbers_in("x = -2, y = 5")', [-2, 5]),
    ('numbers_in("1..5")', [1, 5]),
    ('numbers_in("no number")', []),
    ('numbers_in("")', []),
    ('split_with_structure(list(range(12)), 2, 3)', [[[0, 1], [2, 3], [4, 5]], [[6, 7], [8, 9], [10, 11]]]),
    ('split_with_structure(list(range(12)), 3)', [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]),
    ('split_with_structure(list(range(4)), 2, 2)', [[[0], [1]], [[2], [3]]]),
    ('split_with_structure(list(range(6)), 1)', [[0, 1, 2, 3, 4, 5]]),
    ('split_with_structure([], 2)', [[], []]),
    ('split_with_rows_of_size([1, 2, 3, 4, 5, 6], 3)', [[1, 2, 3], [4, 5, 6]]),
    ('split_with_rows_of_size([1, 2, 3, 4, 5, 6], 1)', [[1], [2], [3], [4], [5], [6]]),
    ('split_with_rows_of_size([1, 2, 3, 4, 5, 6], 6)', [[1, 2, 3, 4, 5, 6]]),
    ('split_with_rows_of_size([], 3)', []),
])
def test_parsing_functions(run, expression, value):
    r = run(PARSING + f'print("value", {expression})')
    assert "value " + str(value) in r.lines, r.report()


@pytest.mark.parametrize("expression", [
    pytest.param('number_in("no number")', marks=bug(PARSING_INVALID)),
    pytest.param('number_in(None)', marks=bug(PARSING_INVALID)),
    pytest.param('numbers_in(None)', marks=bug(PARSING_INVALID)),
    pytest.param('split_with_structure(list(range(12)), 5)', marks=bug(PARSING_INVALID)),
    pytest.param('split_with_structure(list(range(12)), 2, 4)', marks=bug(PARSING_INVALID)),
    pytest.param('split_with_structure(list(range(12)), 0)', marks=bug(PARSING_INVALID)),
    pytest.param('split_with_structure(list(range(12)), -2)', marks=bug(PARSING_INVALID)),
    pytest.param('split_with_structure(tuple(range(12)), 2)', marks=bug(PARSING_INVALID)),
    pytest.param('split_with_structure(list(range(12)), 2.0)', marks=bug(PARSING_INVALID)),
    'split_with_rows_of_size([1, 2, 3, 4, 5, 6, 7], 3)',
    pytest.param('split_with_rows_of_size([1, 2, 3], 0)', marks=bug(PARSING_INVALID)),
    pytest.param('split_with_rows_of_size([1, 2, 3], -3)', marks=bug(PARSING_INVALID)),
])
def test_parsing_functions_invalid(run, expression):
    assert_fails(run(PARSING + f"print({expression})"))


@pytest.mark.parametrize("args, shown", [
    (["-parser=parser.py", "10", "small", "3"], "(a=10, s='small', b=3)"),
    (["10", "-parser=parser.py", "small", "3"], "(a=10, s='small', b=3)"),  # the parameters are the arguments that are not options
])
def test_ask_number_and_string_from_command_line(run, args, shown):
    r = run(SHOW, args=args, files={"parser.py": PARSING + 'data["a"] = ask_number("A?")\ndata["s"] = ask_string("S?")\ndata["b"] = ask_number("B?")'})
    assert "data " + shown in r.lines, r.report()


def test_ask_number_and_string_from_user(run):
    r = run(SHOW, args=["-parser=parser.py", "7"], files={"parser.py": PARSING + textwrap.dedent("""
        import io, sys
        sys.stdin = io.StringIO("large\\n5\\n")  # what the user types
        data["a"] = ask_number("A?")
        data["s"] = ask_string("S?")
        data["b"] = ask_number("B?")
    """)})
    assert "S? B? data (a=7, s='large', b=5)" in r.lines, r.report()  # the messages are displayed by input(), without new line
    assert "A?" not in r.stdout


def test_ask_in_model(run):
    r = run(PARSING + 'print("asked", ask_number("n?"), ask_string("s?"))', args=["5", "abc"])
    assert "asked 5 abc" in r.lines, r.report()


@pytest.mark.parametrize("args", [["-parser=parser.py", "abc"], ["-parser=parser.py"]])  # not an integer, nothing typed by the user
def test_ask_number_invalid(run, args):
    assert_fails(run(SHOW, args=args, files={"parser.py": PARSING + 'data["a"] = ask_number("A?")\ndata["b"] = 0'}))
