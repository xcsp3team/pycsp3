import os

from pycsp3.problems.tests.tester import Tester, run

run(Tester("cop" + os.sep + "complex")
    .add("AircraftLanding", data="airland01.txt", prs_py="AircraftLanding_Parser.py", prs_jv="")  # optimum 70000
    .add("AircraftLanding", data="airland01.txt", prs_py="AircraftLanding_Parser.py", prs_jv="", variant="table")  # optimum 70000
    .add("Amaze", data="Amaze_simple.json")  # optimum 12
    .add("Amaze", data="Amaze_2012-03-07.dzn", prs_py="Amaze_ParserZ.py", prs_jv="")  # optimum 315
    .add("Auction", data="Auction_example.json")  # optimum 54
    .add("Auction", data="Auction_example.txt", prs_py="Auction_Parser", prs_jv="Auction_Parser")  # optimum 54
    .add("Bacp", data="Bacp_10.json", variant="m1")  # optimum 26
    .add("Bacp", data="Bacp_10.json", variant="m2")  # optimum 26
    .add("Bacp", data="Bacp_10.json", variant="m1-d")  # optimum 1
    .add("Bacp", data="Bacp_10.json", variant="m2-d")  # optimum 1
    .add("Bacp", data="Bacp_10.mzn", variant="m1", prs_py="Bacp_ParserZ", prs_jv="Bacp_ParserZ")  # m1 is enough to test parsing; optimum 26
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
    .add("Fapp", data="Fapp_ex2.json")  # optimum 13871
    .add("Fapp", data="Fapp_ex2.json", variant="short")  # optimum 13871
    # .add("Fapp", data="Fapp_01-0200.json")  # TODO too long
    # .add("Fapp", data="Fapp_01-0200.json", variant="short")  # around 22 seconds for generating the file
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
    .add("League", data="League_010-03-04.json")  # optimum 92
    .add("LinearArrangement", data="MinLA01.json")
    .add("Mario", data="Mario_easy-2.json")  # optimum 628
    .add("Mario", data="Mario_easy-2.json", variant="aux")  # optimum 628
    .add("Mario", data="Mario_easy-2.json", variant="table")  # optimum 628
    .add("MultiKnapsack", data="MultiKnapsack_example.txt", prs_py="MultiKnapsack_Parser", prs_jv="MultiKnapsack_Parser")
    .add("NurseRostering", data="NurseRostering_00.json")  # optimum 1202
    .add("NurseRostering", data="NurseRostering_18.json")
    .add("OpenStacks", data="OpenStacks_example.dzn", prs_py="OpenStacks_ParserZ", prs_jv="OpenStacks_ParserZ", variant="m1")  # optimum 45
    .add("OpenStacks", data="OpenStacks_example.dzn", prs_py="OpenStacks_ParserZ", prs_jv="OpenStacks_ParserZ", variant="m2")  # optimum 45
    .add("PizzaVoucher", data="PizzaVoucher_pizza6.json")  # optimum 210
    .add("PrizeCollecting", data="PrizeCollecting_example.dzn", prs_py="PrizeCollecting_ParserZ")  # optimum 20
    .add("PrizeCollecting", data="PrizeCollecting_example.dzn", prs_py="PrizeCollecting_ParserZ", variant="table")  # optimum 20
    .add("ProgressiveParty", data="ProgressiveParty_example.txt", prs_py="ProgressiveParty_Parser")  # optimum 5
    .add("PseudoBoolean", data="PseudoBoolean_example.opb", prs_py="PseudoBoolean_Parser", prs_jv="PseudoBoolean_Parser")  # optimum 20
    .add("QuadraticAssignment", data="QuadraticAssignment_qap.json")  # optimum 4776
    .add("QuadraticAssignment", data="QuadraticAssignment_example.txt", prs_py="QuadraticAssignment_Parser",
         prs_jv="QuadraticAssignment_Parser")  # optimum 4776
    .add("Rack", data="Rack_r2.json")  # optimum 1100
    .add("Rack2", data="Rack_r2b.json")  # optimum 1100
    .add("RCPSP", data="RCPSP_j30-01-01.json")  # optimum 43
    .add("Rehearsal", data="RehearsalSmith.json")  # optimum 17
    .add("Rehearsal", data="RehearsalSmith.json", variant="bis")  # optimum 17
    .add("RLFAP", data="RLFAP_card-scen-04.json", variant="card")  # optimum 46
    .add("RLFAP", data="RLFAP_span-scen-05.json", variant="span")  # optimum 792
    .add("RLFAP", data="RLFAP_max-graph-05.json", variant="max")  # optimum 221  (use -ub=222 with Ace to prove it, or -os=increasing)
    .add("RoadConstruction", data="Road_9.json")  # optimum 3206
    .add("SchedulingFS", data="SchedulingFS-Taillard-os-04-04-0.json")  # optimum 302
    .add("SchedulingFS", data="Taillard-fs-020-05-1.json")
    .add("SchedulingJS", data="Sadeh-js-e0ddr1-0.json")
    .add("SchedulingJS", data="Taillard-js-015-15-1.json")
    .add("SchedulingOS", data="Taillard-os-05-05-1.json")
    .add("SchedulingOS", data="GP-os-01.json")
    .add("SetCovering", data="Subsets_example.json")  # optimum 3
    .add("SetPacking", data="Subsets_example.json")  # optimum 4
    .add("Sonet", data="Sonet_sonet1.json")  # optimum 8
    .add("Sonet", data="Sonet_sonet3-4.json")  # optimum 12
    .add("SteelMillSlab", data="SteelMillSlab_bench_2_0.json")
    .add("SteelMillSlab", data="SteelMillSlab_bench_2_0.json", variant="01")
    .add("Tal", data="Tal-frobserved-7-15-11-13-9-1-11-7-4_1.json")  # optimum 142
    .add("TemplateDesign", data="TemplateDesign_catfood_2.json")  # optimum 2 ; java ace TemplateDesign-catfood_2.xml -valh=Rand -p=SAC3 -sop
    .add("TemplateDesign", data="TemplateDesign_catfood_2.json", variant="aux")
    .add("TravelingPurchaser", data="TravelingPurchaser-7-5-30-1.json")  # optimum 124
    .add("TravelingSalesman", data="TravelingSalesman_10-20-0.json")  # optimum 47
    .add("TravelingSalesman", data="TravelingSalesman_10-20-0.json", variant="table")  # optimum 47
    .add("TravelingTournament", data="TravelingTournament_galaxy04.json", variant="a2")  # optimum 517
    .add("TravelingTournament", data="TravelingTournament_galaxy04.json", variant="a3")  # optimum 416
    .add("TravelingTournamentWithPredefinedVenues", data="Ttppv_circ8bbal.json", variant="a2")  # optimum 94
    .add("TravelingTournamentWithPredefinedVenues", data="Ttppv_circ8bbal.json", variant="a3")  # optimum 80
    .add("Vellino", data="Vellino-5.json")  # optimum 8
    .add("Vrp", data="Vrp_P-n16-k8.json")
    .add("Warehouse", data="Warehouse_example.txt", prs_py="Warehouse_Parser", prs_jv="Warehouse_Parser")  # optimum 383
    .add("Warehouse", data="Warehouse_example.txt", prs_py="Warehouse_Parser", prs_jv="Warehouse_Parser", variant="compact")  # optimum 383
    )
