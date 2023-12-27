import os

from pycsp3.problems.tests.tester import Tester, run

run(Tester("csp", "realistic")
    .add("CarSequencing", data="dingbas.json")  # 6 solutions
    .add("CarSequencing", data="dingbas.json", variant="table")  # 6 solutions
    .add("RadarSurveillance", data="8-24-3-2-00.json")  # sat
    .add("RectPacking", data="perfect-001.json")
    .add("SAT", data="flat30-16.json", variant="clause")  # 1482 solutions
    .add("SAT", data="flat30-16.json", variant="sum")  # 1482 solutions
    .add("SAT", data="flat30-16.json", variant="dual")  # 1482 solutions
    .add("VesselLoading", data="inst1.json")  # 8 solutions
    .add("VesselLoading", data="inst2.json", subdir="data")
    .add("WWTPP", data="ex04400.json")  # unsat
    .add("WWTPP", data="ex04400.json", variant="short")  # unsat
    )
