from pycsp3.problems.data.parsing import *

# python3 pycsp3/problems/g3_pattern/HCPizza.py -data=pycsp3/problems/data/raw/HCPizza_tiny.txt -dataparser=pycsp3/problems/data/parsers/HCPizza_Parser.py -variant=sum

nRows = next_int()
next_int()  # nCols
data["minIngredients"] = next_int()
data["maxSize"] = next_int()
data["pizza"] = [[0 if c == "M" else 1 for c in line if c != '\n'] for line in remaining_lines()]
