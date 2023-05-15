import os

from scripts.classes import BVarI
from scripts.general import full_process, flatt_list, __delete_var, __get_var_value_propositional, __sink_negations, \
    __simplify_tree
from scripts.generate import req_to_string
from scripts.iannopollo import call_aalta_var_list


def check_what_is_wrong(formula, variables):
    # Formula to check which variables are incorrect
    for v in variables:
        n_f = formula + '-> ' + str(v)
        aalta_res, model = call_aalta_var_list('expression.dimacs', n_f)


def simplify_temporal(var_tree, orig_f, model, prob_vars, env_vars, selected_vars):
    # Pasar la formula a NNF
    nnf_tree = __sink_negations(var_tree)
    # Dar los valores correspondientes a las variables
    nnf_tree_substituted = __change_values_tree_temporal(nnf_tree, model, prob_vars, env_vars, selected_vars, 0, False)
    # Simplificar una vez tienes los valores
    nnf_nt = __simplify_tree(nnf_tree_substituted)
    return nnf_nt


def __get_var_value_temporal(variable, model, sel_vars, prob_vars, s0, alwy, pos=True):
    # Pos is False if there is a negation before the variable in the formula
    if variable in sel_vars:
        # Dar los valores de la variable correspondiente en el modelo.
        return __change_value_in(variable, alwy, model, s0, True)
    else:
        vv = BVarI(variable, True)
        # Aqui se podría checkear de alguna manera que fuera una env_var si es cierto que solo tenemos
        # que checkear las variables del entorno.
        for bb in prob_vars:
            if bb == vv:
                if vv.eq_value(bb):
                    return __change_value_in(variable, model, s0, False, pos, True)
                else:
                    return __change_value_in(variable, model, s0, False, pos, False)
        return variable


def __change_value_in(variable, alwy, model, s0, is_sel_var, pos=True, prob_var_value=True):
    # prob_var_value is True is because: in fi & G(pe) pe is True
    # prob_var_value is False i.e fi & G(!pe)
    if alwy:
        out = False
        i = 0
        while not out:
            state = model[i]
            next = state[1]
            if s0 == 0:
                out = True
                if is_sel_var:
                    return __get_var_value_propositional(variable, model)
                else:
                    if pos and prob_var_value:
                        return 'True'
                    elif not pos and not prob_var_value:
                        return 'False'
                    else:
                        return variable
            i = next
            s0 -= 1


def __change_values_tree_temporal(tree, model, prob_vars, env_vars, sel_vars, s0, alwy):
    # Changes the values of a temporal expression according to the prob_vars and the sel_vars (selected variables)
    if not (type(tree) == str):
        if len(tree) == 2:
            if tree[0] == 'G':
                return [tree[0], __change_values_tree_temporal(tree[1], model, prob_vars, env_vars, sel_vars, s0, True)]
            elif tree[0] == 'X':
                s0 += 1
                return [tree[0], __change_values_tree_temporal(tree[1], model, prob_vars, env_vars, sel_vars, s0, alwy)]
            else:
                # Falta tener en cuenta el eventually
                return [tree[0], __get_var_value_temporal(tree, model, sel_vars, prob_vars, s0, alwy, False)]
        elif len(tree) == 3:
            return [tree[0], __change_values_tree_temporal(tree[1], model, prob_vars, env_vars, sel_vars, s0, alwy),
                    __change_values_tree_temporal(tree[2], model, prob_vars, env_vars, sel_vars, s0, alwy)]
        else:
            # No se en que caso se da esto pero por si acaso
            return [__change_values_tree_temporal(tree[0], model, prob_vars, env_vars, sel_vars, s0, alwy)]
    else:
        # Sel_vars tiene todas las variables que hay que modificar que no son del grupo de descomposicion
        # En este caso sabes que el valor de tree es True, porque si fuese con una negacion, lo tratarias antes.
        return __get_var_value_temporal(tree, model, sel_vars, prob_vars, s0, alwy)


def check_if_correct(var_tree, formula, orig_f, env_vars, selected_vars):
    # Checks if the formula obtained is correct having a parcial formula, the original and the
    # environment variables.
    prob_vars_e = 'G('
    prob_vars = []
    for v in env_vars:
        # formula & G(v). If there is a problem is added to prob_vars and prob_vars_expression
        positive = correct_variable(formula, orig_f, v, prob_vars, prob_vars_e, True)
        # If it is ok, must check the negation of v. If there was already a problem you do not need to.
        if not positive:
            # formula & G(!v). If there is a problem is added to prob_vars and prob_vars_expression
            correct_variable(formula, orig_f, v, prob_vars, prob_vars_e, False)
    if prob_vars:
        # Asking for a model in which one or more env_vars has/have problems.
        f2 = orig_f + prob_vars_e[:-3] + ')'
        aalta_res, model = call_aalta_var_list('expression.dimacs', f2)
        if aalta_res == 'sat':
            # The formula is not good, must be examined and modified.
            new_form = simplify_temporal(var_tree, orig_f, model, prob_vars, env_vars, selected_vars)
            return new_form
        else:
            raise Exception('Hay problemas con la idea que tenemos.')
    return formula


def correct_variable(formula, orig_f, v, prob_vars, prob_vars_e, value):
    positive = False
    if value:
        ad = '& G(' + v + ')'
    else:
        ad = '& G(!' + v + ')'
    f = formula + ad
    aalta_res, model = call_aalta_var_list('expression.dimacs', f)
    if aalta_res == 'unsat':
        f1 = orig_f + ad
        aalta_res, model = call_aalta_var_list('expression.dimacs', f1)
        if aalta_res == 'sat':
            if value:
                prob_vars_e += v + ' & '
                vv = BVarI(v, True)
            else:
                prob_vars_e += '!' + v + ' & '
                vv = BVarI(v, False)
            prob_vars.append(vv)
            positive = True
    return positive


def get_new_formula2(var_tree, selected_vars, env_vars):
    # Deletes the other variables that are not correct in that formula.
    original_formula = req_to_string(var_tree)
    for s in selected_vars:
        var_tree = __delete_var(var_tree, selected_vars)
    formula = req_to_string(var_tree)
    check_if_correct(var_tree, formula, original_formula, env_vars, selected_vars)
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
