import os

from scripts.general import full_process, flatt_list, __delete_var
from scripts.generate import req_to_string
from scripts.iannopollo import call_aalta_var_list


def check_what_is_wrong(formula, variables):
    # Formula to check which variables are incorrect
    for v in variables:
        n_f = formula + '-> ' + str(v)
        aalta_res, model = call_aalta_var_list('expression.dimacs', n_f)

def check_if_correct(formula, orig_f, env_vars):
    # Checks if the formula obtained is correct having a parcial formula, the original and the
    # environment variables.
    prob_vars_e = 'G('
    prob_vars = []
    for v in env_vars:
        ad = '& G(' + v + ')'
        f = formula + ad
        aalta_res, model = call_aalta_var_list('expression.dimacs', f)
        if aalta_res == 'unsat':
            f1 = orig_f + ad
            aalta_res, model = call_aalta_var_list('expression.dimacs', f1)
            if aalta_res == 'sat':
                prob_vars_e += v + ' & '
                prob_vars.append(v)
    if prob_vars:
        f2 = orig_f + prob_vars_e[:-3] + ')'
        aalta_res, model = call_aalta_var_list('expression.dimacs', f1)
        if aalta_res == 'sat':
            # Dar los valores del modelo para simplificarlo.
            # Preguntar a montse que hay que hacer algo para sacar el Eventually o el Always y meter
            # hacia abajo los Next.

def get_new_formula2(var_tree, selected_vars, env_vars):
    # Deletes the other variables that are not correct in that formula.
    original_formula = req_to_string(var_tree)
    for s in selected_vars:
        var_tree = __delete_var(var_tree, selected_vars)
    formula = req_to_string(var_tree)
    check_if_correct(formula, original_formula, env_vars)
    return var_tree


def get_the_partition2(formula, var_tree, env_vars, sys_vars, var_groups, is_nusmv):
    f = []
    for i in range(len(var_groups)):
        if i == 0:
            selected_vars = flatt_list(var_groups[i + 1:])
        elif i == len(var_groups) - 1:
            selected_vars = flatt_list(var_groups[:len(var_groups) - 1])
        else:
            selected_vars = flatt_list(var_groups[:i] + var_groups[i + 1:])
        f_i = get_new_formula2(var_tree, selected_vars, env_vars)
        f.append(f_i)
    return f
def principal():
    os.system("python3 general.py -f ../files/form.txt")


if __name__ == '__main__':
    principal()
