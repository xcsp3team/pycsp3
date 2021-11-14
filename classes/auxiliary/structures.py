import types

from pycsp3.tools.curser import queue_in


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
            state1, state2 = transition[0], transition[2]
            assert isinstance(state1, str) and isinstance(state2, str), Diagram.MSG_STATE
            values = transition[1] if isinstance(transition[1], (list, tuple, set, range)) else [transition[1]]
            for value in values:
                assert isinstance(value, int), "currently, the value of a transition is necessarily an integer"
                t.append((state1, value, state2))
        return t

    def transitions_to_string(self):
        if self.num not in Diagram._cache:
            Diagram._cache[self.num] = "".join(["(" + q1 + "," + str(v) + "," + q2 + ")" for (q1, v, q2) in self.transitions])
        return Diagram._cache[self.num]


class Automaton(Diagram):

    @staticmethod
    def q(i, j=None):
        """
        Returns the name of a state from the specified argument(s)

        :param i: the index of the state
        :param j: a secondary index
        :return: the name of a state from the specified argument(s)
        """
        return "q" + str(i) + ("" if j is None else "x" + str(j))

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
