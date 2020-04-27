from pycsp3.problems.tests.tester import Tester, run

NAME = "g7_todo"

diff = (Tester(NAME)
        )

same = (Tester(NAME)
        .add("Molnar", data="[3,5]")
        )

xcsp = (Tester(NAME)
        .add(same.instances)
        )

run(xcsp, diff, same)
