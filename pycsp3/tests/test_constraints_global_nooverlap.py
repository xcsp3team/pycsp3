"""
Tests of the constraint NoOverlap of the section Constraints (Global) of the API
(https://pycsp.org/documentation/api/constraints-global/#NoOverlap): the function NoOverlap(), with tasks (one dimension) and boxes (two or
three dimensions), given by pairs (tasks) or by the named parameters origins and lengths, with the parameter zero_ignored, with the option -mini,
in groups of constraints and in logical expressions.

Each constraint is solved with ACE, CHOCO and COSOCO, all the solutions being compared with the ones computed by brute force.
According to XCSP3 (Semantics 23 and 24 of XCSP3-core, given for zeroIgnored=false):
 - noOverlap(X, L) holds iff, for each pair of tasks i < j, x_i + l_i <= x_j or x_j + l_j <= x_i;
 - noOverlap(X, L) with boxes holds iff, for each pair of boxes i < j, there is a dimension k such that x_i,k + l_i,k <= x_j,k or x_j,k + l_j,k <= x_i,k;
 - with zeroIgnored="true" (the default), the tasks of length 0 (the boxes with a length 0 in a dimension) are discarded.
"""

import pytest

from harness import assert_fails, assert_solutions, brute_force, bug, bug_for

# Bugs of PyCSP3 (each bug is reported in the issue given at the start of its reason)
SIZES = "#327: the sizes of origins and lengths are not checked (a file that is not valid is generated)"
DIMENSIONS = "#328: the dimensions of the boxes (origins and lengths) are not checked (a file that is not valid is generated)"
TRANSPOSED = ("#329: origins and lengths given by dimension ([x, y], [w, h]) are taken as boxes when there are two boxes, and two boxes of "
              "three dimensions are taken as three boxes of two dimensions")
INTEGER_ORIGINS_3D = "#330: an integer origin of a box of three dimensions is written as such (XCSP3 requires variables)"
BOOLEAN = "#331: a Boolean length is written True/False in the XCSP3 file"
ZERO_IGNORED = "#332: the value of zero_ignored is not checked (written as zeroIgnored=\"none\", or discarded)"
INVALID = "#333: invalid arguments stop with an assert without message or a Python error raised inside PyCSP3"
LESS_THAN_TWO = "#334: a constraint NoOverlap with less than two tasks given by origins and lengths, or a single box, is not discarded consistently"
MINI_2D = "#335: with -mini, NoOverlap in two dimensions fails (TypeError: dom.smallest_value without parentheses)"
MINI_VARIABLE_LENGTHS = "#336: with -mini, a NoOverlap with variable lengths is discarded silently (warning: a node is evaluated as a Boolean)"
MINI_ZERO = "#337: with -mini, the tasks of length 0 are not discarded (the tables encode zeroIgnored=false)"
MINI_ZERO_IGNORED = "#338: with -mini, zero_ignored=False stops with an assert without message"
META_NEGATION = "#339: ~NoOverlap(...) with the option -use_meta raises a TypeError inside PyCSP3"
NEGATIVE = "#340 (question): negative lengths are accepted silently"
TASKS_ZIP = "#341: tasks given by a zip stop with a TypeError (object of type 'zip' has no len()), whereas origins and lengths can be zips"

# Bugs of the solvers (sections of the description of the PR of these tests, to be reported after review)
ACE_DUPLICATES = ("PR #326, ACE1: ACE gives solutions several times (the auxiliary 0/1 variable posted for each pair of tasks, option noOverlapAux, "
                  "is not determined by the origins)")
ACE_ZERO = "PR #326, ACE2: ACE does not discard the tasks whose length is the integer 0 (zeroIgnored is true by default)"
ACE_REPEATED = "PR #326, ACE3: ACE: ERROR without message (control in Disjonctive) when a variable is shared by two tasks or boxes"
CHOCO_ZERO_IGNORED_FALSE = "PR #326, CHOCO1: CHOCO ignores zeroIgnored=false in one dimension (the tasks of length 0 are discarded)"
COSOCO_DUPLICATES = "PR #326, cosoco1: cosoco gives solutions several times (auxiliary variables __av; the fix of cosoco#73 is not complete)"
COSOCO_ZERO = "PR #326, cosoco2: cosoco does not discard the tasks whose length is the integer 0 (zeroIgnored is true by default)"
COSOCO_SHARED = "PR #326, cosoco3: cosoco: wrong solutions (Solution Error) when a variable is shared by two boxes"
COSOCO_3D = "PR #326, cosoco4: cosoco: missing solutions, or solutions several times, in three dimensions"
COSOCO_MIXED = "PR #326, cosoco5: cosoco: wrong solutions or segmentation fault when the lengths mix integers and variables (two or three dimensions)"
PARSER_MIXED = ("PR #326, XCSP3-Java-Tools1: ClassCastException in CtrLoaderInteger.noOverlap (ACE and CHOCO) when the lengths mix integers and "
                "variables otherwise than variables in the first dimension and integers in the second one")
ZERO_2D = "PR #326, question Q1: none of the three solvers discards the boxes with a length 0 (zeroIgnored is true by default) in two dimensions"
COSOCO_OLD = ("xcsp3team/cosoco#73: cosoco 2.6.1 gives solutions several times, or misses solutions with variable lengths (fixed after 2.6.1, "
              "not released)")
CHOCO_3D_OLD = ("CHOCO 4.10.15: wrong solutions in three dimensions with variable lengths; the develop version says that the case is not "
                "implemented (not reported)")

# The cases that a solver says it does not handle, and the symbolic variables (not reported)
ACE_ZERO_IGNORED_FALSE = "ACE: zeroIgnored=false is not implemented (unimplemented case for noOverlap)"
ACE_3D = "ACE: noOverlap in three dimensions with fixed lengths is not implemented"
CHOCO_3D = "CHOCO: noOverlap in three dimensions is not implemented (unimplementedCase of XCallbacks2)"
COSOCO_ZERO_IGNORED_FALSE = "COSOCO: zeroIgnored=false is not supported (Nooverlap with zeroIgnored not yet supported)"
SYMBOLIC = "noOverlap on symbolic variables is not part of XCSP3"


# The failures of the solvers, by test (the solvers give the same answers on the XCSP3 files written by hand, without PyCSP3)
SOLVER_BUGS = {
    "test_nooverlap[ACE-2-lengths0]": ACE_DUPLICATES,
    "test_nooverlap[ACE-2-lengths1]": ACE_DUPLICATES,
    "test_nooverlap[ACE-3-lengths2]": ACE_DUPLICATES,
    "test_nooverlap[ACE-4-lengths4]": ACE_DUPLICATES,
    "test_nooverlap[COSOCO-2-lengths0]": COSOCO_OLD,
    "test_nooverlap[COSOCO-2-lengths1]": COSOCO_OLD,
    "test_nooverlap[COSOCO-3-lengths2]": COSOCO_DUPLICATES,
    "test_nooverlap[COSOCO-3-lengths3]": COSOCO_OLD,
    "test_nooverlap[COSOCO-4-lengths4]": COSOCO_DUPLICATES,
    "test_nooverlap_1d_and_2d[ACE]": ACE_DUPLICATES,
    "test_nooverlap_1d_and_2d[COSOCO]": COSOCO_OLD,
    "test_nooverlap_2d[ACE-lengths0]": ACE_DUPLICATES,
    "test_nooverlap_2d[ACE-lengths1]": ACE_DUPLICATES,
    "test_nooverlap_2d[ACE-lengths3]": ACE_DUPLICATES,
    "test_nooverlap_2d[COSOCO-lengths0]": COSOCO_DUPLICATES,
    "test_nooverlap_2d[COSOCO-lengths1]": COSOCO_DUPLICATES,
    "test_nooverlap_2d[COSOCO-lengths3]": COSOCO_DUPLICATES,
    "test_nooverlap_2d_forms[ACE-by dimension]": ACE_DUPLICATES,
    "test_nooverlap_2d_forms[ACE-lists]": ACE_DUPLICATES,
    "test_nooverlap_2d_forms[ACE-tasks]": ACE_DUPLICATES,
    "test_nooverlap_2d_forms[ACE-tuples]": ACE_DUPLICATES,
    "test_nooverlap_2d_forms[ACE-zip]": ACE_DUPLICATES,
    "test_nooverlap_2d_forms[COSOCO-by dimension]": COSOCO_DUPLICATES,
    "test_nooverlap_2d_forms[COSOCO-lists]": COSOCO_DUPLICATES,
    "test_nooverlap_2d_forms[COSOCO-tasks]": COSOCO_DUPLICATES,
    "test_nooverlap_2d_forms[COSOCO-tuples]": COSOCO_DUPLICATES,
    "test_nooverlap_2d_forms[COSOCO-zip]": COSOCO_DUPLICATES,
    "test_nooverlap_2d_on_the_rows_of_a_matrix[ACE]": ACE_DUPLICATES,
    "test_nooverlap_2d_on_the_rows_of_a_matrix[COSOCO]": COSOCO_DUPLICATES,
    "test_nooverlap_2d_with_integers_and_expressions[ACE-expression]": ACE_DUPLICATES,
    "test_nooverlap_2d_with_integers_and_expressions[ACE-integer]": ACE_DUPLICATES,
    "test_nooverlap_2d_with_integers_and_expressions[ACE-shared variable]": ACE_REPEATED,
    "test_nooverlap_2d_with_integers_and_expressions[COSOCO-expression]": COSOCO_DUPLICATES,
    "test_nooverlap_2d_with_integers_and_expressions[COSOCO-integer]": COSOCO_OLD,
    "test_nooverlap_2d_with_integers_and_expressions[COSOCO-shared variable]": COSOCO_SHARED,
    "test_nooverlap_2d_with_positive_variable_lengths[ACE]": ACE_DUPLICATES,
    "test_nooverlap_2d_with_positive_variable_lengths[COSOCO]": COSOCO_DUPLICATES,
    "test_nooverlap_2d_with_two_boxes[ACE]": ACE_DUPLICATES,
    "test_nooverlap_2d_with_two_boxes[COSOCO]": COSOCO_OLD,
    "test_nooverlap_2d_with_unit_lengths[ACE]": ACE_DUPLICATES,
    "test_nooverlap_2d_with_unit_lengths[COSOCO]": COSOCO_DUPLICATES,
    "test_nooverlap_2d_with_variable_and_fixed_lengths[ACE]": ACE_DUPLICATES,
    "test_nooverlap_2d_with_variable_and_fixed_lengths[COSOCO]": COSOCO_DUPLICATES,
    "test_nooverlap_2d_with_variable_heights[ACE]": PARSER_MIXED,
    "test_nooverlap_2d_with_variable_heights[CHOCO]": PARSER_MIXED,
    "test_nooverlap_2d_with_variable_heights[COSOCO]": COSOCO_MIXED,
    "test_nooverlap_2d_with_variable_lengths[ACE]": ZERO_2D,
    "test_nooverlap_2d_with_variable_lengths[CHOCO]": ZERO_2D,
    "test_nooverlap_2d_with_variable_lengths[COSOCO]": ZERO_2D,
    "test_nooverlap_2d_with_variable_widths_and_heights[ACE]": ACE_DUPLICATES,
    "test_nooverlap_2d_with_variable_widths_and_heights[COSOCO]": COSOCO_DUPLICATES,
    "test_nooverlap_2d_with_zero_lengths[ACE-lengths0-True]": ZERO_2D,
    "test_nooverlap_2d_with_zero_lengths[ACE-lengths1-True]": ZERO_2D,
    "test_nooverlap_2d_with_zero_lengths[ACE-lengths2-True]": ZERO_2D,
    "test_nooverlap_2d_with_zero_lengths[CHOCO-lengths0-True]": ZERO_2D,
    "test_nooverlap_2d_with_zero_lengths[CHOCO-lengths1-True]": ZERO_2D,
    "test_nooverlap_2d_with_zero_lengths[CHOCO-lengths2-True]": ZERO_2D,
    "test_nooverlap_2d_with_zero_lengths[COSOCO-lengths0-True]": ZERO_2D,
    "test_nooverlap_2d_with_zero_lengths[COSOCO-lengths1-True]": ZERO_2D,
    "test_nooverlap_2d_with_zero_lengths[COSOCO-lengths2-True]": ZERO_2D,
    "test_nooverlap_3d[COSOCO]": COSOCO_3D,
    "test_nooverlap_3d_with_variable_and_fixed_lengths[ACE]": PARSER_MIXED,
    "test_nooverlap_3d_with_variable_and_fixed_lengths[CHOCO]": PARSER_MIXED,
    "test_nooverlap_3d_with_variable_and_fixed_lengths[COSOCO]": COSOCO_MIXED,
    "test_nooverlap_3d_with_variable_lengths[ACE]": ACE_DUPLICATES,
    "test_nooverlap_3d_with_variable_lengths[CHOCO]": CHOCO_3D_OLD,
    "test_nooverlap_3d_with_variable_lengths[COSOCO]": COSOCO_DUPLICATES,
    "test_nooverlap_example_packing[ACE]": ACE_DUPLICATES,
    "test_nooverlap_example_packing[COSOCO]": COSOCO_DUPLICATES,
    "test_nooverlap_example_scheduling[COSOCO]": COSOCO_DUPLICATES,
    "test_nooverlap_example_zero_ignored[CHOCO]": CHOCO_ZERO_IGNORED_FALSE,
    "test_nooverlap_forms[ACE-Task objects]": ACE_DUPLICATES,
    "test_nooverlap_forms[ACE-generator]": ACE_DUPLICATES,
    "test_nooverlap_forms[ACE-lists]": ACE_DUPLICATES,
    "test_nooverlap_forms[ACE-parameters swapped]": ACE_DUPLICATES,
    "test_nooverlap_forms[ACE-range]": ACE_DUPLICATES,
    "test_nooverlap_forms[ACE-tasks generator]": ACE_DUPLICATES,
    "test_nooverlap_forms[ACE-tasks positional]": ACE_DUPLICATES,
    "test_nooverlap_forms[ACE-tasks with None]": ACE_DUPLICATES,
    "test_nooverlap_forms[ACE-tasks]": ACE_DUPLICATES,
    "test_nooverlap_forms[ACE-tuple of lengths]": ACE_DUPLICATES,
    "test_nooverlap_forms[ACE-tuple of origins]": ACE_DUPLICATES,
    "test_nooverlap_forms[COSOCO-Task objects]": COSOCO_OLD,
    "test_nooverlap_forms[COSOCO-generator]": COSOCO_OLD,
    "test_nooverlap_forms[COSOCO-lists]": COSOCO_OLD,
    "test_nooverlap_forms[COSOCO-parameters swapped]": COSOCO_OLD,
    "test_nooverlap_forms[COSOCO-range]": COSOCO_DUPLICATES,
    "test_nooverlap_forms[COSOCO-tasks generator]": COSOCO_OLD,
    "test_nooverlap_forms[COSOCO-tasks positional]": COSOCO_OLD,
    "test_nooverlap_forms[COSOCO-tasks with None]": COSOCO_OLD,
    "test_nooverlap_forms[COSOCO-tasks]": COSOCO_OLD,
    "test_nooverlap_forms[COSOCO-tuple of lengths]": COSOCO_OLD,
    "test_nooverlap_forms[COSOCO-tuple of origins]": COSOCO_OLD,
    "test_nooverlap_on_the_rows_of_a_matrix[ACE]": ACE_DUPLICATES,
    "test_nooverlap_on_the_rows_of_a_matrix[COSOCO]": COSOCO_DUPLICATES,
    "test_nooverlap_with_a_repeated_origin[COSOCO]": COSOCO_OLD,
    "test_nooverlap_with_a_repeated_origin_and_fixed_lengths[ACE]": ACE_REPEATED,
    "test_nooverlap_with_a_single_length[COSOCO]": COSOCO_OLD,
    "test_nooverlap_with_an_origin_being_a_length[COSOCO]": COSOCO_OLD,
    "test_nooverlap_with_expressions_and_integers[ACE-integer origin]": ACE_DUPLICATES,
    "test_nooverlap_with_expressions_and_integers[ACE-mul origin]": ACE_DUPLICATES,
    "test_nooverlap_with_expressions_and_integers[COSOCO-expression origin]": COSOCO_DUPLICATES,
    "test_nooverlap_with_expressions_and_integers[COSOCO-integer origin]": COSOCO_OLD,
    "test_nooverlap_with_expressions_and_integers[COSOCO-mul origin]": COSOCO_DUPLICATES,
    "test_nooverlap_with_origins_in_another_order[ACE]": ACE_DUPLICATES,
    "test_nooverlap_with_origins_in_another_order[COSOCO]": COSOCO_DUPLICATES,
    "test_nooverlap_with_other_constraints[ACE]": ACE_DUPLICATES,
    "test_nooverlap_with_other_constraints[COSOCO]": COSOCO_OLD,
    "test_nooverlap_with_variable_and_fixed_lengths[COSOCO-one variable]": COSOCO_OLD,
    "test_nooverlap_with_variable_and_fixed_lengths[COSOCO-two variables]": COSOCO_OLD,
    "test_nooverlap_with_variable_lengths[COSOCO]": COSOCO_OLD,
    "test_nooverlap_with_variable_lengths_and_zero_ignored_false[CHOCO]": CHOCO_ZERO_IGNORED_FALSE,
    "test_nooverlap_with_various_domains[ACE-holes]": ACE_DUPLICATES,
    "test_nooverlap_with_various_domains[ACE-negative values]": ACE_DUPLICATES,
    "test_nooverlap_with_various_domains[ACE-shifted]": ACE_DUPLICATES,
    "test_nooverlap_with_various_domains[COSOCO-holes]": COSOCO_DUPLICATES,
    "test_nooverlap_with_various_domains[COSOCO-negative values]": COSOCO_DUPLICATES,
    "test_nooverlap_with_various_domains[COSOCO-shifted]": COSOCO_OLD,
    "test_nooverlap_with_zero_lengths[ACE-lengths0-True]": ACE_ZERO,
    "test_nooverlap_with_zero_lengths[ACE-lengths1-True]": ACE_ZERO,
    "test_nooverlap_with_zero_lengths[CHOCO-lengths0-False]": CHOCO_ZERO_IGNORED_FALSE,
    "test_nooverlap_with_zero_lengths[CHOCO-lengths1-False]": CHOCO_ZERO_IGNORED_FALSE,
    "test_nooverlap_with_zero_lengths[COSOCO-lengths0-True]": COSOCO_ZERO,
    "test_nooverlap_with_zero_lengths[COSOCO-lengths1-True]": COSOCO_ZERO,
    "test_nooverlap_with_zero_lengths[COSOCO-lengths2-True]": COSOCO_ZERO,
    "test_nooverlaps_sharing_variables[ACE]": ACE_DUPLICATES,
    "test_nooverlaps_sharing_variables[COSOCO]": COSOCO_DUPLICATES,
}
SOLVER_SKIPS = {
    "test_nooverlap_2d_with_zero_ignored_false[ACE]": ACE_ZERO_IGNORED_FALSE,
    "test_nooverlap_2d_with_zero_ignored_false[COSOCO]": COSOCO_ZERO_IGNORED_FALSE,
    "test_nooverlap_2d_with_zero_lengths[ACE-lengths0-False]": ACE_ZERO_IGNORED_FALSE,
    "test_nooverlap_2d_with_zero_lengths[ACE-lengths1-False]": ACE_ZERO_IGNORED_FALSE,
    "test_nooverlap_2d_with_zero_lengths[ACE-lengths2-False]": ACE_ZERO_IGNORED_FALSE,
    "test_nooverlap_2d_with_zero_lengths[COSOCO-lengths0-False]": COSOCO_ZERO_IGNORED_FALSE,
    "test_nooverlap_2d_with_zero_lengths[COSOCO-lengths1-False]": COSOCO_ZERO_IGNORED_FALSE,
    "test_nooverlap_2d_with_zero_lengths[COSOCO-lengths2-False]": COSOCO_ZERO_IGNORED_FALSE,
    "test_nooverlap_3d[ACE]": ACE_3D,
    "test_nooverlap_3d[CHOCO]": CHOCO_3D,
    "test_nooverlap_example_zero_ignored[ACE]": ACE_ZERO_IGNORED_FALSE,
    "test_nooverlap_example_zero_ignored[COSOCO]": COSOCO_ZERO_IGNORED_FALSE,
    "test_nooverlap_with_variable_lengths_and_zero_ignored_false[ACE]": ACE_ZERO_IGNORED_FALSE,
    "test_nooverlap_with_variable_lengths_and_zero_ignored_false[COSOCO]": COSOCO_ZERO_IGNORED_FALSE,
    "test_nooverlap_with_zero_lengths[ACE-lengths0-False]": ACE_ZERO_IGNORED_FALSE,
    "test_nooverlap_with_zero_lengths[ACE-lengths1-False]": ACE_ZERO_IGNORED_FALSE,
    "test_nooverlap_with_zero_lengths[ACE-lengths2-False]": ACE_ZERO_IGNORED_FALSE,
    "test_nooverlap_with_zero_lengths[COSOCO-lengths0-False]": COSOCO_ZERO_IGNORED_FALSE,
    "test_nooverlap_with_zero_lengths[COSOCO-lengths1-False]": COSOCO_ZERO_IGNORED_FALSE,
    "test_nooverlap_with_zero_lengths[COSOCO-lengths2-False]": COSOCO_ZERO_IGNORED_FALSE,
}


@pytest.fixture(autouse=True)
def _known_failures_of_the_solvers(request):
    if request.node.name in SOLVER_SKIPS:
        pytest.skip(SOLVER_SKIPS[request.node.name])
    if request.node.name in SOLVER_BUGS:
        request.applymarker(bug(SOLVER_BUGS[request.node.name]))


def no_overlap1(x, lengths, zero_ignored=True):
    """Returns True if the tasks of origins x and lengths do not overlap (one dimension)."""
    n = len(x)
    return all(zero_ignored and (lengths[i] == 0 or lengths[j] == 0) or x[i] + lengths[i] <= x[j] or x[j] + lengths[j] <= x[i]
               for i in range(n) for j in range(i + 1, n))


def no_overlap(origins, lengths, zero_ignored=True):
    """Returns True if the boxes of origins and lengths (tuples of the same size) do not overlap."""
    n = len(origins)
    return all(zero_ignored and (0 in lengths[i] or 0 in lengths[j])
               or any(origins[i][k] + lengths[i][k] <= origins[j][k] or origins[j][k] + lengths[j][k] <= origins[i][k] for k in range(len(origins[i])))
               for i in range(n) for j in range(i + 1, n))


def check(run, solver, code, domains, predicate, args=()):
    r = run(code, solver=solver, args=args)
    assert_solutions(r, brute_force(domains, predicate))
    return r


def arrays(*specs):
    """Returns the code declaring the specified arrays, given as (name, size, dom)."""
    return "".join(f"{name} = VarArray(size={n}, dom={dom})\n" for name, n, dom in specs)


X3 = arrays(("x", 3, "range(5)"))
D3 = [range(5)] * 3
XL = arrays(("x", 3, "range(4)"), ("l", 3, "range(3)"))  # origins and variable lengths
DXL = [range(4)] * 3 + [range(3)] * 3
XY3 = arrays(("x", 3, "range(3)"), ("y", 3, "range(3)"))  # boxes in two dimensions (the predicates take x0 x1 x2 y0 y1 y2)
DXY3 = [range(3)] * 6
XY2 = arrays(("x", 2, "range(3)"), ("y", 2, "range(3)"))
DXY2 = [range(3)] * 4


def boxes(t, n):
    """The origins (x[i], y[i]) of n boxes from the tuple t = x0 ... x(n-1) y0 ... y(n-1)."""
    return [(t[i], t[n + i]) for i in range(n)]


# ------------------------------------------------------------------------------------------------------- one dimension

@pytest.mark.parametrize("n, lengths", [(2, [1, 2]), (2, [3, 3]), (3, [1, 2, 1]), (3, [2, 2, 2]), (4, [1, 1, 2, 1])])
def test_nooverlap(run, solver, n, lengths):
    code = arrays(("x", n, "range(5)")) + f"satisfy(NoOverlap(origins=x, lengths={lengths}))"
    check(run, solver, code, [range(5)] * n, lambda *t: no_overlap1(t, lengths))


@pytest.mark.parametrize("arguments", [
    "origins=x, lengths=[1, 2, 2]",
    "origins=x[:], lengths=(1, 2, 2)",
    "origins=tuple(x), lengths=[1, 2, 2]",
    "origins=(v for v in x), lengths=[1, 2, 2]",
    "origins=x, lengths=range(1, 4)",  # lengths 1 2 3
    "lengths=[1, 2, 2], origins=x",
    "tasks=[(x[0], 1), (x[1], 2), (x[2], 2)]",
    "[(x[0], 1), (x[1], 2), (x[2], 2)]",
    "tasks=((x[i], [1, 2, 2][i]) for i in range(3))",
    "tasks=[(x[0], 1, None), (x[1], 2, None), (x[2], 2, None)]",
    pytest.param("tasks=zip(x, [1, 2, 2])", marks=bug(TASKS_ZIP)),
    "[Task(origin=x[i], length=[1, 2, 2][i]) for i in range(3)]",
], ids=["lists", "tuple of lengths", "tuple of origins", "generator", "range", "parameters swapped", "tasks", "tasks positional",
        "tasks generator", "tasks with None", "tasks zip", "Task objects"])
def test_nooverlap_forms(run, solver, arguments):
    lengths = [1, 2, 3] if "range(1, 4)" in arguments else [1, 2, 2]
    check(run, solver, X3 + f"satisfy(NoOverlap({arguments}))", D3, lambda *t: no_overlap1(t, lengths))


def test_nooverlap_with_a_single_length(run, solver):
    # an integer given as lengths is the length of each task
    check(run, solver, X3 + "satisfy(NoOverlap(origins=x, lengths=2))", D3, lambda *t: no_overlap1(t, [2, 2, 2]))


def test_nooverlap_with_origins_in_another_order(run, solver):
    check(run, solver, X3 + "satisfy(NoOverlap(origins=[x[2], x[0], x[1]], lengths=[1, 2, 3]))", D3,
          lambda a, b, c: no_overlap1((c, a, b), [1, 2, 3]))


@pytest.mark.parametrize("dom, values", [("range(-2, 3)", range(-2, 3)), ("{0, 2, 3, 5}", [0, 2, 3, 5]), ("range(2, 6)", range(2, 6))],
                         ids=["negative values", "holes", "shifted"])
def test_nooverlap_with_various_domains(run, solver, dom, values):
    check(run, solver, arrays(("x", 3, dom)) + "satisfy(NoOverlap(origins=x, lengths=[1, 2, 1]))", [values] * 3,
          lambda *t: no_overlap1(t, [1, 2, 1]))


def test_nooverlap_with_too_long_tasks(run, solver):
    # no solution
    check(run, solver, arrays(("x", 3, "range(3)")) + "satisfy(NoOverlap(origins=x, lengths=[2, 2, 2]))", [range(3)] * 3,
          lambda *t: no_overlap1(t, [2, 2, 2]))


def test_nooverlap_with_unit_lengths(run, solver):
    # equivalent to allDifferent, which is posted instead
    r = check(run, solver, X3 + "satisfy(NoOverlap(origins=x, lengths=[1, 1, 1]))", D3, lambda *t: no_overlap1(t, [1, 1, 1]))
    assert r.xml.find("constraints/allDifferent") is not None and r.xml.find("constraints/noOverlap") is None, r.report()


def test_nooverlap_with_unit_lengths_and_zero_ignored_false(run, solver):
    r = check(run, solver, X3 + "satisfy(NoOverlap(origins=x, lengths=[1, 1, 1], zero_ignored=False))", D3,
              lambda *t: no_overlap1(t, [1, 1, 1], False))
    assert r.xml.find("constraints/allDifferent") is not None, r.report()


# ---------------------------------------------------------------------------------------------------- variable lengths

def test_nooverlap_with_variable_lengths(run, solver):
    # the tasks of length 0 are discarded (zeroIgnored is true by default)
    check(run, solver, XL + "satisfy(NoOverlap(origins=x, lengths=l))", DXL, lambda *t: no_overlap1(t[:3], t[3:]))


def test_nooverlap_with_variable_lengths_and_zero_ignored_false(run, solver):
    check(run, solver, XL + "satisfy(NoOverlap(origins=x, lengths=l, zero_ignored=False))", DXL, lambda *t: no_overlap1(t[:3], t[3:], False))


def test_nooverlap_with_positive_variable_lengths(run, solver):
    code = arrays(("x", 3, "range(4)"), ("l", 3, "range(1, 3)")) + "satisfy(NoOverlap(origins=x, lengths=l))"
    check(run, solver, code, [range(4)] * 3 + [range(1, 3)] * 3, lambda *t: no_overlap1(t[:3], t[3:]))


@pytest.mark.parametrize("lengths, predicate", [
    ("[l[0], 2, 1]", lambda t: [t[3], 2, 1]),
    ("[1, l[1], l[2]]", lambda t: [1, t[4], t[5]]),
    ("[l[0], l[0], 1]", lambda t: [t[3], t[3], 1]),
], ids=["one variable", "two variables", "repeated variable"])
def test_nooverlap_with_variable_and_fixed_lengths(run, solver, lengths, predicate):
    check(run, solver, XL + f"satisfy(NoOverlap(origins=x, lengths={lengths}))", DXL, lambda *t: no_overlap1(t[:3], predicate(t)))


def test_nooverlap_with_an_origin_being_a_length(run, solver):
    # x[0] is the origin of the first task and the length of the second one
    code = arrays(("x", 3, "range(4)")) + "satisfy(NoOverlap(origins=x, lengths=[1, x[0], 2]))"
    check(run, solver, code, [range(4)] * 3, lambda *t: no_overlap1(t, [1, t[0], 2]))


# -------------------------------------------------------------------------------------------------------- length 0

@pytest.mark.parametrize("zero_ignored", [True, False])
@pytest.mark.parametrize("lengths", [[0, 2, 1], [0, 0, 2], [0, 0, 0]])
def test_nooverlap_with_zero_lengths(run, solver, lengths, zero_ignored):
    code = X3 + f"satisfy(NoOverlap(origins=x, lengths={lengths}, zero_ignored={zero_ignored}))"
    check(run, solver, code, D3, lambda *t: no_overlap1(t, lengths, zero_ignored))


# ----------------------------------------------------------------------------------------------- terms of the lists

@pytest.mark.parametrize("arguments, predicate", [
    ("origins=[x[0] + 1, x[1], x[2]], lengths=[1, 2, 1]", lambda t: no_overlap1((t[0] + 1, t[1], t[2]), [1, 2, 1])),
    ("origins=[x[0], 2, x[2]], lengths=[1, 2, 1]", lambda t: no_overlap1((t[0], 2, t[2]), [1, 2, 1])),
    ("origins=[x[0], x[1], x[2]], lengths=[x[2] + 1, 1, 1]", lambda t: no_overlap1(t, [t[2] + 1, 1, 1])),
    ("origins=[x[0], x[1], x[2]], lengths=[abs(x[1] - x[2]), 1, 1]", lambda t: no_overlap1(t, [abs(t[1] - t[2]), 1, 1])),
    ("origins=[x[0], x[1] * 2, x[2]], lengths=[2, 1, 1]", lambda t: no_overlap1((t[0], t[1] * 2, t[2]), [2, 1, 1])),
    ("origins=[x[0], x[1], x[2]], lengths=[Sum(x[1], x[2]), 1, 1]", lambda t: no_overlap1(t, [t[1] + t[2], 1, 1])),
], ids=["expression origin", "integer origin", "expression length", "abs length", "mul origin", "sum length"])
def test_nooverlap_with_expressions_and_integers(run, solver, arguments, predicate):
    # the expressions (and the integer origins) are replaced by auxiliary variables
    check(run, solver, X3 + f"satisfy(NoOverlap({arguments}))", D3, lambda *t: predicate(t))


def test_nooverlap_with_a_repeated_origin(run, solver):
    # the same variable twice: no solution, unless the length of one of the two tasks is 0
    check(run, solver, XL + "satisfy(NoOverlap(origins=[x[0], x[0], x[1]], lengths=l))", DXL,
          lambda *t: no_overlap1((t[0], t[0], t[1]), t[3:]))


def test_nooverlap_with_a_repeated_origin_and_fixed_lengths(run, solver):
    check(run, solver, X3 + "satisfy(NoOverlap(origins=[x[0], x[0], x[1]], lengths=[1, 2, 1]))", D3,
          lambda *t: no_overlap1((t[0], t[0], t[1]), [1, 2, 1]))


# ------------------------------------------------------------------------------------------------------ two dimensions

@pytest.mark.parametrize("lengths", [[(1, 2), (2, 1), (1, 1)], [(2, 2), (1, 1), (1, 1)], [(1, 3), (1, 3), (1, 3)], [(2, 2), (2, 2), (2, 2)]])
def test_nooverlap_2d(run, solver, lengths):
    code = XY3 + f"satisfy(NoOverlap(origins=[(x[i], y[i]) for i in range(3)], lengths={lengths}))"
    check(run, solver, code, DXY3, lambda *t: no_overlap(boxes(t, 3), lengths))


def test_nooverlap_2d_with_two_boxes(run, solver):
    code = XY2 + "satisfy(NoOverlap(origins=[(x[0], y[0]), (x[1], y[1])], lengths=[(2, 1), (1, 2)]))"
    check(run, solver, code, DXY2, lambda *t: no_overlap(boxes(t, 2), [(2, 1), (1, 2)]))


L2 = [(1, 2), (2, 1), (1, 1)]


@pytest.mark.parametrize("arguments", [
    "origins=[(x[i], y[i]) for i in range(3)], lengths=[(1, 2), (2, 1), (1, 1)]",
    "origins=[[x[i], y[i]] for i in range(3)], lengths=[[1, 2], [2, 1], [1, 1]]",
    "origins=zip(x, y), lengths=zip([1, 2, 1], [2, 1, 1])",
    "origins=[x, y], lengths=[[1, 2, 1], [2, 1, 1]]",  # given by dimension
    "tasks=[((x[0], y[0]), (1, 2)), ((x[1], y[1]), (2, 1)), ((x[2], y[2]), (1, 1))]",
], ids=["tuples", "lists", "zip", "by dimension", "tasks"])
def test_nooverlap_2d_forms(run, solver, arguments):
    check(run, solver, XY3 + f"satisfy(NoOverlap({arguments}))", DXY3, lambda *t: no_overlap(boxes(t, 3), L2))


def test_nooverlap_2d_on_the_rows_of_a_matrix(run, solver):
    # each row of the matrix is the origin of a box
    code = "m = VarArray(size=[3, 2], dom=range(3))\nsatisfy(NoOverlap(origins=m, lengths=[(1, 2), (2, 1), (1, 1)]))"
    check(run, solver, code, DXY3, lambda *t: no_overlap([t[0:2], t[2:4], t[4:6]], L2))


@pytest.mark.parametrize("arguments", [
    "origins=[x, y], lengths=[[2, 1], [1, 2]]",
    "origins=[x[:], y[:]], lengths=[(2, 1), (1, 2)]",
], ids=["lists", "tuples"])
@bug(TRANSPOSED)
def test_nooverlap_2d_two_boxes_given_by_dimension(run, solver, arguments):
    check(run, solver, XY2 + f"satisfy(NoOverlap({arguments}))", DXY2, lambda *t: no_overlap(boxes(t, 2), [(2, 1), (1, 2)]))


def test_nooverlap_2d_with_zero_ignored_false(run, solver):
    code = XY3 + "satisfy(NoOverlap(origins=[(x[i], y[i]) for i in range(3)], lengths=[(1, 2), (2, 1), (1, 1)], zero_ignored=False))"
    check(run, solver, code, DXY3, lambda *t: no_overlap(boxes(t, 3), L2, False))


@pytest.mark.parametrize("zero_ignored", [True, False])
@pytest.mark.parametrize("lengths", [[(0, 2), (2, 1), (1, 1)], [(2, 0), (0, 2), (1, 1)], [(0, 0), (2, 2), (1, 1)]])
def test_nooverlap_2d_with_zero_lengths(run, solver, lengths, zero_ignored):
    code = XY3 + f"satisfy(NoOverlap(origins=[(x[i], y[i]) for i in range(3)], lengths={lengths}, zero_ignored={zero_ignored}))"
    check(run, solver, code, DXY3, lambda *t: no_overlap(boxes(t, 3), lengths, zero_ignored))


def test_nooverlap_2d_with_variable_lengths(run, solver):
    code = XY2 + "w = VarArray(size=2, dom=range(3))\nsatisfy(NoOverlap(origins=[(x[0], y[0]), (x[1], y[1])], lengths=[(w[0], 1), (w[1], 2)]))"
    check(run, solver, code, DXY2 + [range(3)] * 2, lambda *t: no_overlap(boxes(t, 2), [(t[4], 1), (t[5], 2)]))


def test_nooverlap_2d_with_positive_variable_lengths(run, solver):
    code = XY2 + "w = VarArray(size=2, dom=range(1, 3))\nsatisfy(NoOverlap(origins=[(x[0], y[0]), (x[1], y[1])], lengths=[(w[0], 1), (w[1], 2)]))"
    check(run, solver, code, DXY2 + [range(1, 3)] * 2, lambda *t: no_overlap(boxes(t, 2), [(t[4], 1), (t[5], 2)]))


def test_nooverlap_2d_with_variable_and_fixed_lengths(run, solver):
    # a dimension mixing integers and variables
    code = XY2 + "w = Var(dom=range(1, 3))\nsatisfy(NoOverlap(origins=[(x[0], y[0]), (x[1], y[1])], lengths=[(w, 1), (1, 2)]))"
    check(run, solver, code, DXY2 + [range(1, 3)], lambda *t: no_overlap(boxes(t, 2), [(t[4], 1), (1, 2)]))


def test_nooverlap_2d_with_variable_heights(run, solver):
    code = XY2 + "h = VarArray(size=2, dom=range(1, 3))\nsatisfy(NoOverlap(origins=[(x[0], y[0]), (x[1], y[1])], lengths=[(1, h[0]), (2, h[1])]))"
    check(run, solver, code, DXY2 + [range(1, 3)] * 2, lambda *t: no_overlap(boxes(t, 2), [(1, t[4]), (2, t[5])]))


def test_nooverlap_2d_with_variable_widths_and_heights(run, solver):
    code = XY2 + "w = VarArray(size=2, dom=range(1, 3))\nh = VarArray(size=2, dom=range(1, 3))\n"
    code += "satisfy(NoOverlap(origins=[(x[0], y[0]), (x[1], y[1])], lengths=[(w[0], h[0]), (w[1], h[1])]))"
    check(run, solver, code, DXY2 + [range(1, 3)] * 4, lambda *t: no_overlap(boxes(t, 2), [(t[4], t[6]), (t[5], t[7])]))


@pytest.mark.parametrize("origins, predicate", [
    ("[(x[0], 1), (x[1], y[1])]", lambda t: [(t[0], 1), (t[1], t[3])]),
    ("[(x[0] + 1, y[0]), (x[1], y[1])]", lambda t: [(t[0] + 1, t[2]), (t[1], t[3])]),
    ("[(x[0], y[0]), (x[1], x[0])]", lambda t: [(t[0], t[2]), (t[1], t[0])]),
], ids=["integer", "expression", "shared variable"])
def test_nooverlap_2d_with_integers_and_expressions(run, solver, origins, predicate):
    code = XY2 + f"satisfy(NoOverlap(origins={origins}, lengths=[(1, 2), (2, 1)]))"
    check(run, solver, code, DXY2, lambda *t: no_overlap(predicate(t), [(1, 2), (2, 1)]))


def test_nooverlap_2d_with_unit_lengths(run, solver):
    # boxes of size 1x1: equivalent to allDifferent-list on the origins
    code = XY3 + "satisfy(NoOverlap(origins=[(x[i], y[i]) for i in range(3)], lengths=[(1, 1)] * 3))"
    check(run, solver, code, DXY3, lambda *t: len(set(boxes(t, 3))) == 3)


# ---------------------------------------------------------------------------------------------------- three dimensions

XYZ = arrays(("x", 3, "range(2)"), ("y", 3, "range(2)"), ("z", 3, "range(2)"))
DXYZ = [range(2)] * 9


def boxes3(t, n):
    return [(t[i], t[n + i], t[2 * n + i]) for i in range(n)]


def test_nooverlap_3d(run, solver):
    lengths = [(1, 1, 2), (1, 2, 1), (2, 1, 1)]
    code = XYZ + f"satisfy(NoOverlap(origins=[(x[i], y[i], z[i]) for i in range(3)], lengths={lengths}))"
    check(run, solver, code, DXYZ, lambda *t: no_overlap(boxes3(t, 3), lengths))


@bug(TRANSPOSED)
def test_nooverlap_3d_with_two_boxes(run, solver):
    code = arrays(("x", 2, "range(2)"), ("y", 2, "range(2)"), ("z", 2, "range(2)"))
    code += "satisfy(NoOverlap(origins=[(x[i], y[i], z[i]) for i in range(2)], lengths=[(1, 1, 2), (2, 1, 1)]))"
    check(run, solver, code, [range(2)] * 6, lambda *t: no_overlap(boxes3(t, 2), [(1, 1, 2), (2, 1, 1)]))


@bug(INTEGER_ORIGINS_3D)
def test_nooverlap_3d_with_an_integer_origin(run, solver):
    lengths = [(1, 1, 2), (1, 2, 1), (2, 1, 1)]
    code = XYZ + f"satisfy(NoOverlap(origins=[(x[0], y[0], 0), (x[1], y[1], z[1]), (x[2], y[2], z[2])], lengths={lengths}))"
    check(run, solver, code, DXYZ, lambda *t: no_overlap([(t[0], t[3], 0), (t[1], t[4], t[7]), (t[2], t[5], t[8])], lengths))


def test_nooverlap_3d_with_variable_lengths(run, solver):
    code = arrays(("x", 2, "range(2)"), ("y", 2, "range(2)"), ("z", 2, "range(2)"), ("w", 6, "range(1, 3)"))
    code += "satisfy(NoOverlap(origins=[(x[0], y[0], z[0]), (x[1], y[1], z[1])], lengths=[(w[0], w[1], w[2]), (w[3], w[4], w[5])]))"
    check(run, solver, code, [range(2)] * 6 + [range(1, 3)] * 6,
          lambda *t: no_overlap([(t[0], t[2], t[4]), (t[1], t[3], t[5])], [t[6:9], t[9:12]]))


def test_nooverlap_3d_with_variable_and_fixed_lengths(run, solver):
    code = arrays(("x", 2, "range(2)"), ("y", 2, "range(2)"), ("z", 2, "range(2)"), ("w", 2, "range(3)"))
    code += "satisfy(NoOverlap(origins=[(x[0], y[0], z[0]), (x[1], y[1], z[1]), (z[0], z[1], x[0])], lengths=[(w[0], 1, 1), (1, w[1], 1), (1, 1, 1)]))"
    check(run, solver, code, [range(2)] * 6 + [range(3)] * 2,
          lambda *t: no_overlap([(t[0], t[2], t[4]), (t[1], t[3], t[5]), (t[4], t[5], t[0])], [(t[6], 1, 1), (1, t[7], 1), (1, 1, 1)]))


# ------------------------------------------------------------------------------------------------ examples of the doc

def test_nooverlap_example_scheduling(run, solver):
    # the first example of the documentation, with the solution given there
    code = "s = VarArray(size=4, dom=range(20))\nsatisfy(NoOverlap(origins=s, lengths=[3, 5, 2, 4]), s[0] == 0, s[1] == 3, s[2] == 8)"
    check(run, solver, code, [range(20)] * 4, lambda *t: no_overlap1(t, [3, 5, 2, 4]) and t[:3] == (0, 3, 8))


def test_nooverlap_example_packing(run, solver):
    # the second example of the documentation, with the solution given there for x
    code = """
        widths, heights = [4, 3, 5], [2, 6, 3]
        x = VarArray(size=3, dom=range(10))
        y = VarArray(size=3, dom=range(10))

        satisfy(
           NoOverlap(origins=[(x[i], y[i]) for i in range(3)], lengths=[(widths[i], heights[i]) for i in range(3)]),

           [(x[i] + widths[i] <= 10, y[i] + heights[i] <= 10) for i in range(3)],
           x == [1, 7, 0], y[0] == 2, y[1] == 4
        )
    """
    r = check(run, solver, code, [[1], [7], [0], [2], [4], range(10)],
              lambda *t: no_overlap(boxes(t, 3), [(4, 2), (3, 6), (5, 3)]) and t[5] + 3 <= 10)
    assert (1, 7, 0, 2, 4, 5) in r.solutions, r.report()


def test_nooverlap_example_zero_ignored(run, solver):
    # the third example of the documentation
    code = "s = VarArray(size=3, dom=range(10))\nsatisfy(NoOverlap(origins=s, lengths=[2, 0, 3], zero_ignored=False))"
    check(run, solver, code, [range(10)] * 3, lambda *t: no_overlap1(t, [2, 0, 3], False))


# ---------------------------------------------------------------------------------------------------------- groups

def test_nooverlap_on_the_rows_of_a_matrix(run, solver):
    code = "m = VarArray(size=[2, 3], dom=range(4))\nsatisfy(NoOverlap(origins=m[i], lengths=[1, 2, 1]) for i in range(2))"
    check(run, solver, code, [range(4)] * 6, lambda *t: no_overlap1(t[:3], [1, 2, 1]) and no_overlap1(t[3:], [1, 2, 1]))


def test_nooverlap_with_other_constraints(run, solver):
    check(run, solver, X3 + "satisfy(NoOverlap(origins=x, lengths=[1, 2, 2]), x[0] < x[1], x[2] != 0)", D3,
          lambda *t: no_overlap1(t, [1, 2, 2]) and t[0] < t[1] and t[2] != 0)


def test_nooverlaps_sharing_variables(run, solver):
    code = X3 + "satisfy(NoOverlap(origins=x[:2], lengths=[2, 2]), NoOverlap(origins=x[1:], lengths=[1, 3]))"
    check(run, solver, code, D3, lambda *t: no_overlap1(t[:2], [2, 2]) and no_overlap1(t[1:], [1, 3]))


def test_nooverlap_1d_and_2d(run, solver):
    code = XY2 + "satisfy(NoOverlap(origins=x, lengths=[1, 1]), NoOverlap(origins=[(x[0], y[0]), (x[1], y[1])], lengths=[(2, 1), (1, 2)]))"
    check(run, solver, code, DXY2, lambda *t: t[0] != t[1] and no_overlap(boxes(t, 2), [(2, 1), (1, 2)]))


# ------------------------------------------------------------------------------------------------ logical contexts

@pytest.mark.parametrize("constraint", ["~NoOverlap(origins=x, lengths=[1, 2, 2])", "NoOverlap(origins=x, lengths=[1, 2, 2]) | (z == 1)",
                                        "NoOverlap(origins=x, lengths=[1, 2, 2]) & (z == 1)", "imply(z == 1, NoOverlap(origins=x, lengths=[1, 2, 2]))",
                                        "iff(z == 1, NoOverlap(origins=x, lengths=[1, 2, 2]))", "NoOverlap(origins=x, lengths=[1, 2, 2]) == 1",
                                        "If(z == 1, Then=NoOverlap(origins=x, lengths=[1, 2, 2]))",
                                        "NoOverlap(origins=[(x[0], x[1]), (x[2], z)], lengths=[(1, 1), (1, 1)]) | (z == 1)"])
def test_nooverlap_in_logical_expressions(run, constraint):
    # a constraint noOverlap cannot be reified: an explicit error is raised
    r = run(X3 + f"z = Var(dom=range(3))\nsatisfy({constraint})")
    assert_fails(r)
    assert "A constraint noOverlap cannot be in a logical expression" in r.stderr + r.stdout, r.report()


def test_nooverlap_with_unit_lengths_in_a_logical_expression(run, solver):
    # posted as allDifferent, which can be in a logical expression
    code = X3 + "z = Var(dom=range(2))\nsatisfy(NoOverlap(origins=x, lengths=[1, 1, 1]) | (z == 1))"
    check(run, solver, code, D3 + [range(2)], lambda *t: len(set(t[:3])) == 3 or t[3] == 1)


@pytest.mark.parametrize("constraint", [
    "NoOverlap(origins=x, lengths=[1, 2, 2]) | (z == 1)",
    pytest.param("~NoOverlap(origins=x, lengths=[1, 2, 2])", marks=bug(META_NEGATION)),
], ids=["disjunction", "negation"])
def test_nooverlap_in_logical_expressions_with_use_meta(run, constraint):
    # with the option -use_meta, a meta-constraint is built
    r = run(X3 + f"z = Var(dom=range(3))\nsatisfy({constraint})", args=["-use_meta"])
    assert r.ok, r.report()
    assert r.xml.find(".//noOverlap") is not None, r.report()


@pytest.mark.parametrize("constraint", ["NoOverlap(origins=x, lengths=[1, 2, 2]) in {0, 1}", "NoOverlap(origins=x, lengths=[1, 2, 2]) <= 1"])
def test_nooverlap_with_a_condition(run, constraint):
    # NoOverlap is not a partial constraint: an explicit error is raised
    assert_fails(run(X3 + f"satisfy({constraint})"))


# ------------------------------------------------------------------------------------------------------- option -mini

@pytest.mark.parametrize("lengths", [[1, 2, 2], [3, 1, 1], [1, 1, 1]])
def test_nooverlap_mini(run, solver, lengths):
    # with -mini, binary tables are posted
    r = check(run, solver, X3 + f"satisfy(NoOverlap(origins=x, lengths={lengths}))", D3, lambda *t: no_overlap1(t, lengths), args=["-mini"])
    assert r.xml.find("constraints//noOverlap") is None and r.xml.find("constraints//allDifferent") is None, r.report()


def test_nooverlap_mini_with_expressions(run, solver):
    check(run, solver, X3 + "satisfy(NoOverlap(origins=[x[0] + 1, x[1], x[2]], lengths=[1, 2, 1]))", D3,
          lambda *t: no_overlap1((t[0] + 1, t[1], t[2]), [1, 2, 1]), args=["-mini"])


@pytest.mark.parametrize("lengths", [[0, 2, 1], [0, 0, 2]])
def test_nooverlap_mini_with_zero_lengths(run, solver, request, lengths):
    request.applymarker(bug(MINI_ZERO))
    check(run, solver, X3 + f"satisfy(NoOverlap(origins=x, lengths={lengths}))", D3, lambda *t: no_overlap1(t, lengths), args=["-mini"])


@bug(MINI_ZERO_IGNORED)
def test_nooverlap_mini_with_zero_ignored_false(run, solver):
    check(run, solver, X3 + "satisfy(NoOverlap(origins=x, lengths=[0, 2, 1], zero_ignored=False))", D3,
          lambda *t: no_overlap1(t, [0, 2, 1], False), args=["-mini"])


@bug(MINI_VARIABLE_LENGTHS)
def test_nooverlap_mini_with_variable_lengths(run, solver):
    check(run, solver, XL + "satisfy(NoOverlap(origins=x, lengths=l))", DXL, lambda *t: no_overlap1(t[:3], t[3:]), args=["-mini"])


@bug(MINI_2D)
def test_nooverlap_mini_2d(run, solver):
    code = XY3 + "satisfy(NoOverlap(origins=[(x[i], y[i]) for i in range(3)], lengths=[(1, 2), (2, 1), (1, 1)]))"
    check(run, solver, code, DXY3, lambda *t: no_overlap(boxes(t, 3), L2), args=["-mini"])


# ----------------------------------------------------------------------------------------------------- XCSP3 files

def _text(e):
    return " ".join(e.text.split()) if e is not None and e.text else None


@pytest.mark.parametrize("constraint, origins, lengths", [
    ("NoOverlap(origins=x, lengths=[1, 2, 3])", "x[]", "1 2 3"),
    ("NoOverlap(origins=x, lengths=2)", "x[]", "2x3"),
    ("NoOverlap(origins=x[:2], lengths=[2, 3])", "x[0] x[1]", "2 3"),
    ("NoOverlap(tasks=[(x[2], 1), (x[0], 2)])", "x[2] x[0]", "1 2"),
    ("NoOverlap(origins=x, lengths=l)", "x[]", "l[]"),
    ("NoOverlap(origins=x, lengths=[0, 1, 1])", "x[]", "0 1 1"),
    ("NoOverlap(origins=[(x[i], y[i]) for i in range(3)], lengths=[(1, 2), (2, 1), (1, 1)])", "(x[0],y[0])(x[1],y[1])(x[2],y[2])", "(1,2)(2,1)(1,1)"),
    ("NoOverlap(origins=[x, y], lengths=[[1, 2, 1], [2, 1, 1]])", "(x[0],y[0])(x[1],y[1])(x[2],y[2])", "(1,2)(2,1)(1,1)"),
    ("NoOverlap(origins=[(x[i], y[i]) for i in range(2)], lengths=[(l[0], 2), (l[1], 1)])", "(x[0],y[0])(x[1],y[1])", "(l[0],2)(l[1],1)"),
])
def test_xcsp3_nooverlap(run, constraint, origins, lengths):
    r = run(XY3 + arrays(("l", 3, "range(3)")) + f"satisfy({constraint})")
    assert r.ok, r.report()
    c = r.xml.find("constraints/noOverlap")
    assert c is not None, r.report()
    assert (_text(c.find("origins")), _text(c.find("lengths")), c.get("zeroIgnored")) == (origins, lengths, None), r.report()


@pytest.mark.parametrize("zero_ignored, expected", [("True", None), ("False", "false")])
def test_xcsp3_nooverlap_zero_ignored(run, zero_ignored, expected):
    r = run(X3 + f"satisfy(NoOverlap(origins=x, lengths=[1, 2, 3], zero_ignored={zero_ignored}))")
    assert r.ok, r.report()
    assert r.xml.find("constraints/noOverlap").get("zeroIgnored") == expected, r.report()


def test_xcsp3_nooverlap_mixed_lengths(run):
    # in one dimension, XCSP3 accepts integers and variables in the lengths: PyCSP3 replaces the integers by auxiliary variables
    r = run(XL + "satisfy(NoOverlap(origins=x, lengths=[l[0], 2, 1]))")
    assert r.ok, r.report()
    assert _text(r.xml.find("constraints/noOverlap/lengths")) == "l[0] aux_gb[0] aux_gb[1]", r.report()


def test_xcsp3_nooverlap_2d_integer_origin(run):
    # in two dimensions, the origins must be variables: an integer is replaced by an auxiliary variable
    r = run(XY2 + "satisfy(NoOverlap(origins=[(x[0], 1), (x[1], y[1])], lengths=[(1, 2), (2, 1)]))")
    assert r.ok, r.report()
    assert _text(r.xml.find("constraints/noOverlap/origins")) == "(x[0],aux_gb[0])(x[1],y[1])", r.report()


@pytest.mark.parametrize("lengths", ["[True, 2, 1]", "[(True, 1), (1, 1), (1, 1)]"], ids=["1D", "2D"])
@bug(BOOLEAN)
def test_xcsp3_nooverlap_with_a_boolean_length(run, lengths):
    # a Boolean is not an integer for XCSP3: either it is refused, or it is written 1
    origins = "x" if "(" not in lengths else "[(x[i], y[i]) for i in range(3)]"
    r = run(XY3 + f"satisfy(NoOverlap(origins={origins}, lengths={lengths}))")
    assert not r.ok or "True" not in _text(r.xml.find("constraints/noOverlap/lengths")), r.report()


# ------------------------------------------------------------------------------------------- degenerated cases

@pytest.mark.parametrize("arguments, n", [("tasks=[(x[0], 1)]", 1), ("tasks=[]", 0), ("origins=x[:1], lengths=[1]", 1),
                                          ("origins=[], lengths=[]", 0)])
def test_nooverlap_with_less_than_two_tasks(run, request, arguments, n):
    # no constraint, with a warning
    if "origins" in arguments:
        request.applymarker(bug(LESS_THAN_TWO))
    r = run(X3 + f"satisfy(NoOverlap({arguments}), x[0] == 1)")
    assert r.ok, r.report()
    assert r.xml.find("constraints//noOverlap") is None, r.report()
    assert f"A constraint NoOverlap discarded because defined with {n} task" in r.stdout + r.stderr, r.report()


@bug(LESS_THAN_TWO)
def test_nooverlap_with_a_single_box(run):
    # XCSP3 requires at least two boxes
    r = run(XY2 + "satisfy(NoOverlap(origins=[(x[0], y[0])], lengths=[(1, 1)]), x[0] == 1)")
    assert r.ok, r.report()
    assert r.xml.find("constraints//noOverlap") is None, r.report()


# --------------------------------------------------------------------------------------------------- invalid cases

INVALID_CASES = [
    ("origins=x, lengths=[1, 2]", "#327"),  # sizes
    ("origins=x[:2], lengths=[1, 2, 3]", "#327"),
    ("origins=[(x[i], y[i]) for i in range(3)], lengths=[(1, 1), (1, 1)]", "#327"),
    ("origins=[(x[i], y[i]) for i in range(3)], lengths=2", "#328"),  # dimensions
    ("origins=[(x[i], y[i]) for i in range(3)], lengths=(1, 2)", "#328"),
    ("origins=[(x[i], y[i]) for i in range(3)], lengths=[1, 2, 1]", "#328"),
    ("origins=[(x[i], y[i]) for i in range(2)], lengths=[(1, 1, 1), (1, 1)]", "#328"),
    ("origins=[(x[0], y[0]), x[1]], lengths=[(1, 1), 2]", "#328"),
    ("origins=[(x[0],), (x[1],)], lengths=[(1,), (1,)]", "#328"),
    ("origins=m, lengths=[1, 2, 1, 1]", "#328"),  # the rows of the matrix are boxes
    ("origins=x, lengths=None", "#333"),  # missing or invalid arguments
    ("origins=None, lengths=[1, 2, 3]", "#333"),
    ("", "#333"),
    ("tasks=[(x[0], 1), (x[1], 2)], origins=x", "#333"),
    ("tasks=[(x[0], 1), (x[1],)]", "#333"),
    ("tasks=[(x[0], 1), x[1]]", "#333"),
    ("tasks=[(x[0], 1), (x[1], 2, 3)]", "#333"),
    ("[Task(origin=x[i], length=2, height=1) for i in range(3)]", "#333"),
    ("origins=x, lengths=[1.5, 2, 1]", None),
    ("origins=x, lengths=['a', 2, 1]", None),
    ("origins=x, lengths=[1, 2, 1], zero_ignored=None", "#332"),
    ("origins=x, lengths=[1, 2, 1], zero_ignored='no'", "#332"),
    ("origins=x, lengths=[1, 2, 1], zero_ignored=0", "#332"),
    ("origins=x, lengths=[-1, 2, 1]", "#340"),
]
MARKS = {"#327": SIZES, "#328": DIMENSIONS, "#332": ZERO_IGNORED, "#333": INVALID, "#340": NEGATIVE}


@pytest.mark.parametrize("arguments", [pytest.param(a, marks=bug(MARKS[p]) if p else ()) for a, p in INVALID_CASES])
def test_invalid_nooverlap(run, arguments):
    code = XY3 + "m = VarArray(size=[2, 2], dom=range(3))\n"
    assert_fails(run(code + f"satisfy(NoOverlap({arguments}))"))


def test_nooverlap_on_symbolic_variables(run, solver):
    pytest.skip(SYMBOLIC)
