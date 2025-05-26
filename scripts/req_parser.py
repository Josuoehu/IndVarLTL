from parsimonious.grammar import Grammar
from classes import IniVisitor
from generate import req_to_string

# Grammar to parse de requirements

# grammar_prop = Grammar(
#             """
#             Bicondicional = (Condicional "<->" Bicondicional) / Condicional
#             Condicional = (Conjuncion "->" Condicional) / Conjuncion
#             Conjuncion = (Disyuncion Or Conjuncion) / Disyuncion
#             Disyuncion = (Literal And Disyuncion) / Literal
#             Literal = Atomo / ("!" Literal)
#             Atomo = Id / Agrupacion
#             Agrupacion = "(" Bicondicional ")"
#             Id          = ~"[A-Za-z0-9_]+"
#             Not         = "!" / "~"
#             And         = "&&" / "&"
#             Or          = "||" / "|"
#             """
# )

# grammar_ltl = Grammar(
#     r"""
#     expr            = _ biconditional _
#
#     biconditional   = conditional (_ BICOND _ conditional)*
#     conditional     = disjunction (_ IMPL _ disjunction)*
#     disjunction     = conjunction (_ OR _ conjunction)*
#     conjunction     = temporal (_ AND _ temporal)*
#
#     temporal        = (unary / binary_temporal)
#     unary           = (NOT _ unary) / (TEMPORAL_UNARY _ unary) / atom
#
#     binary_temporal = LPAR _ expr _ RPAR _ TEMPORAL_BINARY _ LPAR _ expr _ RPAR
#
#     atom            = ID / (LPAR _ expr _ RPAR)
#
#     # Terminales
#     TEMPORAL_UNARY  = "X" / "F" / "G"
#     TEMPORAL_BINARY = "U" / "R"
#     NOT             = "!" / "~"
#     AND             = "&&" / "&"
#     OR              = "||" / "|"
#     IMPL            = "->"
#     BICOND          = "<->"
#     ID              = ~"[a-zA-Z_][a-zA-Z0-9_]*"
#
#     LPAR            = ~"\("
#     RPAR            = ~"\)"
#     _               = ~"\s*"
#     """)

grammar_ltl = Grammar(
           """
           Bicondicional = (Condicional "<->" Bicondicional) / Condicional
           Condicional = (Conjuncion "->" Condicional) / Conjuncion
           Conjuncion  = (Disyuncion Or Conjuncion) / Disyuncion
           Disyuncion  = (Literal And Disyuncion) / Literal
           Literal     = Atomo / (Not Literal)
           Atomo       = (Tempop Agrupacion) / Id / Agrupacion
           Agrupacion  = "(" Bicondicional ")"
           Tempop      = "X" / "F" / "G"
           Id          = ~"[a-z0-9_]+"
           Not         = "!" / "~"
           And         = "&&" / "&"
           Or          = "||" / "|"
           """
)
# ^([a-zA-Z_$][a-zA-Z\\d_$]*)$
# "[A-Za-z0-9_-]+"
#
# PARECE QUE FUNCIONA
# grammar_ltl = Grammar(
#     """
#         rules          = bicondicional
#
#         bicondicional  = condicional ( "<->" bicondicional )?
#         condicional    = conjuncion ( "->" condicional )?
#         conjuncion     = disyuncion ( and_op conjuncion )?
#         disyuncion     = literal ( or_op disyuncion )?
#         literal        = not_op? atom
#         atom           = (temporal_op? agrupacion) / id / agrupacion
#
#         agrupacion     = "(" bicondicional ")"
#
#         temporal_op    = "X" / "F" / "G"
#         not_op         = "!" / "~"
#         and_op         = "&&" / "&"
#         or_op          = "||" / "|"
#         id             = ~"[a-z0-9_]+"
#     """)

# grammar_ltl = Grammar(
#     r"""
#     Bicondicional = Condicional (BICOND Condicional)*
#
#     Condicional   = Disyuncion (IMPL Condicional)*
#
#     Disyuncion    = Conjuncion (OR Conjuncion)*
#
#     Conjuncion    = Literal (AND Literal)*
#
#     Literal       = (NOT Literal) / Atomo
#
#     Atomo         = (Tempop Agrupacion) / Agrupacion / Id
#
#     Agrupacion    = LPAR Bicondicional RPAR
#
#     Tempop        = "X" / "F" / "G"
#
#     Id            = ~"[a-zA-Z_][a-zA-Z0-9_]*"
#
#     NOT           = "!" / "~"
#     AND           = "&&" / "&"
#     OR            = "||" / "|"
#     IMPL          = "->"
#     BICOND        = "<->"
#
#     LPAR          = ~"\("
#     RPAR          = ~"\)"
#     """
# )


def parse_req_exp(exp, gramatica):
    # if gramatica == 'prop':
    #     iv = IniVisitor()
    #     tree = grammar_prop.parse(exp.replace(" ", ""))
    #     return iv.visit(tree)
    if gramatica == 'ltl':
        iv = IniVisitor()
        tree = grammar_ltl.parse(exp.replace(" ", ""))
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
    ltl_input = "(!gl&G(gl->X(gl))&!gr&G(gr->X(gr))&!al&G(al->X(al))&!ar&G(ar->X(ar))&!rl&G(rl->X(rl))&!rr&G(rr->X(rr)))->c1&G(gl->X(!c1))&c4&G(gr->X(!c4))&G(al->X(!c2))&G(ar->X(!c3))&G(!c2|!c3)&G((!gl&!gr)->(F(!c5|!c6)))&G((!gl&!al&!ar&!gr)->F(!c2&!c3&!c5&!c6))&G((!rl|!rr)->c9)&G((!rl&!rr)->c10)"
    innnnput = "((!gl & G(gl -> X(gl))) & (!gr & G(gr -> X(gr))) & (!al & G(al -> X(al))) & (!ar & G(ar -> X(ar))) & (!rl & G(rl -> X(rl))) & (!rr & G(rr -> X(rr)))) -> ((c1 & G(gl -> X(!c1))) & (c4 & G(gr -> X(!c4))) & G(al -> X(!c2)) & G(ar -> X(!c3)) & G(!c2 | !c3) & G((!gl & !gr) -> (F(!c5 | !c6))) & G((!gl & !al & !ar & !gr) -> F(!c2 & !c3 & !c5 & !c6)) & G((!rl | !rr) -> c9) & G((!rl & !rr) -> c10))"
    ltl_prove = "F(G(a))"
    otra_prueba = "((!i & G(F(i)) & G(F(!i))) -> ((o1 & !o2 & !o3) & G((o1 & !i & X(i)) -> (X(!o1) & X(o2) & X(!o3))) & G((o2 & !i & X(i)) -> (X(!o1) & X(!o2) & X(o3))) & G((o3 & !i & X(i)) -> (X(o1) & X(!o2) & X(!o3)))))"

    # tree = grammar_ltl.parse(ltl_prove)
    # print(tree)
    #str = '!F(a) | F(c)'
    print(parse_req_exp(otra_prueba, 'ltl'))

if __name__ == '__main__':
    main()
