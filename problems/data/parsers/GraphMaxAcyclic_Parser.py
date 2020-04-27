from pycsp3.problems.data.parsing import *

while line()[0] == '%':
    next_line()  # To pass comments

t = numbers_in(line())
assert len(t) == 3 and t[2] == 1

n = t[0]
arcs = [[0 for _ in range(n)] for _ in range(n)]
for i in range(n):
    t = numbers_in(next_line())
    for j in range(0, len(t), 2):
        arcs[i][t[j] - 1] = t[j + 1]

data["nNodes"] = n
data["arcs"] = arcs

# data.nNodes = 20
# maxWeight = 30
# p = 0.8
# data.arcs=[]
# for i in range(data.nNodes):
#    tmp = []
#    for j in range(data.nNodes):
#        if random.uniform(0,1) > p:
#           tmp.append(random.randint(0,maxWeight))
#        else:tmp.append(0)
