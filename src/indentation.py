
import re

from .errors import PyxellError


def transform_indented_code(code):
    """
    Adds braces and semicolons to the code with indents.
    """
    lines = code.split('\n')
    indents = ['']
    new_block = False

    for i in range(len(lines)):
        line = lines[i]
        match = re.match(r'(\s*)(\S+)', line)
        if not match or match.group(2).startswith('--'):
            # Skip line with comment or whitespace only.
            continue
        indent = match.group(1)
        prev_indent = indents[-1]

        if new_block:
            if not (indent.startswith(prev_indent) and len(indent) > len(indents[-1])):
                # New block must be indented more than the previous one.
                raise PyxellError(PyxellError.InvalidIndentation(), i+1)
            indents.append(indent)
            new_block = False
        else:
            while indents:
                if indent == indents[-1]:
                    break
                elif indents[-1].startswith(indent):
                    lines[i-1] += '}'
                    indents.pop()
                else:
                    raise PyxellError(PyxellError.InvalidIndentation(), i+1)

        if re.search(r'\W(do|def)\s*(--.*)?$', line):
            lines[i] += '\r{'
            new_block = True
        else:
            lines[i] += '\r;'

    indents.pop()
    lines[-1] += '}' * len(indents)

    return '\n'.join(lines)
