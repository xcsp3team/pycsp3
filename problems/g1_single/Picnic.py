from pycsp3 import *

MINDY, SABRINA, TANYA, ANTON, CHET = "Mindy", "Sabrina", "Tanya", "Anton", "Chet"
friends = {MINDY, SABRINA, TANYA, ANTON, CHET}

jetski, kayak, canoe, sailboard, sailboat = sports = VarArray(size=5, dom=friends)

beer, juice, soda, water, wine = drinks = VarArray(size=5, dom=friends)

bread, cheese, cookies, fish, salad = foods = VarArray(size=5, dom=friends)

satisfy(
    AllDifferent(sports),
    AllDifferent(drinks),
    AllDifferent(foods),
    (beer == MINDY) | (soda == MINDY),
    (beer == jetski) | (soda == jetski),
    jetski != MINDY,
    kayak != CHET,
    fish != CHET,
    water != CHET,
    wine != CHET,
    AllDifferent(kayak, fish, water, wine),
    salad != wine,
    (canoe == SABRINA) | (beer == SABRINA),
    (canoe == cheese) | (beer == cheese),
    canoe != beer,
    cheese != SABRINA,
    eq({jetski, MINDY}, {beer, soda}),
    bread in {MINDY, SABRINA, TANYA},
    juice in {MINDY, SABRINA, TANYA},
    bread == juice,
    sailboat not in {soda, cookies},
    soda != cookies
)
