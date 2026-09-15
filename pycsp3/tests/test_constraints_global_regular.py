"""
Tests of the constraint Regular of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#Regular): the function Regular(), the operator 'in' with an automaton,
and the class Automaton (with its methods q(), states_for(), deterministic_copy(), contains() and to_table()).

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the words recognized by the automaton,
computed by brute force.
"""

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

# Known bugs (each bug is reported in the issue given at the start of its reason)
ALL = ("ACE", "CHOCO", "COSOCO")
STATES = "#109: the start and final states of an automaton are not checked"
RANGES = "#110: labels given by ranges cannot be used with variables of different domains"
INVALID = "#111: invalid automata are reported without explicit message, or accepted"
COSOCO_NFA = "xcsp3team/cosoco#77: cosoco loses solutions with a non-deterministic automaton"

# The cases that a solver says it does not handle (not reported)
ACE_NFA = "ACE does not handle non-deterministic automata (unimplemented case for non deterministic automaton)"
CHOCO_NEGATIVE = "CHOCO does not handle negative values in automata (only integers in [0,65535] are allowed by FiniteAutomaton)"
SYMBOLIC = "symbolic values are not allowed in the transitions of regular in XCSP3-core (the XCSP3 parser of ACE and CHOCO fails, cosoco has no symbolic variables)"


def accepts(word, start, transitions, final):
    """Returns True if the word is recognized by the (possibly non-deterministic) automaton; labels are values, ranges or collections."""
    states = {start}
    for v in word:
        states = {q2 for (q1, label, q2) in transitions if q1 in states and (v in label if isinstance(label, (range, list, tuple, set)) else v == label)}
    return len(states & ({final} if isinstance(final, str) else set(final))) > 0


# the automaton of the documentation, recognizing 0*110+10*
A, B, C, D, E = "a", "b", "c", "d", "e"
DOC = dict(start=A, transitions=[(A, 0, A), (A, 1, B), (B, 1, C), (C, 0, D), (D, 0, D), (D, 1, E), (E, 0, E)], final=E)


def automaton(spec):
    """The code building the automaton with the specified start, transitions and final states."""
    return f"A = Automaton(start={spec['start']!r}, transitions={spec['transitions']!r}, final={spec['final']!r})\n"


def check(run, solver, spec, n, dom, constraint, predicate=None, args=()):
    r = run(automaton(spec) + f"x = VarArray(size={n}, dom={dom!r})\nsatisfy({constraint})", solver=solver, args=args)
    predicate = predicate or (lambda *t: accepts(t, spec["start"], spec["transitions"], spec["final"]))
    assert_solutions(r, brute_force([list(dom)] * n, predicate))
    return r


# --------------------------------------------------------------------------------------------------------- forms

@pytest.mark.parametrize("constraint, predicate", [
    ("x in A", None),
    ("Regular(scope=x, automaton=A)", None),
    ("tuple(x) in A", None),
    ("[x[i] for i in range(7)] in A", None),
    ("(x[0], x[1], x[2], x[3], x[4], x[5], x[6]) in A", None),
    ("x[::-1] in A", lambda *t: accepts(t[::-1], A, DOC["transitions"], E)),
    ("Regular(scope=[x[6], x[5], x[4], x[3], x[2], x[1], x[0]], automaton=A)", lambda *t: accepts(t[::-1], A, DOC["transitions"], E)),
])
def test_regular_forms(run, solver, constraint, predicate):
    check(run, solver, DOC, 7, {0, 1}, constraint, predicate)


def test_regular_not_in(run):
    # 'not in' cannot be used with an automaton: an explicit error is reported (instead of posting x in A)
    r = run(automaton(DOC) + "x = VarArray(size=5, dom={0, 1})\nsatisfy(x not in A)")
    assert_fails(r)
    assert "The operator 'not in' cannot be used with an automaton: only 'x in A' is possible (constraint Regular)" in r.stdout, r.report()


def test_regular_on_rows_and_columns(run, solver):
    # as in a nonogram: each row and each column must be a word of 0*1+0* (a single block of ones)
    spec = dict(start="s", transitions=[("s", 0, "s"), ("s", 1, "b"), ("b", 1, "b"), ("b", 0, "e"), ("e", 0, "e")], final=["b", "e"])
    r = run(automaton(spec) + """
x = VarArray(size=[3, 3], dom={0, 1})
satisfy(
    [x[i] in A for i in range(3)],
    [Regular(scope=x[:, j], automaton=A) for j in range(3)]
)
""", solver=solver)

    def ok(*t):
        rows = [t[i * 3:i * 3 + 3] for i in range(3)]
        cols = [tuple(rows[i][j] for i in range(3)) for j in range(3)]
        return all(accepts(w, "s", spec["transitions"], spec["final"]) for w in rows + cols)
    assert_solutions(r, brute_force([[0, 1]] * 9, ok))


def test_regular_with_other_constraints(run, solver):
    # the example of the documentation: a night shift (2) is followed by a day off (0), and work (1) cannot last more than 2 days
    spec = dict(start="q0", transitions=[("q0", 0, "q0"), ("q0", 1, "q1"), ("q0", 2, "q3"), ("q1", 0, "q0"), ("q1", 1, "q2"), ("q2", 0, "q0"), ("q3", 0, "q0")],
                final=["q0", "q1", "q2", "q3"])
    r = run(automaton(spec) + "x = VarArray(size=5, dom=range(3))\nsatisfy(Count(x, value=0) == 2, x in A)", solver=solver)
    assert_solutions(r, brute_force([range(3)] * 5, lambda *t: t.count(0) == 2 and accepts(t, "q0", spec["transitions"], spec["final"])))


# ------------------------------------------------------------------------------------------------------- automata

AUTOMATA = {
    "several final states": (dict(start="a", transitions=[("a", 0, "b"), ("b", 1, "a"), ("b", 0, "c"), ("c", 1, "c")], final=["a", "c"]), 4, {0, 1}),
    "final state given as a set": (dict(start="a", transitions=[("a", 0, "b"), ("b", 1, "a"), ("b", 0, "c"), ("c", 1, "c")], final={"a", "c"}), 4, {0, 1}),
    "final state given as a tuple": (dict(start="a", transitions=[("a", 0, "b"), ("b", 1, "a"), ("b", 0, "c"), ("c", 1, "c")], final=("c",)), 4, {0, 1}),
    "start state being final": (dict(start="a", transitions=[("a", 0, "a"), ("a", 1, "b"), ("b", 1, "a")], final="a"), 4, {0, 1}),
    "non-deterministic": (dict(start="a", transitions=[("a", 0, "a"), ("a", 1, "a"), ("a", 1, "b"), ("b", 0, "c"), ("b", 1, "c")], final="c"), 4, {0, 1}),
    "non-deterministic with several paths": (dict(start="p", transitions=[("p", 0, "p"), ("p", 0, "q"), ("q", 0, "q"), ("q", 1, "r"), ("p", 1, "r"), ("r", 1, "r")], final=["r"]), 4, {0, 1}),
    "transitions given as a set": (dict(start="a", transitions={("a", 0, "a"), ("a", 1, "b"), ("b", 0, "b")}, final="b"), 4, {0, 1}),
    "transitions given as lists": (dict(start="a", transitions=[["a", 0, "a"], ["a", 1, "b"], ["b", 0, "b"]], final="b"), 4, {0, 1}),
    "values not all used": (dict(start="a", transitions=[("a", 0, "a"), ("a", 2, "b"), ("b", 2, "b")], final="b"), 4, range(3)),
    "negative values": (dict(start="a", transitions=[("a", -2, "b"), ("b", -1, "b"), ("b", 1, "a")], final="b"), 4, range(-2, 3)),
    "values outside the domains": (dict(start="a", transitions=[("a", 0, "a"), ("a", 7, "b"), ("a", 1, "b"), ("b", 1, "b")], final="b"), 4, {0, 1}),
    "numbered states": (dict(start="q0", transitions=[("q0", 0, "q1"), ("q1", 1, "q0"), ("q1", 0, "q2"), ("q2", 0, "q2")], final=["q0", "q2"]), 5, {0, 1}),
    "states with long names": (dict(start="start", transitions=[("start", 1, "one_seen"), ("one_seen", 0, "start"), ("start", 0, "start")], final="start"), 4, {0, 1}),
    "no recognized word": (dict(start="a", transitions=[("a", 0, "b"), ("b", 0, "c")], final="c"), 4, {0, 1}),
    "labels given by ranges": (dict(start="a", transitions=[("a", range(0, 2), "a"), ("a", range(2, 4), "b"), ("b", range(1, 4), "b")], final="b"), 3, range(4)),
    "labels given by lists": (dict(start="a", transitions=[("a", [0, 3], "a"), ("a", [1, 2], "b"), ("b", [0, 1], "b")], final="b"), 3, range(4)),
    "labels given by sets": (dict(start="a", transitions=[("a", {0, 3}, "a"), ("a", {1, 2}, "b"), ("b", {0, 1}, "b")], final="b"), 3, range(4)),
}


@pytest.mark.parametrize("name", AUTOMATA)
def test_automata(run, solver, request, name):
    if solver == "ACE" and name.startswith("non-deterministic"):
        pytest.skip(ACE_NFA)
    if solver == "CHOCO" and name == "negative values":
        pytest.skip(CHOCO_NEGATIVE)
    if name == "non-deterministic":
        bug_for(request, "COSOCO", COSOCO_NFA)
    spec, n, dom = AUTOMATA[name]
    check(run, solver, spec, n, dom, "x in A")


def test_automaton_on_symbolic_variables(run, solver):
    pytest.skip(SYMBOLIC)
    spec = dict(start="s", transitions=[("s", "a", "s"), ("s", "b", "t"), ("t", "c", "t")], final="t")
    r = run(automaton(spec) + "x = VarArray(size=4, dom={'a', 'b', 'c'})\nsatisfy(x in A)", solver=solver)
    assert_solutions(r, brute_force([["a", "b", "c"]] * 4, lambda *t: accepts(t, "s", spec["transitions"], "t")))


def test_automaton_with_ranges_on_different_domains(run, solver, request):
    # the labels given by ranges are applied to variables with different domains
    bug_for(request, ALL, RANGES)
    spec = dict(start="a", transitions=[("a", range(0, 2), "a"), ("a", range(2, 4), "b"), ("b", range(0, 4), "b")], final="b")
    r = run(automaton(spec) + "x = VarArray(size=3, dom=lambda i: range(2 + i))\nsatisfy(x in A)", solver=solver)
    assert_solutions(r, brute_force([range(2), range(3), range(4)], lambda *t: accepts(t, "a", spec["transitions"], "b")))


def test_automaton_used_with_several_domains(run, solver):
    # the same automaton (with labels given by a range) is used for two scopes with different domains
    spec = dict(start="a", transitions=[("a", range(0, 3), "a"), ("a", range(3, 6), "b"), ("b", range(0, 6), "b")], final="b")
    r = run(automaton(spec) + "x = VarArray(size=3, dom=range(4))\ny = VarArray(size=3, dom=range(3, 6))\nsatisfy(x in A, y in A)", solver=solver)
    assert_solutions(r, brute_force([range(4)] * 3 + [range(3, 6)] * 3, lambda *t: accepts(t[:3], "a", spec["transitions"], "b") and accepts(t[3:], "a", spec["transitions"], "b")))


@pytest.mark.parametrize("spec", [
    dict(start="a", transitions=[("a", 0, "a"), ("a", 1, "b")], final=[]),
    dict(start="a", transitions=[("a", 0, "a"), ("a", 1, "b")], final=["z"]),
    dict(start="a", transitions=[("a", 0, "a"), ("a", 1, "b")], final="z"),
    dict(start="z", transitions=[("a", 0, "a"), ("a", 1, "b")], final="b"),
], ids=["no final state", "final state not in transitions (list)", "final state not in transitions (string)", "start state not in transitions"])
def test_automata_without_recognized_word(run, solver, request, spec):
    # no word can be recognized: either the model is unsatisfiable, or an error is reported
    bug_for(request, ("CHOCO", "COSOCO") if spec["start"] == "z" else "CHOCO", STATES)
    r = run(automaton(spec) + "x = VarArray(size=3, dom={0, 1})\nsatisfy(x in A)", solver=solver)
    if r.ok:
        assert_solutions(r, set())
    else:
        assert_fails(r)


# ------------------------------------------------------------------------------------------ methods of Automaton

def test_automaton_states(run):
    r = run("""
        print("q", Automaton.q(3), Automaton.q(1, 2), Automaton.q(0, 1, 2))
        print("states_for", Automaton.states_for(range(3)), Automaton.states_for(1, 5), Automaton.states_for([2, 4]), Automaton.states_for("a", "b"))
    """)
    assert "q q3 q1x2 q0x1x2" in r.lines, r.report()
    assert "states_for ['q0', 'q1', 'q2'] ['q1', 'q5'] ['q2', 'q4'] ['qa', 'qb']" in r.lines


@pytest.mark.parametrize("call", [pytest.param("Automaton.q(1, None, 2)", marks=bug(INVALID)), "Automaton.states_for()", "Automaton.states_for([])", "Automaton.states_for(1.5)"])
def test_automaton_states_invalid(run, call):
    assert_fails(run(f"v = {call}"))


def test_automaton_display(run):
    r = run(automaton(DOC) + 'print("automaton", A)')
    assert "automaton Automaton(start=a, transitions={(a,0,a),(a,1,b),(b,1,c),(c,0,d),(d,0,d),(d,1,e),(e,0,e)}, final=[e])" in r.lines, r.report()


def test_automaton_contains_and_to_table(run):
    r = run("""
        A = Automaton(start="a", final="b", transitions=[("a", 0, "a"), ("a", 1, "b"), ("b", 1, "b")])
        print("contains", A.contains([0, 1, 1]), A.contains([0, 0]), A.contains([1, 0]), A.contains([]), A.contains([1]))
        print("to_table", A.to_table([range(2)] * 3), A.to_table([range(1), range(2)]), A.to_table([range(3)]))
    """)
    assert "contains True False None False True" in r.lines, r.report()
    assert "to_table [(0, 0, 1), (0, 1, 1), (1, 1, 1)] [(0, 1)] [(1,)]" in r.lines


def test_automaton_to_table_solutions(run, solver):
    r = run(automaton(DOC) + "x = VarArray(size=6, dom={0, 1})\nsatisfy(x in A.to_table([x[i].dom for i in range(6)]))", solver=solver)
    assert_solutions(r, brute_force([[0, 1]] * 6, lambda *t: accepts(t, A, DOC["transitions"], E)))


def test_automaton_deterministic_copy_display(run):
    r = run("""
        x = VarArray(size=3, dom=range(2))
        A = Automaton(start="a", final="c", transitions=[("a", 0, "a"), ("a", 0, "b"), ("b", 1, "c")])
        print("copy", A.deterministic_copy(x))
    """)
    assert "copy Automaton(start=a, transitions={(a,0,a_b),(a_b,0,a_b),(a_b,1,c)}, final=[c])" in r.lines, r.report()


NFA = {
    "documentation": dict(start="a", transitions=[("a", 0, "a"), ("a", 0, "b"), ("b", 1, "c")], final="c"),
    "several paths": dict(start="p", transitions=[("p", 0, "p"), ("p", 0, "q"), ("q", 0, "q"), ("q", 1, "r"), ("p", 1, "r"), ("r", 1, "r")], final=["r"]),
    "suffix 101": dict(start="s", transitions=[("s", 0, "s"), ("s", 1, "s"), ("s", 1, "t"), ("t", 0, "u"), ("u", 1, "v")], final="v"),
    "states with underscores": dict(start="q_0", transitions=[("q_0", 0, "q_0"), ("q_0", 1, "q_0"), ("q_0", 1, "q_1"), ("q_1", 1, "q_2")], final="q_2"),
    "final state reached by one path only": dict(start="a", transitions=[("a", 0, "b"), ("a", 0, "c"), ("b", 1, "d"), ("c", 0, "d"), ("d", 0, "d")], final=["d"]),
    "name already used": dict(start="a", transitions=[("a", 0, "a"), ("a", 0, "b"), ("b", 1, "a_b"), ("a_b", 1, "a_b")], final=["a_b"]),
}


@pytest.mark.parametrize("name", NFA)
def test_automaton_deterministic_copy(run, solver, name):
    spec = NFA[name]
    r = run(automaton(spec) + "x = VarArray(size=5, dom={0, 1})\nD = A.deterministic_copy(x)\nsatisfy(x in D)\n"
                              "print('deterministic', all(len({q2 for (q1, v, q2) in D.transitions if (q1, v) == (p, w)}) == 1 for (p, w, _) in D.transitions))",
            solver=solver, timeout=20)  # the copy may not terminate
    assert "deterministic True" in r.lines, r.report()
    assert_solutions(r, brute_force([[0, 1]] * 5, lambda *t: accepts(t, spec["start"], spec["transitions"], spec["final"])))


@pytest.mark.parametrize("name, text", [
    ("documentation", "Automaton(start=a, transitions={(a,0,a_b),(a_b,0,a_b),(a_b,1,c)}, final=[c])"),
    ("several paths", "Automaton(start=p, transitions={(p,0,p_q),(p,1,r),(p_q,0,p_q),(p_q,1,r),(r,1,r)}, final=[r])"),
    ("states with underscores", "Automaton(start=q_0, transitions={(q_0,0,q_0),(q_0,1,q_0_q_1),(q_0_q_1,0,q_0),(q_0_q_1,1,q_0_q_1_q_2),"
                                "(q_0_q_1_q_2,0,q_0),(q_0_q_1_q_2,1,q_0_q_1_q_2)}, final=[q_0_q_1_q_2])"),
    ("name already used", "Automaton(start=a, transitions={(a,0,a_b_1),(a_b_1,0,a_b_1),(a_b_1,1,a_b),(a_b,1,a_b)}, final=[a_b])"),
])
def test_automaton_deterministic_copy_states(run, name, text):
    # the states of the copy are named after the sets of states (with a suffix when the name is already used)
    r = run(automaton(NFA[name]) + "x = VarArray(size=5, dom={0, 1})\nprint('copy', A.deterministic_copy(x))")
    assert "copy " + text in r.lines, r.report()


# --------------------------------------------------------------------------------------------------- XCSP3 files

@pytest.mark.parametrize("spec, dom, transitions, start, final", [
    (DOC, "{0, 1}", "(a,0,a)(a,1,b)(b,1,c)(c,0,d)(d,0,d)(d,1,e)(e,0,e)", "a", "e"),
    (dict(start="a", transitions=[("a", 0, "b"), ("b", 1, "a")], final=["b", "a"]), "{0, 1}", "(a,0,b)(b,1,a)", "a", "a b"),
    (dict(start="a", transitions=[("a", range(0, 2), "b"), ("b", [2, 3], "a")], final="a"), "range(4)", "(a,0,b)(a,1,b)(b,2,a)(b,3,a)", "a", "a"),
])
def test_xcsp3_regular(run, spec, dom, transitions, start, final):
    r = run(automaton(spec) + f"x = VarArray(size=4, dom={dom})\nsatisfy(x in A)")
    assert r.ok, r.report()
    regular = r.xml.find("constraints/regular")
    assert regular is not None, r.report()
    assert [regular.find(t).text.strip() for t in ("list", "transitions", "start", "final")] == ["x[]", transitions, start, final]


# --------------------------------------------------------------------------------------------------- invalid cases

@pytest.mark.parametrize("code", [
    "A = Automaton(start='a', transitions=[], final='a')",
    "A = Automaton(start='a', transitions=[('a', 0)], final='a')",
    "A = Automaton(start='a', transitions=[('a', 0, 1)], final='a')",
    "A = Automaton(start=0, transitions=[('a', 0, 'a')], final='a')",
    pytest.param("A = Automaton(start='a', transitions=[('a', 0, 'a')], final=[0])", marks=bug(STATES)),
    pytest.param("A = Automaton(start='a', transitions=(('a', 0, 'a'),), final='a')", marks=bug(INVALID)),
    pytest.param("A = Automaton(start='a', transitions=(t for t in [('a', 0, 'a')]), final='a')", marks=bug(INVALID)),
    pytest.param("A = Automaton(start='a', transitions=[('a', 2.5, 'a')], final='a')\nsatisfy(x in A)", marks=bug(INVALID)),
    pytest.param("A = Automaton(start='a', transitions=[('a', 'z', 'a')], final='a')\nsatisfy(x in A)", marks=bug(INVALID)),
    pytest.param("A = Automaton(start='a b', transitions=[('a b', 0, 'a b')], final='a b')\nsatisfy(x in A)", marks=bug(INVALID)),
    "A = Automaton(start='a', transitions=[('a', 0, 'a')])",
    "satisfy(Regular(scope=x, automaton=5))",
    "satisfy(Regular(scope=x, automaton=[('a', 0, 'a')]))",
    "A = Automaton(start='a', transitions=[('a', 0, 'a')], final='a')\nsatisfy(Regular(scope=[x[0], 1], automaton=A))",
    "A = Automaton(start='a', transitions=[('a', 0, 'a')], final='a')\nsatisfy(Regular(automaton=A))",
    pytest.param("A = Automaton(start='a', transitions=[('a', 0, 'a')], final='a')\nsatisfy(Regular(scope=[], automaton=A))", marks=bug(INVALID)),
])
def test_invalid_automata(run, code):
    assert_fails(run("x = VarArray(size=3, dom={0, 1})\n" + code))
