import os

from parser import *
from req_parser import is_var_in_tree
from generate import req_to_string
from overlapping import check_overlapping

FILE = read_file('/running_example.json')


def create_document(name, first):
    # Creates a document in order to write on it
    try:
        name = '../smv/' + name + '.smv'
        file = open(name, "a")
        if first:
            file.write("MODULE main \n \n")
        return file
    except IOError:
        print('Maybe you have not introduce the correct path of the file')
        exit()


def close_document(file):
    # Closes the file in file parameter

    file.close()


def write_v_i_c(file, vars, n):
    # Writes the vars, ivars and constant using the str() depending the n parameter writes one heading or another
    if n==0:
        file.write('VAR \n \n')
    for var in vars:
        if type(var) != SVarI:
            file.write(str(var) + ';\n')
            file.write(var.write_pr_var() + ';\n')


def vars_and_req(vars, req, file):
    # Searchs the vars in the left part of the requirement and writes them in the file

    for v in vars:
        requirements = search_var_in_req(v.get_name(), req)
        write_one_req(file, requirements, v)


def search_var_in_req(name, req):
    # Creates the requirement list for the variable which has initial value

    r_list = []
    for r in req:
        izq = r[1]
        der = is_var_in_tree(izq, name)
        if der != '':
            requi = (r[0], der)
            r_list.append(requi)
    return r_list


def write_one_req(file, req, var):
    # Writes in the specified file the initial value of the var and all it's requirements
    # Treatment when it is with the '==' missing. El 'req' hay que mirar donde hacer el tratamiento.

    name = str(var.get_name())
    if not(type(var) == SVar):
        if var.get_value() is not None:
            if type(var) == BVarI:
                st = '\tinit(' + name + ') := ' + var.get_value_str() + ';'
            else:
                st = '\tinit(' + name + ') := ' + str(var.get_value()) + ';'
            file.write(st)
    file.write('\n\tnext(' + name + ') :=\n\t\tcase\n')
    req_list = []
    for r in req:
        st1 = '\t\t\t' + req_to_string(r[0]) + ': ' + r[1] + ';\n'
        req_list.append(st1)
    file.writelines(req_list)
    file.write('\t\t\tTRUE : ' + name + ';\n\t\tesac;\n\n')


def load_vars_n_constants(json):
    data = load_ivars(json), load_vars(json, None, "variables") + load_vars(json, None, "outputs"), load_vars(json, None, "constants")
    return data


def create_file_first_part(variables):
    nuxmv_file = create_document('nuxmv_file', True)

    # Writes de ivars, vars and constants in the nuxmv file
    data = variables
    for i in range(len(data)):
        write_v_i_c(nuxmv_file, data[i], i)
    nuxmv_file.write("\n")

    nuxmv_file.write("FAIRNESS TRUE \n")
    close_document(nuxmv_file)


def assumptions_and_guarantees(json):
    return load_requirements(json, False), load_requirements(json, True)


def create_nusmv_file(env_vars, sys_vars):
    nusmv_file = create_document('nuxmv_file', True)
    nusmv_file.write('VAR \n \n')
    for v in env_vars:
        nusmv_file.write(v + ": boolean;\n")
    for v in sys_vars:
        nusmv_file.write(v + ": boolean;\n")
        nusmv_file.write(v + "_: boolean;\n")
    nusmv_file.write("\nFAIRNESS TRUE")
    close_document(nusmv_file)
