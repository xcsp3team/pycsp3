from pycsp3 import *

# Problem 081 at CSPLib

m = data.nCardsPerSuit
nCards = 4 * m

# x[i] is the value j of the card at the ith position of the built stack.
x = VarArray(size=nCards, dom=range(nCards))

# y[j] is the position i of the card whose value is j
y = VarArray(size=nCards, dom=range(nCards))

table = {(i, j) for i in range(nCards) for j in range(nCards)
         if i % m == (j + 1) % m or j % m == (i + 1) % m}

satisfy(
    Channel(x, y),

    # the Ace of Spades is initially put on the stack
    y[0] == 0,

    # cards must be played in the order of the piles
    [Increasing([y[j] for j in pile], strict=True) for pile in data.piles],

    # each new card put on the stack must be at a rank higher or lower than the previous one.
    Slide((x[i], x[i + 1]) in table for i in range(nCards - 1))
)
