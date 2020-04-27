from pycsp3.problems.tests.tester import Tester, run

NAME = "g3_pattern"

diff = (Tester(NAME)
        .add("Dominoes", data="Dominoes_grid1.json")  # ok, unary constraints managed differently
        .add("Fastfood", data="Fastfood_ff01.json")
        .add("Fastfood", data="Fastfood_ff01.json", variant="table")
        .add("Fastfood", data="Fastfood_example.dzn", prs_py="Fastfood_ParserZ", prs_jv="Fastfood_ParserZ")
        .add("Kakuro", data="Kakuro_easy-000.json")
        .add("Lightup", data="Lightup_example.txt", prs_py="Lightup_Parser", prs_jv="Lightup_Parser")  # ok, JvCSP more compact because reordering vars in count
        .add("MarketSplit", data="MarketSplit_04.json")
        .add("MultiKnapsack", data="MultiKnapsack_example.txt", prs_py="MultiKnapsack_Parser", prs_jv="MultiKnapsack_Parser")
        .add("OpenStacks", data="OpenStacks_example.dzn", prs_py="OpenStacks_ParserZ", prs_jv="OpenStacks_ParserZ", variant="m1")
        .add("OpenStacks", data="OpenStacks_example.dzn", prs_py="OpenStacks_ParserZ", prs_jv="OpenStacks_ParserZ", variant="m2")
        .add("ProgressiveParty", data="ProgressiveParty_example.txt", prs_py="ProgressiveParty_Parser", prs_jv="ProgressiveParty_Parser", special=True)
        # ok, group of alldiffExcept in PyCSp contrary to JvCSP
        # .add("BinPacking", data="BinPacking_n1c1w4a.json", variant="mdd", special=True)
        )

same = (Tester(NAME)
        .add("Auction", data="Auction_example.json")
        .add("Auction", data="Auction_example.txt", prs_py="Auction_Parser", prs_jv="Auction_Parser")
        .add("BinPacking", data="BinPacking_n1c1w4a.json")
        .add("BinPacking", data="BinPacking_n1c1w4a.json", variant="table")
        .add("BinPacking", data="BinPacking_example.txt", prs_py="BinPacking_Parser", prs_jv="BinPacking_Parser")
        .add("Blackhole", data="Blackhole.json")
        .add("Bugs", data="Bugs_example.json")
        .add("Bugs", data="Bugs_example.txt", prs_py="Bugs_Parser", prs_jv="Bugs_Parser")
        .add("BusScheduling", data="BusScheduling_c1a.json")
        .add("BusScheduling", data="BusScheduling_r1.json")
        .add("BusScheduling", data="BusScheduling_t1.json")
        .add("Coloring", data="Coloring_rand1.json")
        .add("Coloring", data="Coloring_rand1.json", variant="csp")
        .add("Cutstock", data="Cutstock_small.json")
        .add("Eternity", data="Eternity_07x05.json")
        .add("Eternity", data="Eternity_example.txt", prs_py="Eternity_Parser", prs_jv="Eternity_Parser")
        .add("Futoshiki", data="Futoshiki_futo3_0.json")
        .add("GraphColoring", data="GraphColoring_1-fullins-3.json")
        .add("GraphColoring", data="GraphColoring_1-fullins-3.json", variant="sum")
        .add("GraphColoring", data="GraphColoring_qwhdec-o18-h120-1.json")
        .add("GraphColoring", data="GraphColoring_qwhdec-o18-h120-1.json", variant="sum")
        .add("GraphMaxAcyclic", data="GraphMaxAcyclic_example.txt", prs_py="GraphMaxAcyclic_Parser", prs_jv="GraphMaxAcyclic_Parser")
        .add("GraphMaxAcyclic", data="GraphMaxAcyclic_example.txt", prs_py="GraphMaxAcyclic_Parser", prs_jv="GraphMaxAcyclic_Parser", variant="cnt")
        .add("HCPizza", data="HCPizza_tiny.txt", prs_py="HCPizza_Parser", prs_jv="HCPizza_Parser")
        .add("HCPizza", data="HCPizza_small.txt", prs_py="HCPizza_Parser", prs_jv="HCPizza_Parser")
        .add("Kakuro", data="Kakuro_easy-000.json", variant="table")
        .add("Knapsack", data="Knapsack_20-50-00.json")
        .add("LatinSquare", data="LatinSquare_qwh-o030-h320.json")
        .add("LatinSquareB", data="LatinSquare2_7-2-0.json")
        .add("LinearArrangement", data="LinearArrangement_04.json")
        .add("MagicSquare", data="MagicSquare_example0.txt", prs_py="MagicSquare_Parser", prs_jv="MagicSquare_Parser")
        .add("MagicSquare", data="MagicSquare_example1.txt", prs_py="MagicSquare_Parser", prs_jv="MagicSquare_Parser")
        .add("Mario", data="Mario_easy-2.json")
        .add("Mario", data="Mario_easy-2.json", variant="table")
        .add("Nonogram", data="Nonogram_example.txt", prs_py="Nonogram_Parser", prs_jv="Nonogram_Parser")
        .add("Nonogram", data="Nonogram_example.txt", prs_py="Nonogram_Parser", prs_jv="Nonogram_Parser", variant="table")
        .add("PrizeCollecting", data="PrizeCollecting_example.dzn", prs_py="PrizeCollecting_ParserZ", prs_jv="PrizeCollecting_ParserZ", special=True)
        .add("PseudoBoolean", data="PseudoBoolean_example.opb", prs_py="PseudoBoolean_Parser", prs_jv="PseudoBoolean_Parser")
        .add("RectPacking", data="RectPacking_perfect-001.json", special=True)
        .add("RoomMate", data="RoomMate_sr0006.json")
        .add("Sat", data="Sat_flat30-16.json", variant="sum")
        .add("Sat", data="Sat_flat30-16.json", variant="dual")
        .add("Sat", data="Sat_flat30-16.json", variant="clause")
        .add("Shikaku", data="Shikaku_grid1.json")
        .add("Sonet", data="Sonet_sonet1.json")
        .add("Sonet", data="Sonet_sonet3-4.json")
        .add("StripPacking", data="StripPacking_C1P1.json")
        .add("Subisomorphism", data="Subisomorphism_A-01.json")
        .add("Sudoku", data="Sudoku_s13a.json")
        .add("Sudoku", data="Sudoku_s13a.json", variant="table")
        .add("Sudoku", data="Sudoku_example.txt", prs_py="Sudoku_Parser", prs_jv="Sudoku_Parser")
        .add("TravelingSalesman", data="TravelingSalesman_10-20-0.json")
        .add("TravelingSalesman", data="TravelingSalesman_10-20-0.json", variant="table")
        .add("VesselLoading", data="VesselLoading-inst1.json")
        )

xcsp = (Tester(NAME)
        .add("Amaze", data="Amaze_simple.json")  #
        .add("Amaze", data="Amaze_2012-03-07.dzn", prs_py="Amaze_ParserZ.py", prs_jv="")  #
        .add("Areas", data="Areas-3-3-3.json")  # 7 solutions
        .add("Auction", data="Auction_example.json")  # optimum 54
        .add("Auction", data="Auction_example.txt", prs_py="Auction_Parser", prs_jv="Auction_Parser")  # optimum 54
        .add("BinPacking", data="BinPacking_n1c1w4a.json")  # optimum 5
        .add("BinPacking", data="BinPacking_n1c1w4a.json", variant="table")  # optimum 5
        .add("BinPacking", data="BinPacking_example.txt", prs_py="BinPacking_Parser", prs_jv="BinPacking_Parser")  # optimum 5
        .add("Blackhole", data="Blackhole.json", options_py="-recognizeSlides")  # 47232 solutions
        .add("Bugs", data="Bugs_example.json")  # optimum 5
        .add("Bugs", data="Bugs_example.txt", prs_py="Bugs_Parser", prs_jv="Bugs_Parser")  # optimum 5
        .add("BusScheduling", data="BusScheduling_c1a.json")
        .add("BusScheduling", data="BusScheduling_r1.json")
        .add("BusScheduling", data="BusScheduling_t1.json")  # optimum 7
        .add("Coloring", data="Coloring_rand1.json")  # optimum 2
        .add("Coloring", data="Coloring_rand1.json", variant="csp")  # sat
        .add("Cutstock", data="Cutstock_small.json")  # optimum 4
        .add("Dominoes", data="Dominoes_grid1.json")  # 128 solutions
        .add("Eternity", data="Eternity_07x05.json")  # 32 solutions
        .add("Eternity", data="Eternity_example.txt", prs_py="Eternity_Parser", prs_jv="Eternity_Parser")  # 32 solutions
        .add("Fastfood", data="Fastfood_ff01.json")  # optimum 3050
        .add("Fastfood", data="Fastfood_ff01.json", variant="table") # optimum 3050
        .add("Fastfood", data="Fastfood_example.dzn", prs_py="Fastfood_ParserZ", prs_jv="Fastfood_ParserZ")  # optimum 3050
        .add("Futoshiki", data="Futoshiki_futo3_0.json")  # 1 solution
        .add("GraphColoring", data="GraphColoring_1-fullins-3.json")  # optimum 3
        .add("GraphColoring", data="GraphColoring_1-fullins-3.json", variant="sum")  # optimum 24
        .add("GraphColoring", data="GraphColoring_qwhdec-o18-h120-1.json")  # optimum 17
        .add("GraphColoring", data="GraphColoring_qwhdec-o18-h120-1.json", variant="sum")  # optimum 2754
        .add("GraphMaxAcyclic", data="GraphMaxAcyclic_example.json")  # optimum 44
        .add("GraphMaxAcyclic", data="GraphMaxAcyclic_example.txt", prs_py="GraphMaxAcyclic_Parser", prs_jv="GraphMaxAcyclic_Parser")  # optimum 44
        .add("GraphMaxAcyclic", data="GraphMaxAcyclic_example.txt", prs_py="GraphMaxAcyclic_Parser", prs_jv="GraphMaxAcyclic_Parser", variant="cnt")  # optimum 44
        .add("HCPizza", data="HCPizza_tiny.json")  # optimum 15
        .add("HCPizza", data="HCPizza_tiny.txt", prs_py="HCPizza_Parser", prs_jv="HCPizza_Parser")  # optimum 15
        .add("HCPizza", data="HCPizza_small.txt", prs_py="HCPizza_Parser", prs_jv="HCPizza_Parser")
        .add("Kakuro", data="Kakuro_easy-000.json")  # 1 solution
        .add("Kakuro", data="Kakuro_easy-000.json", variant="table")  # 1 solution
        .add("Knapsack", data="Knapsack_20-50-00.json")  # optimum 583
        .add("LatinSquare", data="LatinSquare_qwh-o030-h320.json")
        .add("LatinSquare2", data="LatinSquare2_7-2-0.json")  # 480 solutions
        .add("Lightup", data="Lightup_example.json")  # 1 solution
        .add("Lightup", data="Lightup_example.txt", prs_py="Lightup_Parser", prs_jv="Lightup_Parser")  # 1 solution
        .add("LinearArrangement", data="MinLA01.json")
        .add("MagicSquare", data="[4,None]")  # 7040 solutions
        .add("MagicSquare", data="MagicSquare_example1.txt", prs_py="MagicSquare_Parser", prs_jv="MagicSquare_Parser")
        .add("Mario", data="Mario_easy-2.json")  # optimum 628
        .add("Mario", data="Mario_easy-2.json", variant="table")  # optimum 628
        .add("MarketSplit", data="MarketSplit_04.json")  # 1 solution
        .add("MultiKnapsack", data="MultiKnapsack_example.txt", prs_py="MultiKnapsack_Parser", prs_jv="MultiKnapsack_Parser")
        .add("Nonogram", data="Nonogram_example.txt", prs_py="Nonogram_Parser", prs_jv="Nonogram_Parser")  # 1 solution
        .add("Nonogram", data="Nonogram_example.txt", prs_py="Nonogram_Parser", prs_jv="Nonogram_Parser", variant="table")  # 1 solution
        .add("OpenStacks", data="OpenStacks_example.dzn", prs_py="OpenStacks_ParserZ", prs_jv="OpenStacks_ParserZ", variant="m1")  # optimum 45
        .add("OpenStacks", data="OpenStacks_example.dzn", prs_py="OpenStacks_ParserZ", prs_jv="OpenStacks_ParserZ", variant="m2")  # optimum 45
        .add("PrizeCollecting", data="PrizeCollecting_example.dzn", prs_py="PrizeCollecting_ParserZ", prs_jv="PrizeCollecting_ParserZ", special=True)
        .add("ProgressiveParty", data="ProgressiveParty_example.txt", prs_py="ProgressiveParty_Parser", prs_jv="ProgressiveParty_Parser", special=True) # optimum 5
        .add("PseudoBoolean", data="PseudoBoolean_example.opb", prs_py="PseudoBoolean_Parser", prs_jv="PseudoBoolean_Parser")  # optimum 20
        .add("RectPacking", data="RectPacking_perfect-001.json", special=True)
        .add("RoomMate", data="RoomMate_sr0006.json")  # 2 solutions
        .add("Sat", data="Sat_flat30-16.json", variant="clause")  # 1482 solutions
        .add("Sat", data="Sat_flat30-16.json", variant="sum")  # 1482 solutions
        .add("Sat", data="Sat_flat30-16.json", variant="dual")  # 1482 solutions
        .add("Shikaku", data="Shikaku_grid1.json")  # 1 solution
        .add("Sonet", data="Sonet_sonet1.json")  # optimum 8
        .add("Sonet", data="Sonet_sonet3-4.json")  # optimum 12
        .add("StripPacking", data="StripPacking_C1P1.json")
        .add("Subisomorphism", data="Subisomorphism_A-01.json")  # 1 solution
        .add("Sudoku", data="[9,None]")  # None can be replaced by null (but not by an empty string in this context)
        .add("Sudoku", data="Sudoku_s13a.json")  # 1 solution
        .add("Sudoku", data="Sudoku_s13a.json", variant="table")  # 1 solution
        .add("Sudoku", data="Sudoku_example.txt", prs_py="Sudoku_Parser", prs_jv="Sudoku_Parser")  # 1 solution
        .add("TravelingSalesman", data="TravelingSalesman_10-20-0.json")  # optimum 47
        .add("TravelingSalesman", data="TravelingSalesman_10-20-0.json", variant="table")  # optimum 47
        .add("VesselLoading", data="VesselLoading-inst1.json")  # 8 solutions
        .add("VesselLoading", data="VesselLoading-inst2.json")
        )

run(xcsp,diff, same)
