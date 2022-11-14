from scripts.classes import BVarI


def parse_aalta(file_text):
    file = open(file_text, 'r')
    distintic_vars = []
    fin = True
    i = 0
    while fin:
        line = file.readline()
        if not line:
            fin = False
        else:
            if i == 1:
                if line[:-1] == 'unsat':
                    return 'unsat', []
            elif i > 1:
                var_s = treat_line(line)
                if var_s:
                    distintic_vars.extend(var_s)
        i += 1
    return 'sat', distintic_vars


def treat_line(line):
    if line[0] == '{':
        l = line[1:-3]
        variables = l.split(sep=',')
        v_list = n_same_vars(variables)
        return v_list
    else:
        return []


def n_same_vars(variables):
    ret = []
    for i in range(len(variables)):
        var1 = variables[i]
        v1 = know_false_name(var1)
        v1_name = v1.get_name()
        b2 = True
        j = i+1
        while j < len(variables) and b2:
            var2 = variables[j]
            v2 = know_false_name(var2)
            v2_name = v2.get_name()
            if v1.get_value() != v2.get_value():
                if v1_name == v2_name[:-1]:
                    ret.append(v1_name)
                elif v2_name == v1_name[:-1]:
                    ret.append(v2_name)
            else:
                if v1_name == v2_name[:-1] or v2_name == v1_name[:-1]:
                    b2 = False
            j += 1
    return ret


def know_false_name(v):
    if v[0] == '(':
        v_name = v[3:-1]
        v1 = BVarI(v_name, False)
    else:
        v1 = BVarI(v, True)
    return v1





