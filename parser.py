import logging
logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.INFO)
import re
from collections import deque

BRANCH_SYMBOLS = {'R','L','C','D','K','V','I','B','E','F','G','H'}
WIRE_SYMBOLS = {'+','-','|','=', '.'}
GROUND_SYMBOL = '='
LABEL_SYMBOL = '.'


def merge_nodes(schematic: list[str], _node_names: dict[tuple[int, int], str], rows: int, cols: int):
    nodes: list[list[tuple[int, int, str]]] = [[], []]
    visited: list[list[bool]] = [[False for _ in range(cols)] for _ in range(rows)]
    node_idx = 1
    unlabelled_node_idx = 1
    for col in range(cols):
        for row in range(rows):
            grounded = False
            label = ''
            if schematic[row][col] not in WIRE_SYMBOLS:
                continue
            if visited[row][col]:
                continue
            queue = deque()
            queue.append((row, col))
            visited[row][col] = True
            while len(queue) > 0:
                i, j = queue.popleft()
                if not grounded and schematic[i][j] == GROUND_SYMBOL:
                    logging.debug(f'Found ground {GROUND_SYMBOL} at ({i},{j})')
                    grounded = True
                if not grounded and schematic[i][j] == LABEL_SYMBOL:
                    logging.debug(f'Found label {LABEL_SYMBOL} at ({i},{j})')
                    label = _node_names[(i, j)]
                nodes[node_idx].append((i, j, f'N{unlabelled_node_idx:03d}'))
                _node_names[(i, j)] = f'N{unlabelled_node_idx:03d}'
                logging.info(f'Visited ({i},{j}) {schematic[i][j]}')
                if i > 0 and not visited[i-1][j] and schematic[i-1][j] in WIRE_SYMBOLS: # Not first row, add UP char
                    visited[i-1][j] = True
                    queue.append((i-1, j))
                if j > 0 and not visited[i][j-1] and schematic[i][j-1] in WIRE_SYMBOLS: # Not first column, add LEFT char
                    visited[i][j-1] = True
                    queue.append((i, j-1))
                if j < cols-1 and not visited[i][j+1] and schematic[i][j+1] in WIRE_SYMBOLS: # Not last column, add RIGHT char
                    visited[i][j+1] = True
                    queue.append((i, j+1))
                if i < rows-1 and not visited[i+1][j] and schematic[i+1][j] in WIRE_SYMBOLS: # Not last row, add DOWN char
                    visited[i+1][j] = True
                    queue.append((i+1, j))
            if grounded == True:
                for coord in nodes[node_idx]:
                    x, y, l = coord
                    nodes[0].append((x, y, '0'))
                    _node_names[(x,y)] = '0'
                del nodes[node_idx]
                node_idx -= 1
                unlabelled_node_idx -= 1
            if label:
                for n in range(len(nodes[node_idx])):
                    x, y, l = nodes[node_idx][n]
                    nodes[node_idx][n] = (x, y, label) 
                    _node_names[(x, y)] = label
            else:
                unlabelled_node_idx += 1
            node_idx += 1
            nodes.append([])


comments: list[str] = []
schematic: list[str] = []
commands: list[str] = []

_node_names: dict[tuple[int, int], str] = {}
_branch_terminals: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {}
_value_defs: dict[str, str] = {}

section_idx = 0
line_number = 0
while True:
    rawline = input()
    comment_idx = rawline.find('#')
    comment_idx = len(rawline) if comment_idx == -1 else comment_idx
    cleanline = rawline[:comment_idx].rstrip()
    line_number += 1
    if cleanline == '.end':
        commands.append(cleanline)
        break
    if not cleanline:
        continue
    if cleanline == '[SCHEMATIC]' and section_idx == 0:
        section_idx = 1
        continue
    elif cleanline == '[VALUES]' and section_idx == 1:
        section_idx = 2
        rows = len(schematic)
        cols = max([len(line) for line in schematic])
        for i, line in enumerate(schematic):
            if len(line) < cols:
                schematic[i] += ' ' * (cols-len(line))
        NET_LABEL_RE = re.compile(
            r"(?<![A-Za-z0-9_.])"
            r"(?:\.[A-Za-z0-9_]+|[A-Za-z0-9_]+\.)"
            r"(?![A-Za-z0-9_.])"
        )
        HORIZONTAL_BRANCH_RE = re.compile(
            r"-(?P<branch>[A-Z][a-z0-9]*)-"
        )
        VERTICAL_BRANCH_RE = re.compile(
            r"(?<!\S)(?P<branch>[A-Z][a-z0-9_]*)(?!\S)"
        )   
        for row, line in enumerate(schematic):
            for match in NET_LABEL_RE.finditer(line):
                label = match.group()
                period_index = match.start() if label.startswith(".") else match.end() - 1
                _node_names[(row, period_index)] = label.replace('.','')
            for match in HORIZONTAL_BRANCH_RE.finditer(line):
                branch = match.group("branch")
                _branch_terminals[branch] = ((row, match.start()), (row, match.end()-1))
            for match in VERTICAL_BRANCH_RE.finditer(line):
                branch = match.group("branch")
                col = match.start("branch")
                if (row > 0 and row+1 < rows and schematic[row-1][col] == '|' and schematic[row+1][col] == '|') or (branch[0] == 'K'):
                    _branch_terminals[branch] = ((row-1, col), (row+1, col))
        merge_nodes(schematic, _node_names=_node_names, rows=rows, cols=cols)
        continue
    elif cleanline == '[COMMANDS]' and section_idx == 2:
        section_idx = 3
        continue
    elif section_idx == 0:
        cleanline = '*' + cleanline
    match section_idx:
        case 0:
            comments.append(cleanline)
        case 1:
            schematic.append(cleanline)
        case 2:
            tokens = cleanline.split()
            #TODO - actual logic for branches
            branch_id = tokens[0]
            branch_symbol = branch_id[0]
            branch_values = tokens[2:]
            if branch_symbol == '.':
                commands.append(f'.param {branch_id[1:]}={branch_values[-1]}')
                continue
            if branch_symbol not in BRANCH_SYMBOLS:
                raise ValueError(f"Invalid branch symbol at line {line_number}: {branch_symbol}")
            if branch_symbol == 'V' or branch_symbol == 'I':
                if len(branch_values) == 3:
                    formatted_values = f'SIN(0 {branch_values[0]} {branch_values[1]} {branch_values[2]} 0 {branch_values[3]})'
                if len(branch_values) == 2:
                    formatted_values = f'SIN(0 {branch_values[0]} {branch_values[1]})'
                elif len(branch_values) == 1:
                    formatted_values = f'DC {branch_values[0]}'
                else:
                    formatted_values = ' '.join(branch_values)
            elif branch_symbol == 'B':
                if branch_values[-1][-1] == 'V':
                    formatted_values = 'V=' + ''.join(branch_values[:-1])
                elif branch_values[-1][-1] == 'I':
                    formatted_values = 'I=' + ''.join(branch_values[:-1])
                else:
                    raise ValueError(f"Invalid behavioral source definition at line {line_number}: {branch_values[-1][-1]}")
            elif branch_symbol == 'E': # e.g. E 8 R
                ref = branch_values[-1]
                formatted_values = f'{_node_names[_branch_terminals[ref][0]]} {_node_names[_branch_terminals[ref][1]]} {branch_values[0]}'
            elif branch_symbol == 'D':
                formatted_values = branch_id
                commands.append(f'.model {branch_id} D(Vfwd={branch_values[-1]})')
            elif branch_symbol == 'K':
                if branch_values[-1].isnumeric():
                    commands.append(f'{branch_id} {' '.join(tokens[2:])}')
                else:
                    commands.append(f'{branch_id} {' '.join(tokens[2:])} 1')
                continue
            else:
                formatted_values = ' '.join(tokens[2:])
            _value_defs[tokens[0]] = formatted_values
        case 3:
            commands.append(cleanline)


netlist: list[str] = []
for comment in comments:
    netlist.append(comment)
for branch in _branch_terminals:
    if branch[0] == 'K':
        continue
    netlist.append(f'{branch} '
          f'{_node_names[_branch_terminals[branch][0]]} {_node_names[_branch_terminals[branch][1]]} '
          f'{_value_defs[branch]}')
for command in commands:
    netlist.append(command)


print('\n'.join(netlist))