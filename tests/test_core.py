import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))

import call
import general
from alg_paper import renaming
from generate_nuxmv import create_nusmv_file
from read_aalta_result import parse_aalta, parse_aalta_var_list


class RenamingTests(unittest.TestCase):
    def test_renames_identifier_at_every_operator_boundary(self):
        formula = 'a&(!a|X(a))->(b<->a)'
        self.assertEqual(
            renaming(formula, 'a', '_'),
            'a_&(!a_|X(a_))->(b<->a_)',
        )

    def test_does_not_rename_prefix_or_already_renamed_identifier(self):
        self.assertEqual(renaming('aa & a_ & a', 'a', '_'), 'aa & a_ & a_')


class GeneratedFileTests(unittest.TestCase):
    def test_nusmv_model_is_overwritten_not_appended(self):
        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory) / 'model.smv'
            create_nusmv_file([], ['a'], model_path)
            create_nusmv_file([], ['b'], model_path)
            contents = model_path.read_text()

        self.assertEqual(contents.count('MODULE main'), 1)
        self.assertNotIn('a: boolean', contents)
        self.assertIn('b: boolean', contents)


class AaltaParsingTests(unittest.TestCase):
    def _result_file(self, contents):
        handle = tempfile.NamedTemporaryFile(mode='w', delete=False)
        handle.write(contents)
        handle.close()
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)
        return handle.name

    def test_parses_sat_model_independent_of_line_number(self):
        path = self._result_file(
            'diagnostic\nplease input the formula:\nsat\n(\n{(! a),b,}\n)^w\n'
        )
        status, model = parse_aalta_var_list(path)
        self.assertEqual(status, 'sat')
        self.assertEqual(
            [(var.get_name(), var.get_value()) for var in model],
            [('a', False), ('b', True)],
        )

    def test_detects_changed_renamed_variable(self):
        path = self._result_file('prompt\nsat\n(\n{(! a),a_,}\n)^w\n')
        self.assertEqual(parse_aalta(path), ('sat', ['a']))

    def test_parses_unsat_and_rejects_missing_status(self):
        path = self._result_file('prompt\nunsat\n')
        self.assertEqual(parse_aalta(path), ('unsat', []))
        malformed = self._result_file('solver produced no answer\n')
        with self.assertRaises(ValueError):
            parse_aalta(malformed)


class ValidationTests(unittest.TestCase):
    def test_solver_can_be_selected_from_the_command_line(self):
        with patch.object(sys, 'argv', ['general.py', '--solver', 'aalta']):
            arguments = general.parse_arguments()
        self.assertEqual(arguments.solver, 'aalta')

    def test_partition_rejects_overlapping_groups(self):
        with patch.object(general, 'partition_recursive', return_value=[['a'], ['a']]):
            with self.assertRaisesRegex(RuntimeError, 'overlapping'):
                general.partition_general('a', ['a'], [], False, True)

    def test_simplifier_always_returns_text_booleans(self):
        simplify = getattr(general, '__simplify_tree')
        result = simplify(['->', 'a', 'True'])
        self.assertEqual(result, 'True')
        self.assertIsInstance(result, str)

    def test_environment_list_is_trimmed_and_deduplicated(self):
        self.assertEqual(general.extract_env_vars(' p, q, p, '), ['p', 'q'])

    def test_file_environment_variables_must_occur_in_formula(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt') as input_file:
            input_file.write('G(a)\nenv_vars: q\n')
            input_file.flush()
            with patch.object(sys, 'argv', ['general.py', '-f', input_file.name]):
                with self.assertRaisesRegex(SystemExit, "do not occur.*q"):
                    general.full_process(True, True)

    def test_counterexample_filters_current_and_treated_variables(self):
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as trace:
            trace_path = Path(trace.name)
        with patch.object(general, 'parse_xml', return_value=object()), patch.object(
            general, 'not_same_var', return_value=['env', 'a', 'b', 'b']
        ):
            self.assertEqual(
                general.ob_vars(['a'], ['env', 'a'], trace_path),
                ['b'],
            )
        self.assertFalse(trace_path.exists())


class SolverExecutionTests(unittest.TestCase):
    def test_trace_is_removed_when_solver_reports_syntax_error(self):
        trace_path = call.PROJECT_ROOT / 'unit_test_trace.xml'
        trace_path.write_text('stale')
        self.addCleanup(trace_path.unlink, missing_ok=True)
        completed = Mock(returncode=0, stdout='file model.smv: syntax error', stderr='')

        with patch('call._new_output_path', return_value=trace_path), patch(
            'call.subprocess.run', return_value=completed
        ):
            with self.assertRaises(call.SolverError):
                call.call_nusmv('model.smv', 'a', 'unit_test_trace')

        self.assertFalse(trace_path.exists())

    def test_each_solver_call_gets_a_unique_trace_path(self):
        first = call._new_output_path('counterexample', '.xml')
        second = call._new_output_path('counterexample', '.xml')
        self.assertNotEqual(first, second)
        self.assertFalse(first.exists())
        self.assertFalse(second.exists())


if __name__ == '__main__':
    unittest.main()
