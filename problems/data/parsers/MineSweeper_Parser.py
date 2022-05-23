from pycsp3.problems.data.parsing import *

n = number_in(line())
m = number_in(next_line())
data['puzzle'] = [[-1 if c == '.' else int(c) for c in next_line()] for _ in range(n)]
