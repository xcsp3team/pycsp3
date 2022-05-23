from pycsp3.problems.data.parsing import *

n = number_in(line())  # height
width = number_in(next_line())
assert n == width
maxShip = number_in(next_line())
ships = numbers_in(next_line())
assert maxShip == len(ships)
data["fleet"] = [OrderedDict([("size", i + 1), ("cnt", v)]) for i, v in enumerate(ships) if v > 0]
next_line()
hints = [numbers_in(next_line()) for _ in range(n)]
assert all(v == 0 for row in hints for v in row)  # for the moment, no hints
data['hints'] = None
data['rsums'] = numbers_in(next_line())
data['csums'] = numbers_in(next_line())
assert n == len(data['rsums']) == len(data['csums'])
