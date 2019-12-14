from pycsp3 import *

yellow, green, red, white, blue = colors = VarArray(size=5, dom=range(1, 6))
# colors = yellow, green, red, white, blue

countries = VarArray(size=5, dom=range(1, 6))
italy, spain, japan, england, norway = countries

jobs = VarArray(size=5, dom=range(1, 6))
painter, sculptor, diplomat, pianist, doctor = jobs

pets = VarArray(size=5, dom=range(1, 6))
cat, zebra, bear, snails, horse = pets

drinks = VarArray(size=5, dom=range(1, 6))
milk, water, tea, coffee, juice = drinks

satisfy(
    AllDifferent(colors),
    AllDifferent(countries),
    AllDifferent(jobs),
    AllDifferent(pets),
    AllDifferent(drinks),

    painter == horse,
    diplomat == coffee,
    white == milk,
    spain == painter,
    england == red,
    snails == sculptor,
    green + 1 == red,
    blue + 1 == norway,
    doctor == milk,
    japan == diplomat,
    norway == zebra,
    dist(green, white) == 1,
    horse in {diplomat - 1, diplomat + 1},
    italy in {red, white, green}
)
