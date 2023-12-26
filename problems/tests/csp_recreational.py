import os

from pycsp3.problems.tests.tester import Tester, run

run(Tester("csp", "recreational")
    .add("Areas", data="3-3-3.json")  # 7 solutions
    .add("Blackhole", data="example.json", options_py="-recognizeSlides")  # 47232 solutions
    .add("Coloring", data="rand01.json", variant="csp")  # sat
    .add("Crossword", data="vg6-7-ogd.json", subdir="data")  # sat
    .add("Crossword", data="h1501-lex.json", subdir="data")  # sat
    .add("Crossword", data="h0504-lex.json", variant="alt", subdir="data")  # sat
    .add("Dominoes", data="grid01.json")  # 128 solutions
    .add("Eternity", data="07x05.json", subdir="data")  # 32 solutions
    .add("Eternity", data="07x05.txt", prs_py="Eternity_Parser", subdir="data")  # 32 solutions
    .add("Fillomino", data="01.json", subdir="data")  # 22 solutions
    .add("Fillomino", data="08.json")  # sat
    .add("Futoshiki", data="futo3-0.json")  # 1 solution
    .add("Kakuro", data="easy-000.json")  # 1 solution
    .add("Kakuro", data="easy-000.json", variant="table")  # 1 solution
    .add("LatinSquare", data="qwh-o030-h320.json")
    .add("LatinSquare", version="LatinSquare2", data="7-2-0.json")  # 480 solutions
    .add("Layout", data="example.json")  # 2 solutions
    .add("Lightup", data="example.json")  # 1 solution
    .add("Lightup", data="example.txt", prs_py="Lightup_Parser", subdir="data")  # 1 solution
    .add("Lits", data="example.json")  # 1636 solutions
    .add("MagicSquare", data="[4,None]")  # 7040 solutions
    .add("MagicSquare", data="example01.txt", prs_py="MagicSquare_Parser", subdir="data")
    .add("MarketSplit", data="04.json")  # 1 solution
    .add("MineSweeper")  # 4 solutions
    .add("MisteryShopper", data="04.json")  # 501552 solutions
    .add("Nonogram", data="example.txt", prs_py="Nonogram_Parser", subdir="data")  # 1 solution
    .add("Nonogram", data="example.txt", prs_py="Nonogram_Parser", variant="table", subdir="data")  # 1 solution
    .add("RoomMate", data="sr0006.json")  # 2 solutions
    .add("Shikaku", data="grid01.json")  # 1 solution
    .add("SolitaireBattleship", data="12-12-5-0.json")  # 51 solutions
    .add("SolitaireBattleship", data="00113.json")  # 1 solution
    .add("Spiral")  # 5 solutions
    .add("Spiral", variant="table")  # 5 solutions
    .add("StableMarriage", data="example.json")  # 3 solutions
    .add("StripPacking", data="C1P1.json")
    .add("Subisomorphism", data="A-01.json")  # 1 solution
    .add("Sudoku", data="[9,None]")  # None can be replaced by null (but not by an empty string in this context)
    .add("Sudoku", data="s13a.json")  # 1 solution
    .add("Sudoku", data="s13a.json", variant="table")  # 1 solution
    .add("Sudoku", data="example.txt", prs_py="Sudoku_Parser", subdir="data")  # 1 solution
    .add("Survo", data="01.json")  # 1 solution
    )
