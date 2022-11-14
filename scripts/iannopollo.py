import os
import re

from itertools import combinations
from scripts.call import call_nusmv, call_nusmv_bounded, call_aalta
from scripts.generate import req_to_string_2
from scripts.readXML import parse_xml, not_same_var
from scripts.read_aalta_result import parse_aalta


def alg_iannopollo(env_vars, sys_vars, init_env, init_sys, ass, gua):
    groups = []
    treated = []
    for v in sys_vars:
        if not v in treated:
            cv = [v]
            treated.append(v)
            passed = False
            while not passed:
                ncv = not_in_v(cv, sys_vars)
                if not ncv:
                    break
                else:
                    right_f = refine_formula(ass, gua, init_env, init_sys, cv, ncv, False)
                    contraejemplo = False
                    for i in range(len(ncv) - 1, 0, -1):
                        left_f = isolate_vars(ncv, i)
                        calling_exp = "((" + left_f + ") & " + right_f[1:]
                        call_nusmv("nuxmv_file.smv", calling_exp, "counterexample")
                        if os.path.exists("../data/counterexample.xml"):
                            contraejemplo = True
                            manage_counterexample_nusmv(env_vars, cv, treated)
                            break
                    if not contraejemplo:
                        call_nusmv("nuxmv_file.smv", right_f, "counterexample")
                        if os.path.exists("../data/counterexample.xml"):
                            manage_counterexample_nusmv(env_vars, cv, treated)
                        else:
                            passed = True
            sys_vars = not_in_v(cv, sys_vars)
            groups.append(cv)
    return groups


def alg_ainnopollo_nleft(env_vars, sys_vars, init_env, init_sys, ass, gua):
    groups = []
    treated = []
    for v in sys_vars:
        if not v in treated:
            cs = [v]
            treated.append(v)
            ncs = not_in_v(cs, sys_vars)
            fi = refine_formula(ass, gua, init_env, init_sys, cs, ncs, True)
            call_nusmv("nuxmv_file.smv", fi, "counterexample")
            if os.path.exists("../data/counterexample.xml"):
                changing_vars = obtain_vars(env_vars, cs, treated)
                look_for_dependent_variables(cs, fi, changing_vars, env_vars, treated, sys_vars, ass, gua, init_env,
                                             init_sys)
            groups.append(cs)
            sys_vars = not_in_v(cs, sys_vars)
    return groups


def alg_ainnopollo_nleft_aalta(env_vars, sys_vars, init_env, init_sys, ass, gua):
    groups = []
    treated = []
    for v in sys_vars:
        if not v in treated:
            cs = [v]
            treated.append(v)
            ncs = not_in_v(cs, sys_vars)
            if ncs:
                fi = refine_formula(ass, gua, init_env, init_sys, cs, ncs, True)
                nfi = '!(' + fi + ')'
                aalta_res, model = call_full_aalta('expression.dimacs', nfi, env_vars, cs, treated)
                if aalta_res == 'sat' and model:
                    changing_vars = model
                    look_for_dependent_variables_aalta(cs, fi, changing_vars, env_vars, treated, sys_vars, ass, gua,
                                                       init_env, init_sys)
                sys_vars = not_in_v(cs, sys_vars)
            groups.append(cs)
            print('New group ' + str(cs))
    return groups


def create_file(name, expression):
    with open(name, 'w') as f:
        f.write(expression)


def call_full_aalta(file_name, fi, var, cv, treated):
    ruta = '../files/' + file_name
    create_file(ruta, fi)
    call_aalta(file_name, 'result.txt')
    aalta_res, model = parse_aalta('../data/result.txt')
    model = list(set(model))
    l3 = [x for x in model if x not in var]
    l4 = not_in_v(cv, l3)
    l5 = not_in_v(treated, l4)
    os.remove('../data/result.txt')
    os.remove('../files/expression.dimacs')
    return aalta_res, l5


def look_for_dependent_variables(cs, fi, chang_vars, env_vars, treated, sys_vars, ass, gua, init_env, init_sys):
    cz = not_in_v(cs, chang_vars)
    z = cz[0]
    inv = " | F(" + z + " != " + z + "_)"
    nfi = fi + inv
    call_nusmv("nuxmv_file.smv", nfi, "counterexample")
    if os.path.exists("../data/counterexample.xml"):
        changing_vars = obtain_vars(env_vars, cs, treated)
        return look_for_dependent_variables(cs, nfi, changing_vars, env_vars, treated, sys_vars, ass, gua, init_env,
                                            init_sys)
    else:
        cs.append(z)
        treated.append(z)
        ncs = not_in_v(cs, sys_vars)
        if ncs:
            fffi = refine_formula(ass, gua, init_env, init_sys, cs, ncs, True)
            call_nusmv("nuxmv_file.smv", fffi, "counterexample")
            if os.path.exists("../data/counterexample.xml"):
                changing_vars = obtain_vars(env_vars, cs, treated)
                return look_for_dependent_variables(cs, fffi, changing_vars, env_vars, treated, sys_vars, ass, gua,
                                                    init_env, init_sys)
            else:
                return cs
        else:
            return cs


def look_for_dependent_variables_aalta(cs, fi, chang_vars, env_vars, treated, sys_vars, ass, gua, init_env, init_sys):
    cz = not_in_v(cs, chang_vars)
    z = cz[0]
    inv = " | F(" + z + " <-> !" + z + "_)"
    nfi = fi + inv
    nnfi = '!(' + nfi + ')'
    aalta_res, model = call_full_aalta('expression.dimacs', nnfi, env_vars, cs, treated)
    if aalta_res == 'sat' and model:
        changing_vars = model
        return look_for_dependent_variables_aalta(cs, nfi, changing_vars, env_vars, treated, sys_vars, ass, gua,
                                                  init_env,
                                                  init_sys)
    else:
        cs.append(z)
        treated.append(z)
        ncs = not_in_v(cs, sys_vars)
        if ncs:
            fffi = refine_formula(ass, gua, init_env, init_sys, cs, ncs, True)
            nfffi = '!(' + fffi + ')'
            aalta_res, model = call_full_aalta('expression.dimacs', nfffi, env_vars, cs, treated)
            if aalta_res == 'sat' and model:
                changing_vars = model
                return look_for_dependent_variables_aalta(cs, fffi, changing_vars, env_vars, treated, sys_vars, ass,
                                                          gua,
                                                          init_env, init_sys)
            else:
                return cs
        else:
            return cs


def look_for_dependent_variables_aalta_v2(cs, fi, chang_vars, env_vars, treated, sys_vars, ass, gua, init_env,
                                          init_sys):
    cz = not_in_v(cs, chang_vars)
    z = cz[0]

    inv = " | F(" + z + " <-> !" + z + "_)"
    nfi = fi + inv
    nnfi = '!(' + nfi + ')'
    aalta_res, model = call_full_aalta('expression.dimacs', nnfi, env_vars, cs, treated)
    if aalta_res == 'sat' and model:
        changing_vars = model
        return look_for_dependent_variables_aalta(cs, nfi, changing_vars, env_vars, treated, sys_vars, ass, gua,
                                                  init_env, init_sys)
    else:
        cs.append(z)
        treated.append(z)
        ncs = not_in_v(cs, sys_vars)
        if ncs:
            fffi = refine_formula(ass, gua, init_env, init_sys, cs, ncs, True)
            nfffi = '!(' + fffi + ')'
            aalta_res, model = call_full_aalta('expression.dimacs', nfffi, env_vars, cs, treated)
            if aalta_res == 'sat' and model:
                changing_vars = model
                return look_for_dependent_variables_aalta(cs, fffi, changing_vars, env_vars, treated, sys_vars, ass,
                                                          gua,
                                                          init_env, init_sys)
            else:
                return cs
        else:
            return cs


def manage_counterexample_nusmv(var, cv, treated):
    counterex = parse_xml("../data/counterexample.xml")
    os.remove("../data/counterexample.xml")
    dvars = list(set(not_same_var(counterex)))
    l3 = [x for x in dvars if x not in var]
    l4 = not_in_v(cv, l3)
    l5 = not_in_v(treated, l4)
    cv.extend(l5)
    treated.extend(l5)


def obtain_vars(var, cv, treated):
    counterex = parse_xml("../data/counterexample.xml")
    os.remove("../data/counterexample.xml")
    dvars = list(set(not_same_var(counterex)))
    l3 = [x for x in dvars if x not in var]
    l4 = not_in_v(cv, l3)
    l5 = not_in_v(treated, l4)
    return l5


def refine_formula(ass, gua, init_env, init_sys, cv, ncv, always_in):
    full_exp = ""
    contract = ""
    alpha = ""
    fi_ass1 = ""
    # FiA
    if ass:
        fi_ass1 = "("
        fi_ass1 = form_ass_or_gua(ass, fi_ass1)
        fi_ass = "G" + fi_ass1
        # Renamings of the FiA
        fi_ass_v = ""
        fi_ass_nv = ""
        for v in cv:
            fi_ass_v = renaming(fi_ass, v, "_")
        for v in ncv:
            fi_ass_nv = renaming(fi_ass, v, "_")
        # Varibales iniciales del entorno
        if init_env:
            for alp in init_env:
                alpha += alp + " & "
            alpha = "(" + alpha[:-3] + ")"
            full_exp = alpha + " & " + fi_ass + " & " + fi_ass_v + " & " + fi_ass_nv + " & "
        else:
            full_exp = fi_ass + " & " + fi_ass_v + " & " + fi_ass_nv + " & "
    # FiG
    fi_gua1 = "("
    beta = ""
    beta1 = ""
    fi_gua1 = form_ass_or_gua(gua, fi_gua1)
    fi_gua = "G" + fi_gua1
    fi_gua_v = fi_gua
    fi_gua_nv = fi_gua
    for v in cv:
        fi_gua_v = renaming(fi_gua_v, v, "_")
    for v in ncv:
        fi_gua_nv = renaming(fi_gua_nv, v, "_")
    if init_sys:
        for b in init_sys:
            # Hay que tener en cuenta que pueden tener un parentesis al final
            if b[-1] == ')':
                beta += b + " & " + b[:-1] + "_) & "
            else:
                beta += b + " & " + b + "_ & "
            beta1 += b + " & "
        beta = "(" + beta[:-3] + ")"
        beta1 = "(" + beta1[:-3] + ")"
        full_exp += beta + " & " + fi_gua_v + " & " + fi_gua_nv
    else:
        full_exp += fi_gua_v + " & " + fi_gua_nv

    if not ass:
        if not init_sys:
            contract = fi_gua
        else:
            contract = beta1 + " & " + fi_gua
    else:
        if always_in:
            c = "(G(" + fi_ass1 + ") -> G(" + fi_gua1 + "))"
        else:
            c = "G(" + fi_ass1 + " -> " + fi_gua1 + ")"
        if not init_env:
            if not init_sys:
                contract = c
            else:
                contract = beta1 + " & " + c
        else:
            if not init_sys:
                contract = alpha + " -> " + c
            else:
                contract = alpha + " -> (" + beta1 + " & " + c + ")"
    final_res = "(" + full_exp + ") -> (" + contract + ")"
    return final_res


def form_ass_or_gua(ass_or_gua, fi):
    for g in ass_or_gua:
        fi += "(" + g + ") & "
    fi = fi[:-3] + ")"
    return fi


# def refine_formula(ass, gua, init_env, init_sys, cv, ncv):
#     # Missing init ass part
#     isys_exp = ""
#     if init_sys:
#         for v in init_sys:
#             isys_exp += v + "&"
#     exp_main = isys_exp + "G(("
#     ass_text = ""
#     if ass:
#         for a in ass:
#             exp_main += "(" + a + ") & "
#         exp_main = exp_main[:-3]
#         ass_text = "G" + exp_main[2:] + ")"
#         exp_main += ") -> ("
#     for g in gua:
#         exp_main += "(" + g + ") & "
#     exp_main = exp_main[:-3]
#     exp_main += "))"
#     exp_v = exp_main
#     exp_cv = exp_main
#     for v in cv:
#         exp_v = renaming(exp_v, v, "_")
#     for v in ncv:
#         exp_cv = renaming(exp_cv, v, "_")
#     if ass_text != "":
#         final = ass_text + " & " + exp_v + " & " + exp_cv + ") -> " + exp_main
#     else:
#         final = exp_v + " & " + exp_cv + ") -> " + exp_main
#     return final


def isolate_vars(ncv, num_vars):
    combinaciones = combinations(ncv, num_vars)
    exp = ""
    for v in combinaciones:
        exp += "G(" + gen_disj(v) + ") | "
    return exp[:-3]


def gen_disj(ncv):
    res = ""
    for var in ncv:
        res += "(" + var + " = " + var + "_) & "
    return res[:-3]


def renaming(exp, w, r_struct):
    exp1 = r'([( !&|]' + w + r')([) !&|])'
    # reg_exp = re.compile(exp)
    result = re.sub(exp1, r'\1' + r_struct + r'\2', exp)
    return result


# Deletes de vars from var that are in cv
def not_in_v(cv, var):
    res = var.copy()
    for v in cv:
        enc = False
        i = 0
        while not enc and i < len(res):
            if v == res[i]:
                res.remove(res[i])
                enc = True
            i += 1
    return res


def dif_i_var(ivars, vars):
    for iv in ivars:
        encontrado1 = False
        encontrado2 = False
        i = 0
        while (not (encontrado1) or not (encontrado2)) and i < len(vars):
            v = vars[i]
            if iv == v:
                encontrado1 = True
                vars.remove(v)
            elif iv + "_" == v:
                encontrado2 = True
                vars.remove(v)
            i += 1
    return vars


def main():
    print(renaming("hola como estas", "como", "_"))
    # hola = re.sub(r'([(\s!&|]como)([\s)!&|])', r'\1_\2', "hola como estas")
    # print(hola)


if __name__ == '__main__':
    main()
