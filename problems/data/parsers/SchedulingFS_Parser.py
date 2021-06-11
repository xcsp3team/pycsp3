from pycsp3.problems.data.parsing import *

nJobs = next_int()
nComputers = next_int()
next_line(repeat=2)

print("nJobs: ", nJobs)
print("nComputers: ", nComputers)

data["durations"] = []

for idJobs in range(nJobs):
  data["durations"].append([next_int() for i in range(nComputers)])
  next_line(repeat=1)
  
