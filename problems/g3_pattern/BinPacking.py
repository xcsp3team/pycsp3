from pycsp3 import *

capacity = data.binCapacity
weights = sorted(data.itemWeights)
nItems = len(weights)


def n_bins():
    cnt = 0
    curr_load = 0
    for i, weight in enumerate(weights):
        curr_load += weight
        if curr_load > capacity:
            cnt += 1
            curr_load = weight
    return cnt


def max_items_per_bin():
    curr = 0
    for i, weight in enumerate(weights):
        curr += weight
        if curr > capacity:
            return i
    return -1


def occurrences_of_weights():
    pairs = []
    cnt = 1
    for i in range(1, len(weights)):
        if weights[i] != weights[i - 1]:
            pairs.append((weights[i - 1], cnt))
            cnt = 0
        cnt += 1
    pairs.append((weights[-1], cnt))
    return pairs


nBins, maxPerBin = n_bins(), max_items_per_bin()

# u is the number of unused bins
u = Var(dom=range(nBins + 1))

# w[i][j] indicates the weight of the jth object put in the ith bin. It is 0 if there is no object at this place.
w = VarArray(size=[nBins, maxPerBin], dom={0} | set(weights))

if not variant():
    satisfy(
        # not exceeding the capacity of each bin
        [Sum(row) <= capacity for row in w],

        # items are stored decreasingly in each bin according to their weights
        [Decreasing(row) for row in w]
    )
elif variant("table"):
    def table():
        def table_recursive(n_stored, i, curr):
            if len(tuples) > 200000000:  # hard coding (value)
                raise Exception("impossible to build a table of moderate size")
            assert curr + weights[i] <= capacity
            tmp[n_stored] = weights[i]
            n_stored += 1
            curr += weights[i]
            tuples.add(tuple(tmp[j] if j < n_stored else 0 for j in range(len(tmp))))
            for j in range(i):
                if curr + weights[j] > capacity:
                    break
                if j == i - 1 or weights[j] != weights[j + 1]:
                    table_recursive(n_stored, j, curr)

        tuples = set()
        tmp = [0] * maxPerBin
        tuples.add(tuple(tmp))
        for i in range(nItems):
            if i == nItems - 1 or weights[i] != weights[i + 1]:
                table_recursive(0, i, 0)
        return tuples


    table = table()
    satisfy(
        row in table for row in w
    )

satisfy(
    # ensuring that each item is stored in a bin
    Cardinality(w, occurrences={0: nBins * maxPerBin - nItems} + {weight: occ for (weight, occ) in occurrences_of_weights()}),

    # tag(symmetry-breaking)
    LexDecreasing(w),

    # counting the number of unused bins
    Count(w[:, 0], value=0) == u
)

maximize(
    # maximizing the number of unused bins
    u
)
