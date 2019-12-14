
# sudo pip3 install py4j
# sudo pip3 install pandas
# sudo pip3 install xlrd

import datetime
import json
import math

from pycsp3.solvers.abscon import AbsConProcess
from pycsp3 import *

# data.ordonnancement,  data.reductions, data.traitement and data.vols not used

parkings, capacites, ombrages = data.parkings, data.capacites, data.ombrages
strategies, volsStrategies = data.strategies, data.volsStrategies

date = "04/09/2019"  # hard coding fro the moment (see also in the creation of JSON)
k_arrival, k_departure = 600, 600  #  periods of time in seconds


def createAvailableParkings():
    d = OrderedDict()
    for i, element in enumerate(capacites['TA_CLE']):
        if element in d:
            d[element].append(capacites['RSC_COD'][i])
        else:
            d[element] = [capacites['RSC_COD'][i]]
    return d


# keys are parkings and values their indexes
code_parkings = OrderedDict((parking, i) for i, parking in enumerate(parkings['Code']))

available_parkings = createAvailableParkings()

# flights at the given date
vols = [{key: volsStrategies[key][i] for key in volsStrategies.keys()} for i in range(len(volsStrategies['Date arr']))
        if date in {volsStrategies['Date arr'][i].split(" ")[0], volsStrategies['Date dep'][i].split(" ")[0]}]

# parking without the character "/"
renamed_parking = [strategy.split("/")[1] for strategy in strategies['Ressource'] if "/" in strategy]


def table_capacities(vol):
    return [code_parkings[parking] for parking in available_parkings[vol['Type Avion']]]


def table_rewards(vol):
    table = []
    for i, parking in enumerate(code_parkings):
        if parking in renamed_parking:
            value = strategies[vol['Stratégie code dep']][renamed_parking.index(parking)]
            table.append((i, int(value) if not math.isnan(value) else 0))
        else:
            table.append((i, 0))
    return table


def table_shadowing():
    return ([(i, i) for i in range(len(code_parkings))]  # conflict if same parking
            + [(code_parkings[value], code_parkings[ombrages['RSC_COD_OMBRE'][i]]) for i, value in enumerate(ombrages['RSC_COD'])])


def to_datetime(s):
    d, t = s.split(" ")
    day, month, year = (int(v) for v in d.split("/"))
    hour, minute, second = (int(v) for v in t.split(":"))
    return datetime.datetime(year, month, day, hour, minute, second)


def are_overlapping(vol1, vol2):
    arr1 = to_datetime(vol1['Date arr']) - datetime.timedelta(seconds=k_arrival)
    dep1 = to_datetime(vol1['Date dep']) + datetime.timedelta(seconds=k_departure)
    arr2 = to_datetime(vol2['Date arr']) - datetime.timedelta(seconds=k_arrival)
    dep2 = to_datetime(vol2['Date dep']) + datetime.timedelta(seconds=k_departure)
    return arr1 < dep2 and arr2 < dep1


#  f[i] is the parking (code) of the ith flight
f = VarArray(size=[len(vols)], dom=range(len(code_parkings)))

if variant("csp"):
    satisfy(
        # taking into account only parkings authorized for flights
        [f[i] in table_capacities(vol) for i, vol in enumerate(vols)],

        # taking into account shadowing
        [(f[i], f[j]) not in table_shadowing() for i, j in combinations(range(len(vols)), 2) if are_overlapping(vols[i], vols[j])]
    )
else:
    # r[i] is the strategy satisfaction (reward) of the ith flight  
    r = VarArray(size=[len(vols)], dom=range(101))

    satisfy(
        # taking into account only parkings authorized for flights
        [f[i] in table_capacities(vol) for i, vol in enumerate(vols)],

        # computing rewards
        [(f[i], r[i]) in table_rewards(vol) for i, vol in enumerate(vols)],

        # taking into account shadowing
        [(f[i], f[j]) not in table_shadowing() for i, j in combinations(range(len(vols)), 2) if are_overlapping(vols[i], vols[j])]
    )

    # Annotations(decisions=flights)
    maximize(
        r * [vol['Poids total rotation'] for vol in vols]
    )

instance = compile()
solution = AbsConProcess().solve(instance, restarts=1000)
print(solution)

if solution:
    def arr(vol):
        return "04/09/2019 00:00:00" if vol['Date arr'][0:2] == "03" else vol['Date arr']
    def dep(vol):
        return "04/09/2019 23:55:00" if vol['Date dep'][0:2] == "05" else vol['Date dep']

    t = [{
             "index": i,
             "plane": vol['Type Avion'],
             "arrival": arr(vol),
             "departure": dep(vol),
             "company": vol['Comapgnie arr'],
             "parking": parkings['Code'][int(solution.values[i])],
             "reward": solution.values[len(vols) + i],
             "n5": int((to_datetime(dep(vol)) - to_datetime(arr(vol))).total_seconds()) / 300  # nb slots of 5 minutes
         } for i, vol in enumerate(vols)]
    with open("pycsp3/problems/g6_tests/solutionPlaneParking.json", 'w') as g:
        g.write("let flights = ")
        json.dump(t, g, separators=(',', ':'))
    print("Generation of the JSON solution file solutionPlaneParking.json completed.")



# solver = AbsconPy4J()
# solver.loadXCSP3(xml)

# def buildHTML(solution):
#     doc = dominate.document(title='planeParking')
#     with doc:
#         for i, f in enumerate(current_flights):
#             with dominate.tags.div():
#                 diff_time = stringToDatetime(f['Date dep']) - stringToDatetime(f['Date arr'])
#                 nb5 = nb5minutes(diff_time)
#                 dominate.tags.attr(
#                     numvol=i,
#                     avion=f['Type Avion'],
#                     arriver=f['Date arr'],
#                     depart=f['Date dep'],
#                     compagnie=f['Comapgnie arr'],
#                     parking=parkings['Code'][int(solution.values[i])],
#                     reward=solution.values[i + len(flights)],
#                     nb5minutes=nb5)
#     file = open("solutionPlaneParking.html", "w+")
#     file.write(doc.render())
#     file.close()
#     print("Generation of the solution file solutionPlaneParking.html completed.")
