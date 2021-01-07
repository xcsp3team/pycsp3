import random

from pycsp3.compiler import Compilation
from pycsp3.problems.data.parsing import *

nCardsPerSuit = ask_number("Number of cards per suit (e.g., 13)")
nCardsPerPile = ask_number("Number of cards per pile (e.g., 3)")
seed = ask_number("Seed")

nCards = 4 * nCardsPerSuit
nPiles = (nCards - 1) // nCardsPerPile
assert (nCards - 1) % nCardsPerPile == 0

random.seed(seed)
active_piles = list(range(nPiles))
piles = [[] for _ in range(nPiles)]

for i in range(1, nCards):
    r = random.randrange(len(active_piles))
    k = active_piles[r]
    piles[k].insert(0, i)
    if len(piles[k]) == nCardsPerPile:
        del active_piles[r]

data["nCardsPerSuit"] = nCardsPerSuit
data["piles"] = piles

Compilation.string_data = "-" + "-".join(str(v) for v in (nCardsPerSuit, nCardsPerPile, seed))
