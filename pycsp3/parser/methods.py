import re
from io import StringIO
from numpy import loadtxt
from xml.etree.ElementTree import Element

from pycsp3.classes.auxiliary.conditions import Condition, ConditionVariable
from pycsp3.classes.auxiliary.enums import TypeConditionOperator, TypeVar
from pycsp3.classes.main.constraints import Parameter
from pycsp3.classes.main.variables import Variable
from pycsp3.classes.nodes import TypeNode, Node
from pycsp3.parser.constants import DELIMITER_WHITESPACE, DELIMITER_COMMA, DELIMITER_TWO_DOTS, DELIMITER_LISTS
from pycsp3.tools.utilities import ANY

# to speed up re.split(DELIM_LISTS,_) (use re_lists.split(_))
re_lists = re.compile(DELIMITER_LISTS)
re_whitespace = re.compile(DELIMITER_WHITESPACE)
re_two_dots = re.compile(DELIMITER_TWO_DOTS)

is_int = re.compile(r'^-?\d+$').match


# A class to represent several occurrences of the same value.
class Occurrences:

    def __init__(self, value, n_occurrences):
        self.value = value
        self.n_occurrences = n_occurrences

    @staticmethod
    def parse(token):
        if "x" not in token or (token[0] not in ('*', '-', '+') and not token[0].isdigit()):  # '+' seems not possible to occur
            return None
        # we have to deal with a compact forms of a sequence of similar values like 0x20 (e.g. in solutions)
        t = re.split('x', token)
        assert len(t) == 2
        return Occurrences(t[0] if t[0] == '*' else int(t[0]), int(t[1]))


def replace_intern_commas(string):
    processing = False
    s = ""
    for c in string:
        s += ' ' if (processing and c == ',') else c
        if c == '{' or c == '}':
            processing = not processing
    return s


def parse_integer_or_interval(token):
    if ".." not in token:
        return int(token)

    t = re_two_dots.split(token)
    assert len(t) == 2
    a, b = int(t[0]), int(t[1])
    assert a <= b
    return a if a == b else range(a, b + 1)


def parse_domain(s, var_type):
    assert var_type in (TypeVar.SYMBOLIC, TypeVar.INTEGER), "current restrictions"
    tokens = re.split(DELIMITER_WHITESPACE, s)
    return tokens if var_type is TypeVar.SYMBOLIC else [parse_integer_or_interval(token) for token in tokens]


def parse_indexes(size, suffix):  # size is as in XCSP3 for arrays ; suffix starts with [
    t = []
    for v in size:
        pos = suffix.index("]")
        token = suffix[suffix.index("[") + 1:pos]
        t.append(range(v) if len(token) == 0 else parse_integer_or_interval(token))
        suffix = suffix[pos + 1:]
    return t


# Parses a pair of the form (operator, operand)
def parse_condition(parser, token):
    if isinstance(token, Element):
        token = token.text.strip()
    pos = token.index(',')
    op = TypeConditionOperator.value_of(token[0 if token[0] != '(' else 1: pos].strip())
    right_term = token[pos + 1: len(token) - (1 if token[-1] == ')' else 0)].strip()
    if right_term in parser.map_for_vars:
        return ConditionVariable(op, parser.map_for_vars[right_term])
    return Condition.build_condition((op, parse_data(parser, right_term)))


def parse_conditions(parser, elt):
    return [parse_condition(parser, token) for token in re.split(DELIMITER_LISTS, elt.text.strip())[1:-1]]  # TODO is it really [1:-1] ???


def parse_expression(parser, s):
    if '(' not in s:  # i.e., if leaf
        if s in parser.map_for_vars:
            return Node(TypeNode.VAR, parser.map_for_vars[s])
        if s[0] == '%':
            return Node(TypeNode.PAR, int(s[1:]))
        assert '.' not in s, "for the moment, we don't deal with decimal values"
        if s[0] in ('-', '+') or s[0].isdigit():
            return Node(TypeNode.INT, int(s))
        return Node(TypeNode.SYMBOL, s)
    else:
        left, right = s.find('('), s.rfind(')')
        operator = TypeNode[s[:left].upper()]
        if left == right - 1:  # actually, this is also a leaf which is set(), the empty set
            assert operator == TypeNode.SET
            return Node(TypeNode.SET, [])
        content = s[left + 1: right]
        nodes = []
        right = 0
        while right < len(content):
            left = right
            n_opens = 0
            while right < len(content):
                if content[right] == '(':
                    n_opens += 1
                elif content[right] == ')':
                    n_opens -= 1
                elif content[right] == ',' and n_opens == 0:
                    break
                right += 1
            nodes.append(parse_expression(parser, content[left:right].strip()))
            right += 1
        return Node(operator, nodes)


def parse_data(parser, token):
    if isinstance(token, Element):
        token = token.text.strip()
    assert isinstance(token, str), "Pb with " + str(token)
    if token in parser.map_for_vars:
        return parser.map_for_vars[token]
    occurrences = Occurrences.parse(token)
    if occurrences is not None:
        return occurrences
    if token[0] in ('-', '+') or token[0].isdigit():
        # other cases not in XCSP-core should be ultimately handled: rational and decimal (see Java parser)
        return parse_integer_or_interval(token)
    if token[0] == '{':  # set value
        return [int(v.strip()) for v in re.split(DELIMITER_COMMA, token[1:-1])]
    if token[0] == '(':  # condition
        return parse_condition(parser, token)
    if token[0] == '%':
        return Parameter(-1 if token == "%..." else int(token[1:]))
    if '(' in token:
        return parse_expression(parser, token)
    return token  # token must be a symbolic value( or *)


def parse_sequence(parser, seq, delimiter=DELIMITER_WHITESPACE):
    if isinstance(seq, Element):
        seq = seq.text.strip()

    if delimiter == DELIMITER_WHITESPACE:
        splitter = re_whitespace.split
    else:
        splitter = re.compile(delimiter).split

    t = []
    for token in splitter(seq):
        # Fast path for simple integers
        if is_int(token):
            t.append(int(token))
        elif token.startswith("not("):
            t.append(parse_expression(parser, token))
        else:
            pos = token.find("[")
            if pos != -1 and token[:pos] in parser.map_for_arrays:
                t.extend(parser.map_for_arrays[token[:pos]].vars_for(token))
            else:
                occurrences = Occurrences.parse(token)
                if occurrences is not None:
                    for i in range(occurrences.n_occurrences):
                        t.append(occurrences.value)
                else:
                    t.append(parse_data(parser, token))
    present_variable, present_tree = False, False
    for obj in t:
        if isinstance(obj, Variable):
            present_variable = True
        elif isinstance(obj, Node):
            present_tree = True
        else:
            return t  # other kind of element, so we return t directly
    if present_variable and present_tree:
        return [Node(TypeNode.VAR, obj) if isinstance(obj, Variable) else obj for obj in t]
    return t


# Parse a double sequence, i.e. a sequence of tokens separated by the specified delimiter, and composed of entities separated by ','
def parse_double_sequence(parser, elt, delimiter=DELIMITER_LISTS):
    content = elt.text.strip()
    return [parse_sequence(parser, token, DELIMITER_COMMA) for token in re.split(delimiter, content)[1:-1]]  # TODO is it really [1:-1] ???


# Parse a double sequence of variables. Either the double sequence only contains simple variables, or is represented by a compact form
def parse_double_sequence_of_vars(parser, elt):
    content = elt.text.strip()
    assert content[0] != '%', "It is currently not possible to make abstraction of double sequences of variables"
    if content[0] == '(':
        return [parse_sequence(parser, tok, DELIMITER_COMMA) for tok in re.split(DELIMITER_LISTS, content)[1:-1]]  # TODO is it really [1:-1] ???
    pos = content.index("[")
    prefix, suffix = content[:pos], content[pos:]
    array = parser.map_for_arrays[prefix]
    index_expressions = parse_indexes(array.size, suffix)  # we get either int or range values
    indexes = [index if isinstance(index, int) else index.start for index in index_expressions]  # first index
    first, second = -1, -1
    for i in range(len(index_expressions)):
        if isinstance(index_expressions[i], range):
            first = i
            break
    for i in range(len(index_expressions) - 1, -1, -1):
        if isinstance(index_expressions[i], range):
            second = i
            break
    length1, length2 = len(index_expressions[first]), len(index_expressions[second])
    m = []
    for i in range(length1):
        t = []
        indexes[first] = i + index_expressions[first].start
        for j in range(length2):
            indexes[second] = j + index_expressions[second].start
            t.append(array.var_at(indexes))
        m.append(t)
    return m


def parse_ordinary_tuple(s, domains=None):  # actually ordinary/starred tuples
    t = s.split(',')  # re.split(DELIMITER_COMMA, s)
    starred = False
    for i in range(len(t)):
        if t[i] == "*":
            t[i] = ANY
            starred = True
        else:
            value = int(t[i])
            if domains is None or value in domains[i]:
                t[i] = value
            else:
                return None, starred  # None because the tuple can be discarded
    return t, starred


def parse_symbolic_tuple(s, domains=None):
    t = s.split(',')  # re.split(DELIMITER_COMMA, s)
    starred = False
    for i in range(len(t)):
        if t[i] == "*":
            starred = True
        elif domains is not None and t[i] not in domains[i]:
            return None, starred
    return t, starred


def parse_tuples(elt, symbolic, domains=None):
    s = elt.text.strip()
    if len(s) == 0:
        return None, False, False
    if s[0] != '(':  # if unary (when left parenthesis not present as first character)
        tokens = re.split(DELIMITER_WHITESPACE, s)
        assert all(tok != "*" for tok in tokens)  # ANY not handled in unary lists
        # should we indicate how many values/tokens are discarded?
        if symbolic:
            return [tok for tok in tokens if domains is None or tok in domains[0]], False, domains is not None
        else:
            if ".." in s:  # in case we have at least one interval, no validity test on values is performed.
                return [parse_integer_or_interval(tok) for tok in tokens], False, False
            return [value for tok in tokens if (value := int(tok),) and (domains is None or value in domains[0])], False, domains is not None
    starred = ("*" in s)
    if True:  # symbolic or (domains is not None) or starred:
        # original code, some tweaks
        func = parse_symbolic_tuple if symbolic else parse_ordinary_tuple  # reference to function
        tokens = re_lists.split(s[1:-1])  # cut first and last '(', ')'
        m = []
        for tok in tokens:
            t, tok_is_star = func(tok, domains)
            if t is not None:  # if not filtered-out parsed tuple
                m.append(t)
    # else: DISABLED till tested more thoroughly (e.g. instancesXCSP22/MiniCOP/Fapp-ext-01-0200_c18.xml)
    #    # optimized code for non-symbolic, non-star, non-domains case with NumPy
    #    csv_string = s[1:-1].replace(')(','\n')  # convert to CSV
    #    array = loadtxt(StringIO(csv_string), delimiter=',', dtype=int)
    #    m = array.tolist()  # this part is the most time consuming

    return m, starred, domains is not None
