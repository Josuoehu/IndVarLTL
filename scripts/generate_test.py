from generate import req_to_string
from call import *
from readXML import *
from req_parser import parse_req_exp


def generate_calls(req):
    # Returns an array with the different parts of the requirement in order to make the tests

    return rec_generate_calls(req, [])


def rec_generate_calls(req, res):
    # Recursive method

    if not req:
        return []
    else:
        if req[0] == '|':
            rec_generate_calls(req[1], res)
            rec_generate_calls(req[2], res)
            return res
        else:
            res.append(req_to_string(req))
            return res


def make_a_list(right, res):
    # right is a binary tree of the right part of a requirement. Returns a list of variables.

    if not right:
        return []
    else:
        if len(right) == 3:
            if right[0] == '&':
                l = []
                r = []
                if type(right[1]) == str:
                    res.append(new_var([right[1]]))
                else:
                    l = make_a_list(right[1], res)
                if type(right[2]) == str:
                    res.append(new_var([right[2]]))
                else:
                    r = make_a_list(right[2], res)
                # res.append([l,r])
                return res
            elif right[0] == '==':
                # '==' or ">=" or ">" or "<=" or "<" or "!="
                if not(type(right[2]) == str):
                    v = AritVar(right[1], right[2][1], right[2][0], right[2][2])
                    res.append(v)
                    return res
                else:
                    v = new_var(right)
                    res.append(v)
                    return res
            else:
                if type(right[2]) == str:
                    res.append(new_var(right))
                    return res
                else:
                    raise Exception('The right part is not a str. Dont know what happens')
        elif len(right) == 2:
            if type(right[1]) == str:
                res.append(new_var(right))
                return res
            else:
                raise Exception('The right part is not a str (len == 2). Dont know what happens')
        else:
            res.append(new_var([right]))
            return res


def new_var(exp):
    # Creates a type of the var depending of the string

    if len(exp) == 1:
        v = BVarI(exp[0], True)
    elif len(exp) == 2:
        v = BVarI(exp[1], False)
    else:
        valor = exp[2]
        if data_types.REAL == var_type(valor):
            v = RVarI(exp[1], None, None, float(valor))
        elif data_types.INTEGER == var_type(valor):
            v = EVarI(exp[1], None, None, int(valor))
        elif data_types.BOOLEAN == var_type(valor):
            if valor == 'TRUE':
                v = BVarI(exp[1], True)
            else:
                v = BVarI(exp[1], False)
        else:
            v = SVarI(exp[1], valor, None)
    return v


def test_requirement(l, r, index):
    # l is the left part of the requirement and r the right part
    l_list = generate_calls(l)
    devolver = []
    for i in range(len(l_list)):
        prim = str(index) + '.' + str(i)
        # llamada = "!(F(" + l_list[i] + " & X(" + req_to_string(r) + ")))"
        llamada = "!(F(" + l_list[i] + "))"
        print(llamada)
        # call_nusmv("nuxmv_file_prev.smv", llamada, "counterexample", 5000)
        call_nusmv("nuxmv_file_prev.smv", llamada, "counterexample")
        if os.path.exists("../data/counterexample.xml"):
            # Counterexample exists
            listar = make_a_list(r, [])
            if len(l_list) == 1:
                listal = make_a_list(l, [])
            else:
                lll = parse_req_exp(l_list[i])
                listal = make_a_list(lll, [])
            lista = (listal, listar)
            result = parse_xml("../data/counterexample.xml", lista)
            os.remove("../data/counterexample.xml")
            devolver.append((prim, result))
        else:
            devolver.append((prim, ['There is no counter-example']))
            # raise Exception('There is no counter-example.')
    return devolver



def main():
    # result = ['||', ['||', 'hola', 'adios'],['&&', 'josu', 'ander']]
    result = ['&', ['&', 'hola', ['==', 'JUAN', ['+', 'VAR_EXAMPLE', 'BBBBBBBBB']]], 'ADIOS']
    # print(generate_calls(result))
    res = []
    print(len(result))
    print(make_a_list(result, res))

if __name__ == '__main__':
    main()