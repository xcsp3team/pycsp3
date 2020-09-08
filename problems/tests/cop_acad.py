import os

from pycsp3.problems.tests.tester import Tester, run

run(Tester("cop" + os.sep + "academic")
    .add("BoardColoration", data="[8,10]")  # optimum 2
    .add("ChangeMaking", data="10")  # optimum 1
    .add("ChangeMaking", data="10", variant="compact")  # optimum 1
    .add("CoinsGrid", data="[10,4]")  # optimum 98
    .add("GolombRuler", data="8")  # optimum 34
    .add("GolombRuler", data="8", variant="dec")  # optimum 34
    .add("GolombRuler", data="8", variant="aux")  # optimum 34
    .add("LowAutocorrelation", data="16")  # optimum 24
    .add("Opd", data="[4,4,4]")  # optimum 4
    .add("Opd", data="[4,6,4]", variant="aux")  # optimum 3
    .add("PeacableArmies", data="6", variant="m1")  # optimum 5
    .add("PeacableArmies", data="6", variant="m2")  # optimum 5
    .add("QueenAttacking", data="6", options_py="-recognizeSlides")  # optimum 0
    .add("QueenAttacking", data="6", variant="aux", options_py="-recognizeSlides")  # optimum 0
    .add("QueenAttacking", data="6", variant="hybrid", options_py="-recognizeSlides")  # optimum 0
    .add("QueenAttacking", data="6", variant="table", options_py="-recognizeSlides")  # optimum 0
    .add("Ramsey", data="10")  # optimum 2
    .add("StillLife", data="[7,7]")  # optimum 28
    .add("StillLife", data="[8,8]", variant="wastage")  # optimum 36
    .add("WaterBucket", data="[8,5,3,4,4,0,8]")  # optimum 7
    )
