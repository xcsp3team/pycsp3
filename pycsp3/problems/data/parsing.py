import os.path
import re
from collections import OrderedDict

from pycsp3.dashboard import options
from pycsp3.tools.utilities import decrement, error_if

data = None
_dataParser = None


def register_fields(data_value):
    """
    Prepares the reading of the specified data, and returns the dictionary in which the fields of data must be recorded.
    This function is called automatically, with the value of the option -data, before a data parser (option -parser) is executed;
    so, it is only useful when reading data outside the command line (e.g., in a notebook).
    When reading files, empty lines are discarded and all lines are stripped.

    :param data_value: a filename, a URL, a directory (all its files being read, in the order of their names),
                       or a list of such values given between brackets, as in "[f1.txt,f2.txt]"
                       (a value that is neither a file nor a URL is then read as a line)
    :return: the (empty) dictionary to be filled with the fields of data
    :example:
        from pycsp3.problems.data.parsing import *

        # with -data=queens.txt -parser=Queens_Parser.py, register_fields("queens.txt") is called before running the parser
        with open("queens.txt", "w") as f:
            f.write("n = 8;\\n")
        data = register_fields("queens.txt")

        # the fields recorded in data become those of the named tuple given to the model
        data["n"] = number_in(line())
        print(data["n"])  # 8
    """
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
    """
    Returns the current line of the data being parsed, without moving to the next one.
    When a data parser starts, the current line is the first one.

    :return: the current line, or None (after displaying a warning) if all lines have been read
    :example:
        from pycsp3.problems.data.parsing import *

        with open("bacp.txt", "w") as f:
            f.write("n_courses = 9;\\nn_periods = 4;\\n")
        data = register_fields("bacp.txt")

        # the first line is the current one, until next_line() is called
        data["nCourses"] = number_in(line())  # 9
        data["nPeriods"] = number_in(next_line())  # 4
    """
    return _dataParser.curr_line()


def next_line(repeat=0):
    """
    Moves to the next line of the data being parsed, and returns it.
    Some lines can be skipped before, by means of the parameter repeat.

    :param repeat: the number of lines to be skipped before moving to the next line (0 by default)
    :return: the new current line, or None (after displaying a warning) if all lines have been read
    :example:
        from pycsp3.problems.data.parsing import *

        with open("bacp.txt", "w") as f:
            f.write('include "curriculum.mzn.model";\\nn_courses = 9;\\nn_periods = 4;\\nload_per_period_lb = 2;\\n')
        data = register_fields("bacp.txt")

        # the first line is the current one: next_line() gives the second one
        data["nCourses"] = number_in(next_line())  # 9

        # with repeat=1, one line (n_periods = 4;) is skipped before
        data["minCredits"] = number_in(next_line(repeat=1))  # 2
    """
    for _ in range(repeat + 1):
        ln = _dataParser.next_line()
    return ln


def skip_empty_lines(or_prefixed_by=None):
    """
    Moves forward while the current line is empty or, when a prefix is specified, starts with this prefix.
    This is typically used to skip lines of comments.

    :param or_prefixed_by: the prefix of the lines to be skipped (e.g., "%" or "#"), or None (by default)
    :example:
        from pycsp3.problems.data.parsing import *

        with open("data.dzn", "w") as f:
            f.write("% an instance of the problem\\n% generated randomly\\nn = 5;\\n")
        data = register_fields("data.dzn")

        # the two lines of comments are skipped
        skip_empty_lines(or_prefixed_by="%")
        data["n"] = number_in(line())  # 5
    """
    while line() is not None and (len(line().strip()) == 0 or or_prefixed_by and line().startswith(or_prefixed_by)):
        next_line()


def next_int():
    """
    Returns the next integer of the data being parsed, tokens being separated by white spaces.
    Tokens are read one after the other from the current line, and the next line becomes the current one once all tokens have been read.

    :return: the next token, converted into an integer
    :example:
        from pycsp3.problems.data.parsing import *

        # a nonogram: its numbers of rows and columns, and then each pattern given by its number of blocks followed by their sizes
        with open("nonogram.txt", "w") as f:
            f.write("2 3\\n1 2\\n2 1 1\\n1 1\\n1 2\\n1 1\\n")
        data = register_fields("nonogram.txt")

        nRows, nCols = next_int(), next_int()
        data["rows"] = [[next_int() for _ in range(next_int())] for _ in range(nRows)]  # [[2], [1, 1]]
    """
    # skip_empty_lines()
    return _dataParser.next(to_int=True)


def next_str():
    """
    Returns the next token of the data being parsed, as a string, tokens being separated by white spaces.
    Tokens are read one after the other from the current line, and the next line becomes the current one once all tokens have been read.

    :return: the next token
    :example:
        from pycsp3.problems.data.parsing import *

        with open("items.txt", "w") as f:
            f.write("apple 3 banana 5\\nend\\n")
        data = register_fields("items.txt")

        # next_str() and next_int() can be mixed: each one reads the next token
        data["items"] = [(next_str(), next_int()) for _ in range(2)]  # [('apple', 3), ('banana', 5)]
    """
    return _dataParser.next(to_int=False)


def remaining_lines(skip_curr=False):
    """
    Returns the lines that remain to be read, starting from the current line (or from the next one if skip_curr is True).
    Apart from the line possibly skipped, the current line is unchanged.

    :param skip_curr: True if the current line must be skipped
    :return: the list of remaining lines
    :example:
        from pycsp3.problems.data.parsing import *

        with open("bacp.txt", "w") as f:
            f.write("n_courses = 9;\\nconstraint prerequisite(2, 0);\\nconstraint prerequisite(4, 1);\\n")
        data = register_fields("bacp.txt")

        data["nCourses"] = number_in(line())  # 9
        # each line after the current one gives a prerequisite
        data["prerequisites"] = [numbers_in(ln) for ln in remaining_lines(skip_curr=True)]  # [[2, 0], [4, 1]]
    """
    if skip_curr:
        next_line()
    return _dataParser.lines[_dataParser.curr_line_index:]


def next_lines(skip_curr=False, *, prefix_stop):
    """
    Returns the lines from the current one (or from the next one if skip_curr is True), up to the first line starting with the specified prefix.
    This last line is not returned, and becomes the current one; it must exist.

    :param skip_curr: True if the current line must be skipped
    :param prefix_stop: the prefix of the line where the reading stops
    :return: the list of lines read
    :example:
        from pycsp3.problems.data.parsing import *

        with open("graph.txt", "w") as f:
            f.write("edges\\n0 1\\n1 2\\nend\\n")
        data = register_fields("graph.txt")

        # the lines after 'edges', up to the line starting with 'end' (excluded)
        data["edges"] = [numbers_in(ln) for ln in next_lines(skip_curr=True, prefix_stop="end")]  # [[0, 1], [1, 2]]
    """
    if skip_curr:
        next_line()
    left = _dataParser.curr_line_index
    right = next((j for j in range(left, len(_dataParser.lines)) if _dataParser.lines[j].startswith(prefix_stop)), -1)
    _dataParser.curr_line_index = right
    _dataParser.curr_line_tokens = None
    return _dataParser.lines[left:right]


def number_in(ln, offset=0):
    """
    Returns the first integer (possibly negative) present in the specified string, after adding the specified offset.
    An offset of -1 is typically used to convert a number starting from 1 into a number starting from 0.

    :param ln: a string, typically a line of the data being parsed
    :param offset: the value to be added to the integer (0 by default)
    :return: the first integer present in the string, plus the offset
    :example:
        from pycsp3.problems.data.parsing import *

        print(number_in("n_courses = 9;"))  # 9
        print(number_in("first_course = 1;", offset=-1))  # 0
    """
    assert ln is not None
    return int(re.search(r'[-]?\d+', ln).group(0)) + offset


def numbers_in(ln, offset=0):
    """
    Returns all integers (possibly negative) present in the specified string, after adding the specified offset to each of them.
    An offset of -1 is typically used to convert numbers starting from 1 into numbers starting from 0.

    :param ln: a string, typically a line of the data being parsed
    :param offset: the value to be added to each integer (0 by default)
    :return: the list of integers present in the string, plus the offset
    :example:
        from pycsp3.problems.data.parsing import *

        print(numbers_in("course_load = [2, 3, 1, 3];"))  # [2, 3, 1, 3]
        print(numbers_in("constraint prerequisite(2, 1);", offset=-1))  # [1, 0]
    """
    assert ln is not None
    return [int(v) + offset for v in re.findall(r'[-]?\d+', ln)]  # [int(v) for v in ln().split() if v.isdigit()]


def numbers_in_lines_until(stop):
    """
    Returns all integers present in the lines following the current one, up to the first line ending with the specified string (included).
    The current line is not considered, and this last line becomes the current one.
    This is typically used to read an array written over several lines.

    :param stop: the string ending the last line to be read (e.g., ";")
    :return: the list of integers present in the lines read
    :example:
        from pycsp3.problems.data.parsing import *

        with open("data.dzn", "w") as f:
            f.write("costs = [\\n4, 2, 7,\\n3, 5];\\nn = 5;\\n")
        data = register_fields("data.dzn")

        # the integers of the lines after 'costs = [', up to the line ending with ';'
        data["costs"] = numbers_in_lines_until(";")  # [4, 2, 7, 3, 5]
    """
    s = ""
    while not next_line().endswith(stop):
        s += line()
    return numbers_in(s + line())


def split_with_structure(t, *k):
    """
    Returns a multi-dimensional list built from the specified flat list, the sizes of its first dimensions being specified.
    The size of the last dimension is deduced from the length of the list.

    :param t: a flat list
    :param k: the sizes of the first dimensions
    :return: a multi-dimensional list with the elements of t
    :example:
        from pycsp3.problems.data.parsing import *

        # 2 lists, each one composed of 3 lists whose size (2) is deduced
        print(split_with_structure(list(range(12)), 2, 3))  # [[[0, 1], [2, 3], [4, 5]], [[6, 7], [8, 9], [10, 11]]]
    """
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
    """
    Returns a two-dimensional list (matrix) built from the specified flat list, each row being of the specified size.

    :param t: a flat list, whose length is a multiple of k1
    :param k1: the size of each row
    :return: a two-dimensional list with the elements of t
    :example:
        from pycsp3.problems.data.parsing import *

        print(split_with_rows_of_size([1, 2, 3, 4, 5, 6], 3))  # [[1, 2, 3], [4, 5, 6]]
    """
    assert isinstance(t, list) and len(t) % k1 == 0, str(type(list)) + " " + str(len(t)) + " " + str(k1)
    if len(t) == 0:
        return t
    return split_with_structure(t, len(t) // k1)


def ask_number(message):
    """
    Returns the next integer given as parameter on the command line or, if there is none, asks the user for it.
    Parameters are the arguments of the command line that are not options (i.e., not starting with '-').
    This is typically used by random instance generators.

    :param message: the message displayed when asking the user
    :return: an integer given on the command line or by the user
    :example:
        from pycsp3.problems.data.parsing import *

        # with python Warehouse.py -parser=Warehouse_Random.py 10 3, the first call gives 10 and the second one gives 3
        data["nWarehouses"] = ask_number("Number of warehouses?")
        data["seed"] = ask_number("Seed?")
    """
    parameter = options.consume_parameter()
    return int(parameter) if parameter else int(input(message + " "))


def ask_string(message):
    """
    Returns the next string given as parameter on the command line or, if there is none, asks the user for it.
    Parameters are the arguments of the command line that are not options (i.e., not starting with '-').

    :param message: the message displayed when asking the user
    :return: a string given on the command line or by the user
    :example:
        from pycsp3.problems.data.parsing import *

        # with python Model.py -parser=Model_Random.py small, this gives 'small'
        data["size"] = ask_string("Size (small or large)?")
    """
    parameter = options.consume_parameter()
    return parameter if parameter else input(message + " ")


def _pycharm_security():  # for avoiding that imports are removed when reformatting code
    _ = (decrement,)
