"""
Tests of the constraint Table (Extension) of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#Table): the operators 'in' and 'not in' on tuples of variables,
and the function Table(), with ordinary, starred, hybrid and symbolic tables.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
"""

from itertools import product

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

COSOCO_SYMBOLIC = "xcsp3team/cosoco#71: cosoco does not handle symbolic variables (XCSP3Core expected type=integer)"
COSOCO_HOLES = "xcsp3team/cosoco#72: cosoco gives individually the values of the variables involved in no constraint, and pycsp3 fails when recording those of holes"

X3 = "x = VarArray(size=3, dom=range(4))\n"
D3 = [range(4)] * 3
X6 = "x = VarArray(size=3, dom=range(6))\n"
D6 = [range(6)] * 3

# Known bugs (each bug is reported in the issue given at the start of its reason)
ALL = ("ACE", "CHOCO", "COSOCO")
INVALID = "#106: invalid tables are reported without explicit message, or accepted"
ACE_CONFLICTS = "xcsp3team/ACE#14: ACE fails on a table of conflicts with the symbol *"
ACE_HYBRID = "xcsp3team/ACE#15: ACE finds wrong solutions with some hybrid tables of level 2"
COSOCO_HYBRID = "xcsp3team/cosoco#76: cosoco finds wrong solutions or fails on hybrid tables"

# For each group of tests and each constraint (as written in the tests), the known bugs: pairs (solvers, reason)
KNOWN = {
    ("starred", "x not in {(0, ANY, 2), (ANY, 3, ANY)}"): [("ACE", ACE_CONFLICTS)],
    ("starred", "Table(scope=x, conflicts=[(ANY, 1, ANY)])"): [("ACE", ACE_CONFLICTS)],
    ("hybrid", "x not in [(lt(2), ANY, ge(4))]"): [("ACE", ACE_CONFLICTS)],
    ("kept", "x in [(0, 0, 0), (gt(4), ANY, ANY), (ANY, range(1, 3), le(col(1)))]"): [("ACE", ACE_HYBRID)],
    ("kept", "x in [(eq(col(1) + 1), ANY, lt(col(1) + 3))]"): [("ACE", ACE_HYBRID)],
    ("kept", "x in [(ne(col(1)), ne(col(2)), ne(col(0)))]"): [("ACE", ACE_HYBRID)],
}

# The cases that a solver says it does not handle (not reported): for each group of tests and each constraint, the solvers and the reasons
STARS = {"CHOCO": "CHOCO does not handle the symbol * in tables of conflicts (Negative tables with symbol * are not supported)",
         "COSOCO": "cosoco does not handle the symbol * in tables of conflicts (Extension constraint with star and conflict tuples is not yet supported)"}
ACE_UNIMPLEMENTED = "ACE does not implement this hybrid table (not implemented)"
SKIPPED = {
    ("starred", "x not in {(0, ANY, 2), (ANY, 3, ANY)}"): STARS,
    ("starred", "Table(scope=x, conflicts=[(ANY, 1, ANY)])"): STARS,
    ("hybrid", "x not in [(lt(2), ANY, ge(4))]"): STARS,
    ("symbolic", "s in [('a', ANY), ('c', 'b')]"): {"CHOCO": "CHOCO does not handle the symbol * in symbolic tables"},
    ("kept", "x in [(ANY, ANY, eq(col(0) + col(1)))]"): {"ACE": ACE_UNIMPLEMENTED},
    ("kept", "x not in [(ANY, ANY, eq(col(0) + col(1)))]"): {"ACE": ACE_UNIMPLEMENTED},
    ("kept", "x not in [(lt(2), ANY, ge(4))]"): {"ACE": "ACE does not implement negative hybrid tables (unimplemented case for negative hybrid tables)"},
}
CHOCO_HYBRID = "CHOCO does not handle hybrid tables (which are not part of XCSP3-core)"


def known(request, group, constraint):
    """Marks (or skips) the running test according to the known bugs of the specified group of tests and constraint."""
    solver = request.node.callspec.params.get("solver")
    if solver == "CHOCO" and group == "kept":
        pytest.skip(CHOCO_HYBRID)
    if solver in SKIPPED.get((group, constraint), {}):
        pytest.skip(SKIPPED[(group, constraint)][solver])
    for solvers, reason in KNOWN.get((group, constraint), []) + ([("COSOCO", COSOCO_HYBRID)] if group == "kept" else []):
        bug_for(request, solvers, reason)


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


# --------------------------------------------------------------------------------------------------- ordinary tables

T = {(0, 1, 2), (0, 2, 3), (1, 1, 3), (2, 3, 0)}


@pytest.mark.parametrize("constraint, predicate", [
    ("(x[0], x[1], x[2]) in {(0, 1, 2), (0, 2, 3), (1, 1, 3), (2, 3, 0)}", lambda *t: t in T),
    ("x in {(0, 1, 2), (0, 2, 3), (1, 1, 3), (2, 3, 0)}", lambda *t: t in T),
    ("x in [(0, 1, 2), (0, 2, 3), (1, 1, 3), (2, 3, 0)]", lambda *t: t in T),
    ("x in [[0, 1, 2], [0, 2, 3], [1, 1, 3], [2, 3, 0]]", lambda *t: t in T),
    ("x in ((0, 1, 2), (0, 2, 3), (1, 1, 3), (2, 3, 0))", lambda *t: t in T),
    ("tuple(x) in {(0, 1, 2), (3, 3, 3)}", lambda *t: t in {(0, 1, 2), (3, 3, 3)}),
    ("[x[0], x[1], x[2]] in {(0, 1, 2), (3, 3, 3)}", lambda *t: t in {(0, 1, 2), (3, 3, 3)}),
    ("(x[2], x[0], x[1]) in {(0, 1, 2), (3, 3, 3)}", lambda a, b, c: (c, a, b) in {(0, 1, 2), (3, 3, 3)}),
    ("x in [(1, 1, 1)]", lambda *t: t == (1, 1, 1)),
    ("x in [(0, 1, 2), (0, 1, 2), (1, 1, 1)]", lambda *t: t in {(0, 1, 2), (1, 1, 1)}),
    ("x in {(0, 1, 2), (5, 1, 2), (1, -1, 1)}", lambda *t: t == (0, 1, 2)),  # tuples outside the domains
    ("x in {(i, i, i) for i in range(4)}", lambda a, b, c: a == b == c),
    ("x in [(i, (i + 1) % 4, 0) for i in range(4)]", lambda a, b, c: b == (a + 1) % 4 and c == 0),
    ("x in [t for t in product(range(4), repeat=3) if sum(t) == 5]", lambda *t: sum(t) == 5),
    ("(x[0], x[1], x[2]) not in {(0, 1, 2), (0, 2, 3), (1, 1, 3), (2, 3, 0)}", lambda *t: t not in T),
    ("x not in [[0, 1, 2], [3, 3, 3]]", lambda *t: t not in {(0, 1, 2), (3, 3, 3)}),
    ("x not in {(a, b, c) for a in range(4) for b in range(4) for c in range(4) if a != b}", lambda a, b, c: a == b),
    ("Table(scope=x, supports={(0, 1, 2), (0, 2, 3), (1, 1, 3), (2, 3, 0)})", lambda *t: t in T),
    ("Table(scope=[x[0], x[1], x[2]], supports=[(0, 1, 2), (3, 3, 3)])", lambda *t: t in {(0, 1, 2), (3, 3, 3)}),
    ("Table(scope=x, conflicts={(0, 1, 2), (0, 2, 3), (1, 1, 3), (2, 3, 0)})", lambda *t: t not in T),
    ("Table(scope=(x[1], x[2], x[0]), conflicts=[(0, 0, 0)])", lambda a, b, c: (b, c, a) != (0, 0, 0)),
])
def test_ordinary_tables(run, solver, request, constraint, predicate):
    known(request, "ordinary", constraint)
    check(run, solver, "from itertools import product\n" + X3 + f"satisfy({constraint})", D3, predicate)


def test_tables_of_a_matrix(run, solver):
    r = run("""
        x = VarArray(size=[2, 2], dom=range(3))
        satisfy(
            x[0] in {(0, 1), (1, 2), (2, 0)},
            [x[1][j] for j in range(2)] not in {(0, 0), (1, 1)},
            (x[0][0], x[1][1]) in [(0, 0), (1, 2), (2, 2)]
        )
    """, solver=solver)
    assert_solutions(r, brute_force([range(3)] * 4, lambda a, b, c, d: (a, b) in {(0, 1), (1, 2), (2, 0)} and (c, d) not in {(0, 0), (1, 1)} and (a, d) in {(0, 0), (1, 2), (2, 2)}))


def test_several_tables(run, solver):
    r = run(X3 + """
satisfy(
    (x[0], x[1]) in {(0, 1), (1, 2), (2, 3)},
    (x[1], x[2]) in {(1, 0), (2, 0), (3, 3)},
    (x[0], x[2]) not in {(0, 0)}
)
""", solver=solver)
    assert_solutions(r, brute_force(D3, lambda a, b, c: (a, b) in {(0, 1), (1, 2), (2, 3)} and (b, c) in {(1, 0), (2, 0), (3, 3)} and (a, c) != (0, 0)))


def test_large_table_given_by_lists(run, solver):
    # more than 100 tuples, given as lists
    r = run(X6 + "satisfy(x in [[a, b, c] for a in range(6) for b in range(6) for c in range(6) if a + b + c != 5])", solver=solver)
    assert_solutions(r, brute_force(D6, lambda a, b, c: a + b + c != 5))


@pytest.mark.parametrize("constraints, predicate", [
    ("(x[0], x[1]) in {(0, -1), (1, 1)}, (x[2], x[3]) in {(0, -2), (1, 1)}", lambda a, b, c, d: (a, b) in {(0, -1), (1, 1)} and (c, d) in {(0, -2), (1, 1)}),
    ("(x[0], x[1]) in [(-1, 0), (3, 3)], (x[2], x[3]) in [(-2, 0), (3, 3)]", lambda a, b, c, d: (a, b) in {(-1, 0), (3, 3)} and (c, d) in {(-2, 0), (3, 3)}),
    ("x[0] in [-1, 2], x[1] in [-2, 2], x[2] == 0, x[3] == 0", lambda a, b, c, d: a in (-1, 2) and b in (-2, 2) and c == d == 0),
])
def test_tables_with_the_same_hash(run, solver, request, constraints, predicate):
    # in Python, hash(-1) == hash(-2): two different tables may have the same hash
    check(run, solver, f"x = VarArray(size=4, dom=range(-3, 4))\nsatisfy({constraints})", [range(-3, 4)] * 4, predicate)


@pytest.mark.parametrize("constraints, texts", [
    ("(x[0], x[1]) in {(0, -1), (1, 1)}, (x[2], x[3]) in {(0, -2), (1, 1)}", ["(0,-1)(1,1)", "(0,-2)(1,1)"]),
    ("x[0] in [-1, 2], x[1] in [-2, 2]", ["-1 2", "-2 2"]),
    ("(x[0], x[1]) not in {(0, -1)}, (x[2], x[3]) not in {(0, -2)}", ["(0,-1)", "(0,-2)"]),
])
def test_tables_with_the_same_hash_xcsp3(run, constraints, texts):
    r = run(f"x = VarArray(size=4, dom=range(-3, 4))\nsatisfy({constraints})")
    assert r.ok, r.report()
    assert [e.find("supports" if e.find("supports") is not None else "conflicts").text.strip() for e in r.xml.iter("extension")] == texts, r.report()


# ------------------------------------------------------------------------------------------------------ unary tables

@pytest.mark.parametrize("constraint, predicate", [
    ("x in [1, 3]", lambda x: x in (1, 3)),
    ("x in (1, 3)", lambda x: x in (1, 3)),
    ("x in {1, 3}", lambda x: x in (1, 3)),
    ("x in range(-1, 2)", lambda x: x in range(-1, 2)),
    ("x in [-1, 7]", lambda x: x == -1),
    ("x in [(1,), (2,)]", lambda x: x in (1, 2)),
    ("x not in [1, 3]", lambda x: x not in (1, 3)),
    ("x not in {1, 3}", lambda x: x not in (1, 3)),
    ("x not in range(0, 3)", lambda x: x not in range(0, 3)),
    ("Table(scope=[x], supports=[1, 2])", lambda x: x in (1, 2)),
    ("Table(scope=x, supports=[1, 2])", lambda x: x in (1, 2)),
    ("Table(scope=[x], conflicts=[0, 3])", lambda x: x not in (0, 3)),
])
def test_unary_tables(run, solver, constraint, predicate):
    check(run, solver, f"x = Var(dom=range(-3, 4))\nsatisfy({constraint})", [range(-3, 4)], predicate)


# ---------------------------------------------------------------------------------------------------- empty tables

@pytest.mark.parametrize("constraint", ["x in []", "x in set()", "Table(scope=x, supports=[])"])
def test_empty_supports(run, solver, constraint):
    # no tuple is a support: either the model is unsatisfiable, or an error is reported
    r = run(X3 + f"satisfy({constraint}, x[0] != 1)", solver=solver)
    if r.ok:
        assert_solutions(r, set())
    else:
        assert_fails(r)


@pytest.mark.parametrize("constraint", ["x not in []", "x not in set()", "Table(scope=x, conflicts=[])"])
def test_empty_conflicts(run, solver, request, constraint):
    # no tuple is a conflict: the constraint always holds
    known(request, "empty", constraint)
    check(run, solver, X3 + f"satisfy({constraint}, x[0] != 1)", D3, lambda a, b, c: a != 1)


# --------------------------------------------------------------------------------------------------- starred tables

@pytest.mark.parametrize("constraint, predicate", [
    ("x in {(0, ANY, 2), (ANY, 3, ANY), (1, 1, 1)}", lambda a, b, c: (a, c) == (0, 2) or b == 3 or (a, b, c) == (1, 1, 1)),
    ("x in [(ANY, ANY, ANY)]", lambda a, b, c: True),
    ("x in [(ANY, ANY, 0), (0, 0, 0)]", lambda a, b, c: c == 0),
    ("x not in {(0, ANY, 2), (ANY, 3, ANY)}", lambda a, b, c: not ((a, c) == (0, 2) or b == 3)),
    ("Table(scope=x, supports=[(ANY, 1, 2)])", lambda a, b, c: (b, c) == (1, 2)),
    ("Table(scope=x, conflicts=[(ANY, 1, ANY)])", lambda a, b, c: b != 1),
])
def test_starred_tables(run, solver, request, constraint, predicate):
    known(request, "starred", constraint)
    check(run, solver, X3 + f"satisfy({constraint}, x[0] != 1)", D3, lambda a, b, c: predicate(a, b, c) and a != 1)


# ---------------------------------------------------------------------------------------------------- hybrid tables

HYBRID = [
    ("x in [(range(2, 4), gt(3), ANY)]", lambda a, b, c: a in (2, 3) and b > 3),
    ("x in [(lt(2), ANY, ge(4))]", lambda a, b, c: a < 2 and c >= 4),
    ("x in [(5, ne(2), le(1))]", lambda a, b, c: a == 5 and b != 2 and c <= 1),
    ("x in [({1, 3}, ANY, {0, 5})]", lambda a, b, c: a in (1, 3) and c in (0, 5)),
    ("x in [((1, 3), ANY, (0, 5))]", lambda a, b, c: a in (1, 3) and c in (0, 5)),
    ("x in [(4, complement(range(2, 5)), complement(1, 3, 5))]", lambda a, b, c: a == 4 and b not in range(2, 5) and c not in (1, 3, 5)),
    ("x in {(le(1), eq(3), 2), (0, 0, 0)}", lambda a, b, c: (a <= 1 and b == 3 and c == 2) or (a, b, c) == (0, 0, 0)),
    ("x in [(ANY, eq(col(0) - 2), 2)]", lambda a, b, c: b == a - 2 and c == 2),
    ("x in [(1, col(2), ANY)]", lambda a, b, c: a == 1 and b == c),
    ("x in [(ANY, 1, gt(col(0) + 2))]", lambda a, b, c: b == 1 and c > a + 2),
    ("x in [(eq(col(1) + 1), ANY, lt(col(1) + 3))]", lambda a, b, c: a == b + 1 and c < b + 3),
    ("x in [(ANY, ANY, eq(col(0) + col(1)))]", lambda a, b, c: c == a + b),
    ("x in [(ne(col(1)), ne(col(2)), ne(col(0)))]", lambda a, b, c: a != b and b != c and c != a),
    ("x in [(0, 0, 0), (gt(4), ANY, ANY), (ANY, range(1, 3), le(col(1)))]", lambda a, b, c: (a, b, c) == (0, 0, 0) or a > 4 or (b in (1, 2) and c <= b)),
    ("x not in [(lt(2), ANY, ge(4))]", lambda a, b, c: not (a < 2 and c >= 4)),
    ("x not in [(ANY, ANY, eq(col(0) + col(1)))]", lambda a, b, c: c != a + b),
    ("Table(scope=x, supports=[(range(2, 4), gt(3), ANY)])", lambda a, b, c: a in (2, 3) and b > 3),
]


@pytest.mark.parametrize("constraint, predicate", HYBRID)
def test_hybrid_tables(run, solver, request, constraint, predicate):
    # by default, hybrid tables are converted into ordinary (or starred) tables
    known(request, "hybrid", constraint)
    check(run, solver, X6 + f"satisfy({constraint})", D6, predicate)


@pytest.mark.parametrize("constraint, predicate", [
    ("x in [(ne(col(1)), ne(col(2)), 3)]", lambda a, b, c: a != b and b != c and c == 3),  # a chain of restrictions
    ("x in [(eq(col(1) + 1), eq(col(2) + 1), ANY)]", lambda a, b, c: a == b + 1 and b == c + 1),
    ("x in [(lt(col(1)), lt(col(2)), gt(col(0) + 2))]", lambda a, b, c: a < b < c and c > a + 2),  # a cycle
    ("x in [(ANY, ne(col(2)), ne(col(1) - 1))]", lambda a, b, c: b != c and c != b - 1),
    ("x in [(eq(col(1) + col(2)), gt(col(0) - 4), ANY), (0, 0, 0)]", lambda a, b, c: (a == b + c and b > a - 4) or (a, b, c) == (0, 0, 0)),
    ("x not in [(ne(col(1)), ne(col(2)), ne(col(0)))]", lambda a, b, c: not (a != b and b != c and c != a)),
])
def test_hybrid_tables_with_restrictions_referring_to_restricted_columns(run, solver, constraint, predicate):
    # a restriction referring to a column with a restriction (e.g., in a chain or a cycle): the conversion enumerates the involved columns
    check(run, solver, X6 + f"satisfy({constraint})", D6, predicate)


@pytest.mark.parametrize("constraint, predicate", HYBRID)
def test_hybrid_tables_kept(run, solver, request, constraint, predicate):
    # with the option -keep_hybrid, hybrid tables are kept in the XCSP3 file
    known(request, "kept", constraint)
    check(run, solver, X6 + f"satisfy({constraint})", D6, predicate, args=["-keep_hybrid"])


# ------------------------------------------------------------------------------------------------ symbolic tables

@pytest.mark.parametrize("constraint, predicate", [
    ("s in {('a', 'b'), ('c', 'c')}", lambda u, v: (u, v) in {("a", "b"), ("c", "c")}),
    ("s in [('a', ANY), ('c', 'b')]", lambda u, v: u == "a" or (u, v) == ("c", "b")),
    ("s not in {('a', 'b'), ('b', 'a')}", lambda u, v: (u, v) not in {("a", "b"), ("b", "a")}),
    ("Table(scope=s, supports=[('b', 'b')])", lambda u, v: (u, v) == ("b", "b")),
    ("s[0] in ['a', 'c']", lambda u, v: u in ("a", "c") and u != v),
    ("s[1] not in ['a']", lambda u, v: v != "a" and u != v),
])
def test_symbolic_tables(run, solver, request, constraint, predicate):
    bug_for(request, "COSOCO", COSOCO_SYMBOLIC)
    known(request, "symbolic", constraint)
    extra =", s[0] != s[1]" if "s[" in constraint else ""
    check(run, solver, f"s = VarArray(size=2, dom={{'a', 'b', 'c'}})\nsatisfy({constraint}{extra})", [["a", "b", "c"]] * 2, predicate)


# ---------------------------------------------------------------------------------------------------- other cases

def test_table_on_array_with_holes(run, solver, request):
    bug_for(request, "COSOCO", COSOCO_HOLES)
    r = run("""
        y = VarArray(size=3, dom=lambda i: None if i == 1 else range(3))
        satisfy(
            y in {(0, 1), (2, 2)}
        )
    """, solver=solver)
    assert r.variables == ["y[0]", "y[2]"]
    assert_solutions(r, {(0, 1), (2, 2)})


def test_table_restricted_to_domains(run, solver):
    r = check(run, solver, X3 + "satisfy(x in {(0, 1, 2), (5, 1, 2), (1, -1, 1), (3, 3, 3)})", D3, lambda *t: t in {(0, 1, 2), (3, 3, 3)},
              args=["-restrict_tables_wrt_domains"])
    assert r.xml.find("constraints/extension/supports").text.strip() == "(0,1,2)(3,3,3)"


def test_table_with_expressions_in_scope(run, solver):
    # an expression in the scope is replaced by an auxiliary variable
    r = run(X3 + "satisfy((x[0] + x[1], x[2]) in {(0, 1), (5, 3), (6, 0)})", solver=solver)
    assert_solutions(r, brute_force(D3, lambda a, b, c: (a + b, c) in {(0, 1), (5, 3), (6, 0)}))


# ---------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("constraint, tag, text", [
    ("x in {(0, 1, 2), (3, 3, 3)}", "supports", "(0,1,2)(3,3,3)"),
    ("x not in [(3, 3, 3), (0, 1, 2)]", "conflicts", "(0,1,2)(3,3,3)"),
    ("x in [(0, ANY, 2)]", "supports", "(0,*,2)"),
    ("x[0] in [2, 0]", "supports", "0 2"),
    ("Table(scope=x, supports=[(1, 1, 1)])", "supports", "(1,1,1)"),
    ("x in [(lt(2), ANY, 1)]", "supports", "(0,*,1)(1,*,1)"),
])
def test_xcsp3_tables(run, constraint, tag, text):
    r = run(X3 + f"satisfy({constraint})")
    assert r.ok, r.report()
    extension = r.xml.find("constraints/extension")
    assert extension is not None, r.report()
    assert extension.find(tag).text.strip() == text


def test_xcsp3_hybrid_table_kept(run):
    r = run(X3 + "satisfy(x in [(lt(2), ANY, eq(col(0) + 1))])", args=["-keep_hybrid"])
    assert r.ok, r.report()
    extension = r.xml.find("constraints/extension")
    assert extension.get("type") == "hybrid-2", r.report()


# ---------------------------------------------------------------------------------------------------- invalid tables

@pytest.mark.parametrize("constraint", [
    pytest.param("(x[0], x[0]) in {(0, 0), (1, 1)}", marks=bug(INVALID)),
    "(x[0], x[1]) in {(0, 1, 2)}",
    "x in {(0, 1), (1, 2)}",
    "x in [(0, 1, 2), (0, 1)]",
    pytest.param("x in {(0, 1, 'a')}", marks=bug(INVALID)),
    "x in {(0, 1, 2.5)}",
    "x in {(0, 1, None)}",
    "(x[0], 1, x[2]) in {(0, 1, 2)}",
    pytest.param("Table(scope=x)", marks=bug(INVALID)),
    pytest.param("Table(scope=x, supports=[(0, 1, 2)], conflicts=[(1, 1, 1)])", marks=bug(INVALID)),
    "Table(supports=[(0, 1, 2)])",
    pytest.param("Table(scope=[x[0], x[0]], supports=[(0, 0)])", marks=bug(INVALID)),
    "Table(scope=[], supports=[(0, 1, 2)])",
    "Table(scope=x, supports=[0, 1])",
    pytest.param("Table(scope=x, supports=5)", marks=bug(INVALID)),
    "x[0] in ['a', 'b']",
])
def test_invalid_tables(run, constraint):
    assert_fails(run(X3 + f"satisfy({constraint})"))
