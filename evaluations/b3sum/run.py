#!/usr/bin/env python3
"""Replay the b3sum reconstruction evaluation."""

import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PROJECT = ROOT / 'target'
RECOVERED = PROJECT / 'recovered'
VERIFICATION = PROJECT / 'verification'
WORK = REPO / 'work/evaluation/b3sum'
BINARY_SHA256 = '97017f4477d872b24752a9bdbe48a6e0296fe1a66fc4787906c20c040b15c299'
BINARY_URL = 'https://github.com/BLAKE3-team/BLAKE3/releases/download/1.8.7/b3sum_macos_x64_bin'
VECTOR_SHA256 = 'dcb91ea8accc77e6d6e632af7cdc1a99a9f3ae78cf648da595c7d064db32f624'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def command(label, args, checks):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, env={**{k: v for k, v in os.environ.items() if k != 'SDKROOT'}, 'CARGO_TARGET_DIR': str(PROJECT / 'implementation/target'), 'RUSTFLAGS': '-C linker=/usr/bin/clang'})
    log = VERIFICATION / 'logs' / f'{label}-{time.time_ns()}.log'
    log.write_bytes(result.stdout + result.stderr)
    checks.append({'name': label, 'command': args, 'returncode': result.returncode, 'log': str(log.relative_to(REPO))})
    if result.returncode:
        raise RuntimeError(f'The {label} check failed. Read {log}.')
    return result.stdout + result.stderr


def vectors():
    data = json.loads((ROOT / 'fixtures/upstream-vectors.json').read_text())
    cases, expected = [], {}
    encode = lambda value: base64.b64encode(value).decode('ascii')
    for vector in data['cases']:
        size = vector['input_len']
        payload = bytes(i % 251 for i in range(size))
        for mode in ['hash', 'keyed_hash', 'derive_key']:
            for length, seek in [(32, 0), (131, 0), (68, 63)]:
                identity = f'upstream-{size}-{mode}-{length}-{seek}'
                args = ['--raw', '--length', str(length), '--seek', str(seek)]
                case = {'id': identity, 'args': args, 'stdin_b64': encode(payload)}
                if mode == 'keyed_hash':
                    args += ['--keyed', 'input']
                    case['stdin_b64'] = encode(data['key'].encode())
                    case['files'] = {'input': encode(payload)}
                elif mode == 'derive_key':
                    args += ['--derive-key', data['context_string']]
                cases.append(case)
                expected[identity] = bytes.fromhex(vector[mode])[seek:seek + length]
    return cases, expected


def compact(report, name):
    raw = VERIFICATION / 'raw' / name
    write_json(raw, report)
    return {
        'status': report['status'], 'passed': report['passed'], 'failed': report['failed'],
        'executables': report['executables'],
        'cases': [{'input': {'id': row['input']['id'], 'args': row['input']['args']}, 'passed': row['passed'], 'differences': row['differences']} for row in report['cases']],
        'raw_report': str(raw.relative_to(REPO)), 'raw_report_sha256': digest(raw),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path)
    args = parser.parse_args()
    for directory in [WORK, VERIFICATION / 'logs', VERIFICATION / 'raw']:
        directory.mkdir(parents=True, exist_ok=True)
    checks, history, summary = [], [], {'status': 'failed'}
    try:
        check_file = VERIFICATION / 'checks.json'
        history = json.loads(check_file.read_text()).get('commands', []) if check_file.exists() else []
        if sys.platform != 'darwin':
            raise RuntimeError('The pinned reference requires macOS with x86_64 execution support.')
        reference = (args.reference or REPO / 'work/downloads/b3sum').resolve()
        if not reference.exists() and args.reference is None:
            reference = WORK / 'b3sum'
        if not reference.exists():
            command('fetch-reference', ['curl', '-fsSL', '--retry', '2', '--max-time', '120', BINARY_URL, '-o', str(reference)], checks)
            reference.chmod(0o755)
        if digest(reference) != BINARY_SHA256:
            raise RuntimeError('The reference SHA-256 does not match the pinned binary.')
        if digest(ROOT / 'fixtures/upstream-vectors.json') != VECTOR_SHA256:
            raise RuntimeError('The upstream vector SHA-256 does not match the pinned file.')
        frozen = json.loads((ROOT / 'layout-manifest.json').read_text())
        if any(digest(ROOT / name) != value for name, value in frozen['files'].items()):
            raise RuntimeError('A source or model file changed after the layout migration.')
        historical = json.loads((RECOVERED / 'evidence/final-freeze.json').read_text())
        if any(digest(ROOT / new) != historical['files'][old] for old, new in frozen['unchanged_code'].items()):
            raise RuntimeError('The layout migration changed Rust source or Cargo files.')
        agent = WORK / 'agent'
        agent.mkdir(parents=True, exist_ok=True)
        project_spec = importlib.util.spec_from_file_location('rustify_project', REPO / 'skills/rustify/scripts/project.py')
        project = importlib.util.module_from_spec(project_spec)
        project_spec.loader.exec_module(project)
        state_file = RECOVERED / 'state.json'
        if state_file.exists():
            state = json.loads(state_file.read_text())
            state['target']['path'] = str(reference)
            state['work_dir'] = str(agent)
            project.save(PROJECT, state)
        else:
            project.init(PROJECT, reference, 'cli', agent)
        project.status(PROJECT)
        for name in ['rust-design.md', 'plan.json']:
            fixture, destination = ROOT / 'agent-fixtures' / name, agent / name
            if destination.exists() and digest(destination) != digest(fixture):
                raise RuntimeError('The external agent plan changed from this evaluation fixture.')
            if not destination.exists():
                destination.write_bytes(fixture.read_bytes())
        for phase in ['prepare', 'discover', 'plan']:
            if project.status(PROJECT)['next'] == phase:
                project.checkpoint(PROJECT, phase)
        manifest = PROJECT / 'implementation/Cargo.toml'
        cargo = os.environ.get('CARGO', 'cargo')
        command('cargo-fmt', [cargo, 'fmt', '--manifest-path', str(manifest), '--check'], checks)
        command('cargo-clippy', [cargo, 'clippy', '--locked', '--manifest-path', str(manifest), '--all-targets', '--', '-D', 'warnings'], checks)
        test_log = command('cargo-test', [cargo, 'test', '--locked', '--manifest-path', str(manifest)], checks)
        command('cargo-build', [cargo, 'build', '--locked', '--manifest-path', str(manifest)], checks)
        candidate = PROJECT / 'implementation/target/debug/rustify-b3sum'
        comparator = REPO / 'skills/rustify-validate/scripts/compare.py'
        spec = importlib.util.spec_from_file_location('rustify_compare', comparator)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        runtime_file = VERIFICATION / 'raw/runtime-cases.json'
        command('runtime-cases', [sys.executable, str(ROOT / 'fixtures/runtime_cases.py'), str(runtime_file)], checks)
        runtime_cases = json.loads(runtime_file.read_text())
        runtime = module.compare(reference, candidate, runtime_cases, name='b3sum')
        write_json(VERIFICATION / 'comparison.json', compact(runtime, 'runtime-comparison.json'))
        repeat = module.compare(reference, reference, runtime_cases, name='b3sum')
        write_json(VERIFICATION / 'repeatability.json', compact(repeat, 'reference-self.json'))
        vector_cases, expected = vectors()
        vector_report = module.compare(reference, candidate, vector_cases, name='b3sum')
        expected_checks = []
        for row in vector_report['cases']:
            identity = row['input']['id']
            expected_checks.append({'id': identity, 'expected_hex': expected[identity].hex(), **{
                label: row[label]['returncode'] == 0 and not row[label]['error'] and not row[label]['stderr_b64'] and base64.b64decode(row[label]['stdout_b64']) == expected[identity]
                for label in ['reference', 'candidate']
            }})
        write_json(VERIFICATION / 'raw/official-expected-checks.json', expected_checks)
        write_json(VERIFICATION / 'vectors.json', compact(vector_report, 'vector-comparison.json'))
        wrong = VERIFICATION / 'raw/wrong-b3sum'
        wrong.write_text('#!/bin/sh\nprintf "wrong\\n"\n')
        wrong.chmod(0o755)
        negative = module.compare(reference, wrong, [next(case for case in runtime_cases if case['id'] == 'hello')], name='b3sum')
        write_json(VERIFICATION / 'raw/negative-control.json', negative)
        rows = {row['input']['id']: row for report in [runtime, vector_report] for row in report['cases']}
        declarations = []
        for test in json.loads((RECOVERED / 'tests.json').read_text()):
            for scenario in test['scenarios']:
                declarations.append({'id': test['id'], 'scenario': scenario, **{
                    label: all(rows[scenario][label].get(key) == value for key, value in test['expect'].items())
                    for label in ['reference', 'candidate']
                }})
        write_json(VERIFICATION / 'raw/declarative-checks.json', declarations)
        declarative_ok = bool(declarations) and all(row['reference'] and row['candidate'] for row in declarations)
        expected_ok = all(row['reference'] and row['candidate'] for row in expected_checks)
        passed = all(report['status'] == 'passed' for report in [runtime, repeat, vector_report]) and expected_ok and declarative_ok and negative['status'] == 'failed'
        summary = {
            'status': 'passed' if passed else 'failed',
            'reference_sha256': BINARY_SHA256, 'candidate_sha256': digest(candidate),
            'runtime_cases': runtime['passed'], 'runtime_failures': runtime['failed'],
            'repeatability_cases': repeat['passed'], 'vector_cases': vector_report['passed'],
            'official_expected_checks': len(expected_checks) * 2, 'official_expected_outputs_passed': expected_ok,
            'declarative_expected_checks': len(declarations) * 2, 'declarative_expected_outputs_passed': declarative_ok,
            'rust_tests': sum(map(int, re.findall(rb'test result: ok\. (\d+) passed', test_log))),
            'negative_control_detected': negative['status'] == 'failed', 'source_assisted_repairs': True,
            'raw_reports': str((VERIFICATION / 'raw').relative_to(REPO)),
        }
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        summary['error'] = str(error)
    latest = {record['command'][1]: record['returncode'] for record in checks if record['command'][0] == 'cargo'}
    write_json(VERIFICATION / 'checks.json', {'status': 'passed' if all(latest.get(name) == 0 for name in ['fmt', 'clippy', 'test']) else 'failed', 'commands': history + checks})
    if summary['status'] == 'passed':
        try:
            for phase in project.PHASES:
                if project.status(PROJECT)['next'] == phase:
                    project.checkpoint(PROJECT, phase)
            summary['checkpoints'] = project.status(PROJECT)
            if summary['checkpoints']['next'] is not None:
                raise RuntimeError('A checkpoint remains incomplete.')
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
            summary.update(status='failed', error=str(error))
    write_json(VERIFICATION / 'summary.json', summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
