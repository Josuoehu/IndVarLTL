from parsimonious import *
from enum import Enum


class Var(object):
    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def write_pr_var(self):
        return self.name + '_ : '

    def __str__(self):
        v = self.name + ' : '
        return v


# class OVar(Var):
#     def __init__(self, name, typ, initial):
#         super().__init__(name)
#         self.type = typ
#         self.initial = initial
#
#         def get_type(self):
#             return self.typ
#
#     def get_initial(self):
#         return self.initial


class EVar(Var):

    def __init__(self, name, maxim, minim):
        self.maxim = maxim
        self.minim = minim
        super(EVar, self).__init__(name)

    def get_max(self):
        return self.maxim

    def get_min(self):
        return self.minim

    def __str__(self):
        v = super().__str__() + str(self.get_min()) + '..' + str(self.maxim)
        return v


class RVar(Var):
    def __init__(self, name, maxim, minim):
        self.maxim = maxim
        self.minim = minim
        super(RVar, self).__init__(name)

    def get_max(self):
        return self.maxim

    def get_min(self):
        return self.minim

    def __str__(self):
        v = super().__str__() + str(self.minim) + '..' + str(self.maxim)
        return v


class EVarI(EVar):
    def __init__(self, name, ma, mi, value):
        self.value = value
        super(EVarI, self).__init__(name, ma, mi)

    def get_value(self):
        return self.value

    def str2(self):
        s = self.get_name() + ' := ' + str(self.get_value())
        return s

    def __str__(self):
        if self.get_min() is None or self.get_max() is None:
            return self.get_name() + ' : Integer'
        else:
            return super().__str__()

    def __eq__(self, other):
        if type(other) == EVarI:
            if self.name == other.get_name() and self.value == other.get_value():
                return True
            else:
                return False
        else:
            return False


class RVarI(RVar):
    def __init__(self, name, ma, mi, value):
        self.value = value
        super(RVarI, self).__init__(name, ma, mi)

    def get_value(self):
        return self.value

    def str2(self):
        s = self.get_name() + ' := ' + str(self.get_value())
        return s

    def __str__(self):
        if self.get_min() is None or self.get_max() is None:
            return self.get_name() + ' : Real'
        else:
            return super().__str__()

    def __eq__(self, other):
        if type(other) == RVarI:
            if self.name == other.get_name() and self.value == other.get_value():
                return True
            else:
                return False
        else:
            return False


class SVar(Var):
    def __init__(self, name, values):
        # super().set_name(name)
        self.values = values
        super(SVar, self).__init__(name)

    def get_values(self):
        return self.values

    def set_value(self, values):
        self.values = values

    def __str__(self):
        vi = super().__str__() + '{'
        for v in self.values:
            vi = vi + v + ', '
        vi = vi[:-2] + '}'
        return vi


class SVarI(SVar):
    def __init__(self, name, value, values):
        self.value = value
        super(SVarI, self).__init__(name, values)

    def get_value(self):
        return self.value

    def __eq__(self, o: object) -> bool:
        if type(o) == SVarI:
            if self.name == o.get_name() and self.value == o.get_value():
                return True
            else:
                return False

    def __str__(self):
        if self.value is not None:
            return self.name + ' := ' + self.value
        else:
            super()


class AritVar(Var):

    def __init__(self, name, exi, op, exd):
        self.exi = exi
        self.op = op
        self.exd = exd
        super(AritVar, self).__init__(name)

    def get_exp_right(self):
        return self.exd

    def get_exp_left(self):
        return self.exi

    def get_op(self):
        return self.op


class BVar(Var):
    def __init__(self, name):
        # super().set_name(name)
        super(BVar, self).__init__(name)

    def write_pr_var(self):
        return super().write_pr_var() + 'boolean'

    def __str__(self):
        v = super().__str__() + 'boolean'
        return v


class BVarI(BVar):
    def __init__(self, name, value):
        self.value = value
        super(BVarI, self).__init__(name)

    def get_value(self):
        return self.value

    def get_value_str(self):
        if self.get_value():
            return 'TRUE'
        else:
            return 'FALSE'

    def str2(self):
        v = self.get_name() + ' := ' + str(self.value)
        return v

    def eq_name_p(self, o: object):
        if type(o) == BVarI:
            return self.get_name() == o.get_name() + "_" or self.get_name() + "_" == o.get_name()
        else:
            return False

    def __str__(self):
        v = super().__str__()
        return v

    def __eq__(self, o: object) -> bool:
        if type(o) == BVarI:
            if self.name == o.get_name():  # and self.value == o.get_value():
                return True
            else:
                return False


class Types(Enum):
    BOOLEAN = 1
    STATE = 2
    REAL = 3
    INTEGER = 4


class Node(object):
    def __init__(self):
        # Valor is a list of Var
        self.variables = []

    def get_variables(self):
        return self.variables

    def add_variable(self, var):
        self.variables.append(var)

    def add_variables(self, vars):
        for x in vars:
            self.variables.append(x)

    def __str__(self):
        a = ''
        for v in self.variables:
            a = a + ', ' + str(v)
        a = a + ']'
        return '[' + a[2:]


class Edge(object):
    def __init__(self, src, dest, weight):
        self.src = src
        self.dest = dest
        self.weight = weight

    def get_source(self):
        return self.src

    def get_destination(self):
        return self.dest

    def get_weight(self):
        return self.weight

    def __str__(self):
        return str(self.src) + '--' + str(self.weight) + '-->' + \
            str(self.dest)


class Digraph(object):
    # node is a list of the nodes in the graph
    # edges is a dict mapping each node to
    # a list of its children
    def __init__(self):
        self.nodes = []
        self.edges = {}

    def add_node(self, node):
        if node in self.nodes:
            raise ValueError('Duplicate Node')
        else:
            self.nodes.append(node)
            self.edges[node] = []

    def add_edge(self, edge):
        src = edge.get_source()
        dest = edge.get_destination()
        w = edge.get_weight()
        arista = (w, dest)
        if not (src in self.nodes and dest in self.nodes):
            raise ValueError('Node not in graph')
        self.edges[src].append(arista)

    def children_of(self, node):
        return self.edges[node]

    def has_node(self, node):
        return node in self.nodes

    def __str__(self):
        result = ''
        for src in self.nodes:
            for ar in self.edges[src]:
                result = result + str(src) + \
                         '---(' + str(ar[0]) + ')--->' + str(ar[1]) + '\n'
        return result[:-1]  # remove last newline


class IniVisitor(NodeVisitor):
    # def visit_expr(self, node, visited_children):
    #     """ Returns the overall output. """
    #     output = {}
    #     for child in visited_children:
    #         output.update(child[0])
    #     return output
    #
    # def visit_entry(self, node, visited_children):
    #     """ Makes a dict of the section (as key) and the key/value pairs. """
    #     key, values = visited_children
    #     return {key: dict(values)}
    #
    # def visit_section(self, node, visited_children):
    #     """ Gets the section name. """
    #     _, section, *_ = visited_children
    #     return section.text
    #
    # def visit_pair(self, node, visited_children):
    #     """ Gets each key/value pair, returns a tuple. """
    #     key, _, value, *_ = node.children
    #     return key.text, value.text

    def generic_visit(self, node, children):
        if len(children) == 0:
            return node.text
        elif len(children) == 1:
            return children[0]
        elif len(children) == 2:
            return [children[0], children[1]]
        elif children[0] == "(":
            return children[1]
        elif children[1] == "&" or children[1] == "&&":
            return ["&", children[0], children[2]]
        elif children[1] == "|" or children[1] == "||":
            return ["|", children[0], children[2]]
        else:
            return [children[1], children[0], children[2]]


def main():
    entero = RVar("hola", 5, 1)
    print(str(entero))


if __name__ == '__main__':
    main()
