"""
Five friends (three women named Mindy, Sabrina and Tanya and two men named Anton and Chet) agreed to meet on an island
in the middle of the bay for a picnic lunch on Sunday.
Each arrived on a different type of conveyance (jet-ski, kayak, outrigger canoe, sailboard, and sailboat),
and each brought a different beverage (beer, juice, soda, water and wine)
and a different food (bread, cheese, cookies, fish and salad) to share with the others.
We know that:
 - Mindy and the person who arrived on the jet-ski brought, in some order, beer and soda.
 - The five people are Chet, the person who arrived by kayak, and the people who brought the fish, water and wine.
 - The person who brought the salad didn't bring the wine.
 - Sabrina and the person who brought the cheese are, in some order, the person who arrived by outrigger canoe and the one who brought the beer.
 - A woman brought bread and juice.
 - The person who arrived by sailboat is not the person who brought the soda and the other person who brought the cookies.

Execution:
  python3 Picnic.py
"""

from pycsp3 import *

friends = Mindy, Sabrina, Tanya, Anton, Chet = "Mindy", "Sabrina", "Tanya", "Anton", "Chet"

# conveyances[i] is the friend who arrived with the ith conveyance
jetski, kayak, canoe, sailboard, sailboat = conveyances = VarArray(size=5, dom=friends)

# drinks[i] is the friend who brought the ith drink
beer, juice, soda, water, wine = drinks = VarArray(size=5, dom=friends)

# foods[i] is the friend who brought the ith food
bread, cheese, cookies, fish, salad = foods = VarArray(size=5, dom=friends)

satisfy(
    AllDifferent(conveyances),
    AllDifferent(drinks),
    AllDifferent(foods),

    (beer == Mindy) | (soda == Mindy),
    (beer == jetski) | (soda == jetski),
    jetski != Mindy,
    kayak != Chet,
    fish != Chet,
    water != Chet,
    wine != Chet,
    AllDifferent(kayak, fish, water, wine),
    salad != wine,
    (canoe == Sabrina) | (beer == Sabrina),
    (canoe == cheese) | (beer == cheese),
    canoe != beer,
    cheese != Sabrina,
    jetski in {beer, soda},
    Mindy in {beer, soda},
    bread in {Mindy, Sabrina, Tanya},
    juice in {Mindy, Sabrina, Tanya},
    bread == juice,
    sailboat not in {soda, cookies},
    soda != cookies
)
