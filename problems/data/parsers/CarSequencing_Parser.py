from pycsp3.problems.data.parsing import *

nCars, nOptions, nClasses = numbers_in(line())
nums = numbers_in(next_line())
dens = numbers_in(next_line())

t = [numbers_in(next_line()) for _ in range(nClasses)]
assert sum(t[i][1] for i in range(nClasses)) == nCars
assert all(t[i][0] == i for i in range(nClasses))
data["classes"] = [OrderedDict([("demand", t[i][1]), ("options", t[i][2:])]) for i in range(nClasses)]
data["limits"] = [OrderedDict([("num", nums[i]), ("den", dens[i])]) for i in range(nOptions)]
