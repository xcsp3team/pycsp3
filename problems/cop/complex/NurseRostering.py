"""
Realistic employee shift scheduling Problem.

## Data Example
  01.json

## Model
  constraints: Count, Regular, Sum, Table

## Execution
  - python NurseRostering.py -data=<datafile.json>

## Links
  - http://www.schedulingbenchmarks.org/nurseinstances1_24.html
  - https://link.springer.com/chapter/10.1007/978-3-642-04244-7_9
  - https://www.cril.univ-artois.fr/XCSP22/competitions/cop/cop

## Tags
  real, xcsp22
"""

from pycsp3 import *

nDays, shifts, staffs, covers = data

if shifts[-1].id != "_off":  # if not present, we add first a dummy 'off' shift (a named tuple of the right class)
    shifts.append(shifts[0].__class__("_off", 0, None))
OFF = len(shifts) - 1  # value for _off
lengths = [shift.length for shift in shifts]
nWeeks, nShifts, nStaffs = nDays // 7, len(shifts), len(staffs)

on_r = [[next((r for r in staff.onRequests if r.day == day), None) if staff.onRequests else None for day in range(nDays)] for staff in staffs]
off_r = [[next((r for r in staff.offRequests if r.day == day), None) if staff.offRequests else None for day in range(nDays)] for staff in staffs]

# kmin for minConsecutiveShifts, kmax for maxConsecutiveShifts, kday for minConsecutiveDaysOff
_, maxShifts, minTimes, maxTimes, kmin, kmax, kday, maxWeekends, daysOff, _, _ = zip(*staffs)

sp = {shifts[i].id: i for i in range(nShifts)}  # position of shifts in the list 'shifts'
T = {(sp[s1.id], sp[s2]) for s1 in shifts if s1.forbiddenFollowingShifts for s2 in s1.forbiddenFollowingShifts}  # rotation


def costs(day, shift):
    if shift == OFF:
        return [0] * (nStaffs + 1)
    r, wu, wo = covers[day][shift]
    return [abs(r - i) * (wu if i <= r else wo) for i in range(nStaffs + 1)]


def automaton(k, for_shifts):  # automaton_min_consecutive
    q = Automaton.q  # for building state names
    range_off = range(nShifts - 1, nShifts)  # a range with only one value (off)
    range_others = range(nShifts - 1)  # a range with all other values
    r1, r2 = (range_off, range_others) if for_shifts else (range_others, range_off)
    t = [(q(0), r1, q(1)), (q(0), r2, q(k + 1)), (q(1), r1, q(k + 1))]
    t.extend((q(i), r2, q(i + 1)) for i in range(1, k + 1))
    t.append((q(k + 1), range(nShifts), q(k + 1)))
    return Automaton(start=q(0), final=q(k + 1), transitions=t)


# x[d][p] is the shift at day d for person p (value 'OFF' denotes off)
x = VarArray(size=[nDays, nStaffs], dom=range(nShifts))

# nd[p][s] is the number of days such that person p works with shift s
nd = VarArray(size=[nStaffs, nShifts], dom=lambda p, s: range((nDays if s == OFF else maxShifts[p][s]) + 1))

# np[d][s] is the number of persons working on day d with shift s
np = VarArray(size=[nDays, nShifts], dom=range(nStaffs + 1))

# wk[p][w] is 1 iff the weekend w is worked by person p
wk = VarArray(size=[nStaffs, nWeeks], dom={0, 1})

# cn[p][d] is the cost of not satisfying the on-request (if it exists) of person p on day d
cn = VarArray(size=[nStaffs, nDays], dom=lambda p, d: {0, on_r[p][d].weight} if on_r[p][d] else None)

# cf[p][d] is the cost of not satisfying the off-request (if it exists) of person p on day d
cf = VarArray(size=[nStaffs, nDays], dom=lambda p, d: {0, off_r[p][d].weight} if off_r[p][d] else None)

# cc[d][s] is the cost of not satisfying cover for shift s on day d
cc = VarArray(size=[nDays, nShifts], dom=lambda d, s: costs(d, s))

satisfy(
    # days off for staff
    [x[d][p] == OFF for d in range(nDays) for p in range(nStaffs) if d in daysOff[p]],

    # computing number of days
    [Count(x[:, p], value=s) == nd[p][s] for p in range(nStaffs) for s in range(nShifts)],

    # computing number of persons
    [Count(x[d], value=s) == np[d][s] for d in range(nDays) for s in range(nShifts)],

    # computing worked weekends
    [
        (
            If(x[w * 7 + 5][p] != OFF, Then=wk[p][w]),
            If(x[w * 7 + 6][p] != OFF, Then=wk[p][w])
        ) for p in range(nStaffs) for w in range(nWeeks)
    ],

    # rotation shifts
    [Slide((x[i][p], x[i + 1][p]) not in T for i in range(nDays - 1)) for p in range(nStaffs)] if len(T) > 0 else None,

    # maximum number of worked weekends
    [Sum(wk[p]) <= maxWeekends[p] for p in range(nStaffs)],

    # minimum and maximum number of total worked minutes
    [nd[p] * lengths in range(minTimes[p], maxTimes[p] + 1) for p in range(nStaffs)],

    # maximum consecutive worked shifts
    [Count(x[i:i + kmax[p] + 1, p], value=OFF) >= 1 for p in range(nStaffs) for i in range(nDays - kmax[p])],

    # minimum consecutive worked shifts
    [x[i: i + kmin[p] + 1, p] in automaton(kmin[p], True) for p in range(nStaffs) for i in range(nDays - kmin[p])],

    # managing off days on schedule ends
    [
        (
            If(x[0][p] != OFF, Then=x[i][p] != OFF),
            If(x[-1][p] != OFF, Then=x[-1 - i][p] != OFF)
        ) for p in range(nStaffs) if kmin[p] > 1 for i in range(1, kmin[p])
    ],

    # minimum consecutive days off
    [x[i: i + kday[p] + 1, p] in automaton(kday[p], False) for p in range(nStaffs) for i in range(nDays - kday[p])],

    # cost of not satisfying on requests
    [(x[d][p] == sp[on_r[p][d].shift]) == (cn[p][d] == 0) for p in range(nStaffs) for d in range(nDays) if on_r[p][d]],

    # cost of not satisfying off requests
    [(x[d][p] == sp[off_r[p][d].shift]) == (cf[p][d] != 0) for p in range(nStaffs) for d in range(nDays) if off_r[p][d]],

    # cost of under or over covering
    [(np[d][s], cc[d][s]) in enumerate(costs(d, s)) for d in range(nDays) for s in range(nShifts)]
)

minimize(
    Sum(cn) + Sum(cf) + Sum(cc)
)

""" Comments
1) Note that we could have written:
 [iff(x[d][p] == s, cn[p][d] == 0) for (p,d,s) in [(p,d, sp[on_r[p][d].shift]) for p in range(nStaffs) for d in range(nDays) if on_r[p][d]]],
"""
