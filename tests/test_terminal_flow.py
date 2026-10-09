import io
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import general
from ltl_decompose import DecompositionResult, format_result


class TerminalFlowTests(unittest.TestCase):
    def run_flow(self, answer='', interactive=True, complete=False, partition_only=False):
        args = Namespace(decompose=complete, partition_only=partition_only)
        result = DecompositionResult('certified', ['G(a)'], env_vars=['p'], output_groups=[['a']])
        output = io.StringIO()
        with patch('general.__get_formula', return_value=('G(p -> a)', ['p'], '')), \
             patch('general.sys.stdin.isatty', return_value=interactive), \
             patch('general.satisfiable', return_value=(True, '')), \
             patch('general.partition_general', return_value=[['a']]) as partition, \
             patch('general.decompose_ltl', return_value=result) as extract, \
             patch('builtins.input', return_value=answer) as ask, redirect_stdout(output):
            response = general.full_process(True, True, args)
        partition.assert_called_once()
        self.assertIn('Independent system variable sets:', output.getvalue())
        return response, extract, ask

    def test_unsatisfiable_formula_stops_before_partition(self):
        with patch('general.__get_formula', return_value=('q & G(q) & (a U !q)', [], '')), \
             patch('general.sys.stdin.isatty', return_value=False), \
             patch('general.satisfiable', return_value=(False, '')), \
             patch('general.partition_general') as partition:
            with self.assertRaisesRegex(SystemExit, 'UNSATISFIABLE'):
                general.full_process(True, True, Namespace())
        partition.assert_not_called()

    def test_file_distinguishes_missing_and_empty_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'formula.txt'
            for declaration, expected in (('', None), ('env_vars:', []), ('env_vars: a', ['a'])):
                path.write_text('a & b\n' + declaration)
                self.assertEqual(general.terminal_use(Namespace(filename=str(path)))[1], expected)

    def test_no_temporal_operators_still_use_ltl_and_ask_for_inputs(self):
        with patch('general.__get_formula', return_value=('a & b', None, '')), \
             patch('general.sys.stdin.isatty', return_value=True), \
             patch('general.satisfiable', return_value=(True, '')), \
             patch('general.partition_general', return_value=[['b']]) as partition, \
             patch('builtins.input', return_value='a') as ask, redirect_stdout(io.StringIO()):
            response = general.full_process(True, True, Namespace(partition_only=True))
        ask.assert_called_once()
        partition.assert_called_once_with('a & b', ['b'], ['a'], True, True)
        self.assertEqual(response[3], ['a'])

    def test_explicit_empty_environment_does_not_prompt(self):
        with patch('general.__get_formula', return_value=('a & b', [], '')), \
             patch('general.sys.stdin.isatty', return_value=True), \
             patch('general.satisfiable', return_value=(True, '')), \
             patch('general.partition_general', return_value=[['a'], ['b']]) as partition, \
             patch('builtins.input') as ask, redirect_stdout(io.StringIO()):
            general.full_process(True, True, Namespace(partition_only=True))
        ask.assert_not_called()
        partition.assert_called_once_with('a & b', ['a', 'b'], [], True, True)

    def test_batch_requires_environment_even_with_decompose(self):
        with patch('general.__get_formula', return_value=('a & b', None, '')), \
             patch('general.sys.stdin.isatty', return_value=False), \
             patch('general.satisfiable') as solver, patch('builtins.input') as ask:
            with self.assertRaisesRegex(SystemExit, 'Environment variables are not specified'):
                general.full_process(True, True, Namespace(decompose=True))
        solver.assert_not_called()
        ask.assert_not_called()

    def test_yes_reuses_partition(self):
        response, extract, ask = self.run_flow('y')
        extract.assert_called_once_with('G(p -> a)', ['p'], [['a']], 'nusmv')
        ask.assert_called_once_with('\nCompute the full formula decomposition? [y/N]: ')
        self.assertEqual(response[1].status, 'certified')

    def test_no_or_enter_stops_after_partition(self):
        for answer in ('', 'n'):
            response, extract, ask = self.run_flow(answer)
            extract.assert_not_called()
            self.assertIsNone(response[1])

    def test_noninteractive_does_not_ask(self):
        response, extract, ask = self.run_flow(interactive=False)
        ask.assert_not_called()
        extract.assert_not_called()

    def test_decompose_flag_bypasses_question(self):
        response, extract, ask = self.run_flow(interactive=False, complete=True)
        ask.assert_not_called()
        extract.assert_called_once()

    def test_partition_only_suppresses_question(self):
        response, extract, ask = self.run_flow(partition_only=True)
        ask.assert_not_called()
        extract.assert_not_called()

    def test_result_layout_and_uncertified_label(self):
        result = DecompositionResult('certified', ['G(a)'], env_vars=['p'], output_groups=[['a']])
        text = format_result(result)
        self.assertIn('Result: CERTIFIED\n\nComponent 1:', text)
        self.assertIn('  Environment vars: {p}', text)
        self.assertIn('  System vars: {a}', text)
        result.status = 'unknown'
        text = format_result(result)
        self.assertIn('Candidate 1:', text)
        self.assertNotIn('GUARANTEED', text)


if __name__ == '__main__':
    unittest.main()
