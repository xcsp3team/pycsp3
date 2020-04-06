"""
One morning, in 1880, four families (the Boyds, Garveys, Logans and Navarros) stopped by Purdey's general store,.
Each family bought a different item: 50 pounds of flour, two gallons of kerosene, ten yards of muslin cloth, ten pounds of sugar.
One family paid cash, one took the item on credit and the other two traded other items for it (one a cured ham and the other a bushel of peas).
We know that:
 - the Boyds were new in town, and this was their first visit to the store
 - the family (which wasn't the Logans) that traded the bushel of peas didn't buy the kerosene
 - the Boyds and the Garveys bought the kerosene and the muslin in some order
 - one family traded a cured ham for a large sack of flour
 - Purdey only extended credit to regular customers, such as the family that bought the muslin on credit

Execution:
  python3 Purdey.py
"""

from pycsp3 import *

families = Boyds, Garveys, Logans, Navarros = "Boyds", "Garveys", "Logans", "Navarros"

flour = Var(families)
kerosene = Var(families)
cloth = Var(families)
sugar = Var(families)

cash = Var(families)
credit = Var(families)
ham = Var(families)
peas = Var(families)

satisfy(
    AllDifferent(flour, kerosene, cloth, sugar),
    AllDifferent(cash, credit, ham, peas),
    peas != Logans,
    peas != kerosene,
    (kerosene == Boyds) | (cloth == Boyds),
    (kerosene == Garveys) | (cloth == Garveys),
    ham == flour,
    credit == cloth,
    credit != Boyds
)
