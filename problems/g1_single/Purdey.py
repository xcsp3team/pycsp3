from pycsp3 import *

BOYDS, GARVEYS, LOGANS, NAVARROS = families = ["Boyds", "Garveys", "Logans", "Navarros"]

flour = Var(families)
kerozene = Var(families)
cloth = Var(families)
sugar = Var(families)

cash = Var(families)
credit = Var(families)
ham = Var(families)
peas = Var(families)

satisfy(
    AllDifferent(flour, kerozene, cloth, sugar),
    AllDifferent(cash, credit, ham, peas),
    peas != LOGANS,
    peas != kerozene,
    (kerozene == BOYDS) | (cloth == BOYDS),
    (kerozene == GARVEYS) | (cloth == GARVEYS),
    ham == flour,
    credit == cloth,
    credit != BOYDS
)
