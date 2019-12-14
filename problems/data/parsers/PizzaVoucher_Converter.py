from pycsp3.problems.data.dataparser import *
import json
from pycsp3.compiler import Compilation


# illustrating how to convert from a JSON format to another one.

name = ask_string("Name of the JSON file")
with open(name) as f:
    d = json.load(f)

pp, fp = d.get("voucherPayPart"), d.get("voucherFreePart")
assert len(pp) == len(fp)

data.pizzaPrices = d.get("pizzaPrices")
data.vouchers = [DataDict({"payPart": pp[i], "freePart": fp[i]}) for i in range(len(pp))]

pos = name.rfind("/")
Compilation.string_data = "-" + name[pos + 1:] if pos != -1 else name
