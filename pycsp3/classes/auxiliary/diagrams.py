import re
import types
from collections import Counter, defaultdict

from pycsp3.classes.auxiliary.conditions import Condition, inside
from pycsp3.dashboard import options
from pycsp3.tools.curser import queue_in
from pycsp3.tools.utilities import error, error_if, flatten


class Diagram:
    _cnt = 0
    _cache = {}

    _INVALID_CHARACTERS_OF_STATES = re.compile(r"[\s(),]")  # such characters would break the syntax of transitions

    def __init__(self, transitions):
        self.transitions = Diagram._add_transitions(transitions)
        self.states = sorted({q for (q, _, _) in self.transitions} | {q for (_, _, q) in self.transitions})
        # the names of the states are checked once (a single search over all of them, since diagrams may have many states)
        if "" in self.states or Diagram._INVALID_CHARACTERS_OF_STATES.search("\x00".join(self.states)):
            state = next(q for q in self.states if q == "" or Diagram._INVALID_CHARACTERS_OF_STATES.search(q))
            error("The name of a state must be a non-empty string without space, comma or parenthesis, which is not the case of " + repr(state))
        self._label_types = None
        # the labels are checked from the set of their types (computed once), the transitions being traversed only when a type is unexpected
        # (at this point, ranges have been changed into conditions, and tuples and lists into sets)
        label_types = self.label_types()
        if any(not issubclass(tp, (int, str, set, frozenset, Condition)) for tp in label_types) or label_types & {set, frozenset}:
            for (q1, label, q2) in self.transitions:
                if not (isinstance(label, (int, str, Condition)) or (isinstance(label, (set, frozenset)) and all(isinstance(v, (int, str)) for v in label))):
                    error("The label of a transition must be an integer, a symbol, a range or a collection of integers (or symbols), which is not the case of "
                          + repr(label) + " in " + repr((q1, label, q2)))
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
        if not isinstance(transitions, (list, set)) or len(transitions) == 0:
            error("The transitions must be given by a non-empty list or set of 3-tuples, which is not the case of " + repr(transitions))
        t = []
        for transition in transitions:
            if isinstance(transition, list):
                transition = tuple(transition)
            assert isinstance(transition, tuple), "A transition must be given under the form of a 3-tuple (or a list)"
            assert len(transition) == 3, "Error: each transition must be composed of 3 elements"
            state1, label, state2 = transition
            assert isinstance(state1, str) and isinstance(state2, str), Diagram.MSG_STATE
            label = inside(label) if isinstance(label, range) else set(label) if isinstance(label, (tuple, list)) else label
            check_if_already_present = False  # TODO making it as an option?
            if not check_if_already_present or (state1, label, state2) not in t:
                t.append((state1, label, state2))
        return t

    def _label_values(self, scp):
        """
        Returns a function giving, for a source state, the values with which the labels given by ranges (conditions) are developed:
        by default, the union of the domains of the variables of the scope (the variables may have different domains).
        """
        values = sorted({v for x in scp for v in x.dom.all_values()})
        return lambda state: values

    def label_types(self):  # the set of the types of the labels of the transitions (computed once)
        if self._label_types is None:
            self._label_types = {type(label) for (_, label, _) in self.transitions}
        return self._label_types

    def flat_transitions(self, scp):
        values_for = self._label_values(scp)
        trs = []
        for (q1, l, q2) in self.transitions:
            labels = [l] if isinstance(l, (int, str)) else l if isinstance(l, (list, tuple, set, frozenset)) else list(l.filtering(values_for(q1)))
            for label in labels:
                assert isinstance(label, (int, str)), "currently, the label of a transition is necessarily an integer or a symbol"
                trs.append((q1, label, q2))
        return trs

    def transitions_to_string(self, scp):
        def _string(t):
            return "".join(
                ["(" + q1 + "," + (l.str_tuple() if isinstance(l, Condition) else str(l)) + "," + q2 + ")" for (q1, l, q2) in t])

        if self.num not in Diagram._cache:
            if options.keep_smart_transitions or all(isinstance(label, (int, str)) for _, label, _ in self.transitions):
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
        error_if(j is None and k is not None, "Automaton.q(): a third index k cannot be given without a second index j")
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
        :example:
            x = VarArray(size=4, dom=range(2))
            a = Automaton(start="q0", final="q1", transitions=[("q0", 0, "q0"), ("q0", 1, "q1"), ("q1", 1, "q1")])
            satisfy(Regular(scope=x, automaton=a))
        """
        super().__init__(transitions)
        error_if(not isinstance(start, str), "The start state of an automaton must be a string, which is not the case of " + repr(start))
        error_if(start not in self.states, "The start state " + repr(start) + " of an automaton must be a state of its transitions")
        self.start = start
        finals = [final] if isinstance(final, str) else list(final) if isinstance(final, (list, tuple, set, frozenset)) else None
        error_if(finals is None or any(not isinstance(q, str) for q in finals),
                 "The final states of an automaton must be given by a string or a collection of strings, which is not the case of " + repr(final))
        # the final states that do not appear in the transitions are discarded, since they cannot be reached
        self.final = sorted(q for q in set(finals) if q in self.states)
        error_if(len(self.final) == 0, "An automaton must have at least one final state appearing in its transitions, which is not the case of " + repr(final))
        self.access = None

    def deterministic_copy(self, scp):
        """
        Returns a deterministic automaton recognizing the same words (subset construction), the labels being the values of the
        domains of the variables of the specified scope. Each state of the copy corresponds to a set of states of this automaton:
        it is named after its state for a singleton, and after its sorted states joined by '_' otherwise (with a suffix if needed,
        so that two states never have the same name).
        """
        nfa = {}  # for each pair (state, symbol), the set of reached states
        for state1, symbol, state2 in self.flat_transitions(flatten(scp)):
            nfa.setdefault((state1, symbol), set()).add(state2)
        symbols = sorted({symbol for (_, symbol) in nfa})
        names = {}  # for each set of states (frozenset), the name of the corresponding state of the copy
        used = set(self.states)  # the names that cannot be given to a set of several states

        def _name(states):
            if len(states) == 1:
                name = next(iter(states))
            else:
                name = base = "_".join(sorted(states))
                k = 1
                while name in used:
                    name, k = base + "_" + str(k), k + 1
            used.add(name)
            names[states] = name
            return name

        start = frozenset([self.start])
        queue, final, transitions = [start], [], []
        _name(start)
        for states in queue:  # the queue is extended while being traversed
            if any(q in self.final for q in states):
                final.append(names[states])
            for symbol in symbols:
                targets = frozenset(q2 for q1 in states for q2 in nfa.get((q1, symbol), ()))
                if len(targets) > 0:
                    if targets not in names:
                        _name(targets)
                        queue.append(targets)
                    transitions.append((names[states], symbol, names[targets]))
        return Automaton(start=names[start], final=final, transitions=transitions)

    def contains(self, t):  # currently can only be used if deterministic automaton
        if self.access is None:
            # TODO control that the automaton is deterministic
            self.access = {(qb, w): qa for (qb, w, qa) in self.transitions}
        state = self.start
        for v in t:
            if (state, v) not in self.access:
                return None
            state = self.access[(state, v)]
        return state in self.final

    def __rec_tuples_for(self, state, i, domains, t, T):
        for v in domains[i]:
            if (state, v) not in self.access:
                continue
            t[i] = v
            if i + 1 == len(domains):
                if self.access[(state, v)] in self.final:
                    T.append(tuple(t))
            else:
                self.__rec_tuples_for(self.access[(state, v)], i + 1, domains, t, T)

    def to_table(self, domains):
        if self.access is None:
            # TODO control that the automaton is deterministic
            self.access = {(qb, w): qa for (qb, w, qa) in self.transitions}
        T = []
        self.__rec_tuples_for(self.start, 0, domains, [0] * len(domains), T)
        # return  [t for t in itertools.product(*domains) if self.contains(t)]  # can be very inefficient
        return T

    def __str__(self):
        return "Automaton(start=" + str(self.start) + ", " + Diagram.__str__(self) + ", final=[" + ",".join(str(v) for v in self.final) + "])"


class MDD(Diagram):
    def __init__(self, transitions):
        """
        Builds an MDD from the specified set of transitions

        :param transitions: a set of transitions
        :example:
            x = VarArray(size=3, dom=range(2))
            m = MDD([("r", 0, "n1"), ("r", 1, "n2"), ("n1", 1, "t"), ("n2", 0, "t")])
            satisfy(x in m)
        """
        if isinstance(transitions, types.GeneratorType):
            transitions = [t for t in transitions]
        unordered = isinstance(transitions, (set, frozenset))
        if unordered:
            transitions = list(transitions)
        if not isinstance(transitions, list):
            error("The transitions of an MDD must be given by a list or a set of 3-tuples, which is not the case of " + repr(transitions))
        super().__init__(transitions)
        self.root, self.terminal, self.levels = None, None, None
        self._check_structure()
        if unordered:  # a deterministic order, level by level from the root (the order of iteration of a set may change from one execution to another)
            self.transitions.sort(key=lambda t: (self.levels[t[0]], t[0], str(t[1]), t[2]))

    def _check_structure(self):
        """
        Checks that the graph of the MDD is acyclic, with a single root and a single terminal node, and that all the paths from the
        root to the terminal node have the same length (section 4.1.2.2 of XCSP3-Core); the level of each node is recorded.
        """
        in_degrees = Counter(q2 for (_, _, q2) in self.transitions)
        successors = defaultdict(list)
        for (q1, _, q2) in self.transitions:
            successors[q1].append(q2)
        roots, terminals = [q for q in self.states if q not in in_degrees], [q for q in self.states if q not in successors]
        error_if(len(roots) != 1, "An MDD must have exactly one root (node without incoming transition), which is not the case: " + str(roots))
        error_if(len(terminals) != 1, "An MDD must have exactly one terminal node (node without outgoing transition), which is not the case: " + str(terminals))
        self.root, self.terminal = roots[0], terminals[0]
        levels = {self.root: 0}
        order = [self.root]
        append = order.append
        for q1 in order:  # topological order (Kahn's algorithm), the list being extended while being traversed
            level = levels[q1] + 1
            for q2 in successors.get(q1, ()):
                current = levels.get(q2)
                if current is None:
                    levels[q2] = level
                elif current != level:
                    error("The paths of an MDD must have all the same length, which is not the case of the paths reaching " + repr(q2))
                in_degrees[q2] -= 1
                if in_degrees[q2] == 0:
                    append(q2)
        self.levels = levels
        if len(order) != len(self.states):
            error("An MDD must be acyclic, which is not the case (some of the nodes " + str([q for q in self.states if q not in set(order)])
                  + " are in a cycle, or can only be reached from a cycle)")

    def depth(self):  # the length of the paths from the root to the terminal node
        return self.levels[self.terminal]

    def _label_values(self, scp):
        """
        For an MDD, the labels given by ranges (conditions) of the transitions leaving a node are developed with the domain of the
        variable of its level (its distance from the root), the length of the paths being the one of the scope.
        """
        return lambda state: scp[self.levels[state]].dom.all_values()

    def __str__(self):
        return "MDD(" + Diagram.__str__(self) + ")"
