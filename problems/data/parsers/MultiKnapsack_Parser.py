from pycsp3.problems.data.parsing import *

n = next_int()  # number of variables
e = next_int()  # number of constraints
next_line()

objective_coefficients = [next_int() for _ in range(n)]  # objective coefficients
coefficients = [[next_int() for _ in range(n)] for _ in range(e)]  # constraint coefficients
limits = [next_int() for _ in range(e)]  # constraint limits

assert e == len(coefficients) == len(limits)

data["coefficients"] = objective_coefficients
data["constraints"] = [OrderedDict([("coeffs", coefficients[i]), ("limit", limits[i])]) for i in range(e)]
