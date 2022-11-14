def read_new_file(FILE):
    ruta = '../data/inputs' + FILE
    file = open(ruta, 'r')
    lines = file.readlines()
    env_var = treat_vars(lines[1])
    sys_var = treat_vars(lines[3])
    assumptions, init_env, j = ass_and_gua(lines, 6)
    guarantees, init_sys, i = ass_and_gua(lines, j+1)
    return env_var, sys_var, init_env, init_sys, assumptions, guarantees


def treat_vars(string):
    string = string[:-1]
    v = string.split(",")
    return v


def ass_and_gua(lines, i):
    a_or_g = []
    init_cond = []
    white = False
    while not white and i < len(lines):
        e = lines[i][:-1]
        if e == "":
            white = True
        elif e[:2] == 'G(':
            el = e.replace("~", "!")
            el = el[2:]
            el = el[:-1]
            a_or_g.append(el)
        else:
            el = e.replace("~", "!")
            init_cond.append(el)
        i += 1
    return a_or_g, init_cond, i
