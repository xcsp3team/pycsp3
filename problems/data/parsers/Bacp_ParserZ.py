from pycsp3.problems.data.parsing import *

data["nCourses"] = number_in(next_line())
data["nPeriods"] = number_in(next_line())
data["minCredits"] = number_in(next_line())
data["maxCredits"] = number_in(next_line())
data["minCourses"] = number_in(next_line())
data["maxCourses"] = number_in(next_line())
data["credits"] = numbers_in(next_line())

assert data["nCourses"] == len(data["credits"])

data["prerequisites"] = [[int(v) - 1 for v in re.split(r'constraint prerequisite\(|,|\);', line) if len(v) > 0] for line in remaining_lines(skip_curr=True)]
