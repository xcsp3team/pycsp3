"""
The Zebra puzzle (sometimes referred to as Einstein's puzzle) is defined as follows.
There are five houses in a row, numbered from left to right.
Each of the five houses is painted a different color, and has one inhabitant.
The inhabitants are all of different nationalities, own different pets, drink different beverages and have different jobs.
We know that:
 - colors are yellow, green, red, white, and blue
 - nations of inhabitants are italy, spain, japan, england, and norway
 - pets are cat, zebra, bear, snails, and horse
 - drinks are milk, water, tea, coffee, and juice
 - jobs are painter, sculptor, diplomat, pianist, and doctor
 - the painter owns the horse
 - the diplomat drinks coffee
 - the one who drinks milk lives in the white house
 - the Spaniard is a painter
 - the Englishman lives in the red house
 - the snails are owned by the sculptor
 - the green house is on the left of the red one
 - the Norwegian lives on the right of the blue house
 - the doctor drinks milk
 - the diplomat is Japanese
 - the Norwegian owns the zebra
 - the green house is next to the white one
 - the horse is owned by the neighbor of the diplomat
 - the Italian either lives in the red, white or green house

Execution:
  python3 Zebra.py
"""

from pycsp3 import *

houses = range(5)  # each house has a number from 0 (left) to 4 (right)

# colors[i] is the house of the ith color
yellow, green, red, white, blue = colors = VarArray(size=5, dom=houses)

# nations[i] is the house of the inhabitant with the ith nationality
italy, spain, japan, england, norway = nations = VarArray(size=5, dom=houses)

# jobs[i] is the house of the inhabitant with the ith job
painter, sculptor, diplomat, pianist, doctor = jobs = VarArray(size=5, dom=houses)

# pets[i] is the house of the inhabitant with the ith pet
cat, zebra, bear, snails, horse = pets = VarArray(size=5, dom=houses)

# drinks[i] is the house of the inhabitant with the ith preferred drink
milk, water, tea, coffee, juice = drinks = VarArray(size=5, dom=houses)

satisfy(
    AllDifferent(colors),
    AllDifferent(nations),
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
    abs(green - white) == 1,
    horse in {diplomat - 1, diplomat + 1},
    italy in {red, white, green}
)
