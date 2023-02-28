import os.path
import re
from collections import OrderedDict

from pycsp3.dashboard import options
from pycsp3.tools.utilities import decrement, error_if

data = None
_dataParser = None


def register_fields(data_value):
    global data, _dataParser
    data = OrderedDict()
    _dataParser = DataParser(data_value)
    return data


class DataParser:
    def __init__(self, data_value):
        if data_value is None:
            return  # if everything is loaded directly in the dataparser (although not recommended)
        if data_value[0] == '[':
            assert data_value[-1] == ']'
            values = data_value[1:-1].split(',')
        else:
            values = [data_value]
        error_if(len(values) == 1 and not values[0].startswith("http") and not os.path.isfile(values[0]),
                 " It seems that the filename " + values[0] + " is not found")
        self.lines = []
        for value in values:
            if value.startswith("http"):
                from urllib.request import urlopen
                # example: python Nonogram.py -data=https://www.cril.univ-artois.fr/~lecoutre/heart.txt -dataparser=Nonogram_Parser.py
                for l in urlopen(value):
                    self.lines += [l.decode("utf-8").strip()]
            elif os.path.isfile(value):
                with open(value) as f:
                    self.lines += [line[:-1].strip() if line[-1] == '\n' else line.strip() for line in f.readlines() if len(line.strip()) > 0]
            else:
                self.lines += [str(value)]
        self.curr_line_index = 0
        self.curr_line_tokens = None

    def curr_line(self):
        if self.curr_line_index >= len(self.lines):
            print("Warning: no more line")
            return None
        return self.lines[self.curr_line_index]

    def next_line(self):
        self.curr_line_index += 1
        self.curr_line_tokens = None
        return self.curr_line()

    def next(self, to_int=True):
        if self.curr_line_tokens is None:
            if self.curr_line() is not None:
                self.curr_line_tokens = self.curr_line().split()
                self.curr_line_tokens_index = 0
        res = int(self.curr_line_tokens[self.curr_line_tokens_index]) if to_int else self.curr_line_tokens[self.curr_line_tokens_index]
        self.curr_line_tokens_index += 1
        if self.curr_line_tokens_index >= len(self.curr_line_tokens):
            next_line()
            while self.curr_line() is not None and len(self.curr_line().strip()) == 0:
                self.next_line()
        return res


def line():
    return _dataParser.curr_line()


def next_line(repeat=0):
    for _ in range(repeat + 1):
        l = _dataParser.next_line()
    return l


def skip_empty_lines(or_prefixed_by=None):
    while line() is not None and (len(line().strip()) == 0 or or_prefixed_by and line().startswith(or_prefixed_by)):
        next_line()


def next_int():
    # skip_empty_lines()
    return _dataParser.next(to_int=True)


def next_str():
    return _dataParser.next(to_int=False)


def remaining_lines(skip_curr=False):
    if skip_curr:
        next_line()
    return _dataParser.lines[_dataParser.curr_line_index:]


def next_lines(skip_curr=False, *, prefix_stop):
    if skip_curr:
        next_line()
    left = _dataParser.curr_line_index
    right = next((j for j in range(left, len(_dataParser.lines)) if _dataParser.lines[j].startswith(prefix_stop)), -1)
    _dataParser.curr_line_index = right
    _dataParser.curr_line_tokens = None
    return _dataParser.lines[left:right]


def number_in(line, offset=0):
    assert line is not None
    return int(re.search(r'[-]?\d+', line).group(0)) + offset


def numbers_in(line, offset=0):
    assert line is not None
    return [int(v) + offset for v in re.findall(r'[-]?\d+', line)]  # [int(v) for v in line().split() if v.isdigit()]


def numbers_in_lines_until(stop):
    s = ""
    while not next_line().endswith(stop):
        s += line()
    return numbers_in(s + line())


def split_with_structure(t, *k):
    assert isinstance(t, list) and all(isinstance(v, int) for v in k) and len(t) % k[0] == 0
    if len(k) == 0:
        return t
    width = len(t) // k[0]
    m = [[t[i * width + j] for j in range(width)] for i in range(k[0])]
    if len(k) > 1:
        for i in range(len(m)):
            m[i] = split_with_structure(m[i], *tuple(k[1:]))
    return m


def split_with_rows_of_size(t, k1):
    assert isinstance(t, list) and len(t) % k1 == 0, str(type(list)) + " " + str(len(t)) + " " + str(k1)
    if len(t) == 0:
        return t
    return split_with_structure(t, len(t) // k1)


def ask_number(message):
    parameter = options.consume_parameter()
    return int(parameter) if parameter else int(input(message + " "))


def ask_string(message):
    parameter = options.consume_parameter()
    return parameter if parameter else input(message + " ")


def _pycharm_security():  # for avoiding that imports are removed when reformatting code
    _ = (decrement)
