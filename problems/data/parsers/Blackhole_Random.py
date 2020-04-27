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
cards = list(range(nCards))
piles = []
for i in range(nPiles):
    pile = []
    for j in range(nCardsPerPile):
        v = random.randrange(len(cards))
        pile.append(cards[v])
        del cards[v]
    piles.append(pile)

data["nCardsPerSuit"] = nCardsPerSuit
data["piles"] = piles

Compilation.string_data = "-" + "-".join(str(v) for v in (nCardsPerSuit, seed))

# TODO not a good way of building instances because they are most of the time  trivially unsatisfiable
