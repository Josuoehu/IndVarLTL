from parsimonious.grammar import Grammar
from classes import IniVisitor
from generate import req_to_string

# Grammar to parse de requirements
grammar_prop = Grammar(
            """
            Bicondicional = (Condicional "<->" Bicondicional) / Condicional
            Condicional = (Conjuncion "->" Condicional) / Conjuncion
            Conjuncion = (Disyuncion Or Conjuncion) / Disyuncion
            Disyuncion = (Literal And Disyuncion) / Literal
            Literal = Atomo / ("!" Literal)
            Atomo = Id / Agrupacion
            Agrupacion = "(" Bicondicional ")"
            Id          = ~"[A-Za-z0-9_]+"
            Not         = "!" / "~"
            And         = "&&" / "&"
            Or          = "||" / "|"
            """
)
# ^([a-zA-Z_$][a-zA-Z\\d_$]*)$
# "[A-Za-z0-9_-]+"


def parse_req_exp(exp, gramatica):
    if gramatica == 'prop':
        iv = IniVisitor()
        tree = grammar_prop.parse(exp.replace(" ", ""))
        return iv.visit(tree)
    else:
        return None


def is_in_tree(tree, statement):
    # Given a binary tree, check if the simple expression statement is in it. Returns True if is in, False if not.

    if not (type(tree) == str):
        if len(tree) == 2:
            return is_in_tree(tree[1], statement)
        elif len(tree) == 3:
            if tree == statement:
                return True
            else:
                izq = is_in_tree(tree[1], statement)
                der = is_in_tree(tree[2], statement)
                return izq or der
        else:
            return False
    else:
        return False


def is_var_in_tree(tree, var_name):
    # Creo que se puede omitir cuando es de len == 3 y meterlo en un else normal porque diria que no hay arrays de len == 1

    if not (type(tree) == str):
        if len(tree) == 2:
            # !(var_name) quiere decir que pasa a tener un valor FALSE
            if var_name == tree[1]:
                return 'FALSE'
            else:
                return is_var_in_tree(tree[1], var_name)
        elif len(tree) == 3:
            # var_name == x quiere decir que pasa a tener valor 'x' siendo x hasta una expresion aritmetica
            if tree[0] != '&':
                if var_name == tree[1]:
                    return req_to_string(tree[2])
                else:
                    izq = is_var_in_tree(tree[1], var_name)
                    der = is_var_in_tree(tree[2], var_name)
                    return izq + der
            else:
                izq = is_var_in_tree(tree[1], var_name)
                der = is_var_in_tree(tree[2], var_name)
                return izq + der
        else:
            if tree[0] == var_name:
                return 'TRUE'
            else:
                return ''
    else:
        if tree == var_name:
            return 'TRUE'
        else:
            return ''


def insert_in_tree(tree, statement):
    # Insterts the statament in the binary tree

    return ['&', statement, tree]


def main():
    str = '((a -> (b & c)) & (!a -> (!b & !c)))'
    print(parse_req_exp(str))

if __name__ == '__main__':
    main()