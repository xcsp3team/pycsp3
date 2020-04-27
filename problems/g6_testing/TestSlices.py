from pycsp3 import *

x = VarArray(size=[10, 10], dom=range(150))
z = VarArray(size=[10, 10, 10], dom=range(150))

print("slice1:", x[:7, 8])
print("slice2:", x[2:7, 1:4])
print("slice3:", z[1:3, 1:5, 1])

slice1 = [x[0][8], x[1][8], x[2][8], x[3][8], x[4][8], x[5][8], x[6][8]]
slice2 = [[x[2][1], x[2][2], x[2][3]],
          [x[3][1], x[3][2], x[3][3]],
          [x[4][1], x[4][2], x[4][3]],
          [x[5][1], x[5][2], x[5][3]],
          [x[6][1], x[6][2], x[6][3]]
          ]
slice3 = [[z[1][1][1], z[1][2][1], z[1][3][1], z[1][4][1]], [z[2][1][1], z[2][2][1], z[2][3][1], z[2][4][1]]]

assert x[:7, 8] == slice1
assert x[2:7, 1:4] == slice2
assert z[1:3, 1:5, 1] == slice3
