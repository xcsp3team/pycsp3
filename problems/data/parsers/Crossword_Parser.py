from pycsp3.problems.data.parsing import *

n, m = numbers_in(line())
lines = [next_line() for _ in range(n)]
data['spots'] = [[0 if c == '_' else 1 for c in l[l.index("(") + 1:l.rindex(")")].split(" ")] for l in lines]
line = next_line()
assert line.startswith("dict=")
data['dict'] = line[line.index("=") + 1:]
