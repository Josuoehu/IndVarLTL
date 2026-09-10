import io
import sys
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
             patch('general.partition_general', return_value=[['a']]) as partition, \
             patch('general.decompose_ltl', return_value=result) as extract, \
             patch('builtins.input', return_value=answer) as ask, redirect_stdout(output):
            response = general.full_process(True, True, args)
        partition.assert_called_once()
        self.assertIn('Independent system variable sets:', output.getvalue())
        return response, extract, ask

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
