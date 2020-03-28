from pycsp3.problems.tests.tester import Tester, run

NAME = "g6_tests"

tests = (Tester(NAME)
         # .add("UnitTestingIntension")
         .add("UnitTestingExtension")
         .add("UnitTestingSum")
         .add("UnitTestingVariable")
         .add("TestElement")
         .add("TestSums")
         .add("TestSlices")
         .add("TestUnaryConditions")
         .add("TestSumConditions")
         .add("TestSolver")
         )

run(tests, tests=True)
