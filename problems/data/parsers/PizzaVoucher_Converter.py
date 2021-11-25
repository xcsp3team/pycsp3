import json

from pycsp3.compiler import Compilation
from pycsp3.problems.data.parsing import *

# illustrating how to convert from a JSON format to another one.
# For example python3 PizzaVoucher.py -data=zn06-oldformat.json -dataparser=PizzaVoucher_Converter.py -dataexport


name = options.data  # the name of the JSON file whose format must be converted")
with open(name) as f:
    d = json.load(f)

pp, fp = d.get("voucherPayPart"), d.get("voucherFreePart")
assert len(pp) == len(fp)

data["pizzaPrices"] = d.get("pizzaPrices")
data["vouchers"] = [OrderedDict([("pay", pp[i]), ("free", fp[i])]) for i in range(len(pp))]

pos = name.rfind("/")
Compilation.string_data = "-" + name[pos + 1:] if pos != -1 else name
