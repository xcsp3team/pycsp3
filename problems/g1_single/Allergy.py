from pycsp3 import *

"""
 Four friends (two women named Debra and Janet, and two men named Hugh and Rick) found that each of them is allergic to something different:
 eggs, mold, nuts and ragweed.
 We would like to match each one's surname (Baxter, Lemon, Malone and Fleet) with his or her allergy.
 We know that:
  - Rick isn't allergic to mold
  - Baxter is allergic to eggs
  - Hugh isn't surnamed Lemon or Fleet
  - Debra is allergic to ragweed
  - Janet (who isn't Lemon) isn't allergic to eggs or mold
"""

Debra, Janet, Hugh, Rick = friends = ["Debra", "Janet", "Hugh", "Rick"]

# foods[i] is the friend allergic to the ith food
eggs, mold, nuts, ragweed = foods = VarArray(size=4, dom=friends)

# surnames[i] is the friend with the ith surname
baxter, lemon, malone, fleet = surnames = VarArray(size=4, dom=friends)

satisfy(
    AllDifferent(foods),
    AllDifferent(surnames),

    mold != Rick,
    eggs == baxter,
    lemon != Hugh,
    fleet != Hugh,
    ragweed == Debra,
    lemon != Janet,
    eggs != Janet,
    mold != Janet
)
