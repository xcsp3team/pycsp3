from pycsp3 import *

grid = data
nRows, nCols = len(grid), len(grid[0])


def scope(i, j, mode):
    scp = []
    if mode == 'h':  # horizontal scope
        if j == 0 or grid[i][j - 1] != -1 and grid[i][j] == -1:
            while j < len(grid[i]) and grid[i][j] == -1:
                scp.append(x[i][j])
                j += 1
    elif mode == 'v':  # vertical scope
        if i == 0 or grid[i - 1][j] != -1 and grid[i][j] == -1:
            while i < len(grid) and grid[i][j] == -1:
                scp.append(x[i][j])
                i += 1
    elif mode == 'f':  # full scope
        if grid[i][j] != -1:
            return None
        base = j
        while base >= 0 and grid[i][base] == -1:
            base -= 1
        for jj in range(base + 1, len(grid[i])):
            if grid[i][jj] != -1:
                break
            scp.append(x[i][jj])
        base = i
        while base >= 0 and grid[base][j] == -1:
            base -= 1
        for ii in range(base + 1, len(grid)):
            if grid[ii][j] != -1:
                break
            if ii != i:
                scp.append(x[ii][j])
    elif mode == 's':  # side scope
        if i > 0 and grid[i - 1][j] == -1:
            scp.append(x[i - 1][j])
        if i < len(grid) - 1 and grid[i + 1][j] == -1:
            scp.append(x[i + 1][j])
        if j > 0 and grid[i][j - 1] == -1:
            scp.append(x[i][j - 1])
        if j < len(grid[i]) - 1 and grid[i][j + 1] == -1:
            scp.append(x[i][j + 1])
    limit = 2 if mode in {'h', 'v'} else 1
    return scp if len(scp) >= limit else None


# x[i][j] is 1 iff a light bulb is put at row i and col j
x = VarArray(size=[nRows, nCols], dom={0, 1})

satisfy(
    # at most 1 bulb on each maximal sequence of white cells on rows
    [Count(scp, value=1) <= 1 for scp in [scope(i, j, 'h') for i in range(nRows) for j in range(nCols)] if scp],

    # at most 1 bulb on each maximal sequence of white cells on columns
    [Count(scp, value=1) <= 1 for scp in [scope(i, j, 'v') for i in range(nRows) for j in range(nCols)] if scp],

    [Count(scp, value=1) >= 1 for scp in [scope(i, j, 'f') for i in range(nRows) for j in range(nCols)] if scp],

    # tag(clues)
    [Count(scp, value=1) == k for (scp, k) in [(scope(i, j, 's'), grid[i][j]) for i in range(nRows) for j in range(nCols)] if scp and 0 <= k <= 4]
)
