from pycsp3.problems.tests.tester import Tester, run

NAME = "g1_single"

diff = (Tester(NAME)
        .add("Allergy")
        .add("Alpha")
        .add("Picnic")
        .add("Purdey")
        .add("Recipe")
        .add("Sandwich")
        .add("Zebra")
        )

same = (Tester(NAME)
        .add("LabeledDice")
        .add("TrafficLights")
        .add("Witch")
        )

xcsp = (Tester(NAME)
        .add("Agatha")  # 4 solutions
        .add("Allergy")  # 1 solution
        .add("Alpha")  # 1 solution
        .add("Alpha", variant="var")  # 1 solution
        .add("LabeledDice")  # 48 solutions
        .add("NFractions")  # 22 solutions
        .add("Photo")  # optimum 2
        .add("Photo", variant="aux")  # optimum 2
        .add("Picnic")  # 1 solution
        .add("Purdey")  # 1 solution
        .add("Recipe")  # optimum 1700
        .add("Sandwich")  # 8 solutions
        .add("SendMore")  # 1 solution
        .add("TrafficLights")  # 4 solutions
        .add("Witch")  # optimum 1300
        .add("Zebra")  # 48 solutions
        )

run(xcsp, diff, same)
