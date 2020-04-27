from pycsp3.problems.data.parsing import *
from pycsp3.compiler import Compilation
import random


def random_edge():
    x, y = random.randint(0, data.nNodes - 1), random.randint(0, data.nNodes - 1)
    return (x, y) if x != y else random_edge()


data.nNodes = ask_number("Number of nodes ?")
data.nColors = ask_number("Number of colors ?")
nEdges = ask_number("Number of edges ?")
data.edges = [random_edge() for _ in range(nEdges)]

Compilation.string_data = "-" + "-".join(str(v) for v in (data.nNodes, data.nColors, nEdges))
