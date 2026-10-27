"""The tests check the proposed report integration without benchmark cases."""

import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = next(path for path in HERE.parents if (path / 'evaluations/harness.py').is_file())
PROPOSED = HERE / 'run.proposed.py'
if not PROPOSED.exists():
    PROPOSED = ROOT / 'evaluations/open/ninja/run.py'


def report(status='passed', error=None, count=9):
    row = {'id': 'private-placeholder', 'passed': status == 'passed', 'expected': {'error': error, 'errors': [], 'termination': {'qualified': True}, 'supervisor': {'returncode': 0, 'error': None, 'termination': {'qualified': True}}}, 'actual': {'stdout': b'raw'}}
    return {'status': status, 'passed': count if status == 'passed' else 0, 'failed': 0 if status == 'passed' else count, 'cases': [dict(deepcopy(row), id=f'private-placeholder-{index}') for index in range(count)]}


def score(control=None, replay=None, negative=None):
    tree = ast.parse(PROPOSED.read_text())
    tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    responses = iter([control or report(), replay or report(), negative or report('failed')])
    scope = {
        'Path': Path,
        'tempfile': SimpleNamespace(TemporaryDirectory=lambda: tempfile.TemporaryDirectory(dir=HERE)),
        'upstream': SimpleNamespace(sources=lambda: {}, unit_scenarios=lambda files: {}, inventory=lambda files: {}, SCRIPTS={}),
        'cases': SimpleNamespace(milestones=lambda: {'core': [{'id': 'placeholder', 'steps': [{}]}]}),
        'generate': SimpleNamespace(scenarios=lambda: []),
        'runner': SimpleNamespace(compare=lambda expected, actual, items: report('failed' if actual[0][0] == 'wrong' else 'passed', count=1)),
        'browse': SimpleNamespace(compare=lambda *args: deepcopy(next(responses))),
    }
    exec(compile(tree, 'run.proposed.py', 'exec'), scope)
    return scope['score']('/original', '/candidate', '/project')


class IntegrationTests(unittest.TestCase):
    def test_controls_do_not_add_behavior_cases(self):
        reports, failures = score()
        self.assertEqual(failures, [])
        self.assertNotIn('repeatability-browse', reports)
        self.assertEqual(reports['repeatability']['passed'], 1)
        self.assertEqual(reports['repeatability']['browse']['passed'], 9)
        self.assertEqual(reports['replay-browse']['passed'], 9)
        self.assertEqual(reports['repeatability']['control_counts'], {'legacy_repeatability': {'passed': 1, 'failed': 0}, 'browse_repeatability': {'passed': 9, 'failed': 0}})

    def test_raw_captures_survive_harness_pruning(self):
        reports, _ = score()
        for value in reports.values():
            value['cases'] = [{'id': row['id'], 'passed': True} if row['passed'] else row for row in value['cases']]
        self.assertEqual(reports['replay-browse']['raw_cases'][0]['actual']['stdout'], b'raw')
        self.assertEqual(reports['repeatability']['browse']['cases'][0]['actual']['stdout'], b'raw')

    def test_reference_failure_invalidates_repeatability(self):
        reports, _ = score(control=report('failed'))
        self.assertEqual(reports['repeatability']['status'], 'failed')
        reports, _ = score(replay=report('failed', 'The reference exceeded its limit.'))
        self.assertEqual(reports['repeatability']['status'], 'failed')

    def test_incomplete_reference_termination_invalidates_repeatability(self):
        replay = report()
        replay['cases'][0]['expected']['termination']['qualified'] = False
        reports, _ = score(replay=replay)
        self.assertEqual(reports['repeatability']['status'], 'failed')

    def test_candidate_failure_keeps_original_control_valid(self):
        reports, _ = score(replay=report('failed'))
        self.assertEqual(reports['repeatability']['status'], 'passed')
        self.assertEqual(reports['replay-browse']['status'], 'failed')

    def test_wrong_candidate_must_fail(self):
        _, failures = score(negative=report())
        self.assertEqual(failures, ['The control without a browse service passes.'])


if __name__ == '__main__':
    unittest.main()
