from pycsp3 import *

BOYDS, GARVEYS, LOGANS, NAVARROS = "Boyds", "Garveys", "Logans", "Navarros"
families = {BOYDS, GARVEYS, LOGANS, NAVARROS}

flour = Var(dom=families)
kerozene = Var(dom=families)
cloth = Var(dom=families)
sugar = Var(dom=families)

cash = Var(dom=families)
credit = Var(dom=families)
ham = Var(dom=families)
peas = Var(dom=families)

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
