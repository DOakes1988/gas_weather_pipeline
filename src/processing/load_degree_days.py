import urllib
from urllib.request import urlopen

def parse_unknown_fixed_width(f_url):
    # 1. Download and decode the file content into lines
    with urllib.request.urlopen(f_url) as response:
        lines = [f_line.decode('utf-8').rstrip('\r\n') for f_line in response]

    if not lines:
        return []

    # Filter out completely empty lines
    lines = [l for l in lines if l.strip()]
    max_len = max(len(l) for l in lines)

    # 2. Track which character positions are strictly whitespace across ALL rows
    # Initialize a list tracking if a position is a space character
    space_mask = [True] * max_len

    for f_line in lines:
        for j in range(max_len):
            if j < len(f_line):
                if f_line[j] != ' ':
                    space_mask[j] = False
            # If the line is shorter than max_len, the trailing area is implicitly space

    # 3. Convert the space mask into column slice indices
    # We find where a text block starts and where it ends
    col_indices = []
    in_column = False
    start_idx = 0

    for j, is_space in enumerate(space_mask):
        if not is_space and not in_column:
            # Found the start of a data column
            start_idx = j
            in_column = True
        elif is_space and in_column:
            # Found a vertical gap of whitespace
            col_indices.append((start_idx, j))
            in_column = False

    # Catch the last column if it goes to the end of the line
    if in_column:
        col_indices.append((start_idx, max_len))

    # 4. Extract the data using the discovered slice coordinates
    f_parsed_data = []
    for f_line in lines:
        row = []
        for start, end in col_indices:
            # Slice the string and strip trailing/leading padding spaces
            field = f_line[start:end].strip()
            row.append(field)
        f_parsed_data.append(row)

    return f_parsed_data