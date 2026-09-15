"""
Tests of the constraint MDD of the section Constraints (Global) of the API (https://pycsp.org/documentation/api/constraints-global/#MDD):
the function Mdd(), the operator 'in' with an MDD, and the class MDD.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the paths of the MDD, computed by brute force.
"""

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
ALL = ("ACE", "CHOCO", "COSOCO")
RANGES = "#110: labels given by ranges cannot be used with variables of different domains"
INVALID = "#111: invalid MDDs are reported without explicit message, or accepted"
STRUCTURE = "#112: the structure of an MDD is not checked (roots, terminal nodes, cycles, length of the paths)"
SET = "#113: the transitions of an MDD cannot be given by a set"
WRITING = "#114: the transitions of an MDD are not written from the root, and labels outside the domains are kept, which makes the solvers fail"
EXPORT = "#115: Mdd() is not brought by from pycsp3 import *"

SYMBOLIC = "symbolic values are not allowed in the transitions of mdd in XCSP3-core"

IMPORT = "from pycsp3.functions import Mdd  # not brought by from pycsp3 import *\n"


def accepts(word, transitions):
    """Returns True if the word labels a path from the root (the node without incoming transition) to the terminal node (the node without outgoing transition)."""
    sources, targets = {q for q, _, _ in transitions}, {q for _, _, q in transitions}
    roots, terminals = sources - targets, targets - sources
    nodes = set(roots)
    for v in word:
        nodes = {q2 for (q1, label, q2) in transitions if q1 in nodes and (v in label if isinstance(label, (range, list, tuple, set)) else v == label)}
    return len(nodes & terminals) > 0


# the MDD of the documentation (page of the constraint)
DOC = [("r", 0, "n1"), ("r", 1, "n2"), ("r", 2, "n3"), ("n1", 2, "n4"), ("n2", 2, "n4"), ("n3", 0, "n5"), ("n4", 0, "t"), ("n5", 0, "t")]


def check(run, solver, transitions, n, dom, constraint, predicate=None, prefix=""):
    r = run(prefix + f"M = MDD({transitions!r})\nx = VarArray(size={n}, dom={dom!r})\nsatisfy({constraint})", solver=solver)
    predicate = predicate or (lambda *t: accepts(t, transitions))
    assert_solutions(r, brute_force([list(dom)] * n, predicate))
    return r


# --------------------------------------------------------------------------------------------------------- forms

@pytest.mark.parametrize("constraint, predicate", [
    ("x in M", None),
    ("Mdd(scope=x, mdd=M)", None),
    ("tuple(x) in M", None),
    ("(x[0], x[1], x[2]) in M", None),
    ("[x[i] for i in range(3)] in M", None),
    ("x[::-1] in M", lambda *t: accepts(t[::-1], DOC)),
    ("Mdd(scope=[x[2], x[1], x[0]], mdd=M)", lambda *t: accepts(t[::-1], DOC)),
])
def test_mdd_forms(run, solver, constraint, predicate):
    check(run, solver, DOC, 3, range(3), constraint, predicate, prefix=IMPORT)


def test_mdd_stand_alone_variables(run, solver):
    # the example of the page of the constraint
    r = run(f"M = MDD({DOC!r})\nu = Var(0, 1, 2)\nv = Var(0, 1, 2)\nw = Var(0, 1, 2)\nsatisfy((u, v, w) in M)", solver=solver)
    assert_solutions(r, {(0, 2, 0), (1, 2, 0), (2, 0, 0)})


def test_mdd_not_in(run):
    # 'not in' cannot be used with an MDD: an explicit error is reported (instead of posting x in M)
    r = run(f"M = MDD({DOC!r})\nx = VarArray(size=3, dom=range(3))\nsatisfy(x not in M)")
    assert_fails(r)
    assert "The operator 'not in' cannot be used with an MDD: only 'x in M' is possible (constraint MDD)" in r.stdout, r.report()


def test_mdd_on_rows(run, solver):
    r = run(IMPORT + f"""
M = MDD({[("r", 0, "a"), ("r", 1, "b"), ("a", 1, "t"), ("b", 0, "t"), ("b", 1, "t")]!r})
x = VarArray(size=[3, 2], dom={{0, 1}})
satisfy(
    [x[i] in M for i in range(3)],
    Mdd(scope=[x[0][0], x[1][0]], mdd=M)
)
""", solver=solver)
    ok = lambda w: w in {(0, 1), (1, 0), (1, 1)}
    assert_solutions(r, brute_force([[0, 1]] * 6, lambda *t: ok(t[0:2]) and ok(t[2:4]) and ok(t[4:6]) and ok((t[0], t[2]))))


def test_mdd_with_other_constraints(run, solver):
    r = run(f"M = MDD({DOC!r})\nx = VarArray(size=3, dom=range(3))\ny = Var(dom=range(3))\nsatisfy(x in M, y == x[0])", solver=solver)
    assert_solutions(r, {(0, 2, 0, 0), (1, 2, 0, 1), (2, 0, 0, 2)})


# ------------------------------------------------------------------------------------------------------------ MDDs

MDDS = {
    "example of the API": ([("r", 0, "n1"), ("r", 1, "n2"), ("n1", 1, "t"), ("n2", 0, "t")], 2, range(2)),
    "example of the function": ([("r", 0, "n1"), ("r", 1, "n2"), ("n1", 2, "n3"), ("n2", 2, "n3"), ("n3", 0, "t"), ("n3", 1, "t")], 3, range(3)),
    "shared nodes": ([("r", 0, "a"), ("r", 1, "a"), ("r", 2, "b"), ("a", 0, "c"), ("b", 1, "c"), ("b", 2, "c"), ("c", 1, "t"), ("c", 2, "t")], 3, range(3)),
    "several labels between two nodes": ([("r", 0, "a"), ("r", 1, "a"), ("r", 2, "a"), ("a", 0, "t"), ("a", 2, "t")], 2, range(3)),
    "a single path": ([("r", 1, "a"), ("a", 0, "b"), ("b", 1, "t")], 3, range(2)),
    "transitions in another order": ([("n4", 0, "t"), ("n5", 0, "t"), ("n1", 2, "n4"), ("r", 0, "n1"), ("n3", 0, "n5"), ("r", 2, "n3"), ("n2", 2, "n4"), ("r", 1, "n2")], 3, range(3)),
    "transitions given by a generator": ("(t for t in " + repr(DOC) + ")", 3, range(3)),
    "negative values": ([("r", -2, "a"), ("r", 1, "b"), ("a", -1, "t"), ("b", 0, "t"), ("b", -2, "t")], 2, range(-2, 2)),
    "values outside the domains": ([("r", 0, "a"), ("r", 5, "a"), ("r", 1, "b"), ("a", 1, "t"), ("b", 7, "t")], 2, range(2)),
    "numbered nodes": ([("n0", 0, "n1"), ("n0", 1, "n2"), ("n1", 1, "n3"), ("n2", 0, "n3"), ("n2", 1, "n3"), ("n3", 1, "n4")], 3, range(2)),
    "labels given by ranges": ([("r", range(0, 2), "a"), ("r", range(2, 4), "b"), ("a", range(1, 3), "t"), ("b", range(0, 1), "t")], 2, range(4)),
    "labels given by lists": ([("r", [0, 3], "a"), ("r", [1, 2], "b"), ("a", [1, 2], "t"), ("b", [0], "t")], 2, range(4)),
    "labels given by sets": ([("r", {0, 3}, "a"), ("r", {1, 2}, "b"), ("a", {1, 2}, "t"), ("b", {0}, "t")], 2, range(4)),
    "transitions given as lists": ([["r", 0, "a"], ["r", 1, "a"], ["a", 1, "t"]], 2, range(2)),
}


@pytest.mark.parametrize("name", MDDS)
def test_mdds(run, solver, request, name):
    if name == "transitions in another order":
        bug_for(request, ("ACE", "COSOCO"), WRITING)
    if name == "values outside the domains":
        bug_for(request, ALL, WRITING)
    transitions, n, dom = MDDS[name]
    if isinstance(transitions, str):  # a generator
        r = run(f"M = MDD({transitions})\nx = VarArray(size={n}, dom={dom!r})\nsatisfy(x in M)", solver=solver)
        assert_solutions(r, brute_force([list(dom)] * n, lambda *t: accepts(t, DOC)))
    else:
        check(run, solver, transitions, n, dom, "x in M")


def test_mdd_given_by_a_set(run, solver, request):
    bug_for(request, ALL, SET)
    # the documentation says that the transitions are given by a set (or a list)
    check(run, solver, set(DOC), 3, range(3), "x in M")


@bug(EXPORT)
def test_mdd_exported(run):
    # Mdd() is brought by 'from pycsp3 import *', as Regular()
    r = run("x = VarArray(size=3, dom={0, 1})\nM = MDD([('r', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(Mdd(scope=x, mdd=M))")
    assert r.ok, r.report()


def test_mdd_on_symbolic_variables(run, solver):
    pytest.skip(SYMBOLIC)


def test_mdd_with_ranges_on_different_domains(run, solver, request):
    bug_for(request, ALL, RANGES)
    transitions = [("r", range(0, 2), "a"), ("r", range(2, 4), "b"), ("a", range(0, 4), "t"), ("b", range(0, 2), "t")]
    r = run(f"M = MDD({transitions!r})\nx = VarArray(size=2, dom=lambda i: range(3 + i))\nsatisfy(x in M)", solver=solver)
    assert_solutions(r, brute_force([range(3), range(4)], lambda *t: accepts(t, transitions)))


@pytest.mark.parametrize("transitions, n", [
    ([("r", 0, "a"), ("a", 1, "t")], 3),  # the paths are shorter than the scope
    ([("r", 0, "a"), ("a", 1, "b"), ("b", 0, "c"), ("c", 1, "t")], 3),  # the paths are longer than the scope
    ([("r", 0, "a"), ("r", 1, "b"), ("a", 1, "t")], 2),  # two terminal nodes (t and b)
    ([("r", 0, "a"), ("s", 1, "a"), ("a", 1, "t")], 2),  # two roots (r and s)
    ([("r", 0, "a"), ("a", 1, "b"), ("b", 0, "a"), ("a", 0, "t")], 2),  # a cycle
    ([("r", 0, "a"), ("r", 1, "b"), ("a", 1, "t"), ("b", 1, "b2"), ("b2", 0, "t")], 2),  # paths of different lengths
], ids=["paths shorter than the scope", "paths longer than the scope", "two terminal nodes", "two roots", "cycle", "paths of different lengths"])
@bug(STRUCTURE)
def test_invalid_mdds(run, transitions, n):
    # the specification requires a directed acyclic graph with a single root and a single terminal node, whose paths have the length of the scope
    assert_fails(run(f"M = MDD({transitions!r})\nx = VarArray(size={n}, dom={{0, 1}})\nsatisfy(x in M)"))


# ------------------------------------------------------------------------------------------------------- display

def test_mdd_display(run):
    r = run(f"M = MDD({DOC!r})\nprint('mdd', M)")
    assert "mdd MDD(transitions={(r,0,n1),(r,1,n2),(r,2,n3),(n1,2,n4),(n2,2,n4),(n3,0,n5),(n4,0,t),(n5,0,t)})" in r.lines, r.report()


@pytest.mark.parametrize("transitions, dom, text", [
    (DOC, "range(3)", "(r,0,n1)(r,1,n2)(r,2,n3)(n1,2,n4)(n2,2,n4)(n3,0,n5)(n4,0,t)(n5,0,t)"),
    ([("r", range(0, 2), "a"), ("a", [2, 0], "t")], "range(3)", "(r,0,a)(r,1,a)(a,0,t)(a,2,t)"),
])
def test_xcsp3_mdd(run, transitions, dom, text):
    r = run(f"M = MDD({transitions!r})\nx = VarArray(size=2 if len({transitions!r}) == 2 else 3, dom={dom})\nsatisfy(x in M)")
    assert r.ok, r.report()
    mdd = r.xml.find("constraints/mdd")
    assert mdd is not None, r.report()
    assert mdd.find("list").text.strip() in ("x[]", " ".join(f"x[{i}]" for i in range(3 if "n1" in text else 2))) and mdd.find("transitions").text.strip() == text


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("code", [
    "M = MDD([])",
    "M = MDD([('r', 0)])",
    "M = MDD([('r', 0, 1)])",
    pytest.param("M = MDD(5)", marks=bug(INVALID)),
    pytest.param("M = MDD('abc')", marks=bug(INVALID)),
    pytest.param("M = MDD([('r', 2.5, 't')])\nsatisfy(x in M)", marks=bug(INVALID)),
    pytest.param("M = MDD([('r', 'z', 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(x in M)", marks=bug(INVALID)),
    pytest.param("M = MDD([('r 1', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(x in M)", marks=bug(INVALID)),
    "satisfy(Mdd(scope=x, mdd=5))",
    "satisfy(Mdd(scope=x, mdd=[('r', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')]))",
    "M = MDD([('r', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(Mdd(scope=[x[0], 1, x[2]], mdd=M))",
    pytest.param("M = MDD([('r', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(Mdd(scope=[], mdd=M))", marks=bug(INVALID)),
    "M = MDD([('r', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(Mdd(mdd=M))",
])
def test_invalid_mdd_arguments(run, code):
    assert_fails(run(IMPORT + "x = VarArray(size=3, dom={0, 1})\n" + code))
