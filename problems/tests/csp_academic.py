import os

from pycsp3.problems.tests.tester import Tester, run

run(Tester("csp" + os.sep + "academic")
    .add("AllInterval", data="10")  # 148 solutions (296 without symmetry-breaking)
    .add("AllInterval", data="10", variant="aux")  # 104 solutions  (296 without symmetry-breaking)
    .add("Bibd", data="[6,0,0,3,8]")  # 494 solutions
    .add("Bibd", data="[6,0,0,3,8]", variant="aux")  # 494 solutions
    .add("ColouredQueens", data="6")  # unsat
    .add("CostasArray", data="10")  # 2160 solutions
    .add("CoveringArray", data="[3,5,2,10]")  # sat
    .add("CryptoPuzzle", data="[SEND,MORE,MONEY]")  # 1 solution
    .add("CryptoPuzzle", data="[SEND,MORE,MONEY]", variant="carry")  # 1 solution
    .add("CryptoPuzzle", data="[DONALD,GERALD,ROBERT]")  # 1 solution
    .add("DeBruijnSequence", data="[2,5]")  # 2048 solutions
    .add("DiamondFree", data="8")  # 17 solutions
    .add("Domino", data="[200,200]")  # 1 solution
    .add("Domino", data="[200,200]", variant="table", options_py="-recognizeSlides")  # 1 solution
    .add("Dubois", data="10")  # unsat
    .add("Enigme5", data="[364,55440]")
    .add("GracefulGraph", data="[3,5]")  # sat
    .add("KnightTour", data="16", options_py="-recognizeSlides")
    .add("KnightTour", data="16", variant="table-2", options_py="-recognizeSlides")
    .add("KnightTour", data="16", variant="table-3", options_py="-recognizeSlides")
    .add("Langford", data="[3,10]")  # 10 solutions
    .add("LangfordBin", data="8")  # 300 solutions
    .add("MagicHexagon", data="[4,3]")  # sat
    .add("MagicSequence", data="10")  # 1 solution
    .add("NumberPartitioning", data="8")  # 1 solution
    .add("NumberPartitioning", data="10")  # unsat
    .add("Ortholatin", data="5")  # 4 solutions
    .add("Pigeons", data="6")  # unsat
    .add("Pigeons", data="6", variant="dec")  # unsat
    .add("PropStress", data="20")
    .add("QuasiGroup", data="8", variant="base-v3")  # 12960 solutions
    .add("QuasiGroup", data="5", variant="base-v4")  # 12 solutions
    .add("QuasiGroup", data="8", variant="base-v5")  # 720 sols
    .add("QuasiGroup", data="8", variant="base-v6")  # 1440 sols
    .add("QuasiGroup", data="9", variant="base-v7")  # 5040 sols
    .add("QuasiGroup", data="8", variant="aux-v3")  # 12960 solutions
    .add("QuasiGroup", data="5", variant="aux-v4")  # 12 solutions
    .add("QuasiGroup", data="8", variant="aux-v5")  # 720 sols
    .add("QuasiGroup", data="9", variant="aux-v7")  # 5040 sols
    .add("Queens", data="10")  # 724 solutions
    .add("Queens", data="10", variant="v1")  # 724 solutions
    .add("Queens", data="10", variant="v2")  # 724 solutions
    .add("QueensKnights", data="[6,4]")  # 1664 solutions
    .add("QueensKnights", data="[10,5]")  # unsat
    .add("SchurrLemma", data="[6,6]")  # 39870 solutions
    .add("SchurrLemma", data="[8,8]", variant="mod")  # 141120 solutions
    .add("SocialGolfers", data="[4,4,5]")  # 2 solutions
    .add("SocialGolfers", data="[4,4,5]", variant="01")  # 2 solutions
    .add("SportsScheduling", data="6")  # 10 solutions
    .add("SportsScheduling", data="6", variant="dummy")  # 10 solutions
    .add("Steiner3", data="7")  # 151200 solutions
    .add("Superpermutation", data="3")  # 1 solution
    .add("Superpermutation", data="3", variant="table")  # 1 solution
    .add("Talisman", data="[4,2]")  # 34714 solutions
     # .add("WordDesign", data="[WordDesign.json,n=5]")  # sat  (pb in testing mode due to special way of setting parameters (pb with path)
    )

