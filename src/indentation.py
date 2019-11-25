
import re

from .errors import PyxellError


def transform_indented_code(code):
    """
    Adds braces and semicolons to the code with indents.
    """
    lines = code.split('\n')
    j = None
    indents = ['']
    new_block = False

    for i in range(len(lines)):
        line = lines[i]
        match = re.match(r'(\s*)(\S+)', line)
        if not match or match.group(2).startswith('--'):
            # Skip line with comment or whitespace only.
            continue
        indent = match.group(1)

        if new_block:
            if not (indent.startswith(indents[-1]) and len(indent) > len(indents[-1])):
                # New block must be indented more than the previous one.
                raise PyxellError(PyxellError.InvalidIndentation(), i+1)
            indents.append(indent)
            new_block = False
        elif indents[-1].startswith(indent):
            # If the line is indented less than the current block, close the previous blocks.
            while indents:
                if indent == indents[-1]:
                    break
                elif indents[-1].startswith(indent):
                    # Add a closing bracket to the last non-empty line.
                    lines[j] += '}'
                    indents.pop()
                else:
                    # Indentation must match one of the previous blocks.
                    raise PyxellError(PyxellError.InvalidIndentation(), i+1)

        if re.search(r'[^\w\'](do|def)\s*(--.*)?$', line):
            # If the line ends with a `do` or `def` keyword, start a new block.
            lines[i] += '\r{'
            new_block = True
        elif len(lines) == i+1 or not re.match(fr'{indents[-1]}\s', lines[i+1]):
            # If the next line has a bigger indentation than the current block, assume it is a continuation of the expression.
            # Otherwise, put a semicolon at the end of this line.
            lines[i] += '\r;'

        j = i

    indents.pop()
    lines[-1] += '}' * len(indents)

    return '\n'.join(lines)
