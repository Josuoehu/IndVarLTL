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


def look_for_dep_var_while(fi, oldfi, changing_vars, cs, treated, cv, is_model):
    # cz = not_in_v(cs, changing_vars)
    newfi = oldfi
    while is_model:
        z = changing_vars[0]
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
            return look_for_dep_var_while(fi, other_fi, changing_vars, cs, treated, cv, True)
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


def partition_recursive(fi, cv, treated):
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
            cs = look_for_dep_var_while(fi, newfi, changing_vars, cs, treated, cv, True)
        cv = not_in_v(cs, cv)
        os.remove("../smv/nuxmv_file.smv")
        return [cs] + partition_recursive(fi, cv, treated)


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
    print("Do you want the app to look for NuSMV in your computer?\nType 1 if you want, 2 instead.")
    res = input()
    if res == '1':
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
    else:
        print("\nUntil the next one!")
        quit()


def full_process(first):
    # Gets the formula and calls the main method partition_recursive
    if first:
        formula = __get_formula()
    else:
        formula = no_file_terminal()
    # print(formula)
    print("Asking the question...")
    time.sleep(3)
    var_tree = parse_req_exp(formula, 'prop')
    variables = var_list_exp(var_tree)
    # create_nusmv_file([], variables)
    # result = partition(formula, variables)
    result = partition_recursive(formula, variables, [])
    # os.remove("../smv/nuxmv_file.smv")
    return result


def main_in(first, program_name):
    result = full_process(first)
    # os.remove("./call_nusmv.sh")
    # print(str(result))
    print("\nThe result of the decomposition is:\n" + str(result))
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
    print(os.path.abspath('NuSMV'))


if __name__ == '__main__':
    # start_time = time.time()
    main()
