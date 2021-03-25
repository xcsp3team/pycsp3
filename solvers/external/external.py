import os

from pycsp3.solvers.solver import SolverProcess  #, SolverPy4J


class ExternalProcess(SolverProcess):
    def __init__(self, name, command):
        super().__init__(name=name, command=command, cp="")

    def parse_general_options(self, string_options, dict_options, dict_simplified_options):
        return ""
