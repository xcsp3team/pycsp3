from pycsp3 import *

w = Var(range(15))
x = Var(0, 1)
y = Var(0, 2, 4, 6, 8)
z = Var('a', 'b', 'c')

w1 = Var({range(15)})
x1 = Var({0, 1})
y1 = Var({0, 2, 4, 6, 8})
z1 = Var({'a', 'b', 'c'})

w2 = Var(dom={range(15)})
x2 = Var(dom={0, 1})
y2 = Var(dom={0, 2, 4, 6, 8})
z2 = Var(dom={'a', 'b', 'c'})

y3 = Var(i for i in range(10) if i % 2 == 0)
y4 = Var({i for i in range(10) if i % 2 == 0})
y5 = Var(dom={i for i in range(10) if i % 2 == 0})
