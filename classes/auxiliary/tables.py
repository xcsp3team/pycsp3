import itertools

from pycsp3.classes.auxiliary import conditions
from pycsp3.classes.main.variables import Domain
from pycsp3.tools.utilities import ANY


def _remove_condition_nodes_of_table(table, doms):  # convert hybrid binary and ternary conditions into ordinary tuples
    def _remove_condition_nodes_of_tuple():
        r = len(t)
        pos = next((i for i in range(r) if isinstance(t[i], conditions.ConditionNode)), -1)
        if pos == -1:
            return t
        ind, res = t[pos].evaluate(t, doms)
        assert len(ind) in (1, 2)
        return (tuple(v if i == pos else st[0] if i == ind[0] else st[1] if len(ind) == 2 and i == ind[1] else t[i] for i in range(r))
                for v in doms[pos] for st in res if t[pos].operator.check(v, st[-1]))

    done = []
    todo = table
    while len(todo) > 0:
        t = todo.pop(0)
        res = _remove_condition_nodes_of_tuple()
        if res is t:
            done.append(t)
        else:
            todo.extend(res)
    return done


def to_ordinary_table(table, domains, *, possibly_starred=False):
    """
    Converts the specified table that may contain hybrid restrictions and stars into an ordinary table (or a starred table).
    The table contains r-tuples and the domain to be considered are any index i of the tuples is given by domains[i].
    In case, domains[i] is an integer, it is automatically transformed into a range.

    :param table: a table (possibly hybrid or starred)
    :param domains: the domains of integers to be considered for each column of the table
    :param possibly_starred: if True, the returned table may be starred (and not purely ordinary)
    :return: an ordinary or starred table
    """

    def _tuple_of_interest(t):
        for v in t:
            if isinstance(v, conditions.Condition):  # v may be a Condition object (with method 'filtering')
                return True
            if not possibly_starred and v == ANY:
                return True
        return False

    def _develop_tuple(t):
        development = ({v} if isinstance(v, int) else ({v} if possibly_starred else doms[i]) if v == ANY
        else [w for w in v if w in doms[i]] if isinstance(v, (list, tuple, set, frozenset))
        else v.filtering(doms[i]) for i, v in enumerate(t))
        return itertools.product(*development)

    doms = [range(d) if isinstance(d, int) else d.all_values() if isinstance(d, Domain) else d for d in domains]
    T = list()  # we use a list because its processing is faster than a set
    contains_node_condition = False
    for t in table:
        if _tuple_of_interest(t):
            if contains_node_condition is False and any(isinstance(v, conditions.ConditionNode) for v in t):
                contains_node_condition = True
            T.extend(_develop_tuple(t))
        else:
            T.append(t)
    # last removal actions below must be performed after removing other kind of conditions
    return T if not contains_node_condition else _remove_condition_nodes_of_table(list(T), doms)


def to_reified_ordinary_table(table, domains):
    assert len(table) > 0 and len(domains) == len(table[0])
    table = sorted(table)
    assert all(isinstance(v, int) for t in table for v in t)  # currently, only possible on ordinary tables
    i, T = 0, []
    for valid in itertools.product(*[range(d) if isinstance(d, int) else d.all_values() if isinstance(d, Domain) else d for d in domains]):
        if i < len(table) and table[i] == valid:
            T.append((*valid, 1))
            i += 1
        else:
            T.append((*valid, 0))
    return T


def _non_overlapping_tuples_for(t, dom1, dom2, offset, first, x_axis=None):
    for va in dom1:
        for vb in reversed(dom2.all_values()):
            if va + offset > vb:
                break
            sub = (va, vb) if first else (vb, va)
            t.append(sub if x_axis is None else sub + (ANY, ANY) if x_axis else (ANY, ANY) + sub)


def to_starred_table_for_no_overlap1(x1, x2, w1, w2):
    t = []
    _non_overlapping_tuples_for(t, x1.dom, x2.dom, w1, True)
    _non_overlapping_tuples_for(t, x2.dom, x1.dom, w2, False)
    return t


def to_starred_table_for_no_overlap2(x1, x2, y1, y2, w1, w2, h1, h2):
    t = []
    _non_overlapping_tuples_for(t, x1.dom, x2.dom, w1, True, True)
    _non_overlapping_tuples_for(t, x2.dom, x1.dom, w2, False, True)
    _non_overlapping_tuples_for(t, y1.dom, y2.dom, h1, True, False)
    _non_overlapping_tuples_for(t, y2.dom, y1.dom, h2, False, False)
    return t
