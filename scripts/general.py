import os
import argparse

from call import call_nusmv
from generate_nuxmv import create_nusmv_file
from iannopollo import not_in_v, renaming
from readXML import parse_xml, not_same_var
from req_parser import parse_req_exp


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
    dvars = list(set(not_same_var(counterex)))
    l3 = not_in_v(cs, dvars)
    l4 = not_in_v(treated, l3)
    return l4


def terminal_use():
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
            return formula


def no_file_terminal():
    print("Introduce the formula:")
    formula = input()
    return formula


def get_formula():
    t = terminal_use()
    if not t:
        return no_file_terminal()
    else:
        return t


def main():
    formula = get_formula()
    print(formula)
    var_tree = parse_req_exp(formula, 'prop')
    variables = var_list_exp(var_tree)
    create_nusmv_file([], variables)
    result = partition(formula, variables)
    os.remove("../smv/nuxmv_file.smv")
    # print(str(result))
    print("\nThe result of the decomposition is:\n" + str(result))
if __name__ == '__main__':
    # start_time = time.time()
    main()