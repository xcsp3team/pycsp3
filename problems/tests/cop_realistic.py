import os

from pycsp3.problems.tests.tester import Tester, run

run(Tester("cop", "realistic")
    .add("AircraftLanding", data="airland01.txt", prs_py="AircraftLanding_Parser.py", subdir="data")  # optimum 70000
    .add("AircraftLanding", data="airland01.txt", prs_py="AircraftLanding_Parser.py", variant="table", subdir="data")  # optimum 70000
    .add("Auction", data="example.json")  # optimum 54
    .add("Auction", data="example.txt", prs_py="Auction_Parser", subdir="data")  # optimum 54
    .add("BACP", data="10.json", variant="m1")  # optimum 26
    .add("BACP", data="10.json", variant="m2")  # optimum 26
    .add("BACP", data="10.json", variant="m1-d")  # optimum 1
    .add("BACP", data="10.json", variant="m2-d")  # optimum 1
    .add("BACP", data="10.mzn", variant="m1", prs_py="BACP_Parser", subdir="data")  # m1 is enough to test parsing; optimum 26
    .add("BusScheduling", data="c1a.json", subdir="data")
    .add("BusScheduling", data="r1.json", subdir="data")
    .add("BusScheduling", data="t1.json")  # optimum 7
    .add("FAPP", data="ex2.json")  # optimum 13871
    .add("FAPP", data="ex2.json", variant="short")  # optimum 13871
    # .add("FAPP", data="01-0200.json")  # TODO too long
    # .add("FAPP", data="01-0200.json", variant="short")  # around 22 seconds for generating the file
    .add("Fastfood", data="ff01.json")  # optimum 3050
    .add("Fastfood", data="ff01.json", variant="table")  # optimum 3050
    .add("Fastfood", data="ff01.dzn", prs_py="Fastfood_ParserZ", subdir="data")  # optimum 3050
    .add("FreePizza", data="pizza06.json")  # optimum 210
    # .add("MultiKnapsack", data="MultiKnapsack_example.txt", prs_py="MultiKnapsack_Parser")
    .add("NurseRostering", data="00.json")  # optimum 1202
    .add("NurseRostering", data="18.json", subdir="data")
    .add("OpenStacks", data="example.dzn", prs_py="OpenStacks_ParserZ", variant="m1", subdir="data")  # optimum 45
    .add("OpenStacks", data="example.dzn", prs_py="OpenStacks_ParserZ", variant="m2", subdir="data")  # optimum 45
    .add("PrizeCollecting", data="example.dzn", prs_py="PrizeCollecting_ParserZ", subdir="data")  # optimum 20
    .add("PrizeCollecting", data="example.dzn", prs_py="PrizeCollecting_ParserZ", variant="table", subdir="data")  # optimum 20
    .add("Rack", data="r2.json")  # optimum 1100
    .add("Rack", version="Rack2", data="r2b.json")  # optimum 1100
    .add("RCPSP", data="j030-01-01.json")  # optimum 43
    .add("RLFAP", data="scen-04.json", variant="card", subdir="data")  # optimum 46
    .add("RLFAP", data="scen-05.json", variant="span", subdir="data")  # optimum 792
    .add("RLFAP", data="graph-05.json", variant="max", subdir="data")  # optimum 221  (use -ub=222 with Ace to prove it, or -os=increasing)
    .add("RoadConstruction", data="09.json")  # optimum 3206
    .add("SchedulingFS", data="04-04-0.json")  # optimum 302
    .add("SchedulingFS", data="020-05-1.json", subdir="data")
    .add("SchedulingJS", data="e0ddr1-0.json")
    .add("SchedulingJS", data="015-15-1.json", subdir="data")
    .add("SchedulingOS", data="05-05-1.json", subdir="data")
    .add("SchedulingOS", data="GP-os-01.json")
    .add("Sonet", data="sonet1.json", subdir="data")  # optimum 8
    .add("Sonet", data="sonet3-4.json", subdir="data")  # optimum 12
    .add("SteelMillSlab", data="bench-2-0.json")
    .add("SteelMillSlab", data="bench-2-0.json", variant="01")
    .add("VRP", data="P-n16-k8.json", subdir="data")
    .add("Warehouse", data="example.txt", prs_py="Warehouse_Parser", subdir="data")  # optimum 383
    .add("Warehouse", data="example.txt", prs_py="Warehouse_Parser", variant="compact", subdir="data")  # optimum 383
    )
