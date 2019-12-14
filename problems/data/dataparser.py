import re

from pycsp3.dashboard import options
from pycsp3.tools.curser import ListInt
from pycsp3.tools.utilities import is_containing

data = None
_data_file = None
_dataParser = None


class DataDict(dict):
    def __init__(self, element=None):
        if element:
            DataDict._transfer_to(element, self)
            DataDict._browse(self)
    
    @staticmethod
    def __secured_getattribute__(self, name):
        try:
            result = super().__getattribute__(name)
        except AttributeError as e:
            if isinstance(name, str) and not name.endswith("__") and not name.startswith("__"):
                print()
                if options.data:
                    print("We need a value for a data (piece) called " + name + " .Please check the option -data.")
                elif isinstance(options.data,str) and len(options.data.strip()) == 0:
                    print("You have to set a value for the data (piece) called " + name + " .Please check the option -data.")
                else:
                    print("You need to use the option -data since we need a value for " + name)
                print()
            raise e
        return result

    @staticmethod
    def secured_getattribute():
        DataDict.__getattribute__ = DataDict.__secured_getattribute__

    @staticmethod
    def _transfer_to(element, obj):
        assert isinstance(obj, DataDict)
        for k, v in element.items():
            obj[k] = v
            if isinstance(v, (list, tuple)):
                if is_containing(v, int):
                    setattr(obj, k, ListInt([DataDict(x) if isinstance(x, dict) else x for x in v]))
                else:
                    setattr(obj, k, [DataDict(x) if isinstance(x, dict) else x for x in v])
            else:
                setattr(obj, k, DataDict(v) if isinstance(v, dict) else v)

    @staticmethod
    def _browse(element, parent=None, parent_index=None):
        if hasattr(element, "__dict__"):
            for key, value in element.__dict__.items():
                if isinstance(value, (list, tuple)):
                    if is_containing(value, int):
                        element.__dict__[key] = ListInt(value)
                    for v in value:
                        DataDict._browse(v, value)
        else:
            if isinstance(element, (list, tuple)):
                for i, v in enumerate(element):
                    DataDict._browse(v, element, i)
            elif isinstance(element, dict) and parent_index is not None:
                parent[parent_index] = DataDict(element)

    # for k,v in element.__dict__.items() if hasattr(element, "__dict__") else element.items():  #element.items():

    @staticmethod
    def _make_clean(obj):
        assert isinstance(obj, DataDict)
        DataDict._transfer_to(obj, obj)
        DataDict._browse(obj)
        return obj


def register_fields(data_file):
    global data, _data_file, _dataParser
    data = DataDict()
    _data_file = data_file
    _dataParser = DataParser(data_file)
    return data


def make_clean(obj):
    return DataDict._make_clean(obj)


class DataParser:
    def __init__(self, data_file):
        if data_file:
            with open(data_file) as f:
                self.lines = [line[:-1].strip() if line[-1] == '\n' else line.strip() for line in f.readlines() if len(line.strip()) > 0]
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


def next_int():
    return _dataParser.next(to_int=True)


def next_str():
    return _dataParser.next(to_int=False)


def remaining_lines(skip_curr=False):
    if skip_curr:
        next_line()
    return _dataParser.lines[_dataParser.curr_line_index:]


def number_in(line):
    assert line is not None
    return int(re.search(r'[-]?\d+', line).group(0))


def numbers_in(line):
    assert line is not None
    return [int(v) for v in re.findall(r'[-]?\d+', line)]  # [int(v) for v in line().split() if v.isdigit()]


def ask_number(message):
    parameter = options.consume_parameter()
    return int(parameter) if parameter else int(input(message + " "))


def ask_string(message):
    parameter = options.consume_parameter()
    return parameter if parameter else input(message + " ")



    # def setDzn():
    #     global _dataParser
    #     _dataParser = DataParserDzn(_data_file)
    #
    #
    # class DataParserDzn(DataParser):
    #     def __init__(self, data_file):
    #         super().__init__(data_file)
    #
    #     def formLine(self):
    #         s = ""
    #         line = self.curr_line()
    #         while not line[-1] == ';':
    #             if not line[0] == '%' and len(line) > 0:
    #                 s += line
    #             if self.curr_line_index + 1 >= len(self.lines):
    #                 return s
    #             line = self.next_line()
    #         self.next_line()
    #         return s + line
    #
    #     def next(self, to_int=True):
    #         line = self.formLine()
    #         return int(line[line.index("=") + 1: line.index(";")])
    #
    #     def _ints(self, s):
    #         return [int(v) for v in re.split(r'\s*,\s*', s) if len(v) > 0]
    #
    #     def nextInt1D(self):
    #         s = self.formLine()
    #         print("ss", s)
    #         return self._ints(s[s.index('[') + 1:s.rindex(']')])
    #
    #     def nextInt2D(self):
    #         line = self.curr_line()
    #         t = []
    #         t.append(self._ints(line[line.index("[") + 1:]))
    #         while line[-1] != ";":
    #             line = self.next_line()
    #             t.append(self._ints(line if line[-1] != ";" else line[:line.index("]")]))
    #
    #         print("T", t)
    #         return t
    #         # list.add(s.endsWith(";") ? s.substring(0, s.lastIndexOf("]")): s);
    #
    #         # return list.stream().filter(l -> l.length() > 0).map(l -> Stream.of(l.split("\\s*,\\s*")).mapToInt(tok -> Integer.parseInt(tok.trim())).toArray())    .toArray(int[][]::new);


    # def nextInt1D():
    #     return _dataParser.nextInt1D()
    #
    #
    # def nextInt2D():
    #     return _dataParser.nextInt2D()
