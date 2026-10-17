"""Check declarations and emitted calls against a pinned, independent Skyrim API.

The fixture records upstream vanilla declarations, not the compiler stubs or
mock host. The static check rejects diagnostic4's extra Notification argument.
It does not model native execution, saved handles, or the Skyrim VM scheduler.
"""
import json
from pathlib import Path
import re

REFERENCE = Path(__file__).resolve().parent.parent / 'tests/fixtures/skyrim-vanilla-api.json'


def reference():
    data = json.loads(REFERENCE.read_text())
    functions = {(f['script'].lower(), f['name'].lower()): f for f in data['functions']}
    return functions, data['parents']


def verify_stubs(directory):
    expected, _ = reference()
    found = set()
    pattern = re.compile(r'^\s*(?:(\w+)\s+)?Function\s+(\w+)\s*\(([^)]*)\)(.*)$', re.I | re.M)
    for path in Path(directory).glob('*.psc'):
        for match in pattern.finditer(path.read_text()):
            if 'native' not in match[4].lower().split():
                continue
            key = path.stem.lower(), match[2].lower()
            if key not in expected:
                raise ValueError(f'Unverified native declaration: {path.stem}.{match[2]}')
            spec = expected[key]
            returns = (match[1] or 'None').lower()
            parameters = [p.strip().split()[0].lower() for p in match[3].split(',') if p.strip()]
            global_ = 'global' in match[4].lower().split()
            if (returns, parameters, global_) != (spec['returns'], spec['parameters'], spec['global']):
                raise ValueError(f'Native declaration differs from upstream: {path.stem}.{match[2]}')
            found.add(key)
    if found != set(expected):
        raise ValueError(f'Missing checked API declarations: {set(expected) - found}')
    return len(found)


def verify_pex_calls(objects):
    """Resolve emitted calls; verify arity, argument types, and return slots."""
    api, parents = reference()
    scripts = {o['name'].lower(): o for o in objects}
    parents.update({name: obj['parent'].lower() for name, obj in scripts.items()})

    def compatible(actual, expected):
        if actual == 'none' and expected not in ('int', 'float', 'bool', 'string'):
            return True
        seen = set()
        while actual and actual not in seen:
            if actual == expected:
                return True
            seen.add(actual)
            actual = parents.get(actual)
        return False

    def resolve(owner, name):
        seen = set()
        while owner and owner not in seen:
            seen.add(owner)
            if owner in scripts:
                for functions in scripts[owner]['states'].values():
                    for fn_name, fn in functions.items():
                        if fn_name.lower() == name:
                            return {'script': owner, 'name': fn_name, 'returns': fn['returns'].lower(),
                                    'parameters': [kind.lower() for _, kind in fn['parameters']],
                                    'global': False}, False
            if (owner, name) in api:
                return api[owner, name], True
            owner = parents.get(owner)
        raise ValueError(f'Unresolved call: {owner}.{name}')

    count = 0
    for obj in objects:
        for functions in obj['states'].values():
            for fn_name, fn in functions.items():
                # These compiler helpers invoke the implicit state callbacks.
                if fn_name.lower() in ('getstate', 'gotostate'):
                    continue
                types = {name.lower(): var['type'].lower() for name, var in obj['variables'].items()}
                types.update({name.lower(): kind.lower() for name, kind in fn['parameters'] + fn['locals']})
                types['self'] = obj['name'].lower()

                def operand_type(operand):
                    kind, value = operand
                    if kind == 1:
                        return types[value.lower()]
                    return {0: 'none', 2: 'string', 3: 'int', 4: 'float', 5: 'bool'}[kind]

                for instruction in fn['code']:
                    op, args = instruction['op'], instruction['args']
                    if op == 25:
                        key = args[0][1].lower(), args[1][1].lower()
                        if key not in api or not api[key]['global']:
                            raise ValueError(f'Unverified global call: {key}')
                        spec, native = api[key], True
                    elif op == 23:
                        spec, native = resolve(operand_type(args[1]), args[0][1].lower())
                        if spec['global']:
                            raise ValueError('Global API called as a member')
                    else:
                        continue
                    label = f"{spec['script']}.{spec['name']}"
                    actual = instruction['variadic']
                    if len(actual) != len(spec['parameters']):
                        raise ValueError(f"{label} expects {len(spec['parameters'])} arguments; got {len(actual)}")
                    for operand, expected in zip(actual, spec['parameters']):
                        if not compatible(operand_type(operand), expected):
                            raise ValueError(f'{label}: incompatible argument type')
                    destination = operand_type(args[2])
                    if destination != 'none' and not compatible(spec['returns'], destination):
                        raise ValueError(f'{label}: incompatible return slot')
                    count += int(native)
    return count
