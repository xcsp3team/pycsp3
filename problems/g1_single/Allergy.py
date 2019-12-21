from pycsp3 import *

DEBRA, JANET, HUGH, RICK = friends = ["Debra", "Janet", "Hugh", "Rick"]

eggs = Var(friends)
mold = Var(friends)
nuts = Var(friends)
ragweed = Var(friends)

baxter = Var(friends)
lemmon = Var(friends)
malone = Var(friends)
vanfleet = Var(friends)

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
