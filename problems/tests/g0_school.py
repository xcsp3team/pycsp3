from pycsp3.problems.tests.tester import Tester, run

NAME = "g0_school"

diff = (Tester(NAME)
        )

same = (Tester(NAME)
        .add("Pic")
        .add("Pic2")
        .add("Riddle")
        .add("Riddle2")
        .add("Riddle3a")
        .add("Riddle3b")
        .add("Riddle4a")
        .add("Riddle4b")
        .add("Riddle5")
        .add("SimpleColoring")
        )

xcsp = (Tester(NAME)
        .add(same.instances)
        )

run(xcsp, diff, same)
