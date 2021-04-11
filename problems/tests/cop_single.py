import os

from pycsp3.problems.tests.tester import Tester, run

run(Tester("cop" + os.sep + "single")
    .add("DakotaFurniture")  # optimum 280
    .add("Photo")  # optimum 2
    .add("Photo", variant="aux")  # optimum 2
    .add("Recipe")  # optimum 1700
    .add("Witch")  # optimum 1300
)
