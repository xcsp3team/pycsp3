from pycsp3.problems.tests.tester import Tester, run

NAME = "g2_academic"

diff = (Tester(NAME)
        .add("CryptoPuzzle", data="[DONALD,GERALD,ROBERT]")  # ok, aggregation more compact (subgroups in JvCSP)
        .add("DeBruijnSequence", data="[2,5]")
        .add("DiamondFree", data="10")
        .add("GolombRuler", data="8", variant="dec")  # ok, predicate expressions more general (2 sub-groups in JvCSP)
        .add("LowAutocorrelation", data="16")
        .add("Ortholatin", data="10")  # ok, instantiation more compact
        .add("SocialGolfers", data="[4,4,5]")  # ok, instantiation more compact
        .add("SocialGolfers", data="[4,4,5]", variant="01")  # ok, block not formed in JvCSP for lex constraints
        .add("SportsScheduling", data="10")  # ok, class 'dummy-week' put before if in JvCSP
        .add("StillLife", data="[8,8]")
        .add("StillLife", data="[8,8]", variant="wastage")
        )

same = (Tester(NAME)
        .add("AllInterval", data="10")
        .add("AllInterval", data="10", variant="aux")
        .add("Bibd", data="[9,0,0,3,9]")
        .add("Bibd", data="[9,0,0,3,9]", variant="aux")
        .add("BoardColoration", data="[8,10]")
        .add("ChangeMaking", data="10")
        .add("ColouredQueens", data="10")
        .add("CoveringArray", data="[3,5,2,10]")
        .add("CryptoPuzzle", data="[SEND,MORE,MONEY]", variant="carry")
        .add("Dubois", data="10")
        .add("Enigme5", data="[364,55440]")
        .add("GolombRuler", data="8")
        .add("GolombRuler", data="8", variant="aux")
        .add("GracefulGraph", data="[3,5]")
        .add("KnightTour", data="16")
        .add("KnightTour", data="16", variant="table-2")
        .add("KnightTour", data="16", variant="table-3")
        .add("Langford", data="[16,4]")
        .add("LangfordBin", data="16")
        .add("MagicHexagon", data="[4,10]")
        .add("MagicSequence", data="10")
        .add("NumberPartitioning", data="10")
        .add("Opd", data="[4,4,4]")
        .add("Opd", data="[4,6,4]", variant="aux")
        .add("PeacableArmies", data="10", variant="m1")
        .add("PeacableArmies", data="10", variant="m2")
        .add("QuasiGroup", data="10", variant="aux-v3")
        .add("QuasiGroup", data="10", variant="aux-v4")
        .add("QuasiGroup", data="10", variant="aux-v5")
        .add("QuasiGroup", data="10", variant="aux-v7")
        .add("QueenAttacking", data="10")
        .add("Queens", data="10")
        .add("Queens", data="10", variant="v1")
        .add("Queens", data="10", variant="v2")
        .add("Ramsey", data="10")
        .add("SchurrLemma", data="[10,10]")
        .add("SchurrLemma", data="[10,10]", variant="mod")
        .add("Steiner3", data="6")
        .add("Talisman", data="[4,4]")
        .add("WaterBucket", data="[8,5,3,4,4,0,8]")
        )

xcsp = (Tester(NAME)
        .add("AllInterval", data="10")  # 148 solutions (296 without symmetry-breaking)
        .add("AllInterval", data="10", variant="aux")  # 104 solutions  (296 without symmetry-breaking)
        .add("Bibd", data="[6,0,0,3,8]")  # 494 solutions
        .add("Bibd", data="[6,0,0,3,8]", variant="aux")  # 494 solutions
        .add("BoardColoration", data="[8,10]")  # optimum 2
        .add("ChangeMaking", data="10")  # optimum 1
        .add("ChangeMaking", data="10", variant="compact")  # optimum 1
        .add("CoinsGrid", data="[10,4]")  # optimum 98
        .add("ColouredQueens", data="6")  # unsat
        .add("CostasArray", data="10")  # 2160 solutions
        .add("CoveringArray", data="[3,5,2,10]")  # sat
        .add("CryptoPuzzle", data="[SEND,MORE,MONEY]")  # 1 solution
        .add("CryptoPuzzle", data="[SEND,MORE,MONEY]", variant="carry")  # 1 solution
        .add("CryptoPuzzle", data="[DONALD,GERALD,ROBERT]")  # 1 solution
        .add("DeBruijnSequence", data="[2,5]")  # 2048 solutions
        .add("DiamondFree", data="8")  # 17 solutions
        .add("Dubois", data="10")  # unsat
        .add("Enigme5", data="[364,55440]")
        .add("GolombRuler", data="8")  # optimum 34
        .add("GolombRuler", data="8", variant="dec")  # optimum 34
        .add("GolombRuler", data="8", variant="aux")  # optimum 34
        .add("GracefulGraph", data="[3,5]")  # sat
        .add("KnightTour", data="16", options_py="-recognizeSlides")
        .add("KnightTour", data="16", variant="table-2", options_py="-recognizeSlides")
        .add("KnightTour", data="16", variant="table-3", options_py="-recognizeSlides")
        .add("Langford", data="[3,10]")  # 10 solutions
        .add("LangfordBin", data="8")  # 300 solutions
        .add("LowAutocorrelation", data="16")  # optimum 24
        .add("MagicHexagon", data="[4,3]")  # sat
        .add("MagicSequence", data="10")  # 1 solution
        .add("NumberPartitioning", data="8")  # 1 solution
        .add("NumberPartitioning", data="10")  # unsat
        .add("Opd", data="[4,4,4]")  # optimum 4
        .add("Opd", data="[4,6,4]", variant="aux")  # optimum 3
        .add("Ortholatin", data="5")  # 4 solutions
        .add("PeacableArmies", data="6", variant="m1")  # optimum 5
        .add("PeacableArmies", data="6", variant="m2")  # optimum 5
        .add("QuasiGroup", data="8", variant="base-v3")  # 12960 solutions
        .add("QuasiGroup", data="5", variant="base-v4")  # 12 solutions
        .add("QuasiGroup", data="8", variant="base-v5")  # 720 sols
        .add("QuasiGroup", data="8", variant="base-v6")  # 1440 sols
        .add("QuasiGroup", data="9", variant="base-v7")  # 5040 sols
        .add("QuasiGroup", data="8", variant="aux-v3")  # 12960 solutions
        .add("QuasiGroup", data="5", variant="aux-v4")  # 12 solutions
        .add("QuasiGroup", data="8", variant="aux-v5")  # 720 sols
        .add("QuasiGroup", data="9", variant="aux-v7")  # 5040 sols
        .add("QueenAttacking", data="6", options_py="-recognizeSlides")  # optimum 0
        .add("QueenAttacking", data="6", variant="aux", options_py="-recognizeSlides")  # optimum 0
        .add("QueenAttacking", data="6", variant="hybrid", options_py="-recognizeSlides")  # optimum 0
        .add("QueenAttacking", data="6", variant="table", options_py="-recognizeSlides")  # optimum 0
        .add("Queens", data="10")  # 724 solutions
        .add("Queens", data="10", variant="v1")  # 724 solutions
        .add("Queens", data="10", variant="v2")  # 724 solutions
        .add("Ramsey", data="10")  # optimum 2
        .add("SchurrLemma", data="[6,6]")  # 39870 solutions
        .add("SchurrLemma", data="[8,8]", variant="mod")  # 141120 solutions
        .add("SocialGolfers", data="[4,4,5]")  # 2 solutions
        .add("SocialGolfers", data="[4,4,5]", variant="01")  # 2 solutions
        .add("SportsScheduling", data="6")  # 10 solutions
        .add("SportsScheduling", data="6", variant="dummy")  # 10 solutions
        .add("Steiner3", data="7")  # 151200 solutions
        .add("StillLife", data="[7,7]")  # optimum 28
        .add("StillLife", data="[8,8]", variant="wastage")  # optimum 36
        .add("Talisman", data="[4,2]")  # 34714 solutions
        .add("WaterBucket", data="[8,5,3,4,4,0,8]")  # optimum 7
        )

# .add("QuasiGroup", data="10", variant="base-v6")


run(xcsp, diff, same)
