import os

from pycsp3.problems.tests.tester import Tester, run

run(Tester("csp" + os.sep + "complex")
    .add("Areas", data="Areas-3-3-3.json")  # 7 solutions
    .add("Blackhole", data="Blackhole.json", options_py="-recognizeSlides")  # 47232 solutions
    .add("CarSequencing", data="CarSequencing_dingbas.json")  # 6 solutions
    .add("CarSequencing", data="CarSequencing_dingbas.json", variant="table")  # 6 solutions
    .add("Coloring", data="Coloring_rand1.json", variant="csp")  # sat
    .add("Crossword", data="Crossword_vg6-7-ogd.json")  # sat
    .add("Crossword", data="Crossword_h1501-lex.json")  # sat
    .add("Crossword", data="Crossword_h0504-lex.json", variant="alt")  # sat
    .add("Dominoes", data="Dominoes_grid1.json")  # 128 solutions
    .add("Eternity", data="Eternity_07x05.json")  # 32 solutions
    .add("Eternity", data="Eternity_example.txt", prs_py="Eternity_Parser", prs_jv="Eternity_Parser")  # 32 solutions
    .add("Fillomino", data="Fillomino-01.json")  # 22 solutions
    .add("Fillomino", data="Fillomino-08.json")  # sat
    .add("Futoshiki", data="Futoshiki_futo3_0.json")  # 1 solution
    .add("Kakuro", data="Kakuro_easy-000.json")  # 1 solution
    .add("Kakuro", data="Kakuro_easy-000.json", variant="table")  # 1 solution
    .add("LatinSquare", data="LatinSquare_qwh-o030-h320.json")
    .add("LatinSquare2", data="LatinSquare2_7-2-0.json")  # 480 solutions
    .add("Layout", data="Layout_example.json")  # 2 solutions
    .add("Lightup", data="Lightup_example.json")  # 1 solution
    .add("Lightup", data="Lightup_example.txt", prs_py="Lightup_Parser", prs_jv="Lightup_Parser")  # 1 solution
    .add("Lits", data="Lits-example.json")  # 1636 solutions
    .add("MagicSquare", data="[4,None]")  # 7040 solutions
    .add("MagicSquare", data="MagicSquare_example1.txt", prs_py="MagicSquare_Parser", prs_jv="MagicSquare_Parser")
    .add("MarketSplit", data="MarketSplit_04.json")  # 1 solution
    .add("MineSweeper")  # 4 solutions
    .add("MisteryShopper", data="MisteryShopper_04.json")  # 501552 solutions
    .add("Nonogram", data="Nonogram_example.txt", prs_py="Nonogram_Parser", prs_jv="Nonogram_Parser")  # 1 solution
    .add("Nonogram", data="Nonogram_example.txt", prs_py="Nonogram_Parser", prs_jv="Nonogram_Parser", variant="table")  # 1 solution
    .add("RadarSurveillance", data="RadarSurveillance_8-24-3-2-00.json")  # sat
    .add("RectPacking", data="RectPacking_perfect-001.json")
    .add("RoomMate", data="RoomMate_sr0006.json")  # 2 solutions
    .add("Sat", data="Sat_flat30-16.json", variant="clause")  # 1482 solutions
    .add("Sat", data="Sat_flat30-16.json", variant="sum")  # 1482 solutions
    .add("Sat", data="Sat_flat30-16.json", variant="dual")  # 1482 solutions
    .add("Shikaku", data="Shikaku_grid1.json")  # 1 solution
    .add("SolitaireBattleship", data="SolitaireBattleship_sb-12-12-5-0.json")  # 51 solutions
    .add("SolitaireBattleship", data="SolitaireBattleship-battleship_instances-00113.json")  # 1 solution
    .add("Spiral")  # 5 solutions
    .add("Spiral", variant="table")  # 5 solutions
    .add("StableMarriage", data="StableMarriage-example.json")  # 3 solutions
    .add("StripPacking", data="StripPacking_C1P1.json")
    .add("Subisomorphism", data="Subisomorphism_A-01.json")  # 1 solution
    .add("Sudoku", data="[9,None]")  # None can be replaced by null (but not by an empty string in this context)
    .add("Sudoku", data="Sudoku_s13a.json")  # 1 solution
    .add("Sudoku", data="Sudoku_s13a.json", variant="table")  # 1 solution
    .add("Sudoku", data="Sudoku_example.txt", prs_py="Sudoku_Parser", prs_jv="Sudoku_Parser")  # 1 solution
    .add("Survo", data="Survo-01.json")  # 1 solution
    .add("VesselLoading", data="VesselLoading-inst1.json")  # 8 solutions
    .add("VesselLoading", data="VesselLoading-inst2.json")
    .add("Wwtpp", data="Wwtpp_ex04400.json")  # unsat
    .add("Wwtpp", data="Wwtpp_ex04400.json", variant="short")  # unsat
    )
