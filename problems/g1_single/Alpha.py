from pycsp3 import *


def summing(word):
    return Sum(x[i] for i in to_alphabet_positions(word))


#  x[i] is the value for the ith letter of the alphabet
x = VarArray(size=26, dom=range(1, 27))

satisfy(
    AllDifferent(x),

    summing("ballet") == 45,
    summing("cello") == 43,
    summing("concert") == 74,
    summing("flute") == 30,
    summing("fugue") == 50,
    summing("glee") == 66,
    summing("jazz") == 58,
    summing("lyre") == 47,
    summing("oboe") == 53,
    summing("opera") == 65,
    summing("polka") == 59,
    summing("quartet") == 50,
    summing("saxophone") == 134,
    summing("scale") == 51,
    summing("solo") == 37,
    summing("song") == 61,
    summing("soprano") == 82,
    summing("theme") == 72,
    summing("violin") == 100,
    summing("waltz") == 34
)
