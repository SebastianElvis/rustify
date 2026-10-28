#!/usr/bin/env python3
"""The evaluator compares fixed Ninja browse workflows on loopback HTTP."""

import argparse
from email.utils import parsedate_to_datetime
import os
from pathlib import Path
import re
import resource
import signal
import socket
import subprocess
import sys
import tempfile
import time

import yaml

HERE = Path(__file__).resolve().parent
REPOSITORY = next(path for path in HERE.parents if (path / 'eval/harness.py').is_file())
sys.path.insert(0, str(REPOSITORY / 'eval'))
import harness

EXECUTE_SHA256 = 'becf7fef300ac19a9e3b9b4ebfa48854fd8fd34274d978f560d7d6c5a1a18405'
PIN = '117dad1e0c303889221be3149db93cd1cbf496e545786d968402287072bdb92f'
LIMITS = {'timeout': 15, 'memory_mib': 512, 'process_limit': 32, 'output_mib': 8}


def no_core():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # A background shell job inherits an ignored SIGINT.


def identity(pid):
    try:
        result = subprocess.run(['/bin/ps', '-p', ','.join(map(str, pid)) if isinstance(pid, list) else str(pid), '-o', 'pid=,ppid=,pgid=,lstart=,comm='], capture_output=True, timeout=0.5)
        return {'pid': pid, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'pid': pid, 'error': str(error), 'stdout': getattr(error, 'stdout', None), 'stderr': getattr(error, 'stderr', None)}


def helper_pin():
    path = REPOSITORY / 'skills/rustify-probe/scripts/compare.py'
    if Path(harness.compare.__file__).resolve() != path or harness.digest(path) != EXECUTE_SHA256:
        raise ValueError('The compare helper differs from its pin.')


def process_rows(capture):
    rows = {}
    for line in (capture.get('stdout') or b'').splitlines():
        parts = line.split(None, 8)
        if len(parts) < 8:
            raise ValueError('The process identity row is incomplete.')
        pid, parent, group = map(int, parts[:3])
        rows[pid] = {'pid': pid, 'parent_pid': parent, 'group': group, 'started': b' '.join(parts[3:8]).decode('ascii')}
    return rows


def terminal(metrics, captures):
    known, errors = {}, []
    for capture in captures:
        try:
            if capture.get('error') or capture.get('stderr') or capture.get('returncode') not in (0, 1):
                raise ValueError('The process identity check is inconclusive.')
            for pid, row in process_rows(capture).items():
                known[(pid, row['started'])] = row
        except (ValueError, UnicodeError) as error:
            errors.append(str(error))
    for row in metrics.get('peak_memory_processes', []):
        known[(row['pid'], row['started'])] = {'pid': row['pid'], 'started': row['started']}
    pids = sorted({metrics['pid'], *[row['pid'] for row in known.values()]})
    raw = identity(pids)
    try:
        if errors or raw.get('error') or raw.get('stderr') or raw.get('returncode') not in (0, 1):
            raise ValueError('The terminal process check is inconclusive.')
        rows = process_rows(raw)
        if (raw['returncode'] == 1 and rows) or (raw['returncode'] == 0 and not rows) or set(rows) - set(pids):
            raise ValueError('The terminal process check has an inconsistent result.')
        if not any(pid == metrics['pid'] for pid, _ in known):
            raise ValueError('The root process has no recorded start time.')
        states = [dict(row, state='terminated' if row['pid'] not in rows else 'pid_reused' if rows[row['pid']]['started'] != row['started'] else 'pending') for row in known.values()]
        qualified = not any(row['state'] == 'pending' for row in states)
        if not qualified:
            errors.append('An observed process still has its recorded identity.')
    except (ValueError, UnicodeError) as error:
        errors.append(str(error))
        states, qualified = [], False
    return {'qualified': qualified, 'status': 'complete' if qualified else 'incomplete', 'observed': list(known.values()), 'states': states, 'errors': errors, 'raw_ps': raw}


def signal_root(process, first, current, name):
    try:
        if any(row.get('error') or row.get('stderr') or row.get('returncode') != 0 for row in (first, current)):
            raise ValueError('The signal identity check is inconclusive.')
        before, now = process_rows(first), process_rows(current)
        if process.pid not in before or process.pid not in now or before[process.pid]['started'] != now[process.pid]['started'] or process.poll() is not None:
            raise ValueError('The signal target no longer has its recorded identity.')
        process.send_signal(getattr(signal, name))
        return None
    except (OSError, ValueError, UnicodeError) as error:
        return str(error)


def request(port, action):
    method = action.get('method', 'GET')
    raw_request = f'{method} {action["path"]} HTTP/1.0\r\nHost: 127.0.0.1:{port}\r\n\r\n'.encode('ascii')
    response = bytearray()
    deadline = time.monotonic() + 1
    error = None
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=0.25) as client:
            client.sendall(raw_request)
            while True:
                client.settimeout(max(0.001, deadline - time.monotonic()))
                chunk = client.recv(4096)
                if not chunk:
                    break
                response.extend(chunk)
                if len(response) > 128 * 1024 or time.monotonic() >= deadline:
                    raise ValueError('The HTTP response exceeded its limit.')
        status = int(bytes(response).split(b' ', 2)[1])
    except (OSError, ValueError, IndexError) as failure:
        status, error = None, f'{type(failure).__name__}: {failure}'
    return {'request': raw_request, 'response': bytes(response), 'status': status, 'error': error}


def snapshot(root, metadata):
    if sum(path.stat().st_size for path in root.rglob('*') if path.is_file()) > 8 * 1024 * 1024:
        raise ValueError('The files exceeded the 8 MiB capture limit.')
    return harness.compare.capture_files(root, metadata)


def write(root, files):
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode('utf-8'))
        os.utime(path, (harness.compare.FIXTURE_TIME, harness.compare.FIXTURE_TIME))


def worker(config):
    helper_pin()
    root, executable, case = Path(config['root']), Path(config['executable']), config['case']
    home, fixtures = root / 'home', root / 'fixture'
    home.mkdir()
    fixtures.mkdir()
    write(fixtures, case['files'])
    links = root / 'bin'
    links.mkdir()
    (links / 'python').symlink_to(sys.executable)
    env = {'LC_ALL': 'C', 'LANG': 'C', 'TZ': 'UTC', 'HOME': str(home), 'PATH': str(links) + ':/usr/bin:/bin', 'TERM': 'dumb'}
    holder = socket.socket()
    holder.bind(('127.0.0.1', 0))
    port = holder.getsockname()[1]
    if case.get('mode') == 'conflict':
        holder.listen(1)
    else:
        holder.close()
    args = ['ninja', *case.get('prefix', []), '-t', 'browse', '--no-browser', '--hostname=127.0.0.1', f'--port={port}', f'--ninja-command={executable}', *case.get('args', [])]
    result = {'input': case, 'setup': {'root': str(root), 'cwd': str(fixtures), 'env': env, 'argv': args, 'port': port, 'python': str(Path(sys.executable).resolve()), 'core_limit': [0, 0], 'python_sha256': harness.digest(Path(sys.executable)), 'python_link': {'path': str(links / 'python'), 'target': sys.executable}}, 'http': [], 'identities': [], 'errors': []}
    def started(process):
        result['identities'].append({'stage': 'spawn', **identity(process.pid)})
        if case.get('mode') in {'cli', 'conflict'}:
            return
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and process.poll() is None:
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=0.05):
                    break
            except OSError:
                time.sleep(0.02)
        else:
            result['errors'].append('The service did not become ready.')
            return
        try:
            for action in case['actions']:
                write(fixtures, action.get('write', {}))
                capture = request(port, action)
                result['http'].append(capture)
                if capture['error']:
                    result['errors'].append(capture['error'])
                capture['files'] = snapshot(fixtures, capture.setdefault('raw_file_metadata', {}))
                if capture['status'] != action['status'] or action.get('contains', '').encode() not in capture['response']:
                    result['errors'].append('The response failed the fixed completion check.')
        except (OSError, ValueError, IndexError) as error:
            result['errors'].append(f'{type(error).__name__}: {error}')
        finally:
            result['identities'].append({'stage': 'before-signal', **identity(process.pid)})
            name = case.get('signal', 'SIGINT')
            error = signal_root(process, result['identities'][0], result['identities'][-1], name)
            if error:
                result['errors'].append(error)
            else:
                result['signal'] = name
    result['wall_start_ns'] = time.time_ns()
    completed, error, metrics = harness.compare.execute(args, executable=str(executable), cwd=fixtures, env=env, on_spawn=started, preexec_fn=no_core, **LIMITS)
    result['wall_end_ns'] = time.time_ns()
    result.update(returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr, error=error, resources=metrics)
    holder.close()
    result['termination'] = terminal(metrics, result['identities'])
    result['identities'].append({'stage': 'terminal', **result['termination']['raw_ps']})
    with socket.socket() as probe:
        probe.settimeout(0.25)
        result['endpoint_open_after_exit'] = probe.connect_ex(('127.0.0.1', port)) == 0
    if case.get('mode') != 'conflict' and result['endpoint_open_after_exit']:
        result['errors'].append('The endpoint remained open after exit.')
    try:
        result['files'] = snapshot(fixtures, result.setdefault('raw_file_metadata', {}))
    except (OSError, ValueError) as failure:
        result['errors'].append(f'{type(failure).__name__}: {failure}')
    result['directories'] = {path.relative_to(fixtures).as_posix(): path.stat().st_mode for path in fixtures.rglob('*') if path.is_dir()}
    result['raw_directory_metadata'] = {path.relative_to(fixtures).as_posix(): {name: getattr(path.stat(), name) for name in ('st_mode', 'st_ino', 'st_dev', 'st_nlink', 'st_uid', 'st_gid', 'st_size', 'st_atime_ns', 'st_mtime_ns', 'st_ctime_ns')} for path in [fixtures, *fixtures.rglob('*')] if path.is_dir()}
    (root / 'result.yaml').write_text(yaml.safe_dump(result, sort_keys=False))


def play(executable, case, directory):
    directory.mkdir(parents=True)
    config = {'root': str(directory), 'executable': str(Path(executable).resolve()), 'case': case}
    config_path = directory / 'config.yaml'
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    identities = []
    completed, error, resources = harness.compare.execute([sys.executable, str(Path(__file__).resolve()), '--worker', str(config_path)], timeout=22, memory_mib=2048, process_limit=32, output_mib=8, preexec_fn=no_core, on_spawn=lambda process: identities.append(identity(process.pid)))
    outer = {'returncode': completed.returncode, 'stdout': completed.stdout, 'stderr': completed.stderr, 'error': error, 'resources': resources}
    outer['termination'] = terminal(resources, identities)
    outer['identities'] = identities
    path = directory / 'result.yaml'
    result = yaml.safe_load(path.read_text()) if path.exists() else {'error': 'The worker did not return a capture.', 'errors': []}
    result['supervisor'] = outer
    return result


def response_view(data, result):
    head, separator, body = data.partition(b'\r\n\r\n')
    def date(match):
        try:
            value = parsedate_to_datetime(match[1].decode('ascii'))
            stamp = value.timestamp()
            if value.strftime('%a, %d %b %Y %H:%M:%S GMT').encode() == match[1] and result['wall_start_ns'] / 1e9 - 1 <= stamp <= result['wall_end_ns'] / 1e9 + 1:
                return b'Date: <DATE>'
        except (ValueError, TypeError, UnicodeError):
            pass
        return match[0]
    return re.sub(rb'(?m)^Date: ([^\r\n]+)', date, head, count=1) + separator + body


def view(result):
    """The evaluator applies only the variation rules that original controls confirm."""
    port = str(result.get('setup', {}).get('port', -1)).encode()
    pid = str(result.get('resources', {}).get('pid', -1)).encode()
    stdout = result.get('stdout', b'').replace(b'127.0.0.1:' + port, b'127.0.0.1:<PORT>')
    stderr = result.get('stderr', b'').replace(b'Web server pid ' + pid + b'\n', b'Web server pid <PID>\n')
    http = [{'response': response_view(row['response'], result), 'files': row.get('files')} for row in result.get('http', [])]
    return {key: value for key, value in {'returncode': result.get('returncode'), 'stdout': stdout, 'stderr': stderr, 'http': http, 'files': result.get('files'), 'directories': result.get('directories'), 'endpoint_open_after_exit': result.get('endpoint_open_after_exit')}.items()}


def compare(reference, candidate, scenarios=None, output=None):
    helper_pin()
    if harness.digest(Path(reference)) != PIN:
        raise ValueError('The original differs from the fixed pin.')
    before = {str(Path(executable).resolve()): harness.digest(Path(executable)) for executable in (reference, candidate)}
    scenarios = yaml.safe_load((HERE / 'cases.yaml').read_text()) if scenarios is None else scenarios
    rows = []
    with tempfile.TemporaryDirectory(prefix='browse-', dir=output or HERE) as temporary:
        for case in scenarios:
            results = {label: play(executable, case, Path(temporary) / case['id'] / label) for label, executable in (('expected', reference), ('actual', candidate))}
            views = {label: view(result) for label, result in results.items()}
            differences = [field for field in views['expected'] if views['expected'][field] != views['actual'][field]]
            differences += [f'{label}: {message}' for label, result in results.items() for message in [result.get('error'), *result.get('errors', []), result['supervisor'].get('error')] if message]
            differences += [f'{label}: The enclosing supervisor failed.' for label, result in results.items() if result['supervisor']['returncode'] != 0]
            differences += [f'{label}: The {scope} terminal state is incomplete.' for label, result in results.items() for scope, record in (('target', result), ('worker', result['supervisor'])) if not record.get('termination', {}).get('qualified')]
            rows.append({'id': case['id'], **results, 'views': views, 'differences': differences, 'passed': not differences})
    helper_pin()
    if any(harness.digest(Path(path)) != digest for path, digest in before.items()):
        raise ValueError('An executable changed during the comparison.')
    failed = sum(not row['passed'] for row in rows)
    return {'status': 'failed' if failed else 'passed', 'passed': len(rows) - failed, 'failed': failed, 'executables': {label: {'path': str(Path(executable).resolve()), 'sha256': harness.digest(Path(executable))} for label, executable in (('reference', reference), ('candidate', candidate))}, 'helper_sha256': EXECUTE_SHA256, 'cases': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker')
    parser.add_argument('--reference')
    parser.add_argument('--candidate')
    parser.add_argument('--report')
    args = parser.parse_args()
    if args.worker:
        worker(yaml.safe_load(Path(args.worker).read_text()))
        return 0
    report = compare(args.reference, args.candidate)
    Path(args.report).write_text(yaml.safe_dump(report, sort_keys=False))
    print(yaml.safe_dump({key: report[key] for key in ('status', 'passed', 'failed')}, sort_keys=False), end='')
    return int(report['status'] != 'passed')


if __name__ == '__main__':
    raise SystemExit(main())
