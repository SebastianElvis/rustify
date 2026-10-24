"""Generate separate runtime challenges for the frozen replacement."""
import base64
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parent
encode = lambda value: base64.b64encode(value).decode('ascii')
cases = [case for case in json.loads((ROOT.parent / 'target/recovered/scenarios.json').read_text()) if not case['id'].startswith('upstream-')]
rng = random.Random(6221)

def add(identity, args, data=b'', files=None):
    cases.append({'id': 'challenge-' + identity, 'args': args, 'stdin_b64': encode(data), 'files': {name: encode(value) for name, value in (files or {}).items()}})

for size in [0, 1, 2, 63, 64, 65, 1023, 1024, 1025, 2048, 16384, 65537]:
    data = bytes(rng.randrange(256) for _ in range(size))
    for identity, args in [('hash', []), ('raw', ['--raw']), ('seek', ['--raw', '-l', '97', '--seek', '63']), ('derive', ['--derive-key', 'Rustify context 🦀']), ('derive-seek', ['--derive-key', '', '--seek=1023', '--length=65'])]:
        add(f'{identity}-{size}', args, data)
    add(f'file-{size}', ['data'], files={'data': data})
    add(f'keyed-{size}', ['--keyed', 'data'], bytes(range(32)), {'data': data})
    add(f'keyed-seek-{size}', ['--keyed', '--raw', '--seek', '1023', '-l', '65', 'data'], bytes(range(32)), {'data': data})

for length in [0, 1, 2, 31, 32, 33, 63, 64, 65, 127, 8193]:
    add(f'length-{length}', ['-l', str(length)], b'hello')
    add(f'seek-length-{length}', ['--raw', '--seek', str(length), '-l', str(length)], b'hello')

for i, name in enumerate(['space name', 'tab\tname', 'line\nname', 'cr\rname', '中文', 'parentheses (name)']):
    add(f'name-{i}', ['--tag', name], files={name: b'hello'})

hello = 'ea8f163db38682925e4491c5e58d4bb3506ef8c14eb78a86e908c5624a67200f'
check_lines = [
    hello + '  a', hello + '  a\r\n', hello + '  a\n\n',
    hello.upper() + '  a\n', hello[:32] + '  a\n', hello + ' *a\n',
    'BLAKE3 (a) = ' + hello + '\n', 'garbage\n', '\n', hello + '  \n',
    '\\' + hello + '  a\\q\n', '0' * 64 + '  a\n', hello + '  missing\n',
    hello + '  a\n' + '0' * 64 + '  a\n' + hello + '  missing\n',
]
for i, content in enumerate(check_lines):
    for quiet in [False, True]:
        args = ['--check'] + (['--quiet'] if quiet else [])
        add(f'check-{i}-{quiet}', args, content.encode(), {'a': b'hello'})
        add(f'checkfile-{i}-{quiet}', args + ['sums'], files={'sums': content.encode(), 'a': b'hello'})

for size in [0, 1, 31, 33, 64]:
    add(f'key-length-{size}', ['--keyed', 'a'], b'x' * size, {'a': b'hello'})
add('missing-many', ['missing', 'a', 'missing2', 'b'], files={'a': b'hello', 'b': b''})
add('directory-check', ['--check'], (hello + '  directory\n').encode(), {'directory/file': b'hello'})
add('missing-checkfile', ['--check', 'missing'])
hello = 'ea8f163db38682925e4491c5e58d4bb3506ef8c14eb78a86e908c5624a67200f'
for i, value in enumerate([hello + '  a\r', hello + '  a\r\r', '\r', hello + '  a\t', hello + '  a ', '\\' + hello + '  line\\nname']):
    add('extra-check-' + str(i), ['--check'], value.encode(), {'a': b'hello', 'line\nname': b'hello'})
for i, line in enumerate([hello + '  a\0ignored', hello + '  \ufffd', 'BLAKE3 (a  b) = ' + hello, '\\' + hello + '  a']):
    add('audit-check-' + str(i), ['--check'], (line + '\n').encode(), {'a': b'hello', '\ufffd': b'hello', 'a  b': b'hello'})
add('audit-check-invalid-utf8', ['--check'], b'\xff\n')
add('audit-keyed-stdin', ['--keyed', '-'], bytes(range(32)))
Path(sys.argv[1]).write_text(json.dumps(cases, indent=2) + '\n')
print(len(cases), 'cases')
