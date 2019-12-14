from pycsp3.problems.tests.tester import Tester, run

NAME = "g6_tests"

tests = (Tester(NAME)
         # .add("UnitTestingIntension")
         .add("UnitTestingExtension")
         .add("UnitTestingSum")
         .add("UnitTestingVariable")
         .add("ElementGetItem", data="Rack_r2.json")
         .add("ExtendSum")
         .add("ColunmSliceNumPy")
         .add("OverrideOperatorNode")
         .add("OverrideOperatorSum")
         .add("Solve")
         )

run(tests, tests=True)
