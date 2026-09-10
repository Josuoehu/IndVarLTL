"""Exact rewrites and context propagation; no temporal CNF expansion."""
from ltl_ast import Formula as F, TRUE, FALSE, conjunction


def nnf(n, negative=False):
    op, a = n.op, n.args
    if op == '!':
        return nnf(a[0], not negative)
    if op == '->':
        return nnf(F('|', (F('!', (a[0],)), a[1])), negative)
    if op == '<->':
        return nnf(conjunction((F('->', a), F('->', (a[1], a[0])))), negative)
    if not a:
        if n in (TRUE, FALSE):
            return (FALSE if n == TRUE else TRUE) if negative else n
        return F('!', (n,)) if negative else n
    if op in ('&', '|'):
        return F(({'&': '|', '|': '&'}[op] if negative else op),
                 tuple(nnf(x, negative) for x in a))
    if op in ('G', 'F', 'X'):
        return F(({'G': 'F', 'F': 'G', 'X': 'X'}[op] if negative else op),
                 (nnf(a[0], negative),))
    raise ValueError(f'Unsupported operator: {op}')


def literal(n):
    if not n.args and n not in (TRUE, FALSE):
        return n.op, True
    if n.op == '!' and not n.args[0].args:
        return n.args[0].op, False
    return None


def rewrite(n):
    """Expose conjuncts before NNF erases implication structure."""
    a = tuple(rewrite(x) for x in n.args)
    if n.op == '<->':
        return rewrite(conjunction((F('->', a), F('->', (a[1], a[0])))))
    if n.op in ('G', 'X') and a[0].op == '&':
        return conjunction(rewrite(F(n.op, (x,))) for x in a[0].args)
    if n.op == '->':
        if a[1].op == '&':
            return conjunction(rewrite(F('->', (a[0], x))) for x in a[1].args)
        if a[0].op == '|':
            return conjunction(rewrite(F('->', (x, a[1]))) for x in a[0].args)
    return F(n.op, a)


def _pass(n, now, always, contextual=True):
    lit = literal(n)
    if lit:
        name, sign = lit
        value = now.get(name, always.get(name))
        return n if value is None else TRUE if value == sign else FALSE
    if not n.args:
        return n
    if n.op in ('X', 'F', 'G'):
        # Current-state facts never cross a temporal boundary.
        child = _pass(n.args[0], {}, always, contextual)
        if child in (TRUE, FALSE):
            return child
        if n.op in ('G', 'X') and child.op == '&':
            return conjunction(F(n.op, (x,)) for x in child.args)
        return F(n.op, (child,))
    args = []
    for child in n.args:
        child = _pass(child, now, always, contextual)
        args.extend(child.args if child.op == n.op else (child,))
    args = list(dict.fromkeys(args))
    identity, absorbing = (TRUE, FALSE) if n.op == '&' else (FALSE, TRUE)
    if absorbing in args:
        return absorbing
    args = [x for x in args if x != identity]
    signs = {}
    for child in args:
        lit = literal(child)
        if lit:
            if lit[0] in signs and signs[lit[0]] != lit[1]:
                return absorbing
            signs[lit[0]] = lit[1]
    # Sequential updates preserve at least one justification for each fact.
    for index, child in enumerate(args) if contextual else ():
        local, global_facts = dict(now), dict(always)
        for j, sibling in enumerate(args):
            if j == index:
                continue
            lit = literal(sibling)
            if lit:
                local[lit[0]] = lit[1] if n.op == '&' else not lit[1]
            if n.op == '&' and sibling.op == 'G':
                lit = literal(sibling.args[0])
                if lit:
                    global_facts[lit[0]] = lit[1]
        args[index] = _pass(child, local, global_facts, contextual)
    if absorbing in args:
        return absorbing
    args = list(dict.fromkeys(x for x in args if x != identity))
    return identity if not args else args[0] if len(args) == 1 else F(n.op, tuple(args))


def simplify(n, contextual=True):
    n = nnf(rewrite(n))
    while True:
        result = _pass(n, {}, {}, contextual)
        if result == n:
            return n
        n = result


def polarities(n):
    result = {}
    def visit(x):
        lit = literal(x)
        if lit:
            result.setdefault(lit[0], set()).add(lit[1])
        else:
            for child in x.args:
                visit(child)
    visit(nnf(n))
    return result
