"""
Tests of the constraint MDD of the section Constraints (Global) of the API (https://pycsp.org/documentation/api/constraints-global/#MDD):
the function Mdd(), the operator 'in' with an MDD, and the class MDD.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the paths of the MDD, computed by brute force.
"""

import pytest

from harness import assert_fails, assert_solutions, brute_force

SYMBOLIC = "symbolic values are not allowed in the transitions of mdd in XCSP3-core"


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
    check(run, solver, DOC, 3, range(3), constraint, predicate)


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
    r = run(f"""
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
def test_mdds(run, solver, name):
    transitions, n, dom = MDDS[name]
    if isinstance(transitions, str):  # a generator
        r = run(f"M = MDD({transitions})\nx = VarArray(size={n}, dom={dom!r})\nsatisfy(x in M)", solver=solver)
        assert_solutions(r, brute_force([list(dom)] * n, lambda *t: accepts(t, DOC)))
    else:
        check(run, solver, transitions, n, dom, "x in M")


def test_mdd_given_by_a_set(run, solver):
    # the documentation says that the transitions are given by a set (or a list)
    check(run, solver, set(DOC), 3, range(3), "x in M")


@pytest.mark.parametrize("collection", ["set", "frozenset"])
def test_mdd_given_by_a_set_xcsp3(run, collection):
    # the transitions of a set are written in a deterministic order, level by level from the root
    r = run(f"M = MDD({collection}({DOC!r}))\nx = VarArray(size=3, dom=range(3))\nsatisfy(x in M)")
    assert r.ok, r.report()
    assert r.xml.find("constraints/mdd/transitions").text.strip() == "(r,0,n1)(r,1,n2)(r,2,n3)(n1,2,n4)(n2,2,n4)(n3,0,n5)(n4,0,t)(n5,0,t)", r.report()


def test_mdd_exported(run, solver):
    # Mdd() is brought by 'from pycsp3 import *', as Regular() (the tests of this file do not import it otherwise)
    r = run("x = VarArray(size=3, dom={0, 1})\nM = MDD([('r', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(Mdd(scope=x, mdd=M))", solver=solver)
    assert_solutions(r, {(0, 0, 1)})


def test_mdd_on_symbolic_variables(run, solver):
    pytest.skip(SYMBOLIC)


def test_mdd_with_ranges_on_different_domains(run, solver):
    transitions = [("r", range(0, 2), "a"), ("r", range(2, 4), "b"), ("a", range(0, 4), "t"), ("b", range(0, 2), "t")]
    r = run(f"M = MDD({transitions!r})\nx = VarArray(size=2, dom=lambda i: range(3 + i))\nsatisfy(x in M)", solver=solver)
    assert_solutions(r, brute_force([range(3), range(4)], lambda *t: accepts(t, transitions)))


def test_mdd_with_ranges_on_different_domains_xcsp3(run):
    # the labels given by ranges are developed with the domain of the variable of the level of the source node (3 is not in the domain of x[0])
    transitions = [("r", range(0, 2), "a"), ("r", range(2, 4), "b"), ("a", range(0, 4), "t"), ("b", range(0, 2), "t")]
    r = run(f"M = MDD({transitions!r})\nx = VarArray(size=2, dom=lambda i: range(3 + i))\nsatisfy(x in M)")
    assert r.ok, r.report()
    assert r.xml.find("constraints/mdd/transitions").text.strip() == "(r,0,a)(r,1,a)(r,2,b)(a,0,t)(a,1,t)(a,2,t)(a,3,t)(b,0,t)(b,1,t)", r.report()


@pytest.mark.parametrize("transitions, n", [
    ([("r", 0, "a"), ("a", 1, "t")], 3),  # the paths are shorter than the scope
    ([("r", 0, "a"), ("a", 1, "b"), ("b", 0, "c"), ("c", 1, "t")], 3),  # the paths are longer than the scope
    ([("r", 0, "a"), ("r", 1, "b"), ("a", 1, "t")], 2),  # two terminal nodes (t and b)
    ([("r", 0, "a"), ("s", 1, "a"), ("a", 1, "t")], 2),  # two roots (r and s)
    ([("r", 0, "a"), ("a", 1, "b"), ("b", 0, "a"), ("a", 0, "t")], 2),  # a cycle
    ([("r", 0, "a"), ("r", 1, "b"), ("a", 1, "t"), ("b", 1, "b2"), ("b2", 0, "t")], 2),  # paths of different lengths
], ids=["paths shorter than the scope", "paths longer than the scope", "two terminal nodes", "two roots", "cycle", "paths of different lengths"])
def test_invalid_mdds(run, transitions, n):
    # the specification requires a directed acyclic graph with a single root and a single terminal node, whose paths have the length of the scope
    assert_fails(run(f"M = MDD({transitions!r})\nx = VarArray(size={n}, dom={{0, 1}})\nsatisfy(x in M)"))


@pytest.mark.parametrize("transitions, n, message", [
    ([("r", 0, "a"), ("a", 1, "t")], 3, "The paths of the MDD must have the length of the scope (3), which is not the case (2)"),
    ([("r", 0, "a"), ("a", 1, "b"), ("b", 0, "c"), ("c", 1, "t")], 3, "The paths of the MDD must have the length of the scope (3), which is not the case (4)"),
    ([("r", 0, "a"), ("r", 1, "b"), ("a", 1, "t")], 2, "An MDD must have exactly one terminal node (node without outgoing transition), which is not the case: ['b', 't']"),
    ([("r", 0, "a"), ("s", 1, "a"), ("a", 1, "t")], 2, "An MDD must have exactly one root (node without incoming transition), which is not the case: ['r', 's']"),
    ([("r", 0, "a"), ("a", 1, "b"), ("b", 0, "a"), ("a", 0, "t")], 2,
     "An MDD must be acyclic, which is not the case (some of the nodes ['a', 'b', 't'] are in a cycle, or can only be reached from a cycle)"),
    ([("r", 0, "a"), ("r", 1, "b"), ("a", 1, "t"), ("b", 1, "b2"), ("b2", 0, "t")], 2,
     "The paths of an MDD must have all the same length, which is not the case of the paths reaching 't'"),
    ([("r", 0, "a"), ("a", 1, "r")], 2, "An MDD must have exactly one root (node without incoming transition), which is not the case: []"),
], ids=["paths shorter than the scope", "paths longer than the scope", "two terminal nodes", "two roots", "cycle", "paths of different lengths", "no root"])
def test_invalid_mdds_messages(run, transitions, n, message):
    r = run(f"M = MDD({transitions!r})\nx = VarArray(size={n}, dom={{0, 1}})\nsatisfy(x in M)")
    assert not r.ok and message in r.stdout, r.report()


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


@pytest.mark.parametrize("transitions, n, dom, text", [
    (MDDS["transitions in another order"][0], 3, "range(3)", "(r,0,n1)(r,2,n3)(r,1,n2)(n1,2,n4)(n3,0,n5)(n2,2,n4)(n4,0,t)(n5,0,t)"),
    ([("r", 0, "a"), ("a", 1, "t"), ("r", 1, "b"), ("b", 0, "t")], 2, "range(2)", "(r,0,a)(a,1,t)(r,1,b)(b,0,t)"),
    (MDDS["values outside the domains"][0], 2, "range(2)", "(r,0,a)(a,1,t)"),
    ([("r", range(0, 5), "a"), ("a", {1, 7}, "t")], 2, "range(3)", "(r,0,a)(r,1,a)(r,2,a)(a,1,t)"),
], ids=["transitions in another order", "depth-first order kept", "values outside the domains", "ranges and sets outside the domains"])
def test_xcsp3_mdd_written_transitions(run, transitions, n, dom, text):
    # the transitions are written from the root (a valid order being kept), the labels outside the domains being discarded,
    # as well as the transitions that are no longer on a path from the root to the terminal node
    r = run(f"M = MDD({transitions!r})\nx = VarArray(size={n}, dom={dom})\nsatisfy(x in M)")
    assert r.ok, r.report()
    assert r.xml.find("constraints/mdd/transitions").text.strip() == text, r.report()


def test_mdd_without_path_compatible_with_the_domains(run):
    r = run("M = MDD([('r', 5, 'a'), ('a', 0, 't')])\nx = VarArray(size=2, dom=range(2))\nsatisfy(x in M)")
    assert not r.ok and "No path of the MDD is compatible with the domains of the variables of the scope" in r.stdout, r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("code", [
    "M = MDD([])",
    "M = MDD([('r', 0)])",
    "M = MDD([('r', 0, 1)])",
    "M = MDD(5)",
    "M = MDD('abc')",
    "M = MDD([('r', 2.5, 't')])\nsatisfy(x in M)",
    "M = MDD([('r', 'z', 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(x in M)",
    "M = MDD([('r 1', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(x in M)",
    "satisfy(Mdd(scope=x, mdd=5))",
    "satisfy(Mdd(scope=x, mdd=[('r', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')]))",
    "M = MDD([('r', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(Mdd(scope=[x[0], 1, x[2]], mdd=M))",
    "M = MDD([('r', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(Mdd(scope=[], mdd=M))",
    "M = MDD([('r', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(Mdd(mdd=M))",
])
def test_invalid_mdd_arguments(run, code):
    assert_fails(run("x = VarArray(size=3, dom={0, 1})\n" + code))


@pytest.mark.parametrize("code, message", [
    ("M = MDD(5)", "The transitions of an MDD must be given by a list or a set of 3-tuples, which is not the case of 5"),
    ("M = MDD('abc')", "The transitions of an MDD must be given by a list or a set of 3-tuples, which is not the case of 'abc'"),
    ("M = MDD([('r', 2.5, 't')])",
     "The label of a transition must be an integer, a symbol, a range or a collection of integers (or symbols), which is not the case of 2.5 in ('r', 2.5, 't')"),
    ("M = MDD([('r', 'z', 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(x in M)",
     "The label 'z' of the transition ('r', 'z', 'a') is a symbol, which is not possible for the integer variables of the scope of the constraint Mdd"),
    ("M = MDD([('r 1', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')])",
     "The name of a state must be a non-empty string without space, comma or parenthesis, which is not the case of 'r 1'"),
    ("M = MDD([('r', 0, 'a'), ('a', 0, 'b'), ('b', 1, 't')])\nsatisfy(Mdd(scope=[], mdd=M))", "The scope of the constraint Mdd must not be empty"),
])
def test_invalid_mdd_arguments_messages(run, code, message):
    r = run("x = VarArray(size=3, dom={0, 1})\n" + code)
    assert not r.ok and message in r.stdout, r.report()
