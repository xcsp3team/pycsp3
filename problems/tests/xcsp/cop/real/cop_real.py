from pycsp3.problems.tests.tester import Tester, run

run(Tester("cop_real")
    .add("Amaze", data="Amaze_simple.json")  # optimum 12
    .add("Amaze", data="Amaze_2012-03-07.dzn", prs_py="Amaze_ParserZ.py", prs_jv="")  # optimum 315
    .add("Auction", data="Auction_example.json")  # optimum 54
    .add("Auction", data="Auction_example.txt", prs_py="Auction_Parser", prs_jv="Auction_Parser")  # optimum 54
    .add("BinPacking", data="BinPacking_n1c1w4a.json")  # optimum 5
    .add("BinPacking", data="BinPacking_n1c1w4a.json", variant="table")  # optimum 5
    .add("BinPacking", data="BinPacking_example.txt", prs_py="BinPacking_Parser", prs_jv="BinPacking_Parser")  # optimum 5
    .add("Bugs", data="Bugs_example.json")  # optimum 5
    .add("Bugs", data="Bugs_example.txt", prs_py="Bugs_Parser", prs_jv="Bugs_Parser")  # optimum 5
    .add("BusScheduling", data="BusScheduling_c1a.json")
    .add("BusScheduling", data="BusScheduling_r1.json")
    .add("BusScheduling", data="BusScheduling_t1.json")  # optimum 7
    .add("Coloring", data="Coloring_rand1.json")  # optimum 2
    .add("Cutstock", data="Cutstock_small.json")  # optimum 4
    .add("Fastfood", data="Fastfood_ff01.json")  # optimum 3050
    .add("Fastfood", data="Fastfood_ff01.json", variant="table")  # optimum 3050
    .add("Fastfood", data="Fastfood_example.dzn", prs_py="Fastfood_ParserZ", prs_jv="Fastfood_ParserZ")  # optimum 3050
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
    .add("Knapsack", data="Knapsack_20-50-00.json")  # optimum 583
    .add("LinearArrangement", data="MinLA01.json")
    .add("Mario", data="Mario_easy-2.json")  # optimum 628
    .add("Mario", data="Mario_easy-2.json", variant="table")  # optimum 628
    .add("MultiKnapsack", data="MultiKnapsack_example.txt", prs_py="MultiKnapsack_Parser", prs_jv="MultiKnapsack_Parser")
    .add("OpenStacks", data="OpenStacks_example.dzn", prs_py="OpenStacks_ParserZ", prs_jv="OpenStacks_ParserZ", variant="m1")  # optimum 45
    .add("OpenStacks", data="OpenStacks_example.dzn", prs_py="OpenStacks_ParserZ", prs_jv="OpenStacks_ParserZ", variant="m2")  # optimum 45
    .add("PrizeCollecting", data="PrizeCollecting_example.dzn", prs_py="PrizeCollecting_ParserZ")  # optimum 20
    .add("ProgressiveParty", data="ProgressiveParty_example.txt", prs_py="ProgressiveParty_Parser")  # optimum 5
    .add("PseudoBoolean", data="PseudoBoolean_example.opb", prs_py="PseudoBoolean_Parser", prs_jv="PseudoBoolean_Parser")  # optimum 20
    .add("Sonet", data="Sonet_sonet1.json")  # optimum 8
    .add("Sonet", data="Sonet_sonet3-4.json")  # optimum 12
    .add("TravelingSalesman", data="TravelingSalesman_10-20-0.json")  # optimum 47
    .add("TravelingSalesman", data="TravelingSalesman_10-20-0.json", variant="table")  # optimum 47
    )
