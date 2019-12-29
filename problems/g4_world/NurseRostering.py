from pycsp3 import *
from pycsp3.problems.data.dataparser import DataDict

data.shifts.append(DataDict({"id": "_off", "length": 0, "forbiddenFollowingShifts": None}))  # we add first a dummy off shift
off = len(data.shifts) - 1  # value for _off

nDays, nWeeks = data.nDays, data.nDays // 7
shifts, staffs = data.shifts, data.staffs
nShifts, nStaffs = len(shifts), len(staffs)

on_r = [[next((r for r in staff.onRequests if r.day == day), None) if staff.onRequests else None for day in range(nDays)] for staff in staffs]
off_r = [[next((r for r in staff.offRequests if r.day == day), None) if staff.offRequests else None for day in range(nDays)] for staff in staffs]
lengths = [shift.length for shift in shifts]
kmax = [staff.maxConsecutiveShifts for staff in staffs]
kmin = [staff.minConsecutiveShifts for staff in staffs]
kminday = [staff.minConsecutiveDaysOff for staff in staffs]


def shift_pos(s):
    return next(i for i in range(nShifts) if shifts[i].id == s)


table = {(shift_pos(s1.id), shift_pos(s2)) for s1 in shifts if s1.forbiddenFollowingShifts for s2 in s1.forbiddenFollowingShifts}  # rotation


def costs(day, shift):
    c = None if shift == off else data.covers[day][shift]
    return [0 if c is None else abs(c.requirement - i) * (c.weightIfUnder if i <= c.requirement else c.weightIfOver) for i in range(nStaffs + 1)]


def automaton_min_consecutive(k, for_shifts):
    def q(i):
        return "q" + str(i)

    range_off = range(nShifts - 1, nShifts)  # a range with only one value (off)
    range_others = range(nShifts - 1)  # a range with all other values
    r1, r2 = range_off if for_shifts else range_others, range_others if for_shifts else range_off
    t = ([(q(0), r1, q(1)), (q(0), r2, q(k + 1)), (q(1), r1, q(k + 1))]
         + [(q(i), r2, q(i + 1)) for i in range(1, k + 1)]
         + [(q(k + 1), range(nShifts), q(k + 1))])
    return Automaton(start=q(0), final=q(k + 1), transitions=t)


# x[d][p] is the shift at day d for person p (value 'off' denotes off)
x = VarArray(size=[nDays, nStaffs], dom=range(nShifts))

# ps[p][s] is the number of days such that person p works with shift s
ps = VarArray(size=[nStaffs, nShifts], dom=lambda p, s: range((nDays if s == off else staffs[p].maxShifts[s]) + 1))

# ds[d][s] is the number of persons working on day d with shift s
ds = VarArray(size=[nDays, nShifts], dom=range(nStaffs + 1))

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
    [x[d][p] == off for d in range(nDays) for p in range(nStaffs) if d in staffs[p].daysOff],

    # computing number of days
    [Count(x[:, p], value=s) == ps[p][s] for p in range(nStaffs) for s in range(nShifts)],

    # computing number of persons
    [Count(x[d], value=s) == ds[d][s] for d in range(nDays) for s in range(nShifts)],

    # computing worked week-ends
    [[imply(x[w * 7 + 5][p] != off, wk[p][w]), imply(x[w * 7 + 6][p] != off, wk[p][w])] for p in range(nStaffs) for w in range(nWeeks)],

    # rotation shifts
    [Slide((x[i][p], x[i + 1][p]) not in table for i in range(nDays - 1)) for p in range(nStaffs)] if len(table) > 0 else None,

    # maximum number of worked week-ends
    [Sum(wk[p]) <= staffs[p].maxWeekends for p in range(nStaffs)],

    # minimum and maximum number of total worked minutes
    [ps[p] * lengths in range(staff.minTotalMinutes, staff.maxTotalMinutes + 1) for p, staff in enumerate(staffs)],

    # maximum consecutive worked shifts
    [Count(x[i:i + kmax[p] + 1, p], value=off) >= 1 for p in range(nStaffs) for i in range(nDays - kmax[p])],

    # minimum consecutive worked shifts
    [x[i: i + kmin[p] + 1, p] in automaton_min_consecutive(kmin[p], True) for p in range(nStaffs) for i in range(nDays - kmin[p])],

    # managing off days on schedule ends
    [[imply(x[0][p] != off, x[i][p] != off), imply(x[- 1][p] != off, x[- 1 - i][p] != off)] for p in range(nStaffs) if kmin[p] > 1 for i in range(1, kmin[p])],

    # minimum consecutive days off
    [x[i: i + kminday[p] + 1, p] in automaton_min_consecutive(kminday[p], False) for p in range(nStaffs) for i in range(nDays - kminday[p])],

    # cost of not satisfying on requests
    [iff(x[d][p] == shift_pos(on_r[p][d].shift), cn[p][d] == 0) for p in range(nStaffs) for d in range(nDays) if on_r[p][d]],

    # cost of not satisfying off requests 
    [iff(x[d][p] == shift_pos(off_r[p][d].shift), cf[p][d] != 0) for p in range(nStaffs) for d in range(nDays) if off_r[p][d]],

    # cost of under or over covering 
    [(ds[d][s], cc[d][s]) in enumerate(costs(d, s)) for d in range(nDays) for s in range(nShifts)]
)

minimize(
    Sum(cn) + Sum(cf) + Sum(cc)
)

# possible to write ps[p] * lengths or Sum(ps[p] * lengths)

# [iff(x[d][p] == shift, cn[p][d] == 0) for (p,d,shift) in [(p,d, shift_pos(on_request(p, d).shift)) for p in range(nStaffs) for d in range(nDays) if on_request(p, d)]],
