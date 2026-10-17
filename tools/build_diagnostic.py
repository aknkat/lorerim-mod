#!/usr/bin/env python3
"""Compile a diagnostic overlay without changing v0.1.4's saved fields or code."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from build import CAPRICA_SHA256, archive, source_archive, windows_path
from formats import normalize_pex, read_pex, read_plugin, repair_caprica_skyrim_size, vmad

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'build' / 'diagnostic1'
METADATA = 'KhajiitKeenSenses/diagnostic1/'
BASE_SHA256 = '36473781515cb99d1f8bf47a05cff933ed2a4b37c1dd8360fb3b07e39c9a9fad'
NAME = 'LKS_KeenSensesController'
EXTRA = r'''

; Invoked explicitly by console: cqf <controller-quest> LKS_Probe
; All new values are function locals. TryActivate is the unchanged v0.1.4 code.
Function LKS_Probe()
    Actor playerRef = Game.GetPlayer()
    Race currentRace = playerRef.GetRace()
    Bool raceAllowed = currentRace == KhajiitRace || currentRace == KhajiitVampireRace
    Bool spellBound = DetectionSpell != None
    Bool questRunning = IsRunning()
    Float nowHours = Game.GetRealHoursPassed()
    Float beforeDeadline = readyAtHours
    Float beforeRemaining = (beforeDeadline - nowHours) * 3600.0
    Bool accepted = TryActivate(playerRef, playerRef)
    Float afterRemaining = (readyAtHours - Game.GetRealHoursPassed()) * 3600.0
    String report = "LKS DIAG1 - v0.1.4\n"
    report += "Quest running: " + questRunning + "\n"
    report += "Race allowed: " + raceAllowed + "\n"
    report += "Spell bound: " + spellBound + "\n"
    report += "Clock (hours): " + nowHours + "\n"
    report += "Saved deadline (hours): " + beforeDeadline + "\n"
    report += "Remaining before (seconds): " + beforeRemaining + "\n"
    report += "TryActivate accepted: " + accepted + "\n"
    report += "Remaining after (seconds): " + afterRemaining
    Debug.MessageBox(report)
EndFunction
'''


def verify_behavior(original, diagnostic, effect, bindings, manager_bindings):
    """Compare all original functions/fields, then execute the new compiled probe."""
    sys.path.insert(0, str(ROOT / 'tests'))
    from pex_host import Host
    for key in ('name', 'parent', 'variables', 'properties'):
        if original[key] != diagnostic[key]:
            raise ValueError(f'Diagnostic changed saved layout: {key}')
    if set(original['states']) != set(diagnostic['states']):
        raise ValueError('Unexpected script state')
    for state, functions in original['states'].items():
        for name, function in functions.items():
            if diagnostic['states'][state].get(name) != function:
                raise ValueError(f'Diagnostic changed original function: {name}')
    added = set(diagnostic['states']['']) - set(original['states'][''])
    if added != {'LKS_Probe'}:
        raise ValueError(f'Unexpected extra functions: {added}')
    for case in ('ready', 'cooldown', 'wrong-race', 'missing-spell'):
        host = Host(effect, diagnostic, bindings, manager_bindings)
        host.running = True
        if case == 'cooldown':
            host.activate()
            host.advance(15)
            host.casts.clear()
        elif case == 'wrong-race':
            host.race = 0x13746
        elif case == 'missing-spell':
            var = diagnostic['properties']['DetectionSpell']['variable'].lower()
            host.manager.fields[var] = None
        before = dict(host.manager.fields)
        host.manager.invoke('LKS_Probe', [], host)
        if len(host.messages) != 1 or 'LKS DIAG1' not in host.messages[0]:
            raise ValueError(f'Probe report missing: {case}')
        expected = case == 'ready'
        if len(host.casts) != int(expected) or host.registrations:
            raise ValueError(f'Unexpected activation/timer: {case}')
        if f'TryActivate accepted: {expected}' not in host.messages[0]:
            raise ValueError(f'Incorrect report: {case}')
        if case != 'ready' and before != host.manager.fields:
            raise ValueError(f'Rejected probe changed saved state: {case}')
    print('Diagnostic verification: no new saved fields; all original functions identical; four compiled report cases passed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dotnet', default='dotnet')
    parser.add_argument('--caprica', type=Path, required=True)
    parser.add_argument('--wine')
    args = parser.parse_args()
    compiler = args.caprica.resolve()
    if hashlib.sha256(compiler.read_bytes()).hexdigest() != CAPRICA_SHA256:
        parser.error('Compiler is not the pinned Caprica v0.3.0')
    base = ROOT / 'dist' / 'KhajiitKeenSenses-0.1.4-MO2.zip'
    if hashlib.sha256(base.read_bytes()).hexdigest() != BASE_SHA256:
        raise ValueError('Published v0.1.4 archive was changed')
    if WORK.exists():
        shutil.rmtree(WORK)
    source = WORK / 'source'
    package = WORK / 'package'
    source.mkdir(parents=True)
    (package / 'Scripts' / 'Source').mkdir(parents=True)
    (package / METADATA).mkdir(parents=True)
    with zipfile.ZipFile(base) as z:
        original = read_pex(z.read(f'Scripts/{NAME}.pex'))['objects'][0]
        effect = read_pex(z.read('Scripts/LKS_KeenSensesEffect.pex'))['objects'][0]
        original_source = z.read(f'Scripts/Source/{NAME}.psc').decode('utf-8')
        if original_source != (ROOT / 'scripts/source' / (NAME + '.psc')).read_text():
            raise ValueError('Source differs from published v0.1.4')
        esp = WORK / 'base.esp'
        esp.write_bytes(z.read('KhajiitKeenSenses.esp'))
    generated = source / (NAME + '.psc')
    generated.write_text(original_source + EXTRA, encoding='utf-8')
    api = ROOT / 'tools/papyrus-api'
    command = ([args.wine] if args.wine else []) + [str(compiler), '--game=skyrim',
        '--strict', '--champollion-compat=false', '--enable-debug-info=false',
        '--all-warnings-as-errors', '--flags=' + windows_path(api / 'TESV_Papyrus_Flags.flg', args.wine),
        '--import=' + windows_path(api, args.wine),
        '--output=' + windows_path(package / 'Scripts', args.wine), NAME + '.psc']
    subprocess.run(command, cwd=source, check=True)
    pex = package / 'Scripts' / (NAME + '.pex')
    repair_caprica_skyrim_size(pex)
    normalize_pex(pex)
    diagnostic = read_pex(pex)['objects'][0]
    records, _ = read_plugin(esp)
    forms = {r['id'] & 0xFFFFFF: r for r in records[1:]}
    verify_behavior(original, diagnostic, effect,
        vmad(forms[0x801])['LKS_KeenSensesEffect']['properties'],
        vmad(forms[0x804])[NAME]['properties'])
    subprocess.run([args.dotnet, 'run', '--project', str(ROOT / 'tools/PluginBuilder/PluginBuilder.csproj'),
        '--no-build', '--configuration', 'Release', '--', '--verify-pex', str(pex)], cwd=ROOT, check=True)
    shutil.copy2(generated, package / 'Scripts/Source')
    shutil.copy2(ROOT / 'docs/RELOAD_DIAGNOSTIC.md', package / METADATA / 'README.md')
    shutil.copy2(ROOT / 'LICENSE', package / METADATA / 'LICENSE.txt')
    (package / METADATA / 'build-manifest.json').write_text(json.dumps({
        'version': '0.1.4-diagnostic1', 'requires': 'KhajiitKeenSenses 0.1.4',
        'base_sha256': BASE_SHA256, 'new_records': 0, 'new_saved_variables': 0,
        'original_functions_unchanged': True, 'command': 'cqf FECFD804 LKS_Probe',
        'note': 'Probe attempts one normal activation; not a bug fix. Runtime command/display unverified.'
    }, indent=2) + '\n')
    output = ROOT / 'dist/KhajiitKeenSenses-0.1.4-diagnostic1-MO2.zip'
    archive(package, output, checksum_path=METADATA + 'SHA256SUMS.txt')
    with zipfile.ZipFile(output) as z:
        expected = {f'Scripts/{NAME}.pex', f'Scripts/Source/{NAME}.psc'} | {
            METADATA + n for n in ('README.md', 'LICENSE.txt', 'build-manifest.json', 'SHA256SUMS.txt')}
        if set(z.namelist()) != expected or z.testzip() is not None:
            raise ValueError('Invalid diagnostic-only archive')
        for line in z.read(METADATA + 'SHA256SUMS.txt').decode().splitlines():
            digest, name = line.split('  ', 1)
            if hashlib.sha256(z.read(name)).hexdigest() != digest:
                raise ValueError('Diagnostic checksum failure')
    source_archive(ROOT / 'dist/KhajiitKeenSenses-0.1.4-diagnostic1-source.zip')


if __name__ == '__main__':
    main()
