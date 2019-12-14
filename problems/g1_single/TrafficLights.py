from pycsp3 import *

RED, RED_YELLOW, GREEN, YELLOW = "red", "red-yellow", "green", "yellow"

table = {(RED, RED, GREEN, GREEN), (RED_YELLOW, RED, YELLOW, RED), (GREEN, GREEN, RED, RED), (YELLOW, RED, RED_YELLOW, RED)}

# v[i] is the color for the ith vehicle traffic light
v = VarArray(size=4, dom={RED, RED_YELLOW, GREEN, YELLOW})

# p[i] is the color for the ith pedestrian traffic light
p = VarArray(size=4, dom={RED, GREEN})

satisfy(
    (v[i], p[i], v[(i + 1) % 4], p[(i + 1) % 4]) in table for i in range(4)
)
