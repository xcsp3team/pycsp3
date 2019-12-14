from pycsp3.problems.data.dataparser import *

n = next_int()  # number of variables
e = next_int()  # numbe rof constraints
next_line()

data.coefficients = [next_int() for _ in range(n)]  # objective coefficients
coefficients = [[next_int() for _ in range(n)] for _ in range(e)]  # constraint coefficients
limits = [next_int() for _ in range(e)]  # constraint limits

assert e == len(coefficients) == len(limits)

data.constraints = [DataDict({"coeffs": coefficients[i], "limit": limits[i]}) for i in range(e)]
