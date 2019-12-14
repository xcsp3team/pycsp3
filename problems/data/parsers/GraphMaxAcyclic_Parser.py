from pycsp3.problems.data.dataparser import *

while line()[0] == '%':
    next_line()  # To pass comments

t = numbers_in(line())
assert len(t) == 3 and t[2] == 1

data.nNodes = t[0]
data.arcs = [[0 for _ in range(data.nNodes)] for _ in range(data.nNodes)]

for i in range(data.nNodes):
    t = numbers_in(next_line())
    for j in range(0, len(t), 2):
        data.arcs[i][t[j] - 1] = t[j + 1]



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
