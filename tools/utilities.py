import itertools
import os
import sys
import types
from collections.abc import Iterable
from decimal import Decimal
from multiprocessing import cpu_count, Pool
from time import time

from pycsp3 import tools
from pycsp3.classes.auxiliary import conditions
from pycsp3.dashboard import options


class AttributeDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


def check_int(s):
    s = str(s).strip()
    return s[1:].isdigit() if s[0] in ('-', '+') else s.isdigit()


def neg_range(r: range):
    assert isinstance(r, range) and r.step == 1
    return range(-r.stop + 1, -r.start + 1)


def abs_range(r: range):
    assert isinstance(r, range) and r.step == 1
    return range(0 if 0 in r else min(abs(r.start), abs(r.stop - 1)), max(abs(r.start), abs(r.stop - 1)) + 1)


def add_range(r1: range, r2: range):
    assert isinstance(r1, range) and r1.step == 1 and isinstance(r2, range) and r2.step == 1
    return range(r1.start + r2.start, r1.stop + r2.stop - 1)


def possible_range(s: set[int], control_int=False):
    assert isinstance(s, set) and (not control_int or all(isinstance(v, int) for v in s))
    t = sorted(s)
    return range(t[0], t[-1] + 1) if 1 < t[-1] - t[0] + 1 == len(t) else t


class Stopwatch:
    def __init__(self):
        self.initial_time = time()

    def elapsed_time(self, *, reset=False):
        elapsed_time = time() - self.initial_time
        if reset:
            self.initial_time = time()
        return "{:.2f}".format(elapsed_time)


class _Star(float):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def __repr__(self):
        return "*"

    def __str__(self):
        return "*"


ANY = _Star("Inf")  #: used to represent * in short tables
""" Constant used to represent * in starred tables """

ALL = "all"
""" Constant used to indicate, for example, that all solutions must be sought """


def combinations(n, size):
    return itertools.combinations(n if not isinstance(n, int) else range(n), size)


# def product(n, r):
#     return itertools.product(n if not isinstance(n, int) else range(n), r)


def different_values(*args):
    """
    Returns True if
     all specified integers are different
    :return: True if all specified integers are different
    """
    assert all(isinstance(arg, int) for arg in args)
    return all(a != b for (a, b) in combinations(args, 2))


def flatten(*args, keep_none=False, keep_tuples=False):
    """
    Returns a list with all elements that can be encountered when looking into the specified arguments.
    Typically, this is a list (of possibly any dimension).

    :param keep_none: if True, None values are not discarded
    """
    # if not hasattr(flatten, "cache"):  # cannot work (changing to TupleInt and TupleVar instead of ListInt and ListVar while guaranteeing the lifetime? how?)
    #     flatten.cache = {}
    # elif len(args) == 1 and id(args[0]) in flatten.cache:
    #     return flatten.cache[id(args[0])]
    t = []
    for arg in args:
        if arg is None:
            if keep_none:
                t.append(arg)
        elif isinstance(arg, (str, range)) or (isinstance(arg, tuple) and keep_tuples):  # , Domain)):  # Iterable but must be appended, not extended
            t.append(arg)
        elif isinstance(arg, types.GeneratorType):
            res = list(arg)
            if len(res) > 0:
                t.extend(flatten(*res, keep_none=keep_none, keep_tuples=keep_tuples))
        elif isinstance(arg, Iterable):
            t.extend(flatten(*arg, keep_none=keep_none, keep_tuples=keep_tuples))
        else:
            t.append(arg)
    # if len(args) == 1:
    #     flatten.cache[id(args[0])] = t
    return tools.curser.cp_array(t)  # previously: return t


def is_containing(t, types, *, check_first_only=False):
    if isinstance(t, (list, tuple, set, frozenset)):
        if len(t) == 0:
            return None
        found = False
        for v in t:
            if not is_containing(v, types, check_first_only=check_first_only):
                return False
            if check_first_only:
                return True
            found = True
        return True if found else None
    else:
        return isinstance(t, types)


def unique_type_in(t, tpe=None):
    if isinstance(t, (list, tuple, set, frozenset)):
        if len(t) == 0:
            return None
        for v in t:
            tp = unique_type_in(v, tpe)
            if tp is False:
                return False
            if tpe is None:
                tpe = tp
        return tpe
    else:
        return None if t is None else type(t) if tpe is None else tpe if isinstance(t, tpe) else False


def is_1d_tuple(t, types=None):
    if not isinstance(t, tuple):  # or types is not None and len(t) == 0:
        return False
    return all(isinstance(v, types) if types else not isinstance(v, tuple) for v in t)


def is_1d_list(t, types=None):
    if not isinstance(t, list):  # or types is not None and len(l) == 0:
        return False
    return all(isinstance(v, types) if types else not isinstance(v, list) for v in t)


def is_2d_list(m, types=None):
    return isinstance(m, list) and all(is_1d_list(t, types) for t in m)


def is_matrix(m, types=None):
    return is_2d_list(m, types) and all(len(t) == len(m[0]) for t in m)


def is_square_matrix(m, types=None):
    return is_matrix(m, types) and len(m) == len(m[0])


def is_3d_list(c, types=None):
    return isinstance(c, list) and all(is_2d_list(m, types) for m in c)


def is_cube(c, types=None):
    return is_3d_list(c, types) and all(len(m) == len(c[0]) for m in c) and all(all(len(t) == len(m[0]) for t in m) for m in c)


def alphabet_positions(s):
    """
    Returns a tuple with the indexes of the letters (with respect to the 26 letters of the Latin alphabet) of the specified string.

    @param s: a string
    """

    if isinstance(s, (list, tuple, set, frozenset, types.GeneratorType)):
        s = "".join(t for t in s)
    return tuple(ord(c) - ord('a') for c in s.lower())


def all_primes(limit):
    """
    Returns a list with all prime numbers that are strictly less than the specified limit.

    :param limit: an integer
    """
    sieve = [True] * limit
    for i in range(3, int(limit ** 0.5) + 1, 2):
        if sieve[i]:
            sieve[i * i::2 * i] = [False] * ((limit - i * i - 1) // (2 * i) + 1)
    return [2] + [i for i in range(3, limit, 2) if sieve[i]]


def value_in_base(decimal_value, length, base):
    assert type(decimal_value) is type(length) is type(base) is int
    value = [0] * length
    for i in range(len(value) - 1, -1, -1):
        value[i] = decimal_value % base
        decimal_value = decimal_value // base
    assert decimal_value == 0, "The given array is too small to contain all the digits of the conversion"
    return value


def integer_scaling(values):
    """
    Returns a list with all specified values after possibly converting them (when decimal) into integers by means of automatic scaling
    """
    values = list(values) if isinstance(values, types.GeneratorType) else values
    values = [str(v) for v in values]
    scale = 0
    for v in values:
        pos = v.find('.')
        if pos >= 0:
            i = len(v) - 1
            while v[i] == '0':
                i -= 1
            if i - pos > scale:
                scale = i - pos
    return [int(w * (10 ** scale)) for w in [Decimal(v) for v in values]]


def number_of_values_for_sum_ge(tab, limit, reverse=False):
    assert isinstance(tab, list) and all(tab[i] <= tab[i + 1] for i in range(len(tab) - 1))
    csum = 0
    if not reverse:
        for i, v in enumerate(tab):
            csum += v
            if csum >= limit:
                return i + 1
        return -1
    else:
        for i in range(len(tab) - 1, -1, -1):
            csum += tab[i]
            if csum >= limit:
                return len(tab) - i
        return -1


def decrement(t):
    if isinstance(t, int):
        return t - 1
    if isinstance(t, types.GeneratorType):
        t = list(t)
    assert isinstance(t, list)
    for i in range(len(t)):
        if isinstance(t[i], list):
            t[i] = decrement(t[i])
        elif isinstance(t[i], tuple):
            t[i] = tuple(v - 1 for v in t[i])
        else:
            assert isinstance(t[i], int)
            t[i] -= 1
    return t


def matrix_to_string(m):
    return "".join(["(" + ",".join([str(v) for v in t]) + ")" for t in m])
    # return "\n" + "\n".join(["\t(" + ",".join([str(v) for v in t]) + ")" for t in m]) + "\n"


def table_to_string(table, restricting_domains=None, *, parallel=False):
    def _tuple_to_string(t):
        return "(" + ",".join(
            str(v) if isinstance(v, int) else
            ("{" + ",".join(str(w) for w in sorted(v)) + "}") if isinstance(v, (tuple, list, set, frozenset)) else
            conditions.inside(v).str_tuple() if isinstance(v, range) else
            v if isinstance(v, str) else
            "*" if v == ANY else v.str_tuple()
            for v in t) + ")"

    LIMIT = 100000  # hard coding
    if not parallel or len(table) < LIMIT:
        s = []
        previous = ""
        for t in table:  # table is assumed to be sorted (adding an assert?) ; only distinct tuples are kept
            if t != previous:
                if restricting_domains is None or isinstance(t[0], str) \
                        or all(t[i] == ANY or t[i] in restricting_domains[i].all_values() for i in range(len(t))):
                    s.append(_tuple_to_string(t))
                previous = t

        return "".join(s)
    else:
        print("Creation of a table of size: " + str(len(table)) + (" in parallel" if parallel and len(table) >= LIMIT else ""))
        n_threads = cpu_count()
        size = len(table) // n_threads
        pool = Pool(n_threads)
        left, right = 0, size
        t = []
        for piece in range(n_threads):
            t.append(pool.apply_async(table_to_string, args=(table[left:right], restricting_domains)))  # call not in parallel
            left += size
            right = len(table) if piece in {n_threads - 2, n_threads - 1} else right + size
        assert right == len(table)
        pieces = [r.get() for r in t]
        pool.close()
        pool.join()
        # checking and removing similar tuples at the frontiers before returning the string ?
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


def structured_list(m, level=1):
    if m is None or isinstance(m, (list, tuple)) and len(m) == 0:
        return "[]"
    if not isinstance(m, (list, tuple)):
        return str(m)
    gap = "  "
    if isinstance(m[0], (list, tuple)):
        s = ("\n" + gap * level).join(structured_list(v, level + 1) for v in m)
        return "[\n" + gap * level + s + "\n" + (gap * (level - 1) + "]") + ("," if level > 1 else "")
    return "[" + ", ".join(str(v) for v in m) + "]"


def is_windows():
    return os.name == 'nt'


def _proxy_color(s):
    return "" if is_windows() else s


PURPLE, BLUE, GREEN, ORANGE, RED, WHITE, WHITE_BOLD, UNDERLINE = _proxy_color('\033[95m'), _proxy_color('\033[94m'), _proxy_color('\033[92m'), _proxy_color(
    '\033[93m'), _proxy_color('\033[91m'), _proxy_color('\033[0m'), _proxy_color('\033[1m'), _proxy_color('\033[4m')


def string_color(s, start, final=WHITE):
    return start + s + final


class Error:
    errorOccurrence = False


def warning(message):
    print("\n  " + ORANGE + "Warning: " + WHITE + message + "\n")


def warning_if(test, message):
    if test:
        warning(message)


def error(message):
    Error.errorOccurrence = True
    print("\n\t" + RED + "ERROR: " + WHITE, message)
    print("\t\t(add option -ev to your command if you want to see the trace of the error)\n")
    if options.ev:
        raise TypeError(message)
    else:
        sys.exit(1)


def error_if(test, message):
    if test:
        error(message)


polyominoes = [
    {},  # dummy entry
    {  # Monomino
        "p1": [(0, 0)]
    },
    {  # Domino
        "p2": [(0, 0), (1, 0)]
    },
    {  # Trominoes
        "Bar": [(0, 0), (1, 0), (2, 0)],
        "Right": [(0, 0), (1, 0), (1, 1)]
    },
    {  # Tetrominoes
        "Square": [(0, 0), (0, 1), (1, 0), (1, 1)],
        "T": [(0, 0), (0, 1), (0, 2), (1, 1)],
        "Skew": [(0, 0), (0, 1), (1, 1), (1, 2)],
        "L": [(0, 0), (0, 1), (0, 2), (-1, 2)],
        "Bar": [(0, 0), (0, 1), (0, 2), (0, 3)]
    },
    {  # Pentominoes
        "F": [(0, 0), (0, 1), (1, -1), (1, 0), (2, 0)],
        "I": [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],
        "L": [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],
        "N": [(0, 0), (1, -1), (1, 0), (2, -1), (3, -1)],
        "P": [(0, 0), (1, -1), (1, 0), (2, -1), (2, 0)],
        "T": [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
        "U": [(0, 0), (1, 0), (1, 1), (1, 2), (0, 2)],
        "V": [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
        "W": [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
        "X": [(0, 0), (1, -1), (1, 0), (1, 1), (2, 0)],
        "Y": [(0, 0), (1, -1), (1, 0), (2, 0), (3, 0)],
        "Z": [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)]
    },
    {  # Hexominoes
        "A": [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0)],
        "C": [(0, 0), (0, 1), (1, 0), (2, 0), (3, 0), (3, 1)],
        "D": [(0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 2)],
        "E": [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)],
        "highF": [(0, 0), (0, 1), (0, 2), (0, 3), (-1, 3), (1, 2)],
        "LowF": [(0, 0), (1, 0), (1, 1), (1, 2), (1, 3), (2, 2)],
        "G": [(0, 0), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)],
        "H": [(0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1)],
        "I": [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)],
        "J": [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)],
        "K": [(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
        "L": [(0, 0), (0, 1), (1, 0), (2, 0), (3, 0), (4, 0)],
        "M": [(0, 0), (0, 1), (0, 2), (-1, 2), (-1, 3), (1, 0)],
        "longN": [(0, 0), (0, 1), (0, 2), (0, 3), (-1, 3), (-1, 4)],
        "shortN": [(0, 0), (0, 1), (0, 2), (-1, 1), (-1, 2), (-1, 3)],
        "O": [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],
        "P": [(0, 0), (0, 1), (0, 2), (0, 3), (1, 2), (1, 3)],
        "Q": [(0, 0), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)],
        "R": [(0, 0), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)],
        "S": [(0, 0), (0, 1), (0, 2), (-1, 2), (-1, 3), (-1, 4)],
        "tallT": [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 1)],
        "shortT": [(0, 0), (0, 1), (0, 2), (0, 3), (1, 2), (2, 2)],
        "U": [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2)],
        "V": [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (3, 0)],
        "Wa": [(0, 0), (0, 1), (0, 2), (-1, 2), (-1, 3), (-2, 3)],
        "Wb": [(0, 0), (0, 1), (-1, 1), (-1, 2), (-2, 2), (-2, 3)],
        "Wc": [(0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 2)],
        "X": [(0, 0), (0, 1), (0, 2), (0, 3), (-1, 2), (1, 2)],
        "italicX": [(0, 0), (0, 1), (0, 2), (0, 3), (-1, 1), (1, 2)],
        "highY": [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 3)],
        "lowY": [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 2)],
        "tallZ": [(0, 0), (0, 1), (1, 0), (2, 0), (3, -1), (3, 0)],
        "shortZ": [(0, 0), (0, 1), (1, 0), (2, -2), (2, -1), (2, 0)],
        "high4": [(0, 0), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1)],
        "low4": [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 1)]
    }
]
