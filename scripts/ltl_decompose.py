"""Construct and certify LTL factors for an already supplied output partition."""
from dataclasses import dataclass, field
from call import SolverError
from ltl_ast import parse_formula, conjunction, conjuncts, substitute, TRUE, FALSE
from ltl_simplify import simplify, polarities
from ltl_certify import certify


@dataclass
class DecompositionResult:
    status: str
    components: list = field(default_factory=list)
    residual: list = field(default_factory=list)
    counterexample: dict | None = None
    reason: str | None = None


def decompose_ltl(formula, env_vars, independent_groups, solver='nusmv'):
    original = parse_formula(formula)
    inputs = set(env_vars)
    groups = [set(group) for group in independent_groups]
    outputs = [v for group in independent_groups for v in group]
    if (any(not group for group in groups) or len(outputs) != len(set(outputs))
            or inputs & set(outputs) or inputs | set(outputs) != original.variables):
        raise ValueError('Inputs and disjoint nonempty output groups must cover exactly the formula variables')
    normalized = simplify(original, contextual=False)
    requirements = conjuncts(normalized)
    residual = [r for r in requirements
                if sum(bool(r.variables & group) for group in groups) > 1]
    # Step 3: keep all assigned requirements as context for mixed requirements.
    if residual:
        normalized = simplify(normalized)
        requirements = conjuncts(normalized)
        residual = [r for r in requirements
                    if sum(bool(r.variables & group) for group in groups) > 1]
    candidates = []
    for group in groups:
        allowed = inputs | group
        # Already local requirements remain valid even if projection gets stuck.
        local = [r for r in requirements if r.variables <= allowed]
        if residual:
            # Project the WHOLE simplified formula, retaining assigned context.
            projected = normalized
            while True:
                signs = polarities(projected)
                values = {v: TRUE if signs[v] == {True} else FALSE
                          for v in projected.variables - allowed if len(signs[v]) == 1}
                if not values:
                    break
                projected = simplify(substitute(projected, values))
            local.extend(r for r in conjuncts(projected) if r.variables <= allowed)
        candidates.append(simplify(conjunction(local)))
    # With no outputs, retain the input-only specification as a shared obligation.
    if not groups:
        candidates = [normalized]
    result = DecompositionResult(
        status='incomplete', components=[c.text() for c in candidates],
        residual=[r.text() for r in residual],
    )
    try:
        valid, witness = certify(original, conjunction(candidates), solver)
        result.status = 'certified' if valid else 'incomplete'
        result.counterexample = witness
        if valid:
            result.residual = []
        else:
            result.reason = 'The extracted candidates do not reconstruct the original formula.'
    except (SolverError, OSError, ValueError) as exc:
        result.status = 'unknown'
        result.reason = str(exc)
    return result


def format_result(result):
    lines = [f'LTL extraction: {result.status}']
    label = 'Component' if result.status == 'certified' else 'Candidate (not certified)'
    lines.extend(f'{label} {i}: {formula}' for i, formula in enumerate(result.components, 1))
    if result.residual:
        lines.append('Mixed requirements: ' + ' & '.join(result.residual))
    if result.reason:
        lines.append(result.reason)
    if result.counterexample:
        lines.append('Failed implication: ' + result.counterexample['direction'])
        lines.append(result.counterexample['trace'])
    return '\n'.join(lines)
