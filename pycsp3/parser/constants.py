DELIMITER_WHITESPACE = "\s+"
DELIMITER_COMMA = "\s*,\s*"
DELIMITER_TWO_DOTS = "\.\."

# A regex for denoting delimiters used in lists (elements separated by commas and surrounded by parentheses) */
DELIMITER_LISTS = "\s*\)\s*\(\s*|\s*\(\s*|\s*\)\s*"

# A regex for denoting delimiters used in sets (elements separated by a comma and surrounded by brace brackets) */
DELIMITER_SETS = "\s*\}\s*\{\s*|\s*\{\s*|\s*\}\s*"

VALID_IDENTIFIER = "[a-zA-Z][_a-zA-Z0-9\[\]]*"

ID = "id"
CLASS = "class"
AS = "as"

VAR = "var"
ARRAY = "array"
DOMAIN = "domain"
SIZE = "size"
TYPE = "type"
OTHERS = "others"
FOR = "for"

GROUP, BLOCK = "group", "block"

INTENSION = "intension"
MATRIX = "matrix"
INDEX = "index"

COEFFS = "coeffs"
OFFSET = "offset"
COLLECT = "collect"
CIRCULAR = "circular"
RANK = "rank"
COVERED = "covered"
CLOSED = "closed"
START_INDEX = "startIndex"
START_ROW_INDEX = "startRowIndex"
START_COL_INDEX = "startColIndex"
ZERO_IGNORED = "zeroIgnored"

STARRED, UNCLEANED = "starred", "uncleaned"

MINIMIZE, MAXIMIZE = "minimize", "maximize"

DECISION = "decision"
VAL_HEURISTIC = "valHeuristic"
STATIC = "static"
ORDER = "order"
