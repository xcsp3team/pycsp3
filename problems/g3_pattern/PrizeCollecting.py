from pycsp3 import *


# TODO : in progress

n, prizes = data.n, data.prizes
prizes = cp_array(row + [0] for row in prizes)  # we add 0 for unused nodes; note that cp_array is required so as to be able to use the constraint 'element'

# s[i] is the node that succeeds to the ith node in the tour ('n' if unused)
s = VarArray(size=n, dom=range(n + 1))

# p[i] is the position of the ith node in the tour ('n' if unused)
p = VarArray(size=n + 1 if not variant() else n, dom=range(n + 1))

# g[i] is the gain collected when going from the ith node to its successor in the tour
g = VarArray(size=n, dom=lambda i: set(prizes[i]))

satisfy(
    # node 0 is the first node of the tour
    p[0] == 0,

    # managing unused nodes
    [iff(p[i] != n, s[i] != n) for i in range(n)],

    # each node appears at most once during the tour
    [Count(s, value=i) <= 1 for i in range(n)],

    # computing gains
    [prizes[i][s[i]] == g[i] for i in range(n)]
)

if not variant():
    # z[i] is the position of the successor of the ith node in the tour
    z = VarArray(size=n, dom=range(n + 1))


    def tab():
        return {(0, ANY, 0), (n, n, n)} | {(i, j, j + 1) for i in range(1, n) for j in range(0, n - 1)}


    print(sorted(list(tab())))

    satisfy(
        p[n] == n,

        #        [(s[i], p[i], z[i]) in tab() for i in range(n)],

        [imply(p[i] == n - 1, z[i] != n) for i in range(n)],

        [z[i] == ift(s[i] == 0, 0, ift(s[i] == n, n, p[i] + 1)) for i in range(n)],

        [p[s[i]] == z[i] for i in range(n)]
    )


elif variant("table"):
    def table(pos):
        tbl = {(0,) + (ANY,) * n, (n,) + (ANY,) * n}  # tuple([-1] + [ANY] * n), tuple([0] + [ANY] * n)
        for vi in range(n):
            if vi != pos and (vi != 0 or pos == 0):
                for vv in range(1, n):
                    tbl.add((vi,) + tuple(vv if i == vi else vv - 1 if i == pos else ANY for i in range(n)))
        return tbl


    satisfy(
        s[0] == 1,
        s[1] == 2,
        s[2] == 3,
        s[3] == 4,

        # linking variables from s and p
        [(s[i], *p) in table(i) for i in range(n)]
    )

maximize(
    # maximizing the sum of collected gains
    Sum(g)
)



# [imply(s[i] > 0, p[s[i]] == p[i]+1) for i in range(n)],  # TODO alternative to the short table above. How to do that ? meta-constraint ifThen ? reification ?
