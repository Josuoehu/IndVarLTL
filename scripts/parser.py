from classes import *
from req_parser import parse_req_exp, is_in_tree, insert_in_tree


def read_file(file):
    # Reads the file.json and returns a dictionary

    ruta = '../data/inputs' + file
    with open(ruta, 'r') as dict_file:
        dict_text = dict_file.read()
        diccionario = eval(dict_text)
        return diccionario


def load_ivars(ob):
    # Returns a list with the ivars
    lista_ivar = []
    lista = ob.get("observables").get("inputs")
    if not(lista == []):
        # Variables ivar
        for ivar in lista:
            type = ivar["type"]
            """
            if type == "int":
                # Crear variable EVar y hacer gestion de las variables enteras
                var = EVarI(ivar.get("name"), ivar.get("max"), ivar.get("min"), ivar.get("initial"))
                lista_ivar.append(var)
            elif type == "real":
                # Crear variable RVar y hacer gestion de las variables reales
                var = RVarI(ivar.get("name"), ivar.get("max"), ivar.get("min"), ivar.get("initial"))
                lista_ivar.append(var)
            """
            if type == "bool":
                # Crear variable BVar y hacer gestion de las variables booleanas
                var = BVarI(ivar.get("name"), ivar.get("initial"))
                lista_ivar.append(var)
            else:
                # Crear variable SVar y hacer gestion de las variables de estado
                raise SyntaxError('Not a correct Json format')
        return lista_ivar
    else:
        return []


def load_vars(ob, tipos, varout):
    # Before calling this method 'load_types' method must be called in the process
    # Returns a list of variables

    list = ob.get("observables").get(varout)
    if not (list == []):
        lista_var = []
        for var in list:
            name = var["name"]
            type = var["type"]
            """
            if type == "int":
                # I am supposing that Integers do not have the possibility of initial values QUESTION
                variable = EVarI(name, var.get("max"), var.get("min"), var.get("initial"))
                lista_var.append(variable)
            elif type == "real":
                # I am supposing that Floats do not have the possibility of initial values QUESTION
                variable = RVarI(name, var.get("max"), var.get("min"), var.get("initial"))
                lista_var.append(variable)
            """
            if type == "bool":
                variable = BVarI(name, var.get("initial"))
                lista_var.append(variable)
            else:
                initial = var.get("initial")
                dent = True
                i = 0
                # Create de Enum variable
                while dent and i in range(len(tipos)):
                    tipo = tipos[i]
                    if tipo.get_name() == type:
                        dent = False
                        v = None
                        if initial is not None:
                            v = SVarI(name, initial, tipo.get_values())
                        else:
                            v = SVar(name, tipo.get_values())
                        lista_var.append(v)
                    i+=1
        return lista_var
    else:
        return []


def load_types(ob):
    # Returns the types in a list
    list = ob.get("observables").get("types")
    if not (list == []):
        lista_types = []
        for tipo in list:
            name = tipo["name"]
            type = tipo["type"]
            miembros = tipo.get("members")
            elements = miembros.keys()
            v = SVar(name, elements)
            lista_types.append(v)
        return lista_types
    else:
        return []


def load_constants(ob):
    # Returns the constants in a list

    list = ob.get("observables").get("constants")
    if not (list == []):
        list_const = []
        for c in list:
            type = c["type"]
            if type == "int":
                var = EVarI(c["name"], None, None, c["value"])
                list_const.append(var)
            elif type == "real":
                var = RVarI(c["name"], None, None, c["value"])
                list_const.append(var)
            elif type == "bool":
                # Mirar como se muestra el True y False para crear bien el tipo de dato
                var = BVarI(c["name"], c["value"])
                list_const.append(var)
            else:
                # Maybe enum variables should be treated here QUESTION
                # Meanwhile a exception will be raised
                # Treatment of the exception must be done upper
                raise SyntaxError('Not a correct Json format')
        return list_const
    else:
        return []


def load_requirements(ob, require):
    # Returns in a tuple de requirements if require is true and the assumptions if require is false
    if require:
        list = ob.get("requirements")
    else:
        list = ob.get("assumptions")
    if not list:
        return []
    else:
        requisitos = []
        for r in list:
            re = r.get("requirement")
            var = read_full_requirement(re)
            if var is not None:
                requisitos.append(var)
        return requisitos


def read_trigger_req(v):
    # When is a ExpressionEvent (left part) returns it in a binary tree or throws a exception

    if v["type"] == "ExpressionEvent":
        exp = v["expression"]
        return exp
    else:
        raise SyntaxError('Not a correct Json format')


def read_full_requirement(req):
    # Reads the requirement and returns both parts in a binary tree in a tuple (left, right)

    if req["type"] == "StandardRequirement":
        v = req.get("trigger")
        izq_exp = None
        # If there is scope but not trigger
        if v is None:
            v = req.get("scope")
            if v is not None:
                if v["type"] == "Holds":
                    expi = v.get("expression")
                    izq_exp = expi
                else:
                    raise SyntaxError('Not a correct Json format')
            else:
                raise SyntaxError('Not a correct Json format')
        # When there is trigger
        else:
            izq_exp = read_trigger_req(v)
        # Treat the right part of the requirement
        v1 = req.get("response")
        if v1 is not None:
            if v1.get("type") == "StateTransition":
                # Verify if it is necessary to be added in the left part of the requirement
                return treat_state_transition(v1, izq_exp)
            elif v1["type"] == "Satisfy":
                der_exp = v1["expression"]
                return (izq_exp, der_exp)
            else:
                raise SyntaxError('Not a correct Json format')
        else:
            return (izq_exp, None)


def treat_state_transition(right, izq_exp):
    # Modifies the left part of the requirement (if necessary) and returns it in a tuple (left, right)

    name = right.get("state_machine")
    fr = right.get("from_")
    to = right.get("to")
    der_exp = ['==', name, to]
    if fr is not None:
        if to is not None:
            eq = ['==', name, fr]
            if is_in_tree(izq_exp, eq):
                return izq_exp, der_exp
            else:
                # Insert eq part in the left part of the tree
                iz = insert_in_tree(izq_exp, eq)
                return iz, der_exp
        else:
            raise SyntaxError('Not a correct Json format')
    else:
        # If there is not 'from' part I suppose it appears on the left part of the requirement
        if to is not None:
            return izq_exp, der_exp
        else:
            raise SyntaxError('Not a correct Json format')