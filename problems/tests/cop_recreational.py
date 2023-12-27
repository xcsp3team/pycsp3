import os

from pycsp3.problems.tests.tester import Tester, run

run(Tester("cop", "recreational")
    .add("Amaze", data="simple.json")  # optimum 12
    .add("Amaze", data="03-07.dzn", prs_py="Amaze_ParserZ.py", subdir="data")  # optimum 315
    .add("BinPacking", data="n1c1w4a.json")  # optimum 5
    .add("BinPacking", data="n1c1w4a.json", variant="table")  # optimum 5
    .add("BinPacking", data="example.txt", prs_py="BinPacking_Parser", subdir="data")  # optimum 5
    .add("Bugs", data="example.json")  # optimum 5
    .add("Bugs", data="example.txt", prs_py="Bugs_Parser", subdir="data")  # optimum 5
    .add("Coloring", data="rand01.json")  # optimum 2
    .add("Cutstock", data="small.json")  # optimum 4
    .add("GraphColoring", data="1-fullins-3.json")  # optimum 3
    .add("GraphColoring", data="1-fullins-3.json", variant="sum")  # optimum 24
    .add("GraphColoring", data="qwhdec-o18-h120-1.json", subdir="data")  # optimum 17
    .add("GraphColoring", data="qwhdec-o18-h120-1.json", variant="sum", subdir="data")  # optimum 2754
    .add("GraphMaxAcyclic", data="example.json")  # optimum 44
    .add("GraphMaxAcyclic", data="example.txt", prs_py="GraphMaxAcyclic_Parser", subdir="data")  # optimum 44
    .add("GraphMaxAcyclic", data="example.txt", prs_py="GraphMaxAcyclic_Parser", variant="cnt", subdir="data")  # optimum 44
    .add("HCPizza", data="tiny.json", subdir="data")  # optimum 15
    .add("HCPizza", data="tiny.txt", prs_py="HCPizza_Parser", subdir="data")  # optimum 15
    .add("HCPizza", data="small.txt", prs_py="HCPizza_Parser", subdir="data")
    .add("Knapsack", data="20-50-00.json")  # optimum 583
    .add("League", data="010-03-04.json")  # optimum 92
    .add("LinearArrangement", data="MinLA01.json")
    .add("Mario", data="easy-2.json")  # optimum 628
    .add("Mario", data="easy-2.json", variant="aux")  # optimum 628
    .add("Mario", data="easy-2.json", variant="table")  # optimum 628
    .add("ProgressiveParty", data="example.txt", prs_py="ProgressiveParty_Parser", subdir="data")  # optimum 5
    .add("PseudoBoolean", data="example.opb", prs_py="PseudoBoolean_Parser", subdir="data")  # optimum 20
    .add("QuadraticAssignment", data="example.json")  # optimum 4776
    .add("QuadraticAssignment", data="example.txt", prs_py="QuadraticAssignment_Parser", subdir="data")  # optimum 4776
    .add("Rehearsal", data="rs.json")  # optimum 17
    .add("Rehearsal", data="rs.json", variant="bis")  # optimum 17
    .add("SetCovering", data="example.json")  # optimum 3
    .add("SetPacking", data="example.json")  # optimum 4
    .add("TAL", data="frobserved-7-15-11-13-9-1-11-7-4_1.json")  # optimum 142
    .add("TemplateDesign", data="catfood-2.json")  # optimum 2 ; java ace TemplateDesign-catfood_2.xml -valh=Rand -p=SAC3 -sop
    .add("TemplateDesign", data="catfood-2.json", variant="aux")
    .add("TravelingPurchaser", data="7-5-30-1.json")  # optimum 124
    .add("TravelingSalesman", data="10-20-0.json")  # optimum 47
    .add("TravelingSalesman", data="10-20-0.json", variant="table")  # optimum 47
    .add("TravelingTournament", data="galaxy04.json", variant="a2")  # optimum 517
    .add("TravelingTournament", data="galaxy04.json", variant="a3")  # optimum 416
    .add("TravelingTournamentWithPredefinedVenues", data="circ8bbal.json", variant="a2")  # optimum 94
    .add("TravelingTournamentWithPredefinedVenues", data="circ8bbal.json", variant="a3")  # optimum 80
    .add("Vellino", version="Vellino1", data="05.json")  # optimum 8
    )
