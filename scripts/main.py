import os
import time
from generate_nuxmv import *
from generate_test import test_requirement
from readXML import mostrar_secuencia
from scripts.iannopollo import alg_iannopollo, alg_ainnopollo_nleft, alg_ainnopollo_nleft_aalta
from scripts.read_file import read_new_file


def programm(FILE, aalta):
    # Charge variables
    env_vars, sys_vars, init_env, init_sys, assumptions, guarantees = read_new_file(FILE)
    if aalta:
        # Calculate time and call the algorithm
        start_time = time.time()
        descomposition = alg_ainnopollo_nleft_aalta(env_vars, sys_vars, init_env, init_sys, assumptions, guarantees)
        final_time = time.time()
    else:

        # Generate the first part of the file without the LTLSPEC
        create_nusmv_file(env_vars, sys_vars)
        # Calculate time and call the algorithm
        start_time = time.time()
        descomposition = alg_ainnopollo_nleft(env_vars, sys_vars, init_env, init_sys, assumptions, guarantees)
        final_time = time.time()
        # Remove the nusmv file
        os.remove("../smv/nuxmv_file.smv")

    return descomposition, start_time, final_time


def main():
    depprom = '/dependency_problem.ltl'
    deppromdev = '/dependency_problem_developed.ltl'
    finkinit = '/Finkbeiner_example_initials.ltl'
    aluedit = '/ALU_8_bits_edited.ltl'
    alugood = '/ALU_8_bits_good.ltl'
    alu = '/ALU_8_bits.ltl'
    fink = '/Finkbeiner_example.ltl'
    jac = '/jacopo_example.ltl'
    exten = '/example10.ltl'
    simplecook = '/simple_cooker_abstracted.ltl'

    # True because we use aalta.
    result = programm(fink, True)

    print(result[0])
    print("--- %s seconds ---" % (result[2] - result[1]))


def mostrar_resultado(result):
    for v in result:
        if type(v) == BVarI:
            print(v.get_name(), end=' ')
        else:
            print("[", end=' ')
            for w in v:
                print(w.get_name() + ",", end=' ')
            print("]", end=' ')
        print(",", end=' ')
    print('\n')


if __name__ == '__main__':
    # start_time = time.time()
    main()
    # print("--- %s seconds ---" % (time.time() - start_time))