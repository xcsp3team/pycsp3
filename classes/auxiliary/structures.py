from pycsp3 import functions


class Automaton:
    MSG_STATE = "states must given under the form of strings"
    MSG_VALUE = "currently, the value of a transition is necessarily an integer"

    @staticmethod
    def _add_transitions(transitions):
        assert len(transitions) > 0, "at least one transition must be present"
        t = []
        assert isinstance(transitions, (list, set))
        for transition in transitions:
            if isinstance(transition, list):
                transition = tuple(transition)
            assert isinstance(transition, tuple), "A transition must be given by a 3-tuple (or a list)"
            assert len(transition) == 3, "Error: each transition must be composed of 3 elements"
            state1, state2 = transition[0], transition[2]
            assert isinstance(state1, str) and isinstance(state2, str), Automaton.MSG_STATE
            if isinstance(transition[1], (list, tuple, set, range)):
                for value in transition[1]:
                    assert isinstance(value, int), Automaton.MSG_VALUE
                    t.append((state1, value, state2))
            else:
                assert isinstance(transition[1], int), Automaton.MSG_VALUE
                t.append(transition)
        return t

    def __init__(self, *, start, transitions, final):
        self.start = start
        self.transitions = Automaton._add_transitions(transitions)
        self.final = [final] if isinstance(final, str) else sorted(set(final))
        assert isinstance(start, str) and all(isinstance(q, str) for q in self.final), Automaton.MSG_STATE

    def __contains__(self, other):
        functions.queue_in.append((self, other))
        return True
