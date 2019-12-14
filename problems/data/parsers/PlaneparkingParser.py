from pandas import *
from pycsp3.problems.data.dataparser import *


def createObject(name, file):
    xls = ExcelFile(file)
    df = xls.parse(xls.sheet_names[0])
    data[name] = dict()
    for key, value in df.to_dict().items():
        data[name][key] = list(value.values())

createObject('capacites', 'pycsp3/problems/data/raw/Planeparking/capacites.xlsx')
createObject('ombrages', 'pycsp3/problems/data/raw/Planeparking/ombrages.xlsx')
createObject('ordonnancement', 'pycsp3/problems/data/raw/Planeparking/ordonnancement.xlsx')
createObject('parkings', 'pycsp3/problems/data/raw/Planeparking/parkings.xlsx')
createObject('reductions', 'pycsp3/problems/data/raw/Planeparking/reductions.xlsx')
createObject('strategies', 'pycsp3/problems/data/raw/Planeparking/strategies_matrice.xlsx')
createObject('ordonnancement', 'pycsp3/problems/data/raw/Planeparking/ordonnancement.xlsx')
createObject('traitement', 'pycsp3/problems/data/raw/Planeparking/temps_traitement.xlsx')
createObject('vols', 'pycsp3/problems/data/raw/Planeparking/vols.xlsx')
createObject('volsStrategies', 'pycsp3/problems/data/raw/Planeparking/vols_strat.xlsx')


