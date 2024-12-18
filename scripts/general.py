import os
import argparse
import stat
import time

from call import call_nusmv, call_get_path
from generate_nuxmv import create_nusmv_file
from alg_paper import not_in_v, renaming, call_full_aalta, call_aalta_var_list
from readXML import parse_xml, not_same_var
from req_parser import parse_req_exp
from sys import platform
from os import path


def generate_exp(fi, cs, ncs, is_nusmv):
    """
    This function generates the formula to ask the checker or the SAT Tool.

    Parameters
    ----------

    fi : str
        Initial formula.
    cs : list
        Variables in one group which after must be renamed.
    ncs : list
        Complementary group of variables.
    is_nusmv : bool
        If the expression is generated for NuSMV or for Aalta. (A model checker or a SAT solver).

    Returns
    -------
    str
        The original formula renamed with the corresponding variables.
    """
    fi_cs = fi
    fi_not_cs = fi
    for v in cs:
        fi_cs = renaming(fi_cs, v, "_")
    for v in ncs:
        fi_not_cs = renaming(fi_not_cs, v, "_")
    if is_nusmv:
        # !fi_cs || !fi_ncs || fi
        # return "!(" + fi_cs + ") | !(" + fi_not_cs + ") | (" + fi + ")"
        return f"!({fi_cs}) | !({fi_not_cs}) | ({fi})"
    else:
        # fi_cs && fi_ncs && !fi
        # return "(" + fi_cs + ") & (" + fi_not_cs + ") & !(" + fi + ")"
        return f"({fi_cs}) & ({fi_not_cs}) & !({fi})"


def look_for_dep_var(fi, oldfi, changing_vars, cs, treated, cv):
    # cz = not_in_v(cs, changing_vars)
    z = changing_vars[0]
    inv = " | !(" + z + " <-> " + z + "_)"
    newfi = oldfi + inv
    call_nusmv("nuxmv_file.smv", newfi, "counterexample")
    if os.path.exists("../counterexample.xml"):
        new_changing_vars = ob_vars(cs, treated)
        return look_for_dep_var(fi, newfi, new_changing_vars, cs, treated, cv)
    else:
        cs.append(z)
        treated.append(z)
        ncs = not_in_v(cs, cv)
        if ncs:
            other_fi = generate_exp(fi, cs, ncs, True)
            call_nusmv("nuxmv_file.smv", other_fi, "counterexample")
            if os.path.exists("../counterexample.xml"):
                changing_vars = ob_vars(cs, treated)
                return look_for_dep_var(fi, other_fi, changing_vars, cs, treated, cv)
            else:
                return cs
        else:
            return cs


def look_for_dep_var_while_aalta(fi, oldfi, changing_vars, cs, treated, cv, is_model, is_temporal):
    # cz = not_in_v(cs, changing_vars)
    newfi = oldfi
    while is_model:
        z = changing_vars[0]
        if is_temporal:
            inv = " & G(" + z + " <-> " + z + "_)"
        else:
            inv = " & (" + z + " <-> " + z + "_)"
        newfi += inv
        aalta_res, model = call_full_aalta('expression.dimacs', newfi, cs, treated)
        if aalta_res == 'sat' and model:
            changing_vars = model
        else:
            is_model = False
            # He cambiado esto dentro del else por la variable z
            cs.append(z)
            treated.append(z)
    ncs = not_in_v(cs, cv)
    if ncs:
        other_fi = generate_exp(fi, cs, ncs, False)
        aalta_res, model = call_full_aalta('expression.dimacs', other_fi, cs, treated)
        if aalta_res == 'sat' and model:
            changing_vars = model
            return look_for_dep_var_while_aalta(fi, other_fi, changing_vars, cs, treated, cv, True, is_temporal)
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
        if os.path.exists("../counterexample.xml"):
            new_changing_vars = ob_vars(cs, treated)
            changing_vars = new_changing_vars
        else:
            is_model = False
            # He cambiado esto dentro del else por la variable z
            cs.append(z)
            treated.append(z)
    ncs = not_in_v(cs, cv)
    if ncs:
        other_fi = generate_exp(fi, cs, ncs, True)
        call_nusmv("nuxmv_file.smv", other_fi, "counterexample")
        if os.path.exists("../counterexample.xml"):
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
                newfi = generate_exp(fi, cs, ncs, True)
                call_nusmv("nuxmv_file.smv", newfi, "counterexample")
                if os.path.exists("../counterexample.xml"):
                    changing_vars = ob_vars(cs, treated)
                    cs = look_for_dep_var(fi, newfi, changing_vars, cs, treated, cv)
                cv = not_in_v(cs, cv)
            conjuntos.append(cs)
            # print("New group " + str(cs))
    return conjuntos


def partition_general(fi, cv, treated, is_temporal, is_nusmv):
    if is_nusmv:
        return partition_recursive(fi, cv, treated, is_temporal)
    else:
        return partition_recursive_aalta(fi, cv, treated, is_temporal)


def partition_recursive_aalta(fi, cv, treated, is_temporal):
    if not cv:
        return []
    # elif len(cv) == 1:
    #     return [cv]
    else:
        v = cv[0]
        cs = [v]
        treated.append(v)
        ncs = not_in_v(cs, cv)
        newfi = generate_exp(fi, cs, ncs, False)
        aalta_res, model = call_full_aalta('expression.dimacs', newfi, cs, treated)
        if aalta_res == 'sat' and model:
            changing_vars = model
            cs = look_for_dep_var_while_aalta(fi, newfi, changing_vars, cs, treated, cv, True, is_temporal)
        cv = not_in_v(cs, cv)
        return [cs] + partition_recursive_aalta(fi, cv, treated, is_temporal)


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
        newfi = generate_exp(fi, cs, ncs, True)
        call_nusmv("nuxmv_file.smv", newfi, "counterexample")
        if os.path.exists("../counterexample.xml"):
            changing_vars = ob_vars(cs, treated)
            cs = look_for_dep_var_while(fi, newfi, changing_vars, cs, treated, cv, True, is_temporal)
        cv = not_in_v(cs, cv)
        os.remove("nuxmv_file.smv")
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
    counterex = parse_xml("../counterexample.xml")
    os.remove("../counterexample.xml")
    # No se si aquí es necesario list(set())
    dvars = list(set(not_same_var(counterex)))
    l3 = not_in_v(cs, dvars)
    # l4 = not_in_v(treated, l3)
    return l3


def __env_process(l):
    vars = l.lower().split(":")
    # print(str(vars) + " Split interior.")
    if vars[0] == "env_vars":
        return extract_env_vars(vars[1])
    else:
        return []


def terminal_use():
    # Read the arguments from the terminal
    parser = argparse.ArgumentParser(description="Descomposition tool")
    parser.add_argument("-f", dest="filename", help="Input the file with the logical expression", 
                        metavar="FILE")
    args = parser.parse_args()
    # print("Entra aquí")
    if not args.filename:
        return "", [], ""
    else:
        if not os.path.exists(args.filename):
            raise Exception
        else:
            formula = ""
            e_vars = []
            file = open(args.filename, "r")
            lines = file.readlines()
            for line in lines:
                if line[-1] == '\n':
                    l = str(line[:-1])
                    e_vars = __env_process(l)
                    if not e_vars:
                        formula += l
                else:
                    e_vars = __env_process(line)
                    if not e_vars:
                        formula += str(line)
            file.close()
            # print("No hay variables de entorno" + str(e_vars))
            return formula, e_vars, args.filename


def no_file_terminal():
    # When there is no file in the arguments
    print("\nIntroduce the formula:")
    formula = input()
    return formula


def __get_formula():
    file_name = ""
    f, e, file_name = terminal_use()
    if not f:
        f = no_file_terminal()
    return f, e, file_name


def create_bash_file(path, is_nusmv):
    # Create the NuSMV bash file to call it given the path
    if is_nusmv:
        f = open("call_nusmv.sh", "w")
        f.write("#!/bin/bash\n\n" + str(path) + " -int $2 <<< $1")
        f.close()
        os.chmod("./call_nusmv.sh", stat.S_IRWXU)
    else:
        f = open("call_aalta.sh", "w")
        f.write("#!/bin/bash\n\ncat $1 | " + str(path) + " -e > $2")
        f.close()
        os.chmod("./call_aalta.sh", stat.S_IRWXU)


def get_app_path(is_linux, is_nusmv):
    # Given if the system is Linux or not (MacOS) gets the path of NuSMV in the computer
    call_get_path(is_linux, is_nusmv)
    try:
        f = open("../files/allpaths.txt")
        line = f.readline()
        if line[-1] == '\n':
            line = line[:-1]
        os.remove("../files/allpaths.txt")
    except Exception:
        return ""
    else:
        return line


def checker_path(is_linux, is_nusmv):
    # Gets the path and creates the bash file for NuSMV or Aalta
    path = get_app_path(is_linux, is_nusmv)
    if path:
        create_bash_file(path, is_nusmv)



def pregunta_path(is_linux, is_nusmv):
    # Questions to start the app
    print("Looking for the path...")
    checker_path(is_linux, is_nusmv)



def get_the_partition(formula, var_tree, variables, var_groups, is_nusmv):
    # Save the expression tree when created
    # Ask NuSMV for a model of the original formula
    # Save the value of the variables
    # While there are groups of the variables left
    #   Give the value to the rest of the variables and treat the tree
    #   Save the result of the final expression
    model = None
    if is_nusmv:
        create_nusmv_file(variables, [])
        call_nusmv("nuxmv_file.smv", '!(' + formula + ')', "counterexample")
        if os.path.exists("../counterexample.xml"):
            counterex = parse_xml("../counterexample.xml")
            os.remove("../counterexample.xml")
            # Accedo al primer elemento de la lista compuesta por nodos, y luego a las variables normales
            model = counterex[0][0]
            os.remove("nuxmv_file.smv")
        else:
            quit('It does not exist a model for the formula.')
    else:
        aalta_res, model = call_aalta_var_list('expression.dimacs', formula)
        if not model:
            quit('It does not exist a model for the formula.')
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
    evars = extract_env_vars(res)
    for v in evars:
        if v not in variables:
            print("The variable " + v + " does not exist in the formula. Try again or leave the process typing "
                                        "\"quit\":\n")
            r = input()
            r = r.replace(" ", "")
            if r == "quit":
                quit("\nSee you next time!")
            else:
                return ask_for_env(variables, r)
    return evars

# G((p -> X(v & !(t))) & (! p -> X(!(v) & t)) & (v -> X(!(w) & u)) & (!(v) -> X(w & !(u))))
def extract_env_vars(res):
    res_a = res.replace(" ", "")
    evars = res_a.split(",")
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


def full_process(first, is_nusmv):
    # Gets the formula and calls the main method partition_recursive
    if first:
        formula, env_vars, file_name = __get_formula()
        # print(file_name)
    else:
        formula = no_file_terminal()
        env_vars = []
        file_name = ""
    var_tree = parse_req_exp(formula, 'ltl')
    variables = var_list_exp(var_tree)
    if check_is_temporal(var_tree):
        sys_vars = variables.copy()
        if not env_vars:
            print("\nCan you tell me which are the environment variables? If there are not type \"-\":")
            res = input()
            if res != "-":
                env_vars = ask_for_env(variables, res)
                sys_vars = not_in_v(env_vars, variables)
        else:
            sys_vars = not_in_v(env_vars, variables)
        print("Asking the question...")
        time.sleep(1)
        var_groups = partition_general(formula, sys_vars, env_vars, True, is_nusmv)
        form_groups = []
    else:
        print("Asking the question...")
        time.sleep(1)
        var_groups = partition_general(formula, variables, [], False, is_nusmv)
        form_groups = get_the_partition(formula, var_tree, variables, var_groups, is_nusmv)
    return var_groups, form_groups, file_name


def get_so():
    if platform == "linux" or platform == "linux2":
        return "linux"
    elif platform == "darwin":
        return "macos"
    elif platform == "win32":
        return "windows"
    else:
        quit("\nThere are some problems with your SO, see you next time!")


def output_file(v_g, f_g, name):
    # Creation of the output file
    frag = name.split(sep="/")
    real_name = frag[len(frag)-1]
    ruta = '../results/' + real_name[:-4] + '_r.txt'
    out_file = open(ruta, 'w')
    out_file.write("Results of the Decomposition of " + real_name + " file.\n\n")
    out_file.write("The variables are decomposed in the following groups: ")
    __print_variables(out_file, v_g)
    if not f_g:
        out_file.write("Formula decomposition for LTL functionality is not available yet, coming soon...")
    else:
        out_file.write("The formulas are decomposed the following way: ")
        __print_variables(out_file, f_g)
    out_file.close()


def __print_variables(out_file, v_g):
    line = ""
    for groups in v_g:
        line += str(groups)
        line += ", "
    out_file.write(line[:-2] + "\n")


def main_in(first, program_name, is_nusmv):
    var_groups, form_groups, file_name = full_process(first, is_nusmv)
    print("\nThe variable decomposition is:\n" + str(var_groups))
    print("The formula decomposition is:\n" + str(form_groups))
    if file_name != "":
        # print("Entra en el if the creacion de fichero.")
        output_file(var_groups, form_groups, file_name)
    time.sleep(1)
    print("\nWill you continue using " + program_name + "?\nType 1 if so, anything else if not.")
    res1 = input()
    if res1 == '1':
        main_in(False, program_name, is_nusmv)
    else:
        print("\nSee you next time!")


def main():
    program_name = "IndVarLTL"
    print("Welcome to " + program_name + " Tool.")
    is_nusmv = True
    os = get_so()
    if os == "windows":
        quit("We cannot execute this programm on Windows, sorry. See you in the near future!")
    elif os == "macos":
        print("We are using NuSMV during the hole process because we cannot use Aalta in MacOS.")
        if not path.isfile("./call_nusmv.sh"):
            pregunta_path(False, True)
    else:
        print("\nWould you like to use NuSMV or Aalta?\nType 1 for NuSMV, 2 for Aalta, anything else if you want to leave.")
        res1 = input()
        if res1 == '1':
            if not path.isfile("./call_nusmv.sh"):
                pregunta_path(True, is_nusmv)
        elif res1 == '2':
            is_nusmv = False
            if not path.isfile("./call_aalta.sh"):
                pregunta_path(True, is_nusmv)
        else:
            quit("\nSee you next time!")

    if path.isfile("./call_nusmv.sh") or path.isfile("./call_aalta.sh"):
        main_in(True, program_name, is_nusmv)
    else:
        print("A problem has been found. Please check that you have NuSMV or Aalta installed"
              ".\nIn case you have alredy installed you can contact the developers by email:"
              " \"josu.oca@udg.edu\".")


if __name__ == '__main__':
    # start_time = time.time()
    main()
    # prueba()
