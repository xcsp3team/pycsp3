import os

from pycsp3.problems.tests.tester import Tester, run

run(Tester("csp", "recreational")
    .add("CarSequencing", data="CarSequencing_dingbas.json")  # 6 solutions
    .add("CarSequencing", data="CarSequencing_dingbas.json", variant="table")  # 6 solutions
    .add("RadarSurveillance", data="RadarSurveillance_8-24-3-2-00.json")  # sat
    .add("RectPacking", data="RectPacking_perfect-001.json")
    .add("Sat", data="Sat_flat30-16.json", variant="clause")  # 1482 solutions
    .add("Sat", data="Sat_flat30-16.json", variant="sum")  # 1482 solutions
    .add("Sat", data="Sat_flat30-16.json", variant="dual")  # 1482 solutions
    .add("VesselLoading", data="VesselLoading-inst1.json")  # 8 solutions
    .add("VesselLoading", data="VesselLoading-inst2.json")
    .add("Wwtpp", data="Wwtpp_ex04400.json")  # unsat
    .add("Wwtpp", data="Wwtpp_ex04400.json", variant="short")  # unsat
    )
