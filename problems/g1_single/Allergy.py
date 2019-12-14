from pycsp3 import *

DEBRA, JANET, HUGH, RICK = "Debra", "Janet", "Hugh", "Rick"
friends = {DEBRA, JANET, HUGH, RICK}

eggs = Var(dom=friends)
mold = Var(dom=friends)
nuts = Var(dom=friends)
ragweed = Var(dom=friends)

baxter = Var(dom=friends)
lemmon = Var(dom=friends)
malone = Var(dom=friends)
vanfleet = Var(dom=friends)

satisfy(
    AllDifferent(eggs, mold, nuts, ragweed),
    AllDifferent(baxter, lemmon, malone, vanfleet),
    mold != RICK,
    eggs == baxter,
    lemmon != HUGH,
    vanfleet != HUGH,
    ragweed == DEBRA,
    lemmon != JANET,
    eggs != JANET,
    mold != JANET
)
