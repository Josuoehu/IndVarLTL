"""Require explicit solver answers to certify both implication directions."""
import re
import tempfile
from pathlib import Path
from call import _run, SolverError
from project_paths import SCRIPTS_DIR
from ltl_ast import Formula as F


def satisfiable(formula, solver):
    """Return (is_sat, raw witness/output); raise on missing/failed answers."""
    with tempfile.TemporaryDirectory(prefix='indvar_cert_') as directory:
        root = Path(directory)
        if solver == 'aalta':
            source, target = root / 'formula.ltl', root / 'result.txt'
            source.write_text(formula.text('aalta'))
            _run([SCRIPTS_DIR / 'call_aalta.sh', source, target], cwd=root)
            output = target.read_text()
            answers = re.findall(r'^(sat|unsat)\s*$', output, re.M)
            if len(answers) != 1:
                raise SolverError('Aalta did not return one explicit SAT/UNSAT answer')
            return answers[0] == 'sat', output
        if solver != 'nusmv':
            raise ValueError('solver must be nusmv or aalta')
        model, trace = root / 'model.smv', root / 'trace.xml'
        declarations = '\n'.join(f'{v}: boolean;' for v in sorted(formula.variables))
        model.write_text('MODULE main\n' + ('VAR\n' + declarations if declarations else ''))
        command = (f'go;check_ltlspec -p "!({formula.text()})"; '
                   f'show_traces -p 4 -o "{trace}";quit')
        completed = _run([SCRIPTS_DIR / 'call_nusmv.sh', command, model], cwd=root)
        answers = re.findall(r'-- specification .* is (true|false)\s*$', completed.stdout, re.M)
        if len(answers) != 1:
            raise SolverError('NuSMV did not return one explicit validity answer')
        sat = answers[0] == 'false'
        return sat, trace.read_text() if sat and trace.exists() else completed.stdout


def certify(original, candidate, solver):
    for direction, left, right in (
        ('original_to_components', original, candidate),
        ('components_to_original', candidate, original),
    ):
        sat, witness = satisfiable(F('&', (left, F('!', (right,)))), solver)
        if sat:
            return False, {'direction': direction, 'trace': witness}
    return True, None
