import datetime
import time as clock
import types
from collections import OrderedDict
from collections.abc import Iterable
from multiprocessing import cpu_count, Pool

from pycsp3.classes.main.domains import Domain
from pycsp3.tools.curser import ListInt


# used to save data in jSON
def prepare_for_json(obj):
    if hasattr(obj, "__dict__") and not isinstance(obj, ListInt):
        d = obj.__dict__
        for k, v in d.items():
            d[k] = prepare_for_json(v)
        return d
    else:
        if isinstance(obj, datetime.time):
            return str(obj)
        if hasattr(obj, "__getitem__") and hasattr(obj, "__setitem__") and hasattr(obj, "__iter__"):  # TODO do we need all three tests?
            for i, v in enumerate(obj):
                obj[i] = prepare_for_json(v)
        return obj


class Stopwatch:
    def __init__(self):
        self.initial_time = clock.time()

    def elapsed_time(self, *, reset=False):
        elapsed_time = clock.time() - self.initial_time
        if reset:
            self.initial_time = clock.time()
        return elapsed_time


class DefaultListOrderedDict(OrderedDict):
    def __missing__(self, k):
        self[k] = []
        return self[k]


def is_1d_list(l, type=None):
    return isinstance(l, list) and all(isinstance(v, type) if type else not isinstance(v, list) for v in l)


def is_1d_tuple(l, type):
    return isinstance(l, tuple) and all(isinstance(v, type) for v in l)


def is_2d_list(m, type=None):
    return isinstance(m, list) and all(is_1d_list(l, type) for l in m)


def is_matrix(m, type=None):
    return is_2d_list(m, type) and all(len(l) == len(m[0]) for l in m)


def is_square_matrix(m, type=None):
    return is_matrix(m, type) and len(m) == len(m[0])


def transpose(m):
    assert is_matrix(m)
    return [[m[j][i] for j in range(len(m))] for i in range(len(m[0]))]


def flatten(*args):
    assert isinstance(args, tuple), "Arguments in flatten represent a tuple of arguments"
    output = []
    for arg in args:
        if isinstance(arg, type(None)):
            pass
        elif isinstance(arg, (str, range, Domain)):  # Iterable but must be appended, not extended
            output.append(arg)
        elif isinstance(arg, Iterable):
            output.extend(flatten(*arg))
        elif isinstance(arg, types.GeneratorType):
            output.extend(flatten(*list(arg)))
        else:
            output.append(arg)
    return output


def is_containing(l, types, *, check_first_only=False):
    if isinstance(l, (list, tuple)):
        if len(l) == 0:
            return None
        found = False
        for v in l:
            res = is_containing(v, types, check_first_only=check_first_only)
            if res is False:
                return False
            elif res is True:
                if check_first_only:
                    return True
                found = True
        return True if found else None
    else:
        return isinstance(l, types)


def alphabet_positions(s):
    assert isinstance(s, str)
    return tuple(ord(c) - ord('a') for c in s.lower())


def matrix_to_string(m):
    return "\n".join(["\t(" + ",".join([str(v) for v in t]) + ")\n" for t in m])


def transitions_to_string(ts):
    return "".join(["(" + q1 + "," + str(v) + "," + q2 + ")" for (q1, v, q2) in ts])


def value_in_base(decimal_value, length, base):
    assert type(decimal_value) == type(length) == type(base) is int
    value = [0] * length
    for i in range(len(value) - 1, -1, -1):
        value[i] = decimal_value % base
        decimal_value = decimal_value // base
    assert decimal_value == 0, "The given array is too small to contain all the digits of the conversion"
    return value


def parallel_table_to_string(table):
    if len(table) < 100000:
        return "".join(table_to_string(table))
    print("Parallel creation of a table of size: " + str(len(table)))
    nb_threads = cpu_count()
    nb_elements = len(table) // nb_threads
    pool = Pool(nb_threads)
    start_position = 0
    end_position = nb_elements
    result_objects = []

    for i in range(nb_threads):
        result_objects.append(pool.apply_async(table_to_string, args=(table[start_position:end_position],)))
        start_position += nb_elements
        end_position = len(table) if i in {nb_threads - 2, nb_threads - 1} else end_position + nb_elements
    assert end_position == len(table)

    results = [r.get() for r in result_objects]
    pool.close()
    pool.join()

    previous_part = None
    for i in results:
        if previous_part is not None:
            pos_last = len(previous_part) - 1
            if previous_part[pos_last] == i[0]:
                previous_part.pop()
        previous_part = i

    return "".join("".join(t) for t in results)


# table is assumed to be sorted (adding an assert?)
# only distinct tuples are kept
def table_to_string(table):
    s = []
    previous = ""
    for t in table:
        if t != previous:
            s.append("(" + ",".join(str(v) for v in t) + ")")
            previous = t
    return s


def integers_to_string(numbers):
    if len(numbers) == 0:
        return ''
    numbers = sorted(numbers)
    t = list()
    prev = numbers[0]
    for curr in numbers:
        if curr != prev + 1:
            t.append([curr])  # the start of a possible interval
        elif len(t[-1]) > 1:
            t[-1][-1] = curr  # to modify the end of the interval
        else:
            t[-1].append(curr)  # to set the end of the interval
        prev = curr
    return ' '.join(str(i[0]) if len(i) == 1 else str(i[0]) + ('..' if i[0] != i[1] - 1 else ' ') + str(i[1]) for i in t)


def display_constraints(ctr_entities, separator=""):
    for ce in ctr_entities:
        if ce is not None:
            if hasattr(ce, "entities"):
                print(separator + str(ce))
                display_constraints(ce.entities, separator + "\t")
            else:
                print(separator + str(ce.constraint))


PURPLE, BLUE, GREEN, ORANGE, RED, WHITE, WHITE_BOLD, UNDERLINE = '\033[95m', '\033[94m', '\033[92m', '\033[93m', '\033[91m', '\033[0m', '\033[1m', '\033[4m'


def warning(message):
    print("  " + ORANGE + "Warning: " + WHITE + message)
