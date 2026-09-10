import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from call import SolverError
from ltl_ast import parse_formula, Formula, TRUE
from ltl_simplify import simplify, polarities
from ltl_decompose import decompose_ltl
from ltl_certify import certify, satisfiable


class ExtractionTests(unittest.TestCase):
    def test_polarity_accounts_for_implication_and_equivalence(self):
        self.assertEqual(polarities(parse_formula('G(a -> !b)')), {'a': {False}, 'b': {False}})
        self.assertEqual(polarities(parse_formula('a <-> b')), {'a': {True, False}, 'b': {True, False}})

    def test_invalid_partition_rejected_before_solver(self):
        for groups in ([['a'], ['a', 'b']], [['a']], [['a'], []]):
            with self.assertRaises(ValueError):
                decompose_ltl('a & b', [], groups)

    def test_solver_failure_cannot_certify(self):
        with patch('ltl_decompose.certify', side_effect=SolverError('no answer')):
            result = decompose_ltl('G(a)', [], [['a']])
        self.assertEqual(result.status, 'unknown')
        self.assertIn('no answer', result.reason)

    def test_missing_validity_answer_rejected(self):
        from unittest.mock import Mock
        with patch('ltl_certify._run', return_value=Mock(stdout='no result')):
            with self.assertRaises(SolverError):
                satisfiable(parse_formula('a'), 'nusmv')


@unittest.skipUnless(shutil.which('NuSMV') and
                    (Path(__file__).resolve().parents[1] / 'scripts/call_nusmv.sh').exists(),
                    'NuSMV and its configured launcher are needed')
class SemanticTests(unittest.TestCase):
    def assertEquivalent(self, left, right):
        valid, witness = certify(parse_formula(left), parse_formula(right), 'nusmv')
        self.assertTrue(valid, witness)

    def test_global_context_recovers_independent_factors(self):
        result = decompose_ltl('G(b) & G(a | !b)', [], [['a'], ['b']])
        self.assertEqual(result.status, 'certified')
        self.assertEquivalent(result.components[0], 'G(a)')
        self.assertEquivalent(result.components[1], 'G(b)')

    def test_running_example(self):
        root = Path(__file__).resolve().parents[1]
        formula = (root / 'files/running_example.txt').read_text().split('env_vars:')[0].strip()
        result = decompose_ltl(formula, ['p'], [['v', 'w', 'u'], ['t']])
        self.assertEqual(result.status, 'certified', result.reason)
        for text, allowed in zip(result.components, ({'p','v','w','u'}, {'p','t'})):
            self.assertLessEqual(parse_formula(text).variables, allowed)

    def test_invalid_split_rejected_with_witness(self):
        for formula in ('G(a | b)', 'F(a & b)'):
            result = decompose_ltl(formula, [], [['a'], ['b']])
            self.assertEqual(result.status, 'incomplete')
            self.assertEqual(result.counterexample['direction'], 'components_to_original')

    def test_initial_fact_does_not_fix_future(self):
        original = parse_formula('b & X(!b)')
        self.assertTrue(certify(original, simplify(original), 'nusmv')[0])
        self.assertTrue(satisfiable(simplify(original), 'nusmv')[0])

    def test_contextual_rules_preserve_languages(self):
        examples = [
            'G(a) & G(b) & G(a <-> b)',
            'a & (a | b)', '!a & (a | b)',
            'a | (a & b)', '!a | (a & b)',
            'a | X(a)', 'a & F(!a)', 'G(a) & F(!a)',
            '(a | G(a)) & X(!a)',
            'G(a) & (a | X(b))',
            'G(a -> (b & !c))', 'X(a & b)',
            '(a | b) -> G(c)', '!G(a & F(b))',
            '(G(a) & G(b)) | (G(c) & F(!c))',
        ]
        for text in examples:
            with self.subTest(text=text):
                original = parse_formula(text)
                self.assertTrue(certify(original, simplify(original), 'nusmv')[0])

    def test_shared_input_obligation_preserved(self):
        result = decompose_ltl('G(p) & G(a) & G(b)', ['p'], [['a'], ['b']])
        self.assertEqual(result.status, 'certified')
        for component in result.components:
            self.assertIn('p', parse_formula(component).variables)

    def test_positive_projection_and_mixed_context(self):
        result = decompose_ltl('F(a) & F(b) & F(a | b)', [], [['a'], ['b']])
        self.assertEqual(result.status, 'certified', result.reason)
        self.assertEquivalent(result.components[0], 'F(a)')
        self.assertEquivalent(result.components[1], 'F(b)')


if __name__ == '__main__':
    unittest.main()
