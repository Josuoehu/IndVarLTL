from classes import BVarI


def _read_result(file_path):
    with open(file_path, 'r') as result_file:
        lines = [line.strip() for line in result_file if line.strip()]

    for line in lines:
        if line == 'unsat':
            return 'unsat', lines
        if line == 'sat':
            return 'sat', lines
    raise ValueError(f"Aalta output does not contain a satisfiability result: {file_path}")


def parse_aalta(file_text):
    status, lines = _read_result(file_text)
    if status == 'unsat':
        return status, []

    distinct_vars = []
    for line in lines:
        distinct_vars.extend(treat_line(line))
    return status, distinct_vars


def parse_aalta_var_list(file_text):
    status, lines = _read_result(file_text)
    if status == 'unsat':
        return status, []

    for line in lines:
        if line.startswith('{'):
            return status, all_line_values(line)
    return status, []


def _tokens(line):
    text = line.strip()
    if not (text.startswith('{') and text.endswith('}')):
        return []
    return [token.strip() for token in text[1:-1].split(',') if token.strip()]


def treat_line(line):
    return n_same_vars(_tokens(line))


def all_line_values(line):
    return [know_false_name(value) for value in _tokens(line)]


def n_same_vars(variables):
    result = []
    parsed = [know_false_name(variable) for variable in variables]
    for index, first in enumerate(parsed):
        for second in parsed[index + 1:]:
            first_name = first.get_name()
            second_name = second.get_name()
            same_base = (
                first_name == second_name + '_'
                or second_name == first_name + '_'
            )
            if same_base and first.get_value() != second.get_value():
                base_name = first_name[:-1] if first_name.endswith('_') else first_name
                if base_name not in result:
                    result.append(base_name)
    return result


def know_false_name(value):
    token = value.strip()
    if token.startswith('(!') and token.endswith(')'):
        return BVarI(token[2:-1].strip(), False)
    if token.startswith('!'):
        return BVarI(token[1:].strip(), False)
    return BVarI(token, True)
