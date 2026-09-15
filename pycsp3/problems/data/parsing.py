import os.path
import re
from collections import OrderedDict

from pycsp3.dashboard import options
from pycsp3.tools.utilities import decrement, error, error_if

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
        if len(values) == 1 and os.path.isdir(values[0]):  # in case of a directory, consider all files in the directory
            # this is very specific as we concat contents of files (in the order of their names)
            values = [os.path.join(values[0], f) for f in sorted(os.listdir(values[0])) if os.path.isfile(os.path.join(values[0], f))]
        error_if(len(values) == 1 and not values[0].startswith("http") and not os.path.isfile(values[0]),
                 " It seems that the filename " + values[0] + " is not found")
        self.lines = []
        for value in values:
            if value.startswith("http"):
                from urllib.request import urlopen
                # example: python Nonogram.py -data=https://www.cril.univ-artois.fr/~lecoutre/heart.txt -dataparser=Nonogram_Parser.py
                for ln in urlopen(value):
                    self.lines += [ln.decode("utf-8").strip()]
            elif os.path.isfile(value):
                with open(value) as f:
                    self.lines += [ln[:-1].strip() if ln[-1] == '\n' else ln.strip() for ln in f.readlines() if len(ln.strip()) > 0]
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

    def _skip_empty_lines(self):  # silently, contrary to curr_line() and next_line(), which display a warning beyond the last line
        while self.curr_line_index < len(self.lines) and len(self.lines[self.curr_line_index].split()) == 0:
            self.curr_line_index += 1

    def next(self, to_int=True):
        if self.curr_line_tokens is None:
            self._skip_empty_lines()
            error_if(self.curr_line_index >= len(self.lines), "No more token to read with next_int() or next_str(): all the lines of the data have been read")
            self.curr_line_tokens = self.lines[self.curr_line_index].split()
            self.curr_line_tokens_index = 0
        res = int(self.curr_line_tokens[self.curr_line_tokens_index]) if to_int else self.curr_line_tokens[self.curr_line_tokens_index]
        self.curr_line_tokens_index += 1
        if self.curr_line_tokens_index >= len(self.curr_line_tokens):  # moving to the next non-empty line, without warning when there is none
            self.curr_line_index += 1
            self.curr_line_tokens = None
            self._skip_empty_lines()
        return res


def line():
    return _dataParser.curr_line()


def next_line(repeat=0):
    for _ in range(repeat + 1):
        ln = _dataParser.next_line()
    return ln


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
    if skip_curr:  # silently, the error below being reported if there is no more line
        _dataParser.curr_line_index += 1
    left = _dataParser.curr_line_index
    right = next((j for j in range(left, len(_dataParser.lines)) if _dataParser.lines[j].startswith(prefix_stop)), None)
    error_if(right is None, "next_lines(): no line starts with " + repr(prefix_stop))
    _dataParser.curr_line_index = right
    _dataParser.curr_line_tokens = None
    return _dataParser.lines[left:right]


def number_in(ln, offset=0):
    if not isinstance(ln, str):
        error("number_in() expects a line (a string), not " + repr(ln))
    match = re.search(r'[-]?\d+', ln)
    if match is None:
        error("number_in(): no integer in the line " + repr(ln))
    return int(match.group(0)) + offset


def numbers_in(ln, offset=0):
    if not isinstance(ln, str):
        error("numbers_in() expects a line (a string), not " + repr(ln))
    return [int(v) + offset for v in re.findall(r'[-]?\d+', ln)]  # [int(v) for v in ln().split() if v.isdigit()]


def numbers_in_lines_until(stop):
    lines = []
    while True:
        error_if(_dataParser.curr_line_index + 1 >= len(_dataParser.lines), "numbers_in_lines_until(): no line ends with " + repr(stop))
        ln = next_line()
        if ln.endswith(stop):  # the lines are joined with a space, so that the numbers at the end of a line and the start of the next one are not merged
            return numbers_in(" ".join(lines + [ln]))
        lines.append(ln)


def _is_strictly_positive_integer(v):
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def split_with_structure(t, *k):
    if not isinstance(t, list):
        error("split_with_structure() expects a list, not a " + type(t).__name__)
    if not all(_is_strictly_positive_integer(v) for v in k):
        error("split_with_structure(): the sizes must be strictly positive integers, which is not the case of " + str(k))
    if len(k) == 0:
        return t
    product = 1
    for v in k:
        product *= v
    if len(t) % product != 0:  # checked once for all the sizes, instead of for the intermediate lists of the recursive calls
        error("split_with_structure(): the length of the list (" + str(len(t)) + ") must be a multiple of "
              + (str(product) if len(k) == 1 else " × ".join(str(v) for v in k) + " = " + str(product)))
    width = len(t) // k[0]
    m = [[t[i * width + j] for j in range(width)] for i in range(k[0])]
    if len(k) > 1:
        for i in range(len(m)):
            m[i] = split_with_structure(m[i], *tuple(k[1:]))
    return m


def split_with_rows_of_size(t, k1):
    if not isinstance(t, list):
        error("split_with_rows_of_size() expects a list, not a " + type(t).__name__)
    if not _is_strictly_positive_integer(k1):
        error("split_with_rows_of_size(): the size of the rows must be a strictly positive integer, not " + repr(k1))
    if len(t) % k1 != 0:
        error("split_with_rows_of_size(): the length of the list (" + str(len(t)) + ") must be a multiple of the size of the rows (" + str(k1) + ")")
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
    _ = (decrement,)
