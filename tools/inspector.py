import inspect
import sys

from pycsp3.dashboard import options
from pycsp3.tools.utilities import flatten, is_windows

if not is_windows():
    try:
        import readline
    except ImportError:
        if "Intel" in sys.version:
            s = 'With Intel compilers, the module readline must be installed by the user.'
        else:
            s = 'Problem when importing the module readline'
        raise ImportError(s)

fileToTrace = [arg for arg in sys.argv if arg.endswith(".py") and "compiler.py" not in arg] + ["<stdin>"]


def _global_value_of(variable):
    stack = list(reversed(inspect.stack(context=1)))
    frames = [frame for frame in stack for trace in fileToTrace if trace in frame.filename]
    # frames = [frame for frame in stack if frame.filename in fileToTrace]
    if len(frames) == 0:
        return None
    globs = frames[0].frame.f_globals
    return str(globs[variable]) if variable in globs.keys() else None


def is_comment_line(line):
    if not isinstance(line, str):
        return False
    line = line.strip()
    return len(line) > 2 and line[0] == '#' and line.replace(" ", "")[1] != '!'


def is_empty_line(line):
    return isinstance(line, str) and len(line.strip()) == 0


def is_continued_line(line):
    return isinstance(line, str) and line.strip().endswith('\\')


# Starts at the end of the function and runs it up until the function name is found
def browse_code_bottom_to_top(lines, function_name):
    code = []
    function_name_found = False
    for line in lines:
        if function_name_found is False:
            code.append(line)
            if function_name in line and not is_comment_line(line):
                function_name_found = True
        else:
            if is_continued_line(line) or is_empty_line(line) or is_comment_line(line):
                code.append(line)
            else:
                break
    return code


def browse_code_top_to_bottom(lines, function_name):
    code = []
    function_name_found = False
    level = 0
    for line in lines:
        if function_name in line and not is_comment_line(line):
            function_name_found = True
            code.append(line)
            line = line.split(function_name)[1]
        else:
            code.append(line)
        if function_name_found:
            for letter in line:
                if letter in {'(', '['}:
                    level = level + 1
                if letter in {')', ']'}:
                    level = level - 1
        if level == 0:
            break
    return list(reversed(code))


def _extract_correct_frame(function_name):
    for i, frame_info in enumerate(reversed(inspect.stack(context=1))):
        if i > 0 and (frame_info.function == function_name or frame_info.function == "__init__" and function_name in frame_info.code_context[0]):
            return i - 1, previous  # Get the correct frame
        previous = frame_info
    return None


def _extract_code(function_name):
    index, frame_info = _extract_correct_frame(function_name)  # getting the good frame

    if frame_info.filename == "<stdin>":  # Console case
        if is_windows():
            assert False, "Console mode is not available on Windows"
        lines = reversed(list(readline.get_history_item(i + 1) for i in range(readline.get_current_history_length())))
        return browse_code_bottom_to_top(lines, function_name)

    # The index of the line in the stack of the inspector changes between python 3.7 and 3.8:
    # In 3.8 the index is the line where the function name appears
    # In 3.7 and lower versions, it is the line at the end of the function
    # So the algorithms are completely different
    frame_info = list(reversed(inspect.stack(context=2000)))[index]  # TODO how to avoid this constant?
    if sys.version_info[1] >= 8 and function_name != "Var" and function_name != "VarArray":  # why special cases for Var and VarArray?
        lines = list(frame_info.code_context[frame_info.index:])
        return browse_code_top_to_bottom(lines, function_name)
    else:
        lines = reversed(frame_info.code_context[:frame_info.index + 1])
        return browse_code_bottom_to_top(lines, function_name)


# returns a pair (left,right) of positions of the first occurrence of the specified separators in the line, or None
def _find_separators(line, left_separator, right_separator):
    left = line.find(left_separator)
    if left == -1:
        return None
    right = line[left + len(left_separator):].find(right_separator)
    return (left, left + len(left_separator) + right) if right != -1 else None


def _find_tags(line):
    positions = _find_separators(line, "tag(", ")")
    return " ".join(line[positions[0] + 4: positions[1]].split(",")) if positions else None


# remove tags if any, and get global values (i.e, values of variables whose names are between quotes)
def _prepare(line):
    while True:
        positions = _find_separators(line, "'", "'")
        if positions is None:
            break
        left, right = positions
        value = _global_value_of(line[left + 1:right])
        if value:
            line = line[:left] + value + line[right + 1:]
        else:
            break  # we abandon the process
    positions = _find_separators(line, "tag(", ")")
    if positions:
        line = line[:positions[0]] + line[positions[1] + 1:]
    return None if line == "" or line.strip() == "#" else line.strip()[1:].strip()


def comment_and_tags_of(*, function_name):
    lines = []
    found = False  # the function name
    for line in _extract_code(function_name):  # code is given bottom-up
        if not is_comment_line(line) and function_name in line:
            found = True
            continue
        elif is_comment_line(line) and found:
            lines.append(line)
        elif is_empty_line and found:
            break
    if len(lines) == 0:
        return None, None
    comment, tags = "", ""
    for line in reversed(lines):
        if _find_tags(line) is not None:
            tags += ("" if len(tags) == 0 else " ") + _find_tags(line).strip()
        if _prepare(line) is not None:
            comment += ("" if len(comment) == 0 else " " if comment[-1] in {'.', ','} else " - ") + _prepare(line)
    return comment, tags


def _remove_matching_brackets(line):
    bracket = None
    for i, c in enumerate(line):
        if c in {'(', '[', '{'}:  # todo adding 'for'?
            left = i
            bracket = c
        elif (c, bracket) in {(')', '('), (']', '['), ('}', '{')}:  # todo adding ('for', 'in') ?
            right = i + 1
            break
    else:  # no break
        return line
    return _remove_matching_brackets(line[:left] + line[right:])  # recursive call


# Delete ( ) parts and [ ] parts of each line excepts for comment lines
def _delete_bracket_part(code, nb_parameters):
    # if nb_parameters == 1 and len(code) == 1:  # TODO  code for case like variant aux-v7 in Quasigroup (remonving ,)
    #     code = [line.strip() if is_comment_line(line) else line.replace(",", "").strip() for line in code]
    # else:
    code = [line.strip() if is_comment_line(line) else _remove_matching_brackets(line).strip() for line in code]
    if len(code) > 0 and len(code[-1]) > 0 and code[-1][-1] == ',':  # removing useless trailing comma of specify() if any
        code[-1] = code[-1][:-1]
    return code


def comments_and_tags_of_parameters_of(*, function_name, args, no_extraction=False):
    if len(args) == 0:
        return [], [], [], []

    comments1 = [""] * len(args)  # comments at first level (i.e., at level of the parameters)
    comments2 = [[""] for _ in args]  # comments at second level (i.e, for elements of intern lists)
    tags1 = [""] * len(args)  # tags at first level
    tags2 = [[""] for _ in args]  # tags at second level
    if no_extraction:
        return comments1, comments2, tags1, tags2

    code = list(reversed(_extract_code(function_name)))
    are_empty_lines = [is_empty_line(line) for line in code]

    code = _delete_bracket_part(code, len(args))
    level = 0
    i1 = 0  # index indicating the position of the current parameter
    i2 = 0  # index indicating the position of the element of the current list (inside the current parameter)
    found = False
    for i, line in enumerate(code):
        if not is_comment_line(line):
            new_line = ""  # possibly a new line to replace line
            for j, c in enumerate(line):
                if c == '#':  # if comment in code line
                    break
                if function_name in line:
                    if j < line.index(function_name):  # Fix for '(' or '[' before the name of the function
                        continue
                    else:
                        found = True  # Fix function name for comment of level 2
                if c in {'(', '['}:
                    level += 1
                elif c in {')', ']'}:
                    level -= 1
                elif c == ",":
                    if level == 1:
                        i1 += 1
                        i2 = 0
                        new_line += c
                    elif level == 2:
                        i2 += 1
                        comments2[i1].append("")
                        tags2[i1].append("")
                        new_line += '$'
                    else:
                        assert level != 0, line + " " + str(level)
                        new_line += '_'
                else:
                    new_line += c
            code[i] = "" if level != 1 else new_line

        if found and level == 2 and is_comment_line(line):
            s = _prepare(line)
            comments2[i1][i2] += ("" if len(comments2[i1][i2]) == 0 else " - ") + ("" if s is None else s)
            tags = _find_tags(line)
            if tags:
                tags2[i1][i2] += ("" if len(tags2[i1][i2]) == 0 else " ") + tags
            code[i] = ""

    # n_commas = sum(s.count(',') for s in code if not is_comment_line(s))  # TODO problem with subvariant aux-v7 of Quasigroup
    # assert len(args) == n_commas + 1, "Inspector error: numbers of commas incorrect in satisfy():" + str(n_commas) + " in " + str(code)

    # collecting comments and tags for each parameter (i.e., at level 1)
    i1 = 0
    found = False  # the function name
    for i, line in enumerate(code):
        if function_name in line:
            found = True
        if found and is_comment_line(line) and _prepare(line) and i + 1 < len(code):
            comments1[i1] += ("" if len(comments1[i1]) == 0 else " " if comments1[i1][-1] in {'.', ','} else " - ") + _prepare(line)
            if are_empty_lines[i + 1]:
                comments1[i1] = ""
        tags = _find_tags(line)
        if tags:
            tags1[i1] += ("" if len(tags1[i1]) == 0 else " ") + tags
        elif not is_comment_line(line) and ',' in line:
            i1 += line.count(',')
    return comments1, comments2, tags1, tags2


def extract_declaration_for(function_name):
    code = list(reversed(_extract_code(function_name)))
    for line in code:
        if function_name in line and not is_comment_line(line):
            pos = line.find(function_name)
            if "=" in line[:pos]:
                break
    else:
        return None  # assert False, " the object returned by " + function_name + " should be assigned to a variable"
    declaration = line[:pos].strip()
    if declaration.endswith("pycsp3."):  # if the name of the package is present as a suffix, we remove it
        declaration = declaration[:-8]
    if declaration[-1] == '=':
        declaration = declaration[:-1].strip()
    assert declaration.count('=') < 2
    if '=' in declaration:
        t = declaration.split('=')
        declaration = t[0] if ',' in t[0] else t[1]
    if function_name == "Var":
        assert "," not in declaration and ")" not in declaration, \
            "Every simple declaration must be on its own line. For example, 'x, y = Var(dom={0,1}), Var(dom={0,1})' is not allowed."
        return declaration
    elif function_name == "VarArray":
        assert ")" not in declaration
        return declaration if "," not in declaration else [v.strip() for v in declaration.split(",")]


# def docstringOf(name):
#    att = getattr(functions, name, None)
#    return None if att is None else att.__doc__


def checkType(obj, allowed_types, message=""):
    if options.checker == "none":
        return True
    if options.checker == "fast" and isinstance(obj, (list, tuple, set, frozenset)) and len(obj) > 100:
        obj = obj[:1]  # TODO problem here: sets cannot be indexed
    allowed_types = (allowed_types,) if not isinstance(allowed_types, tuple) else allowed_types
    for allowedType in allowed_types:
        if not isinstance(allowedType, list):
            if isinstance(obj, allowedType):
                return True
        elif isinstance(obj, (list, tuple, set)):
            for p in flatten(obj):
                if not any(isinstance(p, typ) for typ in allowedType):
                    break  # raise TypeMCSPError(inspector.getCalling(), p, allowedTypes, message, position)
            else:
                return True
    if message == "":
        message = "Wrong type for " + str(obj) + " (allowable types: " + str(allowed_types) + ")\n"
    raise TypeError(message)

    # stack = inspect.stack(context=1)
    # name_function_stack = [s.function for s in stack]
    # position_functions_file = [i for i, s in enumerate(stack) if s.filename.endswith("functions.py")][0]
    # modeling_file = stack[position_functions_file + 2] if len(stack) > position_functions_file + 2 else None
    # if modeling_file is None and "<module>" in name_function_stack:
    #     modeling_file = stack[[i for i, s in enumerate(stack) if s.function == "<module>"][0]]
    # function_name = "satisfy"
    # problem_lines = []
    # if function_name in name_function_stack: #  satisfy case
    #     code = list(reversed(_extract_code(function_name)))
    #     if len(code) > 0:
    #         without_bracket_code = _delete_bracket_part(code, functions.nb_parameter_satisfy)
    #         found = False  # the function name
    #         pos_parameter = 0
    #         for i, line in enumerate(without_bracket_code):
    #             if function_name in line:
    #                 found = True
    #             if found and pos_parameter == functions.no_parameter_satisfy and not is_comment_line(line):
    #                 problem_lines.append(code[i])
    #             if not is_comment_line(line) and ',' in line:
    #                 pos_parameter += line.count(',')
    # else:
    #     if modeling_file:
    #         problem_lines.extend(modeling_file.code_context)
    #         noline = modeling_file.lineno
    #     else:
    #         problem_lines.extend(stack[2].code_context)
    #         noline = stack[2].lineno
    #     functions.no_parameter_satisfy = None
    #
    # s = "\n\tAt line " + str(stack[1].lineno) + " of function " + stack[1].function + " in file " + stack[1].filename[stack[1].filename.rindex(os.sep) + 1:]
    # s += "\n\tThis assertion fails: " + stack[1].code_context[0].strip()
    # if modeling_file is not None and len(problem_lines) > 0:
    #     if functions.no_parameter_satisfy is not None:
    #         s += "\n\n\tThe problem comes from parameter " + str(functions.no_parameter_satisfy) + " of satisfy() in file " \
    #              + modeling_file.filename[modeling_file.filename.rindex(os.sep) + 1:] + ","
    #     else:
    #         s += "\n\n\tThe problem is at line " + str(noline) + " of file " + modeling_file.filename[modeling_file.filename.rindex(os.sep) + 1:] + ","
    #     s += "\n\tWhen executing:\n\t\t" + "\n\t\t".join(problem_lines) + "\n\t" + message if message is not None else ""
    #
    #     # TODO get the good docstring
    #     # s += "\n\n\tDocumentation for function: " + stack[1].function
    #     # doc = docstringOf(stack[1].function)
    #     # s += doc if doc is not None else "\n\tNo python docstring for this function"

    # s)
