from pycsp3.tools.curser import queue_in


class Diagram:
    def __init__(self, transitions):
        self.transitions = Diagram._add_transitions(transitions)

    def __contains__(self, other):
        queue_in.append((self, other))
        return True

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


class Automaton(Diagram):
    @staticmethod
    def q(i, j=None):
        return "q" + str(i) + ("" if j is None else "x" + str(j))

    def __init__(self, *, start, transitions, final):
        super().__init__(transitions)
        self.start = start
        self.final = [final] if isinstance(final, str) else sorted(set(final))
        assert isinstance(self.start, str) and all(isinstance(f, str) for f in self.final), Diagram.MSG_STATE


class MDD(Diagram):
    def __init__(self, transitions):
        assert isinstance(transitions, list)  # currently, a list is wanted for a MDD (and not a set); to be changed?
        super().__init__(transitions)
