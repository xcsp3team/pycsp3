from pycsp3 import *

n, prizes = data.n, data.prizes

# s[i] is the node that succeeds to node i in tour (0 for last edge and -1 for unused)
s = VarArray(size=n, dom=range(-1, n))

# p[i] is the position of node i in the tour (-1 if not in the tour)
p = VarArray(size=n, dom=range(-1, n))

# g[i] is the gain obtained from node i in the tour
g = VarArray(size=n, dom=lambda i: set(prizes[i]))


def table(pos):
    # we build the short table for 'vector[index] = value + offset' where index and value are both variables and value assumed to be in vector
    def short_table_for_element(vector, index, value, offset):
        position = protect().execute(next((i for i, x in enumerate(vector) if x == value), -1))  # is value present in the vector?
        assert position != -1  # this current version assumes that fact. Should be generalized in the future
        arity = len(vector) + 1  # since the assumption just above
        tuples = []
        for vi in (v for v in index.dom if 0 <= v < len(vector)):
            if vi == position:
                if offset == 0:  # only case for a support
                    tuples.append(tuple(vi if i == 0 else ANY for i in range(arity)))
            else:
                for vv in (v for v in vector[vi].dom if v - offset in value.dom):
                    tuples.append(tuple(vi if i == 0 else vv if i == 1 + vi else vv - offset if i == 1 + position else ANY for i in range(arity)))
        return tuples

    tbl = short_table_for_element(p, s[pos], p[pos], 1)
    t1, t2 = (-1, *(ANY,) * n), (0, *(ANY,) * n)  # tuple([-1] + [ANY] * n), tuple([0] + [ANY] * n)
    return [t1, t2] + (tbl if pos == 0 else [t for t in tbl[2:] if t[0] != 0])


satisfy(
    p[0] == 0,

    # If used, the next position in tour is not -1
    [iff(p[i] > -1, s[i] > -1) for i in range(n)],

    # Linking s and p
    [[x] + p in table(i) for i, x in enumerate(s)],

    # [imply(s[i] > 0, p[s[i]] == p[i]+1) for i in range(n)],  # TODO alternative to the short table above. How to do that ? meta-constraint ifThen ? reification ?

    # at most one node with i (different from 0) as its successor
    [Count(s, value=i) <= 1 for i in range(n)],

    # managing gains
    [prizes[i][s[i]] == g[i] for i in range(n)]
)

maximize(
    Sum(g)
)
