"""
See model in OscaR

A number with an interesting property: when I divide it by v, the remainder is v-1,
and this from v ranging from 2 to 9.
It's not a small number, but it's not really big, either.
When I looked for a smaller number with this property I couldn't find one.
Can you find it?

Execution:
  python3 MagicModuloNumber.py
"""

from pycsp3 import *

x = Var(range(10000))

satisfy(
    x % i == i - 1 for i in range(2, 10)
)
