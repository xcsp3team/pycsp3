from pycsp3.problems.tests.tester import Tester, run

NAME = "g1_single"

diff = (Tester(NAME)
        .add("Allergy")
        .add("Picnic")
        .add("Purdey")
        .add("Recipe")
        .add("Sandwich")
        .add("Zebra")
        )

same = (Tester(NAME)
        .add("Alpha")
        .add("LabeledDice")
        .add("TrafficLights")
        .add("Witch")
        )

xcsp = (Tester(NAME)
        .add(same.instances)
        .add("Agatha")
        .add("Photo")
        .add("SendMore")
        )

run(diff, same, xcsp)
