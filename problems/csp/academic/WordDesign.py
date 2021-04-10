"""
See Problem 033 on CSPLib

The problem is to find as large as possible a set S of strings (words) of length 8
over the alphabet W = { A,C,G,T } with the following properties:
 - each word in S has 4 symbols from { C,G }
 - each pair of distinct words in S differ in at least 4 positions
 - each pair of words x and y in S (where x and y may be identical) are such that
   xR and yC differ in at least 4 positions. Here, (x1,...,x8 )R = (x8,...,x1) is
   the reverse of (x1,...,x8) and (x1,...,x8)C is the Watson-Crick complement of
   (x1,...,x8), i.e. the word where each A is replaced by a T and vice versa
   and each C is replaced by a G and vice versa.

This problem has its roots in Bioinformatics and Coding Theory.

Example of Execution:
  python3 WordDesign.py -data=[WordDesign.json,n=10]
"""

from pycsp3 import *

words, n = data  # each word has 4 symbols from {C,G} and is such that its reverse and Watson-Crick complement differ in at least 4 positions

# x[i][k] is the kth letter (0-A, 1-C, 2-G, 3-T) of the ith word
x = VarArray(size=[n, 8], dom=range(4))

# y[i][k] is the kth letter of the Watson-Crick complement of the ith word (in x)
y = VarArray(size=[n, 8], dom=range(4))

satisfy(
    # computing the Watson-Crick complement of words
    [x[i][k] + y[i][k] == 3 for i in range(n) for k in range(8)],

    # each word must be well formed
    [x[i] in words for i in range(n)],

    # ordering words  tag(symmetry-breaking)
    LexIncreasing(x, strict=True),

    # each pair of distinct words differ in at least 4 positions
    [Sum(x[i][k] != x[j][k] for k in range(8)) >= 4 for i, j in combinations(range(n), 2)],

    # each pair of distinct words are such that the reverse of the former and the Watson-Crick complement of the latter differ in at least 4 positions
    [Sum(x[i][7 - k] != y[j][k] for k in range(8)) >= 4 for i in range(n) for j in range(n) if i != j]
)

""" Comments
1) for computing the Watson-Crick complement of words, we could have written:
   [(x[i][k], y[i][k]) in {(0, 3), (1, 2), (2, 1), (3, 0)} for i in range(n) for k in range(8)],

2) the second parameter n is given independently of the JSON file
"""
