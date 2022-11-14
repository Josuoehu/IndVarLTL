import xml.etree.ElementTree as ET
import time
from itertools import chain

from classes import *
from classes import Types as data_types
import re



def main():
    # v1 = SVarI('STATE', 'STATE_SET_COOKING_TIME', None)
    # v1 = AritVar('var_desiredTime', 'var_desiredTimePrev', '+', '10.0')
    v1 = EVarI('at_speed_2', None, None, 3600)

    list = [v1]
    start_time = time.time()
    secuence = parse_xml('../data/counterexample.xml', list)
    # mostrar_secuencia1(secuence)
    print("--- %s seconds ---" % (time.time() - start_time))


def not_same_var(countex):
    changing_vars = []
    for state in countex:
        s_vars = state[0]
        for i in range(len(s_vars)):
            for j in range(i, len(s_vars)):
                if s_vars[i].eq_name_p(s_vars[j]):
                    if s_vars[i].get_value() != s_vars[j].get_value():
                        var_name = s_vars[i].get_name()
                        if var_name[:-1] == s_vars[j].get_name():
                            if not s_vars[j] in changing_vars:
                                changing_vars.append(s_vars[j].get_name())
                        else:
                            if not s_vars[i] in changing_vars:
                                changing_vars.append(s_vars[i].get_name())
    return changing_vars


def state_reached(previous, variables, var_state):
    salir = True
    izq = var_state[0]
    for v in izq:
        if not(v in previous):
            salir = False
    if salir:
        der = var_state[1]
        for v in der:
            if type(v) == AritVar:
                prev = previous[0]
                v = treat_arit_variable(v, prev)
            if not(v in variables):
                salir = False
                break
    return salir


def treat_arit_variable(v, previous):
    der = v.get_exp_right()
    izq = v.get_exp_left()
    tipo_izq = var_type(izq)
    tipo_der = var_type(der)
    if tipo_izq == data_types.STATE:
        izq_value = search_variable(previous, izq)
        tipo_izq_value = type(izq_value)
        if tipo_der == data_types.STATE:
            der_value = search_variable(previous, der)
            tipo_der_value = type(der_value)
            if not izq_value or not der_value:
                raise Exception('None value. Not found the variable in the variables so returns a None.')
            else:
                if tipo_izq_value == int and tipo_der_value == int:
                    a = int(izq_value)
                    b = int(der_value)
                    valor = operation(v.get_op(), a, b)
                    now_variable = EVarI(v.get_name(), None, None, valor)
                else:
                    a = float(izq_value)
                    b = float(der_value)
                    valor = operation(v.get_op(), a, b)
                    now_variable = RVarI(v.get_name(), None, None, valor)
        elif tipo_der == data_types.INTEGER:
            if tipo_izq_value == int:
                a = int(izq_value)
                b = int(der)
                valor = operation(v.get_op(), a, b)
                now_variable = EVarI(v.get_name(), None, None, valor)
            else:
                a = float(izq_value)
                b = float(der)
                valor = operation(v.get_op(), a, b)
                now_variable = RVarI(v.get_name(), None, None, valor)
        else:
            a = float(izq_value)
            b = float(der)
            valor = operation(v.get_op(), a, b)
            now_variable = RVarI(v.get_name(), None, None, valor)
    elif var_type(izq) == data_types.INTEGER:
        if tipo_der == data_types.STATE:
            der_value = search_variable(previous, der)
            tipo_der_value = type(der_value)
            if tipo_der_value == int:
                a = int(izq)
                b = int(der_value)
                valor = operation(v.get_op(), a, b)
                now_variable = EVarI(v.get_name(), None, None, valor)
            else:
                a = float(izq)
                b = float(der_value)
                valor = operation(v.get_op(), a, b)
                now_variable = RVarI(v.get_name(), None, None, valor)
        else:
            raise Exception('Impossible to be for example: 34.2 + 1.4')
    else:
        if tipo_der == data_types.STATE:
            der_value = search_variable(previous, der)
            a = float(izq)
            b = float(der_value)
            valor = operation(v.get_op(), a, b)
            now_variable = RVarI(v.get_name(), None, None, valor)
        else:
            raise Exception('Impossible to be for example: 34.2 + 1.4')
    return now_variable


def operation(op, a, b):
    if op == '/':
        return a/b
    elif op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a*b
    elif op == 'mod':
        return a % b


def search_variable(lista, var_name):
    i = 0
    while i < len(lista):
        var = lista[i]
        if var.get_name() == var_name:
            return var.get_value()
        else:
            i += 1
    return None


def parse_xml(file):
    l = []
    tree = ET.parse(file)
    root = tree.getroot()
    # longitud = len(root)
    # for i in range(longitud):
    for node in root.iter('node'):
        # node = root[i]
        variables = bucle_var([], node[0])
        if len(node) == 2:
            ivariables = bucle_var([], node[1])
            nod_gen = (variables, ivariables)
        else:
            nod_gen = (variables, None)
        l.append(nod_gen)
    return l


# def parse_xml_rec(previous, states, var_states):
#     if not states:
#         return False
#     else:
#         node = states[0]
#         tam = len(states)
#         variables = bucle_var([], node[0])
#         ivariables = bucle_var([], node[1])
#
#         return parse_xml_rec(node, states[-tam:], var_states)

def bucle_var(variables, vars):
    for v in vars:
        attr = v.attrib
        name = attr['variable']
        valor = v.text
        ivar = create_var(name, valor)
        variables.append(ivar)
    return variables


def mostrar_secuencia(secuence):
    # print(secuence)

    for s in secuence:
        for j in s:
            print(j[0])
            print("----------")
            for i in j[1]:
                for k in i[0]:
                    if type(k) != RVarI and type(k) != EVarI:
                        print(k)
                    else:
                        print(k.str2())
                if not (not i[1]):
                    for k in i[1]:
                        if type(k) != RVarI and type(k) != EVarI:
                            print(k)
                        else:
                            print(k.str2())
                print(' -   -   -   - ')
            print("----------")
            print("\n")

def mostrar_secuencia1(secuence):
    # print(secuence)

    for s in secuence:
        for i in s[0]:
            print(i)
        for j in s:
            print(j[0])
            print("----------")
            for i in j[1]:
                for k in i[0]:
                    print(k)
                if not (not i[1]):
                    for k in i[1]:
                        print(k)
                print(' -   -   -   - ')
            print("----------")
            print("\n")


def create_var(name, valor):
    '''Creates a variable of different class depending on the atribute valor'''
    if var_type(valor) == data_types.BOOLEAN:
        if valor == 'TRUE':
            var = BVarI(name, True)
        else:
            var = BVarI(name, False)
    elif var_type(valor) == data_types.REAL:
        var = RVarI(name, None, None,float(valor))
    elif var_type(valor) == data_types.INTEGER:
        var = EVarI(name, None, None, int(valor))
    else:
        var = SVarI(name, valor, None)
    return var


def var_type(word):
    if word == 'TRUE' or word == 'FALSE':
        return data_types.BOOLEAN
    elif re.match(r"((\+|-)?([0-9]+)\.([0-9]+)?)|((\+|-)?\.[0-9]+)", word):
        return data_types.REAL
    elif re.match(r"[-+]?[0-9]+", word):
        return data_types.INTEGER
    else:
        return data_types.STATE

if __name__ == '__main__':
    main()
