"""The tests check known process termination and YAML worker transport."""

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import sys
import unittest
from unittest.mock import Mock, patch

import yaml

ROOT = next(path for path in Path(__file__).resolve().parents if (path / 'evaluations/harness.py').is_file())
sys.path.insert(0, str(ROOT / 'evaluations/open/ninja'))
import browse

START = 'Tue Oct 27 13:00:00 2026'
LATER = 'Tue Oct 27 13:00:01 2026'


def ps(rows=b'', returncode=None, error=None):
    return {'pid': [42, 43], 'returncode': int(not rows) if returncode is None else returncode, 'stdout': rows, 'stderr': b'', 'error': error}


def row(pid=42, started=START):
    return f'{pid} 1 42 {started} /owned/ninja\n'.encode()


def metrics():
    return {'pid': 42, 'peak_memory_processes': [{'pid': 42, 'started': START}, {'pid': 43, 'started': START}]}


def matching(termination=None):
    return {'returncode': 0, 'stdout': b'same', 'stderr': b'', 'files': {}, 'error': None, 'errors': [], 'termination': termination or {'qualified': True}, 'supervisor': {'returncode': 0, 'error': None, 'termination': {'qualified': True}}}


class TerminalTests(unittest.TestCase):
    def compare_fake(self, result):
        reference = browse.HERE / 'unused-reference'
        with patch.object(browse, 'play', return_value=result), patch.object(browse.harness, 'digest', side_effect=lambda path: browse.EXECUTE_SHA256 if path.name == 'compare.py' else browse.PIN):
            return browse.compare(reference, reference, [{'id': 'termination-control'}])

    def test_matching_views_with_live_known_child_fail(self):
        raw = ps(row(43))
        with patch.object(browse, 'identity', return_value=raw):
            termination = browse.terminal(metrics(), [ps(row())])
        self.assertFalse(termination['qualified'])
        self.assertEqual(termination['raw_ps'], raw)
        self.assertEqual([state['state'] for state in termination['states']], ['terminated', 'pending'])
        report = self.compare_fake(matching(termination))
        self.assertEqual(report['failed'], 1)
        self.assertIn('expected: The target terminal state is incomplete.', report['cases'][0]['differences'])

    def test_matching_inconclusive_terminal_checks_fail(self):
        raw = ps(row(), error='The process check timed out.')
        with patch.object(browse, 'identity', return_value=raw):
            termination = browse.terminal(metrics(), [ps(row())])
        self.assertFalse(termination['qualified'])
        self.assertEqual(termination['raw_ps']['stdout'], row())
        self.assertEqual(self.compare_fake(matching(termination))['failed'], 1)

    def test_incomplete_worker_termination_fails(self):
        result = matching()
        result['supervisor']['termination']['qualified'] = False
        self.assertEqual(self.compare_fake(result)['failed'], 1)

    def test_missing_terminal_measurement_fails(self):
        result = matching()
        del result['termination']
        self.assertEqual(self.compare_fake(result)['failed'], 1)

    def test_absent_known_processes_qualify(self):
        with patch.object(browse, 'identity', return_value=ps()):
            result = browse.terminal(metrics(), [ps(row())])
        self.assertTrue(result['qualified'])
        self.assertEqual({state['state'] for state in result['states']}, {'terminated'})

    def test_reused_pid_does_not_receive_a_signal(self):
        with patch.object(browse, 'identity', return_value=ps(row(42, LATER))), patch.object(browse.os, 'kill') as kill:
            result = browse.terminal(metrics(), [ps(row())])
        self.assertTrue(result['qualified'])
        self.assertEqual(result['states'][0]['state'], 'pid_reused')
        kill.assert_not_called()
        process = Mock(pid=42)
        process.poll.return_value = None
        self.assertIsNotNone(browse.signal_root(process, ps(row()), ps(row(42, LATER)), 'SIGINT'))
        process.send_signal.assert_not_called()

    def test_missing_start_time_is_inconclusive(self):
        with patch.object(browse, 'identity', return_value=ps()):
            result = browse.terminal({'pid': 42}, [ps()])
        self.assertFalse(result['qualified'])

    def test_invalid_ps_result_is_inconclusive(self):
        for raw in (ps(b'malformed\n'), ps(returncode=2), ps(row(), returncode=1), ps(returncode=0)):
            with self.subTest(raw=raw), patch.object(browse, 'identity', return_value=raw):
                self.assertFalse(browse.terminal(metrics(), [ps(row())])['qualified'])

    def test_signal_requires_a_current_owned_identity(self):
        process = Mock(pid=42)
        process.poll.return_value = None
        self.assertIsNone(browse.signal_root(process, ps(row()), ps(row()), 'SIGINT'))
        process.send_signal.assert_called_once_with(browse.signal.SIGINT)
        process.send_signal.reset_mock()
        self.assertIsNotNone(browse.signal_root(process, ps(row()), ps(error='The identity check timed out.'), 'SIGINT'))
        process.send_signal.assert_not_called()

    def test_worker_configuration_uses_yaml(self):
        case = {'id': 'yaml-transport', 'files': {'build.ninja': 'build all: phony\n'}, 'actions': []}
        def execute(command, **options):
            config_path = Path(command[-1])
            self.assertEqual(config_path.name, 'config.yaml')
            config = yaml.safe_load(config_path.read_text())
            self.assertEqual(config['case'], case)
            self.assertFalse(config_path.with_suffix('.json').exists())
            options['on_spawn'](SimpleNamespace(pid=42))
            (Path(config['root']) / 'result.yaml').write_text(yaml.safe_dump(matching()))
            return SimpleNamespace(returncode=0, stdout=b'', stderr=b''), None, metrics()
        with tempfile.TemporaryDirectory(dir=browse.HERE) as directory, patch.object(browse.harness.compare, 'execute', side_effect=execute), patch.object(browse, 'identity', side_effect=[ps(row()), ps()]):
            result = browse.play('/candidate', case, Path(directory) / 'run')
        self.assertTrue(result['supervisor']['termination']['qualified'])

    def test_loaded_helper_path_stays_strict(self):
        with patch.object(browse.harness.compare, '__file__', '/substitute/compare.py'), patch.object(browse.harness, 'digest', return_value=browse.EXECUTE_SHA256):
            with self.assertRaisesRegex(ValueError, 'differs from its pin'):
                browse.helper_pin()

    def test_original_pin_stays_strict(self):
        with patch.object(browse.harness, 'digest', side_effect=lambda path: browse.EXECUTE_SHA256 if path.name == 'compare.py' else 'changed'):
            with self.assertRaisesRegex(ValueError, 'original differs'):
                browse.compare(browse.HERE / 'reference', browse.HERE / 'candidate', [{'id': 'pin-control'}])

    def test_helper_pin_stays_strict(self):
        with patch.object(browse.harness, 'digest', return_value='changed'):
            with self.assertRaisesRegex(ValueError, 'differs from its pin'):
                browse.helper_pin()


if __name__ == '__main__':
    unittest.main()
