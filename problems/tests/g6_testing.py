from pycsp3.problems.tests.tester import Tester, run

NAME = "g6_testing"

xcsp = (Tester(NAME)
         # .add("UnitTestingIntension")
         .add("TestAbscon")
         .add("TestElement")
         .add("TestSlices")
         .add("TestSumConditions")
         .add("TestSums")
         .add("TestUnaryConditions")
         .add("UnitTestingExtension")
         .add("UnitTestingSum")
         .add("UnitTestingVariable")
         )

run(xcsp)
