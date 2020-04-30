from pycsp3.problems.tests.tester import Tester, run

NAME = "g5_special"

diff = (Tester(NAME)
        )

same = (Tester(NAME)
        .add("DistinctVectors", data="[10,6,4]")
        .add("Domino", data="[200,200]")
        .add("Domino", data="[200,200]", variant="table")
        .add("Hanoi", data="5")
        .add("Knights", data="[16,4]")
        .add("Pigeons", data="6")
        .add("Pigeons", data="6", variant="dec")
        .add("Pions", data="[6,4]")
        .add("PropStress", data="20")
        .add("QueensPions", data="[6,4,3]")
        .add("QueensPions", data="[6,4,3]", variant="mul")
        )

xcsp = (Tester(NAME)
        .add("DistinctVectors", data="[10,6,4]")
        .add("Domino", data="[200,200]")
        .add("Domino", data="[200,200]", variant="table", options_py="-recognizeSlides")
        .add("Hanoi", data="5", options_py="-recognizeSlides")
        .add("Knights", data="[16,4]", options_py="-recognizeSlides")
        .add("Pigeons", data="6")
        .add("Pigeons", data="6", variant="dec")
        .add("Pions", data="[6,4]")
        .add("PropStress", data="20")
        .add("QueensPions", data="[6,4,3]")
        .add("QueensPions", data="[6,4,3]", variant="mul")
        )

run(xcsp,diff, same)
