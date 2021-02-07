
import re

from .errors import PyxellError as err


def remove_comments(code):
    # https://stackoverflow.com/a/241506

    def replacer(match):
        s = match.group(0)
        if s.startswith('#') or s.startswith('{#'):
            return re.sub('[^\n]', ' ', s)  # to preserve error line and column indices
        else:
            return s

    pattern = re.compile(r'#.*?$|{#.*?#}|"(?:\\.|[^\\"])*"|(^|[^\w\'])\'(?:\\.|[^\\\'])*\'', re.DOTALL | re.MULTILINE)
    return re.sub(pattern, replacer, code)


def transform_indented_code(code, filepath):
    """
    Adds braces and semicolons to the code with indents.
    """
    code = remove_comments(code)
    lines = code.split('\n')  # note the difference to `splitlines()`: https://docs.python.org/3/library/stdtypes.html#str.splitlines

    j = None  # index of the previous non-empty line
    indents = ['']
    new_block = False

    for i in range(len(lines)):
        line = lines[i]
        match = re.match(r'(\s*)(\S+)', line)
        if not match:
            # Skip line with whitespace only.
            continue
        indent = match.group(1)

        if new_block:
            if len(indent) <= len(indents[-1]):
                # New block must be indented more than the previous one.
                raise err(filepath, (i+1, len(indent)+1), err.InvalidSyntax())
            indents.append(indent)
            new_block = False

        elif len(indent) <= len(indents[-1]):
            # If the line isn't indented more than the current block and doesn't start with a closing parenthesis or bracket,
            # put a semicolon at the end of the previous line.
            # Otherwise, assume it is continuation of the previous expression.
            if j is not None and not re.match(r'\s*[)\]\}]', line):
                lines[j] += ';'

            # If the line is indented less than the current block, close the previous blocks.
            while indents:
                if indent == indents[-1]:
                    break
                elif len(indent) < len(indents[-1]):
                    # Add a closing brace to the last non-empty line.
                    lines[j] += '};'
                    indents.pop()
                else:
                    # Indentation must match one of the previous blocks.
                    raise err(filepath, (i+1, len(indent)+1), err.InvalidSyntax())

        if re.search(r'[^\w\'](do|def)\s*$', line):
            # If the line ends with a `do` or `def` keyword, start a new block.
            lines[i] += '{'
            new_block = True

        j = i

    indents.pop()
    if j is not None:
        lines[-1] += ';' + '};' * len(indents)

    return lines
