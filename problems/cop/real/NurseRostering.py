"""
See http://www.schedulingbenchmarks.org/nurseinstances1_24.html

Example of Execution:
  python3 NurseRostering.py -data=NurseRostering_00.json
"""

from pycsp3 import *

nDays, shifts, staffs, covers = data
if shifts[-1].id != "_off":  # if not present, we add first a dummy 'off' shift (a named tuple of the right class)
    shifts.append(shifts[0].__class__("_off", 0, None))
off = len(shifts) - 1  # value for _off
nWeeks, nShifts, nStaffs = nDays // 7, len(shifts), len(staffs)

on_r = [[next((r for r in staff.onRequests if r.day == day), None) if staff.onRequests else None for day in range(nDays)] for staff in staffs]
off_r = [[next((r for r in staff.offRequests if r.day == day), None) if staff.offRequests else None for day in range(nDays)] for staff in staffs]
lengths = [shift.length for shift in shifts]

# kmin for minConsecutiveShifts, kmax for maxConsecutiveShifts, kday for minConsecutiveDaysOff
_, maxShifts, minTotalMinutes, maxTotalMinutes, kmin, kmax, kday, maxWeekends, daysOff, _, _ = zip(*staffs)

sp = {shifts[i].id: i for i in range(nShifts)}  # position of shifts in the list 'shifts'
table = {(sp[s1.id], sp[s2]) for s1 in shifts if s1.forbiddenFollowingShifts for s2 in s1.forbiddenFollowingShifts}  # rotation


def costs(day, shift):
    if shift == off:
        return [0] * (nStaffs + 1)
    r, wu, wo = covers[day][shift]
    return [abs(r - i) * (wu if i <= r else wo) for i in range(nStaffs + 1)]


def automaton(k, for_shifts):  # automaton_min_consecutive
    q = Automaton.q  # for building state names
    range_off = range(nShifts - 1, nShifts)  # a range with only one value (off)
    range_others = range(nShifts - 1)  # a range with all other values
    r1, r2 = range_off if for_shifts else range_others, range_others if for_shifts else range_off
    t = ([(q(0), r1, q(1)), (q(0), r2, q(k + 1)), (q(1), r1, q(k + 1))]
         + [(q(i), r2, q(i + 1)) for i in range(1, k + 1)]
         + [(q(k + 1), range(nShifts), q(k + 1))])
    return Automaton(start=q(0), final=q(k + 1), transitions=t)


# x[d][p] is the shift at day d for person p (value 'off' denotes off)
x = VarArray(size=[nDays, nStaffs], dom=range(nShifts))

# nd[p][s] is the number of days such that person p works with shift s
nd = VarArray(size=[nStaffs, nShifts], dom=lambda p, s: range((nDays if s == off else maxShifts[p][s]) + 1))

# np[d][s] is the number of persons working on day d with shift s
np = VarArray(size=[nDays, nShifts], dom=range(nStaffs + 1))

# wk[p][w] is 1 iff the week-end w is worked by person p
wk = VarArray(size=[nStaffs, nWeeks], dom={0, 1})

# cn[p][d] is the cost of not satisfying the on-request (if it exists) of person p on day d
cn = VarArray(size=[nStaffs, nDays], dom=lambda p, d: {0, on_r[p][d].weight} if on_r[p][d] else None)

# cf[p][d] is the cost of not satisfying the off-request (if it exists) of person p on day d
cf = VarArray(size=[nStaffs, nDays], dom=lambda p, d: {0, off_r[p][d].weight} if off_r[p][d] else None)

# cc[d][s] is the cost of not satisfying cover for shift s on day d
cc = VarArray(size=[nDays, nShifts], dom=lambda d, s: costs(d, s))

satisfy(
    # days off for staff
    [x[d][p] == off for d in range(nDays) for p in range(nStaffs) if d in daysOff[p]],

    # computing number of days
    [Count(x[:, p], value=s) == nd[p][s] for p in range(nStaffs) for s in range(nShifts)],

    # computing number of persons
    [Count(x[d], value=s) == np[d][s] for d in range(nDays) for s in range(nShifts)],

    # computing worked week-ends
    [(imply(x[w * 7 + 5][p] != off, wk[p][w]), imply(x[w * 7 + 6][p] != off, wk[p][w])) for p in range(nStaffs) for w in range(nWeeks)],

    # rotation shifts
    [Slide((x[i][p], x[i + 1][p]) not in table for i in range(nDays - 1)) for p in range(nStaffs)] if len(table) > 0 else None,

    # maximum number of worked week-ends
    [Sum(wk[p]) <= maxWeekends[p] for p in range(nStaffs)],

    # minimum and maximum number of total worked minutes
    [nd[p] * lengths in range(minTotalMinutes[p], maxTotalMinutes[p] + 1) for p in range(nStaffs)],

    # maximum consecutive worked shifts
    [Count(x[i:i + kmax[p] + 1, p], value=off) >= 1 for p in range(nStaffs) for i in range(nDays - kmax[p])],

    # minimum consecutive worked shifts
    [x[i: i + kmin[p] + 1, p] in automaton(kmin[p], True) for p in range(nStaffs) for i in range(nDays - kmin[p])],

    # managing off days on schedule ends
    [(imply(x[0][p] != off, x[i][p] != off), imply(x[-1][p] != off, x[-1 - i][p] != off)) for p in range(nStaffs) if kmin[p] > 1 for i in range(1, kmin[p])],

    # minimum consecutive days off
    [x[i: i + kday[p] + 1, p] in automaton(kday[p], False) for p in range(nStaffs) for i in range(nDays - kday[p])],

    # cost of not satisfying on requests
    [iff(x[d][p] == sp[on_r[p][d].shift], cn[p][d] == 0) for p in range(nStaffs) for d in range(nDays) if on_r[p][d]],

    # cost of not satisfying off requests
    [iff(x[d][p] == sp[off_r[p][d].shift], cf[p][d] != 0) for p in range(nStaffs) for d in range(nDays) if off_r[p][d]],

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
