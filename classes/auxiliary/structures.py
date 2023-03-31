import types

from pycsp3.tools.curser import queue_in
from pycsp3.tools.utilities import flatten
from pycsp3.dashboard import options
from pycsp3.classes.auxiliary.conditions import Condition, ConditionInterval, inside, IN


class Diagram:
    _cnt = 0
    _cache = {}

    def __init__(self, transitions):
        self.transitions = Diagram._add_transitions(transitions)
        self.states = sorted({q for (q, _, _) in self.transitions} | {q for (_, _, q) in self.transitions})
        self.num = Diagram._cnt
        Diagram._cnt += 1

    def __contains__(self, other):
        queue_in.append((self, other))
        return True

    def __str__(self):
        return "transitions={" + ",".join("(" + s1 + "," + str(v) + "," + s2 + ")" for (s1, v, s2) in self.transitions) + "}"

    MSG_STATE = "states must given under the form of strings"

    @staticmethod
    def _add_transitions(transitions):
        assert len(transitions) > 0, "at least one transition must be present"
        assert isinstance(transitions, (list, set))
        t = []
        for transition in transitions:
            if isinstance(transition, list):
                transition = tuple(transition)
            assert isinstance(transition, tuple), "A transition must be given under the form of a 3-tuple (or a list)"
            assert len(transition) == 3, "Error: each transition must be composed of 3 elements"
            state1, label, state2 = transition
            assert isinstance(state1, str) and isinstance(state2, str), Diagram.MSG_STATE
            label = inside(label) if isinstance(label, range) else set(label) if isinstance(label, (tuple, list)) else label
            if (state1, label, state2) not in t:
                t.append((state1, label, state2))
        return t

    def flat_transitions(self, scp):
        values = scp[0].dom.all_values()
        assert all(values == scp[i].dom.all_values() for i in range(1, len(scp)))
        trs = []
        for (q1, l, q2) in self.transitions:
            labels = [l] if isinstance(l, (int, str)) else l if isinstance(l, (list, tuple, set, frozenset)) else list(l.filtering(values))
            for label in labels:
                assert isinstance(label, (int, str)), "currently, the label of a transition is necessarily an integer or a symbol"
                trs.append((q1, label, q2))
        return trs

    def transitions_to_string(self, scp):
        def _string(t):
            return "".join(
                ["(" + q1 + "," + (l.str_tuple() if isinstance(l, Condition) else str(l)) + "," + q2 + ")" for (q1, l, q2) in t])

        if self.num not in Diagram._cache:
            if options.keepsmarttransitions or all(isinstance(label, (int, str)) for _, label, _ in self.transitions):
                Diagram._cache[self.num] = _string(self.transitions)
            else:
                trs = self.flat_transitions(scp)
                return _string(trs)  # we don't put in the cache because domains of scopes may be different
        return Diagram._cache[self.num]


class Automaton(Diagram):

    @staticmethod
    def q(i, j=None, k=None):
        """
        Returns the name of a state from the specified argument(s)

        :param i: the index of the state
        :param j: a secondary index
        :param k: a third index
        :return: the name of a state from the specified argument(s)
        """
        assert j is not None or k is None
        suffix = ("x" + str(j) if j is not None else "") + ("x" + str(k) if k is not None else "")
        return "q" + str(i) + suffix

    @staticmethod
    def states_for(*values):
        """
        Returns a list with the names of states corresponding to the specified values

        :param values: a list of integers (or strings)
        :return: a list of names of states, one for each specified value
        """
        if len(values) == 1 and isinstance(values[0], (range, types.GeneratorType)):
            values = list(values[0])
        else:
            values = flatten(values)
        assert len(values) > 0 and all(isinstance(v, (int, str)) for v in values), values
        return [Automaton.q(v) for v in values]

    def __init__(self, *, start, transitions, final):
        """
        Builds an automaton from the specified arguments: a starting state, a set of transitions and a set of final states

        :param start: the starting state
        :param transitions: a set of transitions
        :param final: the final state(s)
        """
        super().__init__(transitions)
        self.start = start
        self.final = [final] if isinstance(final, str) else sorted(q for q in set(final) if q in self.states)
        assert isinstance(self.start, str) and all(isinstance(f, str) for f in self.final), Diagram.MSG_STATE

    def deterministic_copy(self, scp):
        nfa = {}
        symbols = set()
        for state1, symbol, state2 in self.flat_transitions(flatten(scp)):
            symbols.add(symbol)
            if state1 not in nfa:
                nfa[state1] = {}
            if symbol not in nfa[state1]:
                nfa[state1][symbol] = []
            nfa[state1][symbol].append(state2)
        symbols = sorted(list(symbols))
        dfa = {}
        states = [self.start]
        queue = [self.start]
        while len(queue) != 0:
            state1 = queue.pop(0)
            dfa[state1] = {}
            tokens = [v for v in state1.split('_')]
            for symbol in symbols:
                state2 = "_".join(v for tok in tokens if tok in nfa and symbol in nfa[tok] for v in nfa[tok][symbol])
                if len(state2) > 0:
                    dfa[state1][symbol] = state2
                    if state2 not in states:
                        queue.append(state2)
                        states.append(state2)
        final = [state for state in dfa if any(tok in self.final for tok in state.split('_'))]
        transitions = [(state, symbol, dfa[state][symbol]) for state in dfa for symbol in symbols if symbol in dfa[state]]
        return Automaton(start=self.start, final=final, transitions=transitions)

    def __str__(self):
        return "Automaton(start=" + str(self.start) + ", " + Diagram.__str__(self) + ", final=[" + ",".join(str(v) for v in self.final) + "])"


class MDD(Diagram):
    def __init__(self, transitions):
        """
        Builds an MDD from the specified set of transitions

        :param transitions: a set of transitions
        """
        if isinstance(transitions, types.GeneratorType):
            transitions = [t for t in transitions]
        assert isinstance(transitions, list)  # currently, a list is wanted for a MDD (and not a set); to be changed?
        super().__init__(transitions)

    def __str__(self):
        return "MDD(" + Diagram.__str__(self) + ")"
