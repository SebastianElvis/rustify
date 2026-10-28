"""The tests check browse comparison boundaries without a candidate."""

from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

ROOT = next(path for path in Path(__file__).resolve().parents if (path / 'evaluations/harness.py').is_file())
sys.path.insert(0, str(ROOT / 'evaluations/open/ninja'))
import browse


class BrowseTests(unittest.TestCase):
    def test_date_changes_only_current_header(self):
        data = b'HTTP/1.0 200 OK\r\nDate: Tue, 27 Oct 2026 05:00:00 GMT\r\n\r\nDate: raw body\n'
        result = {'wall_start_ns': 1793077200 * 10**9, 'wall_end_ns': 1793077201 * 10**9}
        self.assertEqual(browse.response_view(data, result), b'HTTP/1.0 200 OK\r\nDate: <DATE>\r\n\r\nDate: raw body\n')

    def test_stale_or_invalid_date_stays_exact(self):
        for date in (b'invalid', b'Tue, 27 Oct 2026 05:00:00 GMT'):
            data = b'HTTP/1.0 200 OK\r\nDate: ' + date + b'\r\n\r\n'
            self.assertEqual(browse.response_view(data, {'wall_start_ns': 0, 'wall_end_ns': 1}), data)

    def test_pid_and_port_rules_keep_other_bytes(self):
        result = {'setup': {'port': 123}, 'resources': {'pid': 456}, 'stdout': b'127.0.0.1:123 other 123', 'stderr': b'Web server pid 456\nother 456\n'}
        view = browse.view(result)
        self.assertEqual(view['stdout'], b'127.0.0.1:<PORT> other 123')
        self.assertEqual(view['stderr'], b'Web server pid <PID>\nother 456\n')

    def test_file_bytes_stay_in_comparison(self):
        left = {'files': {'f': {'data_b64': 'YQ=='}}}
        right = {'files': {'f': {'data_b64': 'Yg=='}}}
        self.assertNotEqual(browse.view(left), browse.view(right))

    def test_matching_execution_errors_fail(self):
        reference = browse.HERE / 'unused-reference'
        bad = {'error': 'The process exceeded the time limit.', 'errors': [], 'supervisor': {'returncode': 0, 'error': None}}
        with patch.object(browse, 'play', return_value=bad), patch.object(browse.harness, 'digest', side_effect=lambda path: browse.EXECUTE_SHA256 if path.name == 'compare.py' else browse.PIN):
            report = browse.compare(reference, reference, [{'id': 'bounded-failure'}])
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['failed'], 1)

    def test_snapshot_rejects_large_file(self):
        with tempfile.TemporaryDirectory(dir=browse.HERE) as directory:
            path = Path(directory) / 'large'
            with path.open('wb') as stream:
                stream.truncate(8 * 1024 * 1024 + 1)
            with self.assertRaisesRegex(ValueError, '8 MiB'):
                browse.snapshot(Path(directory), {})


if __name__ == '__main__':
    unittest.main()
