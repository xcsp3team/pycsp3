"""
See https://en.wikipedia.org/wiki/Light_Up_(puzzle)

Examples of Execution:
  python3 Lightup.py -data=Lightup_example.json
  python3 Lightup.py -data=Lightup_example.txt -dataparser=Lightup_Parser.py
"""

from pycsp3 import *

grid = data  # -1 is for a white cell, 0 to 4 for a hint and 5 for a black cell
n, m = len(grid), len(grid[0])


def scope(i, j, mode):
    scp = []
    if mode == 'h':  # horizontal scope
        if j == 0 or grid[i][j - 1] != -1 and grid[i][j] == -1:  # a left border
            while j < m and grid[i][j] == -1:
                scp.append(x[i][j])
                j += 1
    elif mode == 'v':  # vertical scope
        if i == 0 or grid[i - 1][j] != -1 and grid[i][j] == -1:  # a top border
            while i < n and grid[i][j] == -1:
                scp.append(x[i][j])
                i += 1
    elif mode == 'f':  # full scope
        if grid[i][j] != -1:
            return None
        base = j
        while base >= 0 and grid[i][base] == -1:
            base -= 1
        for jj in range(base + 1, m):
            if grid[i][jj] != -1:
                break
            scp.append(x[i][jj])
        base = i
        while base >= 0 and grid[base][j] == -1:
            base -= 1
        for ii in range(base + 1, n):
            if grid[ii][j] != -1:
                break
            if ii != i:
                scp.append(x[ii][j])
    elif mode == 's':  # side scope
        if i > 0 and grid[i - 1][j] == -1:
            scp.append(x[i - 1][j])
        if i < n - 1 and grid[i + 1][j] == -1:
            scp.append(x[i + 1][j])
        if j > 0 and grid[i][j - 1] == -1:
            scp.append(x[i][j - 1])
        if j < m - 1 and grid[i][j + 1] == -1:
            scp.append(x[i][j + 1])
    limit = 2 if mode in {'h', 'v'} else 1
    return scp if len(scp) >= limit else None


# x[i][j] is 1 iff a light bulb is put at row i and col j
x = VarArray(size=[n, m], dom={0, 1})

satisfy(
    # at most 1 bulb on each maximal sequence of white cells on rows
    [Count(scp) <= 1 for scp in [scope(i, j, 'h') for i in range(n) for j in range(m)] if scp],

    # at most 1 bulb on each maximal sequence of white cells on columns
    [Count(scp) <= 1 for scp in [scope(i, j, 'v') for i in range(n) for j in range(m)] if scp],

    [Count(scp) >= 1 for scp in [scope(i, j, 'f') for i in range(n) for j in range(m)] if scp],

    # tag(clues)
    [Count(scp) == k for (scp, k) in [(scope(i, j, 's'), grid[i][j]) for i in range(n) for j in range(m)] if scp and 0 <= k <= 4]
)
