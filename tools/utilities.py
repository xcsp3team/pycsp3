import sys
import types
from collections import OrderedDict
from collections.abc import Iterable
from multiprocessing import cpu_count, Pool
from time import time

from pycsp3.classes.main.domains import Domain
from pycsp3.dashboard import options


class Stopwatch:
    def __init__(self):
        self.initial_time = time()

    def elapsed_time(self, *, reset=False):
        elapsed_time = time() - self.initial_time
        if reset:
            self.initial_time = time()
        return elapsed_time


class _Star(float):
    def __init__(self, val):
        super().__init__()

    def __str__(self):
        return "*"


ANY = _Star("inf")


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
    if isinstance(l, (list, tuple, set, frozenset)):
        if len(l) == 0:
            return None
        found = False
        for v in l:
            if not is_containing(v, types, check_first_only=check_first_only):
                return False
            if check_first_only:
                return True
            found = True
        return True if found else None
    else:
        return isinstance(l, types)


def alphabet_positions(s):
    assert isinstance(s, str)
    return tuple(ord(c) - ord('a') for c in s.lower())


def value_in_base(decimal_value, length, base):
    assert type(decimal_value) == type(length) == type(base) is int
    value = [0] * length
    for i in range(len(value) - 1, -1, -1):
        value[i] = decimal_value % base
        decimal_value = decimal_value // base
    assert decimal_value == 0, "The given array is too small to contain all the digits of the conversion"
    return value


def matrix_to_string(m):
    return "".join(["(" + ",".join([str(v) for v in t]) + ")" for t in m])
    # return "\n" + "\n".join(["\t(" + ",".join([str(v) for v in t]) + ")" for t in m]) + "\n"


def transitions_to_string(ts):
    return "".join(["(" + q1 + "," + str(v) + "," + q2 + ")" for (q1, v, q2) in ts])


def table_to_string(table, *, parallel=False):
    if not parallel or len(table) < 100000:
        s = []
        previous = ""
        for t in table:  # table is assumed to be sorted (adding an assert?) ; only distinct tuples are kept
            if t != previous:
                s.append("(" + ",".join(str(v) for v in t) + ")")
                previous = t
        return "".join(s)
    else:
        print("Parallel creation of a table of size: " + str(len(table)))
        n_threads = cpu_count()
        size = len(table) // n_threads
        pool = Pool(n_threads)
        left, right = 0, size
        t = []
        for piece in range(n_threads):
            t.append(pool.apply_async(table_to_string, args=(table[left:right],)))  # call not in parallel
            left += size
            right = len(table) if piece in {n_threads - 2, n_threads - 1} else right + size
        assert right == len(table)
        pieces = [r.get() for r in t]
        pool.close()
        pool.join()
        # checking and removing similar tuples before returning the string ?
        previous = None
        for piece in pieces:
            if previous and previous[-1] == piece[0]:
                previous.pop()
            previous = piece
        return "".join("".join(piece) for piece in pieces)


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


def error(s):
    print("\n\t" + RED + "ERROR: " + WHITE, s, "\n")
    print("\t\t(add option -ev to your command if you want to see the trace of the error)\n")
    if options.ev:
        raise TypeError(s)
    else:
        sys.exit(0)
