"""
From http://jimorlin.wordpress.com/2009/02/17/colored-letters-labeled-dice-a-logic-puzzle/
There are 13 words as follows: buoy, cave, celt, flub, fork, hemp, judy, junk, limn, quip, swag, visa, wish.
There are 24 different letters that appear in the 13 words.
The question is: can one assign the 24 letters to 4 different cubes so that the four letters of each word appears on different cubes.
There is one letter from each word on each cube.
The puzzle was created by Humphrey Dudley.

Execution:
  python3 LabeledDice.py
"""

from pycsp3 import *

words = ["buoy", "cave", "celt", "flub", "fork", "hemp", "judy", "junk", "limn", "quip", "swag", "visa", "wish"]
letters = alphabet_positions(words)  # indexes of present letters
cubes = range(1, 5)  # the indexes 0, 1, 2, 3 of the four cubes

# x[i] is the cube where the ith letter of the alphabet is put
x = VarArray(size=26, dom=lambda i: cubes if i in letters else None)

satisfy(
    # the four letters of each word appear on different cubes
    [AllDifferent(x[i] for i in alphabet_positions(w)) for w in words],

    # each cube is assigned 6 letters
    Cardinality(x, occurrences={i: 6 for i in cubes})
)
