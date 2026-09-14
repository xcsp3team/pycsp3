"""
Tests of the section Variables of the API (https://pycsp.org/documentation/api/variables/):
Var(), VarArray(), VarArrayMultiple(), var(), and the classes Variable, VariableInteger, Domain, ListVar and ListInt.
"""

from itertools import product

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for, declared_variables

# Known bugs shared by several tests (each bug is reported in the issue given at the start of its reason)
NOT_EXPLICIT = "#83: the error is not explicit (assert without message, or exception raised by Python inside PyCSP3)"
COSOCO_SYMBOLIC = "xcsp3team/cosoco#71: cosoco does not handle symbolic variables (XCSP3Core expected type=integer)"


def not_explicit(*values):
    return pytest.param(*values, marks=bug(NOT_EXPLICIT))


# ------------------------------------------------------------------------------------------------------------ Var()

@pytest.mark.parametrize("declaration, values", [
    ("x = Var(0, 1)", [0, 1]),
    ("x = Var(0, 2, 4)", [0, 2, 4]),
    ("x = Var(4, 0, 2)", [0, 2, 4]),
    ("x = Var(-3, 3)", [-3, 3]),
    ("x = Var(5)", [5]),
    ("x = Var([0, 2, 4])", [0, 2, 4]),
    ("x = Var(range(5))", [0, 1, 2, 3, 4]),
    ("x = Var(range(2), 5)", [0, 1, 5]),
    ("x = Var(dom=range(10))", list(range(10))),
    ("x = Var(dom=range(-3, 3))", [-3, -2, -1, 0, 1, 2]),
    ("x = Var(dom=range(0, 10, 3))", [0, 3, 6, 9]),
    ("x = Var(dom={0, 3, 6})", [0, 3, 6]),
    ("x = Var(dom={v for v in range(20) if v % 7 == 0})", [0, 7, 14]),
    ("x = Var(dom=frozenset({1, 2}))", [1, 2]),
    ("x = Var(dom=(3, 1, 2))", [1, 2, 3]),
    ("x = Var(dom=[0, 1, 2, 3, 5])", [0, 1, 2, 3, 5]),
    ("x = Var(dom=[[0, 1], [5, 6]])", [0, 1, 5, 6]),
    ("x = Var(dom=5)", [5]),
    ("x = Var(dom=lambda: range(4))", [0, 1, 2, 3]),
    ("x = Var(dom=[True, False])", [0, 1]),
    ("x = Var('red', 'green')", ["green", "red"]),
    ("x = Var(dom={'red', 'green', 'blue'})", ["blue", "green", "red"]),
    ("x = Var(dom=['b', 'a'])", ["a", "b"]),
    ("x = Var(dom=[0, 0, 1])", [0, 1]),
    ("x = Var(2, 5, 2)", [2, 5]),
    ("x = Var('a', 'b', 'a')", ["a", "b"]),
    ("x = Var(dom=True)", [1]),
])
def test_var_domain(run, declaration, values):
    assert declared_variables(run(declaration)) == {"x": values}


def test_var_large_domain(run):
    assert declared_variables(run("x = Var(dom=range(-10**9, 10**9))")) == {"x": ["-1000000000..999999999"]}


@pytest.mark.parametrize("declaration", [
    not_explicit("x = Var(0, 'red')"),
    "x = Var(dom=set())",
    "x = Var(dom=[])",
    "x = Var(dom={})",
    "x = Var(dom=range(0))",
    "x = Var(dom=range(5, 2))",
    "x = Var(dom=2.5)",
    "x = Var(dom=[1.5, 2.5])",
    "x = Var(dom=[None])",
    "x = Var(dom=object())",
    not_explicit("x = Var(dom=lambda i: range(4))"),
    "x = Var(dom=lambda: None)",
    "x = Var(1, 2, dom=range(3))",
    "x = Var(0, 1, dom=range(3))",
    "x = Var()",
    "x = Var(dom=None)",
    "x = Var(id='foo')",
])
def test_var_invalid_domain(run, declaration):
    assert_fails(run(declaration))


@pytest.mark.parametrize("declaration, name", [
    ("x = Var(dom=range(3))", "x"),
    ("my_variable_2 = Var(dom=range(3))", "my_variable_2"),
    ("x = Var(dom=range(3), id='foo')", "foo"),
    ("x = Var(dom=range(3), id='a_1')", "a_1"),
    ("x = Var(dom=range(3), id='')", "x"),
    ("x = Var(dom=range(3), id=None)", "x"),
    ("Var(dom=range(3), id='z')", "z"),
])
def test_var_identifier(run, declaration, name):
    assert list(declared_variables(run(declaration))) == [name]


@pytest.mark.parametrize("declaration", [
    "x = Var(dom=range(3), id='foo bar')",
    "x = Var(dom=range(3), id='x[0]')",
    "x = Var(dom=range(3), id='x-y')",
    "x = Var(dom=range(3), id=12)",
    "x = Var(dom=range(3), id=['a'])",
    "x = Var(dom=range(3), id='1x')",
    "x = Var(dom=range(3), id='_x')",
    "x = Var(dom=range(3), id='é')",
    "Var(dom=range(3))",
    "x, y = Var(dom=range(3)), Var(dom=range(3))",
    "x = Var(dom=range(3))\nx = Var(dom=range(3))",
    "x = Var(dom=range(3), id='y')\ny = Var(dom=range(3))",
])
def test_var_invalid_identifier(run, declaration):
    assert_fails(run(declaration))


def test_var_comment(run):
    r = run("""
        # the number of items
        x = Var(dom=range(3))
    """)
    assert r.xml.find("variables/var").get("note") == "the number of items"


@pytest.mark.parametrize("dom, values", [
    ("{0, 3, 6}", [0, 3, 6]),
    ("range(-2, 2)", range(-2, 2)),
    ("{'red', 'green', 'blue'}", ["red", "green", "blue"]),
    ("{7}", [7]),
])
def test_var_solutions(run, solver, request, dom, values):
    if isinstance(values[0], str):
        bug_for(request, "COSOCO", COSOCO_SYMBOLIC)
    r = run(f"""
        x = Var(dom={dom})
        y = Var(dom={dom})
        satisfy(x != y)
    """, solver=solver)
    assert_solutions(r, brute_force([values, values], lambda x, y: x != y))


# ------------------------------------------------------------------------------------------------------- VarArray()

def _cells(name, *sizes):
    return [name + "".join("[" + str(i) + "]" for i in t) for t in product(*(range(s) for s in sizes))]


@pytest.mark.parametrize("size, cells", [
    ("3", _cells("x", 3)),
    ("1", _cells("x", 1)),
    ("[4]", _cells("x", 4)),
    ("[2, 3]", _cells("x", 2, 3)),
    ("(2, 3)", _cells("x", 2, 3)),
    ("[1, 1]", _cells("x", 1, 1)),
    ("[2, 2, 2]", _cells("x", 2, 2, 2)),
    ("range(3)", _cells("x", 3)),
    ("[range(2), 3]", _cells("x", 2, 3)),
])
def test_vararray_size(run, size, cells):
    assert sorted(declared_variables(run(f"x = VarArray(size={size}, dom=range(2))"))) == sorted(cells)


@pytest.mark.parametrize("size", [
    "0",
    "[2, 0]",
    not_explicit("2.0"),
    "'3'",
    not_explicit("None"),
    not_explicit("[]"),
    "[3, 'a']",
    not_explicit("range(0)"),
    not_explicit("range(1, 3)"),
    "-1",
    "[2, -1]",
    "[-2, 3]",
])
def test_vararray_invalid_size(run, size):
    assert_fails(run(f"x = VarArray(size={size}, dom=range(2))"))


@pytest.mark.parametrize("dom, values", [
    ("range(4)", [0, 1, 2, 3]),
    ("range(-5, -2)", [-5, -4, -3]),
    ("{0, 1}", [0, 1]),
    ("4", [0, 1, 2, 3]),
    ("[0, 0, 1]", [0, 1]),
    ("[3, 1, 2, 0]", [0, 1, 2, 3]),
    ("[0, 2, 4]", [0, 2, 4]),
    ("(5, 6)", [5, 6]),
    ("frozenset({2, 9})", [2, 9]),
    ("[[1, 2], [5]]", [1, 2, 5]),
    ("{'a', 'b'}", ["a", "b"]),
    ("lambda i: [2, 0]", [0, 2]),
    ("lambda *t: {1, 4}", [1, 4]),
])
def test_vararray_domain(run, dom, values):
    assert declared_variables(run(f"x = VarArray(size=2, dom={dom})")) == {"x[0]": values, "x[1]": values}


@pytest.mark.parametrize("declaration", [
    "x = VarArray(size=2, dom=0)",
    not_explicit("x = VarArray(size=2, dom=set())"),
    not_explicit("x = VarArray(size=2, dom=[])"),
    "x = VarArray(size=2, dom={'a', 1})",
    "x = VarArray(size=2, dom=2.5)",
    "x = VarArray(size=2, dom=object())",
    not_explicit("x = VarArray(size=2, dom=lambda i: set())"),
    not_explicit("x = VarArray(size=2, dom=lambda i: [])"),
    "x = VarArray(size=2, dom=lambda: range(2))",
    "x = VarArray(size=2, dom=lambda i, j: range(2))",
    not_explicit("x = VarArray(size=[2, 3], dom=lambda i: range(2))"),
    "x = VarArray(size=[2, 3], dom=lambda i, j, k: range(2))",
    "x = VarArray(size=3)",
    "x = VarArray(size=3, dom=None)",
])
def test_vararray_invalid_domain(run, declaration):
    assert_fails(run(declaration))


def test_vararray_domain_depending_on_index(run):
    r = run("x = VarArray(size=3, dom=lambda i: {0, 5} if i == 0 else range(2))")
    assert declared_variables(r) == {"x[0]": [0, 5], "x[1]": [0, 1], "x[2]": [0, 1]}


def test_vararray_domain_depending_on_index_solutions(run, solver, request):
    bug_for(request, "ACE", "xcsp3team/ACE#11: ace fails (ArrayIndexOutOfBoundsException in STR0a) on AllDifferent with a variable whose domain is a single value")
    r = run("""
        x = VarArray(size=3, dom=lambda i: range(i + 1))
        satisfy(AllDifferent(x))
    """, solver=solver)
    assert_solutions(r, brute_force([range(1), range(2), range(3)], lambda *t: len(set(t)) == 3))


@pytest.mark.parametrize("dom", ["lambda i, j: range(i + j + 1)", "lambda *t: range(sum(t) + 1)"])
def test_vararray_domain_depending_on_indexes_solutions(run, solver, dom):
    r = run(f"""
        x = VarArray(size=[2, 2], dom={dom})
        satisfy(Sum(x) == 2)
    """, solver=solver)
    assert_solutions(r, brute_force([range(1), range(2), range(2), range(3)], lambda *t: sum(t) == 2))


def test_vararray_hole_solutions(run, solver):
    r = run("""
        x = VarArray(size=3, dom=lambda i: None if i == 1 else range(2))
        satisfy(x[0] != x[2])
    """, solver=solver)
    assert r.variables == ["x[0]", "x[2]"]
    assert_solutions(r, {(0, 1), (1, 0)})


@pytest.mark.parametrize("declaration", [
    "x = VarArray(size=3, dom=lambda i: None if i == 1 else range(2))",
    "from pycsp3.classes.main.variables import Domain\nx = VarArray([Domain(range(2)), None, Domain(range(2))])",
    "x = VarArray(size=3, dom=lambda i: None if i == 1 else range(i + 1))",
])
def test_vararray_hole_not_declared(run, declaration):
    assert sorted(declared_variables(run(declaration))) == ["x[0]", "x[2]"]


def test_vararray_positional_domains(run):
    r = run("""
        from pycsp3.classes.main.variables import Domain
        x = VarArray([Domain(range(2)), Domain({5, 7})])
    """)
    assert declared_variables(r) == {"x[0]": [0, 1], "x[1]": [5, 7]}


@pytest.mark.parametrize("declaration", [
    not_explicit("x = VarArray([range(2)])"),
    not_explicit("x = VarArray((Domain(range(2)),))"),
    not_explicit("x = VarArray([Domain(range(2))], size=1)"),
    not_explicit("x = VarArray([Domain(range(2))], dom=range(2))"),
    "x = VarArray([])",
])
def test_vararray_invalid_positional_domains(run, declaration):
    assert_fails(run("from pycsp3.classes.main.variables import Domain\n" + declaration))


def test_vararray_dom_border_solutions(run, solver):
    r = run("""
        x = VarArray(size=[3, 3], dom=range(3), dom_border={0})
        satisfy(Sum(x) == 2)
    """, solver=solver)
    domains = [[0] if i in (0, 2) or j in (0, 2) else range(3) for i in range(3) for j in range(3)]
    assert_solutions(r, brute_force(domains, lambda *t: sum(t) == 2))


def test_vararray_dom_border_with_lambda(run):
    r = run("x = VarArray(size=[3, 4], dom=lambda i, j: range(j + 2), dom_border={9})")
    expected = {cell: [9] for cell in _cells("x", 3, 4)}
    expected.update({"x[1][1]": [0, 1, 2], "x[1][2]": [0, 1, 2, 3]})
    assert declared_variables(r) == expected


@pytest.mark.parametrize("declaration", [
    not_explicit("x = VarArray(size=3, dom=range(5), dom_border={0})"),
    "x = VarArray(size=[3, 3], dom_border={0})",
    not_explicit("x = VarArray(size=[2, 2, 2], dom=range(2), dom_border={0})"),
])
def test_vararray_invalid_dom_border(run, declaration):
    assert_fails(run(declaration))


@pytest.mark.parametrize("size, dom, n_variables", [
    ("[2, [1, 3]]", "range(2)", 4),
    ("[3, [1, 0, 2]]", "range(2)", 3),
    ("[2, [1, 3]]", "lambda i, j: range(j + 2)", 4),
    ("[3, [2, 0, 1]]", "lambda i, j: {i, j + 5}", 3),
])
def test_vararray_variable_length(run, size, dom, n_variables):
    r = run(f"""
        x = VarArray(size={size}, dom={dom})
        print("variables", len([v for v in flatten(x) if v is not None]))
    """)
    assert "variables " + str(n_variables) in r.lines, r.report()


def test_vararray_variable_length_solutions(run, solver):
    r = run("""
        x = VarArray(size=[2, [1, 3]], dom=range(2))
        satisfy(Sum(x[1]) == x[0][0] + 1)
    """, solver=solver)
    assert r.variables == ["x[0][0]", "x[1][0]", "x[1][1]", "x[1][2]"]
    assert_solutions(r, brute_force([range(2)] * 4, lambda a, b, c, d: b + c + d == a + 1))


@pytest.mark.parametrize("declaration, names", [
    ("x = VarArray(size=3, dom=range(2), id='y')", _cells("y", 3)),
    ("x = VarArray(size=3, dom=range(2), id='')", _cells("x", 3)),
    ("x, y, z = VarArray(size=3, dom=range(2))", ["x", "y", "z"]),
    ("x = VarArray(size=2, dom=range(2))\nx_0 = Var(dom=range(2))", ["x[0]", "x[1]", "x_0"]),
])
def test_vararray_identifier(run, declaration, names):
    assert sorted(declared_variables(run(declaration))) == sorted(names)


@pytest.mark.parametrize("declaration", [
    "x = VarArray(size=3, dom=range(2), id='y z')",
    "x = VarArray(size=3, dom=range(2), id='y[0]')",
    "x = VarArray(size=3, dom=range(2), id=5)",
    "VarArray(size=3, dom=range(2))",
    "x = VarArray(size=3, dom=range(2))\nx = VarArray(size=3, dom=range(2))",
    "x = Var(dom=range(2))\nx = VarArray(size=3, dom=range(2))",
    "x = VarArray(size=2, dom=range(2))\ny = Var(dom=range(2), id='x')",
    "x, y = VarArray(size=[2, 2], dom=range(2))",
    "x, y = VarArray(size=2, dom=range(2), id='w')",
    "x, x = VarArray(size=2, dom=range(2))",
    "x, y, x = VarArray(size=3, dom=range(2))",
    "x, y = VarArray(size=3, dom=range(2))",
    "x, y, z = VarArray(size=2, dom=range(2))",
])
def test_vararray_invalid_identifier(run, declaration):
    assert_fails(run(declaration))


def test_vararray_individual_names_solutions(run, solver):
    r = run("""
        x, y = VarArray(size=2, dom=range(3))
        satisfy(x < y)
    """, solver=solver)
    assert r.variables == ["x", "y"]
    assert_solutions(r, brute_force([range(3)] * 2, lambda x, y: x < y))


@pytest.mark.parametrize("declaration, note, tags", [
    ("x = VarArray(size=2, dom=range(2), comment='hello')", "hello", None),
    ("# my comment\nx = VarArray(size=2, dom=range(2))", "my comment", None),
    ("# my comment\nx = VarArray(size=2, dom=range(2), comment='hello')", "hello", None),
    ("x = VarArray(size=2, dom=range(2), tags=['t1', 't2'])", None, "t1 t2"),
    ("x = VarArray(size=2, dom=range(2), tags='t1 t2')", None, "t1 t2"),
    ("x = VarArray(size=2, dom=range(2), comment='c', tags=['t'])", "c", "t"),
    ("x = VarArray(size=2, dom=range(2), tags=[])", None, None),
])
def test_vararray_comment_and_tags(run, declaration, note, tags):
    array = run(declaration).xml.find("variables/array")
    assert (array.get("note"), array.get("class")) == (note, tags)


@pytest.mark.parametrize("declaration", [
    "x = VarArray(size=2, dom=range(2), comment=12)",
    "x = VarArray(size=2, dom=range(2), comment=['a'])",
])
def test_vararray_invalid_comment(run, declaration):
    assert_fails(run(declaration))


def test_vararray_python_objects(run):
    r = run("""
        x = VarArray(size=[2, 3], dom=range(3))
        s = VarArray(size=2, dom={"a", "b"})
        print("types", type(x).__name__, type(x[0]).__name__, type(x[0][0]).__name__, type(s[0]).__name__)
        print("fields", x[1][2], x[1][2].id, x[1][2].dom, len(x), len(x[0]), s[1].dom)
        print("slices", type(x[0][1:]).__name__, x[0][1:], x[1][-1], type(x[0] + x[1]).__name__, len(x[0] + x[1]))
    """)
    assert "types ListVar ListVar VariableInteger VariableSymbolic" in r.lines
    assert "fields x[1][2] x[1][2] 0..2 2 3 a b" in r.lines
    assert "slices ListVar [x[0][1], x[0][2]] x[1][2] ListVar 6" in r.lines


def test_vararray_symbolic_solutions(run, solver, request):
    bug_for(request, "COSOCO", COSOCO_SYMBOLIC)
    r = run("""
        x = VarArray(size=3, dom={"red", "green", "blue"})
        satisfy(AllDifferent(x))
    """, solver=solver)
    colours = ["red", "green", "blue"]
    assert_solutions(r, brute_force([colours] * 3, lambda *t: len(set(t)) == 3))


# ----------------------------------------------------------------------------------------------- VarArrayMultiple()

def test_vararraymultiple_declaration(run):
    r = run("""
        p = VarArrayMultiple(size=2, fields={"a": range(3), "b": {5, 6}})
        q = VarArrayMultiple(size=[2, 2], fields={"c": lambda i, j: range(i + j + 1)})
    """)
    assert declared_variables(r) == {"p_a[0]": [0, 1, 2], "p_a[1]": [0, 1, 2], "p_b[0]": [5, 6], "p_b[1]": [5, 6],
                                     "q_c[0][0]": [0], "q_c[0][1]": [0, 1], "q_c[1][0]": [0, 1], "q_c[1][1]": [0, 1, 2]}
    assert [a.get("note") for a in r.xml.find("variables")] == ["field a of p", "field b of p", "field c of q"]


def test_vararraymultiple_python_objects(run):
    r = run("""
        p = VarArrayMultiple(size=2, fields={"a": range(3), "b": {5, 6}})
        print("cell", p[0].a, p[0].b, p[1].a)
        print("fields", p.a, p.b)
        print("same", p[1].a is p.a[1])
    """)
    assert "cell p_a[0] p_b[0] p_a[1]" in r.lines
    assert "fields [p_a[0], p_a[1]] [p_b[0], p_b[1]]" in r.lines
    assert "same True" in r.lines


@pytest.mark.parametrize("declaration", [
    not_explicit("p = VarArrayMultiple(size=2, fields={'a': range(3), 1: range(2)})"),
    not_explicit("p = VarArrayMultiple(size=2, fields=['a', 'b'])"),
    not_explicit("p = VarArrayMultiple(size=2, fields=None)"),
    "p = VarArrayMultiple(size=0, fields={'a': range(3)})",
    "p = VarArrayMultiple(size='2', fields={'a': range(3)})",
    "p = VarArrayMultiple(size=2, fields={'a b': range(3)})",
    not_explicit("p = VarArrayMultiple(size=2, fields={'a': set()})"),
    "p = VarArrayMultiple(fields={'a': range(3)})",
    "p = VarArrayMultiple(size=2)",
    "p = VarArrayMultiple(2, {'a': range(3)})",
    "p = VarArrayMultiple(size=2, fields={})",
])
def test_vararraymultiple_invalid(run, declaration):
    assert_fails(run(declaration))


def test_vararraymultiple_solutions(run, solver):
    r = run("""
        p = VarArrayMultiple(size=2, fields={"a": range(3), "b": range(2)})
        satisfy(
            p[0] == p[1],
            p[0].a > p[0].b
        )
    """, solver=solver)
    assert r.variables == ["p_a[0]", "p_a[1]", "p_b[0]", "p_b[1]"]
    assert_solutions(r, brute_force([range(3), range(3), range(2), range(2)], lambda a0, a1, b0, b1: a0 == a1 and b0 == b1 and a0 > b0))


# ------------------------------------------------------------------------------------------------------------ var()

def test_var_function(run):
    r = run("""
        x = Var(dom=range(3))
        y = VarArray(size=2, dom=range(3))
        z = Var(dom=range(3), id="zz")
        print("found", var("x") is x, var("y[1]") is y[1], var("zz") is z, var("y"))
    """)
    assert "found True True True [y[0], y[1]]" in r.lines, r.report()


@pytest.mark.parametrize("call", ["var('u')", "var('X')", "var('')", not_explicit("var(12)"), not_explicit("var(None)"), not_explicit("var(x)"), "var('x[5]')"])
def test_var_function_invalid(run, call):
    assert_fails(run("x = VarArray(size=2, dom=range(3))\n" + call))


def test_var_function_in_constraints(run, solver):
    r = run("""
        x = Var(dom=range(10))
        Var(dom=range(10), id="z")
        satisfy(
            var("x") >= 3,
            var("z") < var("x") - 6
        )
    """, solver=solver)
    assert_solutions(r, brute_force([range(10)] * 2, lambda x, z: x >= 3 and z < x - 6))


def test_var_function_array_indexed_by_variable(run, solver):
    r = run("""
        y = VarArray(size=3, dom=range(3))
        i = Var(dom=range(3))
        satisfy(
            var("y")[i] == 2,
            AllDifferent(y)
        )
    """, solver=solver)
    assert_solutions(r, brute_force([range(3)] * 4, lambda a, b, c, i: len({a, b, c}) == 3 and (a, b, c)[i] == 2))


# -------------------------------------------------------------------------------------------------------- Variable

def test_variable_fields(run, solver):
    r = run(f"""
        x = VarArray(size=2, dom=range(3))
        satisfy(x[0] + 1 == x[1], x[1] == 2)
        print("before", x[0].id, x[0].dom, x[0].value, x[0].values)
        if solve(solver={solver}) is SAT:
            print("after", x[0].value, x[1].value, x[0].values, x[1].values, x.values)
    """)
    assert "before x[0] 0..2 None []" in r.lines, r.report()
    assert "after 1 2 [1] [2] [1, 2]" in r.lines, r.report()


def test_variable_values_of_all_solutions(run, solver):
    r = run(f"""
        x = VarArray(size=2, dom=range(3))
        satisfy(x[0] < x[1])
        if solve(solver={solver}, sols=ALL) is SAT:
            print("all", sorted(zip(x[0].values, x[1].values)))
    """)
    assert "all [(0, 1), (0, 2), (1, 2)]" in r.lines, r.report()


def test_variable_name(run):
    r = run("""
        x = VarArray(size=3, dom=range(5))
        x[0].name("first")
        x[2].name("last")
        print("found", var("first") is x[0], var("last") is x[2])
    """)
    assert "found True True" in r.lines, r.report()


@pytest.mark.parametrize("call", [
    "x[0].name('x')",
    "x[0].name('x[1]')",
    "x[0].name('bad name')",
    "x[0].name('')",
    "x[0].name('2nd')",
    "x[0].name(5)",
    "x[0].name(None)",
    "x[0].name('a')\nx[1].name('a')",
])
def test_variable_invalid_name(run, call):
    assert_fails(run("x = VarArray(size=3, dom=range(5))\n" + call))


def test_variable_name_in_constraints(run, solver):
    r = run("""
        x = VarArray(size=2, dom=range(3))
        x[0].name("first")
        satisfy(var("first") > x[1])
    """, solver=solver)
    assert_solutions(r, brute_force([range(3)] * 2, lambda a, b: a > b))


# ------------------------------------------------------------------------------------------------- VariableInteger

@pytest.mark.parametrize("expression, allowed", [
    pytest.param("x.among(1, 3)", {1, 3}, id="among(1, 3)"),
    pytest.param("x.among([1, 3])", {1, 3}, id="among([1, 3])"),
    pytest.param("x.among((1, 3))", {1, 3}, id="among((1, 3))"),
    pytest.param("x.among({1, 3})", {1, 3}, id="among({1, 3})"),
    pytest.param("x.among(range(1, 4))", {1, 2, 3}, id="among(range(1, 4))"),
    pytest.param("x.among(2)", {2}, id="among(2)"),
    pytest.param("x.among(1, 1)", {1}, id="among(1, 1)"),
    pytest.param("x.among(2, 9)", {2}, id="among(2, 9)"),
    pytest.param("x.among(-1, 0)", {0}, id="among(-1, 0)"),
    pytest.param("x.among(1.5, 2)", {2}, id="among(1.5, 2)"),
    pytest.param("x.among(range(5))", {0, 1, 2, 3, 4}, id="among(range(5))"),
    pytest.param("x.among(7, 8)", set(), id="among(7, 8)"),
    pytest.param("x.among()", set(), id="among()"),
    pytest.param("[x.among(7, 8), x.among(1, 3)]", set(), id="[among(7, 8), among(1, 3)]"),
    pytest.param("x.not_among(1, 3)", {0, 2, 4}, id="not_among(1, 3)"),
    pytest.param("x.not_among([1, 3])", {0, 2, 4}, id="not_among([1, 3])"),
    pytest.param("x.not_among(range(1, 4))", {0, 4}, id="not_among(range(1, 4))"),
    pytest.param("x.not_among(2)", {0, 1, 3, 4}, id="not_among(2)"),
    pytest.param("x.not_among(2, 9)", {0, 1, 3, 4}, id="not_among(2, 9)"),
    pytest.param("x.not_among(range(5))", set(), id="not_among(range(5))"),
    pytest.param("x.not_among(7, 8)", {0, 1, 2, 3, 4}, id="not_among(7, 8)"),
    pytest.param("x.not_among()", {0, 1, 2, 3, 4}, id="not_among()"),
])
def test_among(run, solver, expression, allowed):
    r = run(f"""
        x = Var(dom=range(5))
        y = Var(dom=range(2))
        satisfy(
            {expression},
            y == 1  # so that the model has a constraint, even when the expression is simplified into true
        )
    """, solver=solver)
    assert_solutions(r, {(v, 1) for v in allowed})


@pytest.mark.parametrize("code", [
    "x = Var(dom={'a', 'b'})\nsatisfy(x.among('a'))",
    not_explicit("x = Var(dom=range(5))\ny = Var(dom=range(5))\nsatisfy(x.among(y))"),
])
def test_among_invalid(run, code):
    assert_fails(run(code))


# ---------------------------------------------------------------------------------------------------------- Domain

@pytest.mark.parametrize("domain, text, smallest, greatest, values", [
    ("Domain(range(5))", "0..4", 0, 4, [0, 1, 2, 3, 4]),
    ("Domain(range(-3, 0))", "-3..-1", -3, -1, [-3, -2, -1]),
    ("Domain({1, 3, 5, 6, 7})", "1 3 5 6 7", 1, 7, [1, 3, 5, 6, 7]),
    ("Domain(3, range(5, 8), 1)", "1 3 5..7", 1, 7, [1, 3, 5, 6, 7]),
    ("Domain(range(5), 3)", "0..4", 0, 4, [0, 1, 2, 3, 4]),
    ("Domain(range(5), 3, 4)", "0..4", 0, 4, [0, 1, 2, 3, 4]),
    ("Domain(3, range(3, 6))", "3..5", 3, 5, [3, 4, 5]),
    ("Domain(range(5), range(3, 8), range(10, 13))", "0..7 10..12", 0, 12, [0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12]),
    ("Domain(range(5), 5)", "0..4 5", 0, 5, [0, 1, 2, 3, 4, 5]),
    ("Domain(-2, -5)", "-5 -2", -5, -2, [-5, -2]),
    ("Domain(7)", "7", 7, 7, [7]),
    ("Domain([4, 5, 6])", "4 5 6", 4, 6, [4, 5, 6]),
    ("Domain({'b', 'a'})", "a b", "a", "b", ["a", "b"]),
])
def test_domain_methods(run, domain, text, smallest, greatest, values):
    r = run(f"""
        from pycsp3.classes.main.variables import Domain
        d = {domain}
        print("str", d)
        print("smallest", repr(d.smallest_value()))
        print("greatest", repr(d.greatest_value()))
        print("all_values", list(d.all_values()))
        print("iteration", [v for v in d])
        print("indexing", repr(d[0]), repr(d[-1]))
    """)
    assert "str " + text in r.lines, r.report()
    assert "smallest " + repr(smallest) in r.lines
    assert "greatest " + repr(greatest) in r.lines
    assert "all_values " + str(values) in r.lines
    assert "iteration " + str(values) in r.lines
    assert "indexing " + repr(values[0]) + " " + repr(values[-1]) in r.lines


def test_domain_of_variable(run):
    r = run("""
        x = Var(dom={1, 3, 5, 6, 7})
        y = Var(dom=range(1, 10))
        print("odd", [v for v in x.dom if v % 2 == 1])
        print("bounds", y.dom.smallest_value(), y.dom.greatest_value(), y.dom.all_values())
        print("equality", x.dom == y.dom, y.dom == Var(dom=range(1, 10), id="z").dom)
    """)
    assert "odd [1, 3, 5, 7]" in r.lines, r.report()
    assert "bounds 1 9 range(1, 10)" in r.lines
    assert "equality False True" in r.lines


def test_domain_overlapping_intervals(run):
    r = run("""
        from pycsp3.classes.main.variables import Domain
        d = Domain(range(5), range(3, 8))
        print("values", list(d.all_values()), d.smallest_value(), d.greatest_value())
    """)
    assert "values [0, 1, 2, 3, 4, 5, 6, 7] 0 7" in r.lines, r.report()


@pytest.mark.parametrize("domain", ["Domain()", "Domain(2.5)", "Domain(None)", "Domain(0, 'a')", "Domain(set())", "Domain(range(3))[5]"])
def test_domain_invalid(run, domain):
    assert_fails(run("from pycsp3.classes.main.variables import Domain\nd = " + domain))


# --------------------------------------------------------------------------------------------------------- ListVar

def test_listvar_neighbourhood(run):
    r = run("""
        x = VarArray(size=[3, 3], dom=range(2))
        print("at_border", [x.at_border(i, j) for i in range(3) for j in range(3)])
        print("around", x.around(0, 0), x.around(1, 1))
        print("beside", x.beside(0, 0), x.beside(1, 1))
        print("cross", x.cross(0, 0), x.cross(2, 2))
        print("types", type(x.around(1, 1)).__name__, type(x.beside(1, 1)).__name__, type(x.cross(1, 1)).__name__)
    """)
    assert "at_border [True, True, True, True, False, True, True, True, True]" in r.lines, r.report()
    assert "around [x[0][1], x[1][0], x[1][1]] [x[0][0], x[0][1], x[0][2], x[1][0], x[1][2], x[2][0], x[2][1], x[2][2]]" in r.lines
    assert "beside [x[0][1], x[1][0]] [x[1][0], x[1][2], x[0][1], x[2][1]]" in r.lines
    assert "cross [x[0][0], x[0][1], x[1][0]] [x[2][2], x[2][1], x[1][2]]" in r.lines
    assert "types ListVar ListVar ListVar" in r.lines


def test_listvar_neighbourhood_of_small_arrays(run):
    r = run("""
        x = VarArray(size=[1, 1], dom=range(2))
        y = VarArray(size=[2, 4], dom=range(2))
        print("single", x.at_border(0, 0), x.around(0, 0), x.beside(0, 0), x.cross(0, 0))
        print("rectangle", y.at_border(1, 2), y.around(1, 3), y.beside(0, 3), y.cross(1, 0))
    """)
    assert "single True [] [] [x[0][0]]" in r.lines, r.report()
    assert "rectangle True [y[0][2], y[0][3], y[1][2]] [y[0][2], y[1][3]] [y[1][0], y[1][1], y[0][0]]" in r.lines


@pytest.mark.parametrize("call", [
    not_explicit("x.at_border(3, 0)"),
    not_explicit("x.at_border(0, -1)"),
    not_explicit("x.around(-1, 0)"),
    not_explicit("x.beside(0, 3)"),
    not_explicit("x.cross(3, 3)"),
    "y.at_border(0, 0)",
    "y.around(0, 0)",
    "y.beside(0, 0)",
    "y.cross(0, 0)",
])
def test_listvar_neighbourhood_invalid(run, call):
    assert_fails(run("x = VarArray(size=[3, 3], dom=range(2))\ny = VarArray(size=3, dom=range(2))\n" + call))


def test_listvar_around_solutions(run, solver):
    r = run("""
        x = VarArray(size=[3, 3], dom=range(2))
        satisfy(Sum(x.around(1, 1)) == 3)
    """, solver=solver)
    assert_solutions(r, brute_force([range(2)] * 9, lambda *t: sum(t) - t[4] == 3))


def test_listvar_cross_solutions(run, solver):
    r = run("""
        x = VarArray(size=[2, 2], dom=range(2))
        satisfy(Sum(x.cross(0, 0)) == 2, Sum(x.beside(1, 1)) == 1)
    """, solver=solver)
    assert_solutions(r, brute_force([range(2)] * 4, lambda a, b, c, d: a + b + c == 2 and b + c == 1))


def test_listvar_indexed_by_variable(run, solver):
    r = run("""
        x = VarArray(size=3, dom=range(3))
        i = Var(dom=range(3))
        satisfy(
            x[i] == 2,
            AllDifferent(x)
        )
    """, solver=solver)
    assert_solutions(r, brute_force([range(3)] * 4, lambda a, b, c, i: len({a, b, c}) == 3 and (a, b, c)[i] == 2))


@pytest.mark.parametrize("operator", ["<=", "<", ">=", ">"])
def test_listvar_lexicographic_comparison(run, solver, operator):
    r = run(f"""
        x = VarArray(size=2, dom=range(2))
        y = VarArray(size=2, dom=range(2))
        satisfy(x {operator} y)
    """, solver=solver)
    compare = {"<=": lambda u, v: u <= v, "<": lambda u, v: u < v, ">=": lambda u, v: u >= v, ">": lambda u, v: u > v}[operator]
    assert_solutions(r, brute_force([range(2)] * 4, lambda a, b, c, d: compare((a, b), (c, d))))


# --------------------------------------------------------------------------------------------------------- ListInt

def test_listint_python_objects(run):
    r = run("""
        t = cp_array([3, 5, 7])
        print("types", type(t).__name__, type(t[1:]).__name__, type(t + [1]).__name__)
        print("values", t, t[1:], t + [1], t[-1])
    """)
    assert "types ListInt ListInt ListInt" in r.lines, r.report()
    assert "values [3, 5, 7] [5, 7] [3, 5, 7, 1] 7" in r.lines


def test_listint_from_data(run):
    r = run("""
        print("types", type(data.t).__name__, type(data.m).__name__, type(data.m[0]).__name__)
    """, args=["-data=data.json"], files={"data.json": '{"t": [3, 5, 7], "m": [[1, 2], [3, 4]]}'})
    assert "types ListInt ListInt ListInt" in r.lines, r.report()


def test_listint_indexed_by_variable(run, solver):
    r = run("""
        t = cp_array([3, 5, 7])
        i = Var(dom=range(3))
        v = Var(dom=range(10))
        satisfy(t[i] == v)
    """, solver=solver)
    assert_solutions(r, brute_force([range(3), range(10)], lambda i, v: [3, 5, 7][i] == v))


@pytest.mark.parametrize("expression", ["cp_array([1, 2, 3]) * x == 3", "x * cp_array([1, 2, 3]) == 3"])
def test_listint_scalar_product(run, solver, expression):
    r = run(f"""
        x = VarArray(size=3, dom=range(2))
        satisfy({expression})
    """, solver=solver)
    assert_solutions(r, brute_force([range(2)] * 3, lambda a, b, c: a + 2 * b + 3 * c == 3))
