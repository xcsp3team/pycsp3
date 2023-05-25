"""
See https://en.wikipedia.org/wiki/Boolean_satisfiability_problem

Example of Execution:
  python3 Sat.py -data=Sat_flat30-16.json -variant=clause
  python3 Sat.py -data=Sat_flat30-16.json -variant=sum
  python3 Sat.py -data=Sat_flat30-16.json -variant=dual
"""

from pycsp3 import *

n, e, clauses = data


def scope(clause):
    return [x[abs(j) - 1] for j in clause]


def phases(clause):
    return [j >= 0 for j in clause]


if variant("clause"):
    # x[i] is the ith propositional variable
    x = VarArray(size=n, dom={0, 1})

    satisfy(
        Clause(scope(clause), phases=phases(clause)) for clause in clauses
    )

elif variant("sum"):
    # x[i] is the ith propositional variable
    x = VarArray(size=n, dom={0, 1})

    satisfy(
        scope(clause) * [1 if j >= 0 else -1 for j in clause] != -len([j for j in clause if j < 0]) for clause in clauses
    )

elif variant("dual"):  # dual construction [Bacchus, Extending forward checking, 2000]
    def dual_table(i, j):
        def base_value(decimal_value, length, base):
            t = []
            for _ in range(length):
                t.insert(0, decimal_value % base)
                decimal_value = decimal_value // base
            assert decimal_value == 0, "The given array is too small to contain all the digits of the conversion"
            return t

        def atom_value_at(clause, phasedLitPos, value):
            pos = phasedLitPos if phasedLitPos >= 0 else -phasedLitPos - 1
            return base_value(value, len(clause), 2)[pos] == (1 if phasedLitPos >= 0 else 0)  # > 0 = positive atom

        def check(clause1, clause2, a, b, links):
            return all(atom_value_at(clause1, link[0], a) == atom_value_at(clause2, link[1], b) for link in links)

        c1, c2 = clauses[i], clauses[j]
        links = [(i if c1[i] > 0 else -i - 1, j if c2[j] > 0 else -j - 1) for i in range(len(c1)) for j in range(len(c2)) if abs(c1[i]) == abs(c2[j])]
        return None if len(links) == 0 else [(v1, v2) for v1 in range(1, 2 ** len(c1)) for v2 in range(1, 2 ** len(c2)) if check(c1, c2, v1, v2, links)]


    x = VarArray(size=e, dom=lambda i: range(1, 2 ** len(clauses[i])))

    satisfy(
        (x[i], x[j]) in dual_table(i, j) for i, j in combinations(e, 2) if dual_table(i, j)
    )
