"""Immutable syntax for the prototype's Boolean/X/F/G fragment."""
import re
from dataclasses import dataclass
from req_parser import parse_req_exp


@dataclass(frozen=True)
class Formula:
    op: str
    args: tuple = ()

    @property
    def variables(self):
        if not self.args:
            return set() if self.op in ('TRUE', 'FALSE') else {self.op}
        return set().union(*(a.variables for a in self.args))

    def text(self, solver='nusmv'):
        if not self.args:
            if self.op in ('TRUE', 'FALSE') and solver == 'aalta':
                return self.op.lower()
            return self.op
        if len(self.args) == 1:
            return f'{self.op}({self.args[0].text(solver)})'
        return '(' + f' {self.op} '.join(a.text(solver) for a in self.args) + ')'


def parse_formula(text):
    def convert(tree):
        if isinstance(tree, str):
            return Formula({"true": "TRUE", "false": "FALSE"}.get(tree, tree))
        op = {'~': '!', '&&': '&', '||': '|'}.get(tree[0], tree[0])
        return Formula(op, tuple(convert(a) for a in tree[1:]))
    text = re.sub(r'\b(TRUE|FALSE)\b', lambda m: m.group().lower(), text)
    return convert(parse_req_exp(text, 'ltl'))


TRUE, FALSE = Formula('TRUE'), Formula('FALSE')


def conjunction(items):
    items = tuple(items)
    return TRUE if not items else items[0] if len(items) == 1 else Formula('&', items)


def conjuncts(node):
    return list(node.args) if node.op == '&' else [node]


def substitute(node, values):
    """Replace whole signals (also below temporal operators)."""
    if not node.args:
        return values.get(node.op, node)
    return Formula(node.op, tuple(substitute(a, values) for a in node.args))
