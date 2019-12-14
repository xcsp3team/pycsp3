from pycsp3.problems.data.dataparser import *
from pycsp3.compiler import Compilation
import random


def random_edge():
    x, y = random.randint(0, data.nNodes - 1), random.randint(0, data.nNodes - 1)
    return (x, y) if x != y else random_edge()


data.nCardsPerSuit = ask_number("Number of cards per suit (e.g., 13)")
data.nCardsPerPile = ask_number("Number of cards per pile (e.g., 3)")
seed = ask_number("Seed")
nCards = 4 * data.nCardsPerSuit
nPiles = (nCards - 1) // data.nCardsPerPile
assert (nCards - 1) % data.nCardsPerPile == 0

random.seed(seed)
cards = list(range(nCards))
data.piles = []
for i in range(nPiles):
    pile = []
    for j in range(data.nCardsPerPile):
        v = random.randrange(len(cards))
        pile.append(cards[v])
        del cards[v]
    data.piles.append(pile)

print(data.piles)

# TODO not a good way of building instances because they are most of the time  trivially unsatisfiable

Compilation.string_data = "-" + "-".join(str(v) for v in (data.nCardsPerSuit, data.nCardsPerPile, seed))
