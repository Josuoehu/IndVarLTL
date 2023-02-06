import os
import argparse
import stat
import time
from operator import is_

from call import call_nusmv, call_get_path
from generate_nuxmv import create_nusmv_file
from iannopollo import not_in_v, renaming
from readXML import parse_xml, not_same_var
from req_parser import parse_req_exp
from classes import BVarI


# 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
def generate_exp(fi, cs, ncs):
    fi_cs = fi
    fi_not_cs = fi
    for v in cs:
        fi_cs = renaming(fi_cs, v, "_")
    for v in ncs:
        fi_not_cs = renaming(fi_not_cs, v, "_")
    # !fi_cs || !fi_ncs || fi
    return "!(" + fi_cs + ") | !(" + fi_not_cs + ") | (" + fi + ")"


def look_for_dep_var(fi, oldfi, changing_vars, cs, treated, cv):
    # cz = not_in_v(cs, changing_vars)
    z = changing_vars[0]
    inv = " | !(" + z + " <-> " + z + "_)"
    newfi = oldfi + inv
    call_nusmv("nuxmv_file.smv", newfi, "counterexample")
    if os.path.exists("../data/counterexample.xml"):
        new_changing_vars = ob_vars(cs, treated)
        return look_for_dep_var(fi, newfi, new_changing_vars, cs, treated, cv)
    else:
        cs.append(z)
        treated.append(z)
        ncs = not_in_v(cs, cv)
        if ncs:
            other_fi = generate_exp(fi, cs, ncs)
            call_nusmv("nuxmv_file.smv", other_fi, "counterexample")
            if os.path.exists("../data/counterexample.xml"):
                changing_vars = ob_vars(cs, treated)
                return look_for_dep_var(fi, other_fi, changing_vars, cs, treated, cv)
            else:
                return cs
        else:
            return cs


def look_for_dep_var_while(fi, oldfi, changing_vars, cs, treated, cv, is_model, is_temporal):
    # cz = not_in_v(cs, changing_vars)
    newfi = oldfi
    while is_model:
        z = changing_vars[0]
        if is_temporal:
            inv = " | F(!(" + z + " <-> " + z + "_))"
        else:
            inv = " | !(" + z + " <-> " + z + "_)"
        newfi += inv
        call_nusmv("nuxmv_file.smv", newfi, "counterexample")
        if os.path.exists("../data/counterexample.xml"):
            new_changing_vars = ob_vars(cs, treated)
            changing_vars = new_changing_vars
        else:
            is_model = False
            # He cambiado esto dentro del else por la variable z
            cs.append(z)
            treated.append(z)
    ncs = not_in_v(cs, cv)
    if ncs:
        other_fi = generate_exp(fi, cs, ncs)
        call_nusmv("nuxmv_file.smv", other_fi, "counterexample")
        if os.path.exists("../data/counterexample.xml"):
            changing_vars = ob_vars(cs, treated)
            return look_for_dep_var_while(fi, other_fi, changing_vars, cs, treated, cv, True, is_temporal)
        else:
            return cs
    else:
        return cs


def partition(fi, cv):
    conjuntos =[]
    cs = []
    treated = []
    for v in cv:
        if not v in treated:
            cs = [v]
            treated.append(v)
            ncs = not_in_v(cs, cv)
            if ncs:
                newfi = generate_exp(fi, cs, ncs)
                call_nusmv("nuxmv_file.smv", newfi, "counterexample")
                if os.path.exists("../data/counterexample.xml"):
                    changing_vars = ob_vars(cs, treated)
                    cs = look_for_dep_var(fi, newfi, changing_vars, cs, treated, cv)
                cv = not_in_v(cs, cv)
            conjuntos.append(cs)
            # print("New group " + str(cs))
    return conjuntos


def partition_recursive(fi, cv, treated, is_temporal):
    if not cv:
        return []
    # elif len(cv) == 1:
    #     return [cv]
    else:
        v = cv[0]
        cs = [v]
        create_nusmv_file(treated, cv)
        treated.append(v)
        ncs = not_in_v(cs, cv)
        newfi = generate_exp(fi, cs, ncs)
        call_nusmv("nuxmv_file.smv", newfi, "counterexample")
        if os.path.exists("../data/counterexample.xml"):
            changing_vars = ob_vars(cs, treated)
            cs = look_for_dep_var_while(fi, newfi, changing_vars, cs, treated, cv, True, is_temporal)
        cv = not_in_v(cs, cv)
        os.remove("../smv/nuxmv_file.smv")
        return [cs] + partition_recursive(fi, cv, treated, is_temporal)


def __var_list_from_tree(exp):
    # From a binary tree of a requirement returns it on a string

    if not (type(exp) == str):
        if len(exp) == 2:
            return __var_list_from_tree(exp[1])
        elif len(exp) == 3:
            return __var_list_from_tree(exp[1]) + __var_list_from_tree(exp[2])
        else:
            return [exp[0]]
    else:
        return [exp]


def var_list_exp(exp):
    l = __var_list_from_tree(exp)
    return list(dict.fromkeys(l))


def ob_vars(cs, treated):
    counterex = parse_xml("../data/counterexample.xml")
    os.remove("../data/counterexample.xml")
    # No se si aquí es necesario list(set())
    dvars = list(set(not_same_var(counterex)))
    l3 = not_in_v(cs, dvars)
    # l4 = not_in_v(treated, l3)
    return l3


def terminal_use():
    # Read the arguments from the terminal
    parser = argparse.ArgumentParser(description="Descomposition tool")
    parser.add_argument("-f", dest="filename", help="Input the file with the logical expression", 
                        metavar="FILE")
    args = parser.parse_args()
    if not args.filename:
        return ""
    else:
        if not os.path.exists(args.filename):
            raise Exception
        else:
            formula = ""
            file = open(args.filename, "r")
            lines = file.readlines()
            for line in lines:
                if line[-1] == '\n':
                    l = line[:-1]
                    formula += str(l)
                else:
                    formula += str(line)
            file.close()
            return formula


def no_file_terminal():
    # When there is no file in the arguments
    print("\nIntroduce the formula:")
    formula = input()
    return formula


def __get_formula():
    t = terminal_use()
    if not t:
        return no_file_terminal()
    else:
        return t


def create_bash_file(path):
    # Create the NuSMV bash file to call it given the path
    f = open("call_nusmv.sh", "w")
    f.write("#!/bin/bash\n\n" + str(path) + " -int ../smv/$2 <<< $1")
    f.close()
    os.chmod("./call_nusmv.sh", stat.S_IRWXU)


def get_app_path(is_linux):
    # Given if the system is Linux or not (MacOS) gets the path of NuSMV in the computer
    call_get_path(is_linux, True)
    f = open("../files/allpaths.txt")
    line = f.readline()
    if line[-1] == '\n':
        line = line[:-1]
    os.remove("../files/allpaths.txt")
    return line


def checker_path(is_linux):
    # Gets the path and creates the bash file for NuSMV
    path = get_app_path(is_linux)
    create_bash_file(path)


def pregunta_path():
    # Questions to start the app
    is_linux = False
    print("Are you using this app on a linux or a mac?\nType 1 if linux, 2 if mac, any other thing if other.")
    res1 = input()
    if res1 == '1':
        is_linux = True
    elif res1 == '2':
        is_linux = False
    else:
        print("Until the next one!")
        quit()
    print("Looking for the path...\n")
    checker_path(is_linux)


def get_the_partition(formula, var_tree, variables, var_groups):
    # Save the expression tree when created
    # Ask NuSMV for a model of the original formula
    # Save the value of the variables
    # While there are groups of the variables left
    #   Give the value to the rest of the variables and treat the tree
    #   Save the result of the final expression
    create_nusmv_file(variables, [])
    call_nusmv("nuxmv_file.smv", '!(' + formula + ')', "counterexample")
    if os.path.exists("../data/counterexample.xml"):
        counterex = parse_xml("../data/counterexample.xml")
        os.remove("../data/counterexample.xml")
        # Accedo al primer elemento de la lista compuesta por nodos, y luego a las variables normales
        model = counterex[0][0]
    else:
        quit('It does not exist a model for the formula.')
    os.remove("../smv/nuxmv_file.smv")
    f = []
    i = 0
    for i in range(len(var_groups)):
        if i == 0:
            selected_vars = flatt_list(var_groups[i+1:])
        elif i == len(var_groups)-1:
            selected_vars = flatt_list(var_groups[:len(var_groups)-1])
        else:
            selected_vars = flatt_list(var_groups[:i] + var_groups[i+1:])
        f_i = get_new_formula(var_tree, model, selected_vars)
        f.append(f_i)
    return f


def flatt_list(l):
    return [item for sublist in l for item in sublist]


def get_new_formula(tree, model, sel_vars):
    # Given a tree of the formula and a model that satisfies it, returns
    t = __change_values_tree(tree, model, sel_vars)
    nt = __simplify_tree(t)
    return nt


def __change_values_tree(tree, model, sel_vars):
    if not (type(tree) == str):
        if len(tree) == 2:
            return [tree[0], __change_values_tree(tree[1], model, sel_vars)]
        elif len(tree) == 3:
            return [tree[0], __change_values_tree(tree[1], model, sel_vars), __change_values_tree(tree[2], model, sel_vars)]
        else:
            # No se en que caso se da esto pero por si acaso
            return [__change_values_tree(tree[0], model, sel_vars)]
    else:
        if tree in sel_vars:
            return __get_var_value(tree, model)
        else:
            return tree


def __simplify_tree(tree):
    if type(tree) != str:
        if len(tree) == 2:
            if tree[1] == 'True':
                return 'False'
            elif tree[1] == 'False':
                return 'True'
            else:
                return tree[0] + '(' + __simplify_tree(tree[1]) + ')'
        elif len(tree) == 3:
            if tree[1] == 'True':
                if tree[0] == '&':
                    return __simplify_tree(tree[2])
                elif tree[0] == '|':
                    return 'True'
                else:
                    # ->
                    return __simplify_tree(tree[2])
            elif tree[1] == 'False':
                if tree[0] == '&':
                    return 'False'
                elif tree[0] == '|':
                    return __simplify_tree(tree[2])
                else:
                    # ->
                    return 'True'
            elif tree[2] == 'True':
                if tree[0] == '&':
                    return __simplify_tree(tree[1])
                elif tree[0] == '|':
                    return 'True'
                else:
                    # ->
                    return True
            elif tree[2] == 'False':
                if tree[0] == '&':
                    return 'False'
                elif tree[0] == '|':
                    return __simplify_tree(tree[1])
                else:
                    # ->
                    return __simplify_tree(['!', tree[1]])
            else:
                izq = __simplify_tree(tree[1])
                der = __simplify_tree(tree[2])
                if izq == 'True':
                    if tree[0] == '&':
                        return der
                    elif tree[0] == '|':
                        return 'True'
                    else:
                        # ->
                        return der
                elif izq == 'False':
                    if tree[0] == '&':
                        return 'False'
                    elif tree[0] == '|':
                        return der
                    else:
                        # ->
                        return 'True'
                elif der == 'True':
                    if tree[0] == '&':
                        return izq
                    elif tree[0] == '|':
                        return 'True'
                    else:
                        # ->
                        return 'True'
                elif der == 'False':
                    if tree[0] == '&':
                        return 'False'
                    elif tree[0] == '|':
                        return izq
                    else:
                        # ->
                        return '!(' + izq + ')'
                else:
                    return '(' + izq + ' ' + tree[0] + ' ' + der + ')'
        else:
            return tree[0]
    else:
        return tree


def __get_var_value(v, model):
    for m in model:
        if v == m.get_name():
            return str(m.get_value())


def ask_for_env(variables, res):
    res_a = res.replace(" ", "")
    evars = res_a.split(",")
    for v in evars:
        if v not in variables:
            print("The variable " + v + "does not exist in the formula. Try again or leave the process typing "
                                        "\"quit\":\n")
            r = input()
            r = r.replace(" ", "")
            if r == "quit":
                quit("See you next time!")
            else:
                return ask_for_env(variables, r)
    return evars


def check_is_temporal(var_tree):
    if not (type(var_tree) == str):
        if len(var_tree) == 2:
            if var_tree[0] == "F" or var_tree[0] == "G" or var_tree[0] == "X":
                return True
            else:
                return check_is_temporal(var_tree[1])
        elif len(var_tree) == 3:
            if var_tree[0] == "F" or var_tree[0] == "G" or var_tree[0] == "X":
                return True
            else:
                return check_is_temporal(var_tree[1]) or check_is_temporal(var_tree[2])
        else:
            if var_tree[0] == "F" or var_tree[0] == "G" or var_tree[0] == "X":
                return True
            else:
                return False
    else:
        return False


def full_process(first):
    # Gets the formula and calls the main method partition_recursive
    if first:
        formula = __get_formula()
    else:
        formula = no_file_terminal()
    # print(formula)
    var_tree = parse_req_exp(formula, 'ltl')
    variables = var_list_exp(var_tree)
    if check_is_temporal(var_tree):
        print("Can you tell me which are the environment variables? If there are not type \"-\":")
        res = input()
        print("\nAsking the question...")
        time.sleep(3)
        if res == "-":
            var_groups = partition_recursive(formula, variables, [], True)
        else:
            env_vars = ask_for_env(variables, res)
            sys_vars = not_in_v(env_vars, variables)
            var_groups = partition_recursive(formula, sys_vars, env_vars, True)
        form_groups = []
    else:
        var_groups = partition_recursive(formula, variables, [], False)
        form_groups = get_the_partition(formula, var_tree, variables, var_groups)
    return var_groups, form_groups


def main_in(first, program_name):
    result = full_process(first)
    print("\nThe Groups of the decomposition are:\n" + str(result[0]))
    print("The result of the decomposition is:\n" + str(result[1]))
    time.sleep(1)
    print("\nWill you continue using " + program_name + "?\nType 1 if so, anything else if not.")
    res1 = input()
    if res1 == '1':
        main_in(False, program_name)
    else:
        print("\nSee you next time!")


def main():
    program_name = "Decomposition"
    print("Is the first time you use this version of the app in this computer?\nType 1 if so, anything else if not.")
    res = input()
    if res == '1':
        pregunta_path()
    main_in(True, program_name)

def prueba():
    expresion = '(a | ((b & c) & (c | d)))'
    v1 = BVarI('a', False)
    v2 = BVarI('b', True)
    v3 = BVarI('c', True)
    v4 = BVarI('d', False)
    model = [v1, v2, v3, v4]
    t = parse_req_exp(expresion, 'prop')
    sel = ['c']
    nt = __change_values_tree(t, model, sel)
    print(nt)
    ntt = __simplify_tree(nt)
    print(ntt)




if __name__ == '__main__':
    # start_time = time.time()
    main()
    # prueba()