from pycsp3.problems.tests.tester import Tester, run

NAME = "g4_world"

diff = (Tester(NAME)
        .add("Bacp", data="Bacp_10.json", variant="m1")
        .add("Bacp", data="Bacp_10.json", variant="m2")
        .add("Bacp", data="Bacp_10.json", variant="m1-d")
        .add("Bacp", data="Bacp_10.json", variant="m2-d")
        .add("Bacp", data="Bacp_10.mzn", variant="m1", prs_py="Bacp_ParserZ", prs_jv="Bacp_ParserZ")  # m1 is enough to test parsing
        .add("CarSequencing", data="CarSequencing_dingbas.json")
        .add("CarSequencing", data="CarSequencing_dingbas.json", variant="table")
        .add("League", data="League_010-03-04.json")
        .add("NurseRostering", data="NurseRostering_00.json")
        .add("NurseRostering", data="NurseRostering_18.json")
        .add("PizzaVoucher", data="PizzaVoucher_pizza6.json")
        .add("Rack", data="Rack_r2.json")
        .add("Rack2", data="Rack_r2b.json")
        .add("RadarSurveillance", data="RadarSurveillance_8-24-3-2-00.json")
        .add("SolitaireBattleship", data="SolitaireBattleship_sb-12-12-5-0.json")  # 54 solutions
        .add("SolitaireBattleship", data="SolitaireBattleship-battleship_instances-00113.json")  # different order of groups in a block
        .add("SteelMillSlab", data="SteelMillSlab_bench_2_0.json")
        .add("SteelMillSlab", data="SteelMillSlab_bench_2_0.json", variant="01")
        .add("TemplateDesign", data="TemplateDesign_catfood_2.json")
        .add("TemplateDesign", data="TemplateDesign_catfood_2.json", variant="aux")
        .add("Tal", data="Tal-frobserved-7-15-11-13-9-1-11-7-4_1.json")
        .add("TravelingPurchaser", data="TravelingPurchaser-7-5-30-1.json")  # intension constraints more compact in PyCSP
        .add("Vrp", data="Vrp_P-n16-k8.json")
        .add("Warehouse", data="Warehouse_example.txt", prs_py="Warehouse_Parser", prs_jv="Warehouse_Parser")
        .add("Wwtpp", data="Wwtpp_ex04400.json")
        .add("Wwtpp", data="Wwtpp_ex04400.json", variant="short")
        )

same = (Tester(NAME)
        .add("Crossword", data="Crossword_vg6-7-ogd.json")
        .add("Crossword", data="Crossword_h1501-lex.json")
        .add("Crossword", data="Crossword_h0504-lex.json", variant="alt")
        .add("Fapp", data="Fapp_ex2.json")
        .add("Fapp", data="Fapp_ex2.json", variant="short")
        # .add("Fapp", data="Fapp_01-0200.json")  # TODO too long (and seems to crash)
        # .add("Fapp", data="Fapp_01-0200.json", variant="short")
        .add("QuadraticAssignment", data="QuadraticAssignment_qap.json")
        .add("QuadraticAssignment", data="QuadraticAssignment_example.txt", prs_py="QuadraticAssignment_Parser", prs_jv="QuadraticAssignment_Parser")
        .add("MisteryShopper", data="MisteryShopper_04.json")
        .add("Rcpsp", data="Rcpsp_j30-01-01.json")
        .add("Rlfap", data="Rlfap_card-scen-04.json", variant="card")
        .add("Rlfap", data="Rlfap_span-scen-05.json", variant="span")
        .add("SchedulingFS", data="Taillard-fs-020-05-1.json")
        .add("SchedulingFS", data="SchedulingFS-Taillard-os-04-04-0.json")
        .add("SchedulingJS", data="Taillard-js-015-15-1.json")
        .add("SchedulingJS", data="Sadeh-js-e0ddr1-0.json")
        .add("SchedulingOS", data="Taillard-os-05-05-1.json")
        .add("SchedulingOS", data="GP-os-01.json")
        .add("TravelingTournament", data="TravelingTournament_galaxy04.json", variant="a2")
        .add("TravelingTournament", data="TravelingTournament_galaxy04.json", variant="a3")
        .add("TravelingTournamentWithPredefinedVenues", data="Ttppv_circ8bbal.json", variant="a2")
        .add("TravelingTournamentWithPredefinedVenues", data="Ttppv_circ8bbal.json", variant="a3")
        )

xcsp = (Tester(NAME)
        .add("Bacp", data="Bacp_10.json", variant="m1")  # optimum 26
        .add("Bacp", data="Bacp_10.json", variant="m2")  # optimum 26
        .add("Bacp", data="Bacp_10.json", variant="m1-d")  # optimum 1
        .add("Bacp", data="Bacp_10.json", variant="m2-d")  # optimum 1
        .add("Bacp", data="Bacp_10.mzn", variant="m1", prs_py="Bacp_ParserZ", prs_jv="Bacp_ParserZ")  # m1 is enough to test parsing; optimum 26
        .add("CarSequencing", data="CarSequencing_dingbas.json")  # 6 solutions
        .add("CarSequencing", data="CarSequencing_dingbas.json", variant="table")  # 6 solutions
        .add("Crossword", data="Crossword_vg6-7-ogd.json")  # sat
        .add("Crossword", data="Crossword_h1501-lex.json")  # sat
        .add("Crossword", data="Crossword_h0504-lex.json", variant="alt")
        .add("Fapp", data="Fapp_ex2.json")  # optimum 13871
        .add("Fapp", data="Fapp_ex2.json", variant="short")  # optimum 13871
        # .add("Fapp", data="Fapp_01-0200.json")  # TODO too long
        # .add("Fapp", data="Fapp_01-0200.json", variant="short")  # around 22 seconds for generating the file
        .add("League", data="League_010-03-04.json")  # optimum 92
        .add("MisteryShopper", data="MisteryShopper_04.json")  # 501552 solutions
        .add("NurseRostering", data="NurseRostering_00.json")  # optimum 1202
        .add("NurseRostering", data="NurseRostering_18.json")
        .add("PizzaVoucher", data="PizzaVoucher_pizza6.json")  # optimum 210
        .add("QuadraticAssignment", data="QuadraticAssignment_qap.json")  # optimum 4776
        .add("QuadraticAssignment", data="QuadraticAssignment_example.txt", prs_py="QuadraticAssignment_Parser",
             prs_jv="QuadraticAssignment_Parser")  # optimum 4776
        .add("Rack", data="Rack_r2.json")  # optimum 1100
        .add("Rack2", data="Rack_r2b.json")  # optimum 1100
        .add("RadarSurveillance", data="RadarSurveillance_8-24-3-2-00.json")  # sat
        .add("Rcpsp", data="Rcpsp_j30-01-01.json")
        .add("Rlfap", data="Rlfap_card-scen-04.json", variant="card")  # optimum 46
        .add("Rlfap", data="Rlfap_span-scen-05.json", variant="span")  # optimum 792
        .add("Rlfap", data="Rlfap_max-graph-05.json", variant="max")  # optimum 221  (use -ub=222 with AbsCon to prove it, or -os=increasing)
        .add("SchedulingFS", data="SchedulingFS-Taillard-os-04-04-0.json")  # optimum 302
        .add("SchedulingFS", data="Taillard-fs-020-05-1.json")
        .add("SchedulingJS", data="Sadeh-js-e0ddr1-0.json")
        .add("SchedulingJS", data="Taillard-js-015-15-1.json")
        .add("SchedulingOS", data="Taillard-os-05-05-1.json")
        .add("SchedulingOS", data="GP-os-01.json")
        .add("SolitaireBattleship", data="SolitaireBattleship_sb-12-12-5-0.json")  # 51 solutions
        .add("SolitaireBattleship", data="SolitaireBattleship-battleship_instances-00113.json")  # 1 solution
        .add("SteelMillSlab", data="SteelMillSlab_bench_2_0.json")
        .add("SteelMillSlab", data="SteelMillSlab_bench_2_0.json", variant="01")
        .add("Tal", data="Tal-frobserved-7-15-11-13-9-1-11-7-4_1.json")  # optimum 142
        .add("TemplateDesign", data="TemplateDesign_catfood_2.json")  # optimum 2 ; java AbsCon TemplateDesign-catfood_2.xml -valh=Rand -p=SAC3 -sop
        .add("TemplateDesign", data="TemplateDesign_catfood_2.json", variant="aux")
        .add("TravelingPurchaser", data="TravelingPurchaser-7-5-30-1.json")  # optimum 124
        .add("TravelingTournament", data="TravelingTournament_galaxy04.json", variant="a2")  # optimum 517
        .add("TravelingTournament", data="TravelingTournament_galaxy04.json", variant="a3")  # optimum 416
        .add("TravelingTournamentWithPredefinedVenues", data="Ttppv_circ8bbal.json", variant="a2")  # optimum 94
        .add("TravelingTournamentWithPredefinedVenues", data="Ttppv_circ8bbal.json", variant="a3")  # optimum 80
        .add("Vrp", data="Vrp_P-n16-k8.json")
        .add("Warehouse", data="Warehouse_example.txt", prs_py="Warehouse_Parser", prs_jv="Warehouse_Parser")  # optimum 383
        .add("Wwtpp", data="Wwtpp_ex04400.json")  # unsat
        .add("Wwtpp", data="Wwtpp_ex04400.json", variant="short")  # unsat
        )

run(xcsp, diff, same)
