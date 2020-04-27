from pycsp3.problems.data.parsing import *

nRestaurants = number_in(line())
next_line()
names = [next_line()[1:-2] for _ in range(nRestaurants)]
names[-1] = names[-1][:-1]  # because an additional symbol ']' on this line
next_line()
positions = [number_in(next_line()) for _ in range(nRestaurants)]

data["nDepots"] = number_in(next_line())
data["restaurants"] = [OrderedDict([("name", names[i]), ("position", positions[i])]) for i in range(nRestaurants)]
