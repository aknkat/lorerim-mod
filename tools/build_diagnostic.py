#!/usr/bin/env python3
"""Compile a power-triggered diagnostic overlay with unchanged saved fields."""
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
from verify_papyrus_api import verify_pex_calls, verify_stubs

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'build' / 'diagnostic5'
METADATA = 'KhajiitKeenSenses/diagnostic5/'
BASE_SHA256 = '36473781515cb99d1f8bf47a05cff933ed2a4b37c1dd8360fb3b07e39c9a9fad'
NAME = 'LKS_KeenSensesController'
EFFECT = 'LKS_KeenSensesEffect'
EXTRA = r'''

; Invoked by the instrumented input effect. No console command is required.
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
    String report = "LKS DIAG5 - v0.1.4\n"
    report += "Quest running: " + questRunning + "\n"
    report += "Race allowed: " + raceAllowed + "\n"
    report += "Spell bound: " + spellBound + "\n"
    report += "Clock (hours): " + nowHours + "\n"
    report += "Saved deadline (hours): " + beforeDeadline + "\n"
    report += "Remaining before (seconds): " + beforeRemaining + "\n"
    report += "TryActivate accepted: " + accepted + "\n"
    report += "Remaining after (seconds): " + afterRemaining
    If accepted
        Debug.Notification("LKS: ACCEPTED - cast requested")
    Else
        Debug.Notification("LKS: BLOCKED")
    EndIf
    Debug.Trace(report)
EndFunction

; Retain the diagnostic2 entry point.
Function LKSProbe()
    LKS_Probe()
EndFunction
'''

TRIGGER = r'''Event OnEffectStart(Actor akTarget, Actor akCaster)
    Debug.Notification("LKS: INPUT")
    Actor playerRef = Game.GetPlayer()
    If akTarget != playerRef || akCaster != playerRef
        Debug.Notification("LKS: ERROR - not PlayerRef")
    ElseIf CooldownController == None
        Debug.Notification("LKS: ERROR - controller not bound")
    Else
        Bool controllerReady = CooldownController.IsRunning()
        If !controllerReady
            controllerReady = CooldownController.Start()
        EndIf
        If controllerReady
            LKS_KeenSensesController controller = CooldownController as LKS_KeenSensesController
            If controller != None
                controller.LKSProbe()
            Else
                Debug.Notification("LKS: ERROR - script cast None")
            EndIf
        Else
            Debug.Notification("LKS: ERROR - Start failed")
        EndIf
    EndIf
EndEvent
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
    if added != {'LKS_Probe', 'LKSProbe'}:
        raise ValueError(f'Unexpected extra functions: {added}')
    for case in ('ready', 'cooldown', 'wrong-race', 'missing-spell'):
        host = Host(effect, diagnostic, bindings, manager_bindings)
        host.running = True
        if case == 'cooldown':
            host.activate()
            host.advance(15)
            host.casts.clear()
            host.notifications.clear()
            host.traces.clear()
        elif case == 'wrong-race':
            host.race = 0x13746
        elif case == 'missing-spell':
            var = diagnostic['properties']['DetectionSpell']['variable'].lower()
            host.manager.fields[var] = None
        before = dict(host.manager.fields)
        host.manager.invoke('lksprobe', [], host)
        if host.messages or len(host.traces) != 1 or 'LKS DIAG5' not in host.traces[0]:
            raise ValueError(f'Probe report missing: {case}')
        expected = case == 'ready'
        if len(host.casts) != int(expected) or host.registrations:
            raise ValueError(f'Unexpected activation/timer: {case}')
        if f'TryActivate accepted: {expected}' not in host.traces[0]:
            raise ValueError(f'Incorrect report: {case}')
        expected_notice = 'LKS: ACCEPTED - cast requested' if expected else 'LKS: BLOCKED'
        if host.notifications != [expected_notice]:
            raise ValueError(f'Incorrect nonmodal notification: {case}')
        if case != 'ready' and before != host.manager.fields:
            raise ValueError(f'Rejected probe changed saved state: {case}')
    print('Controller diagnostic: no new saved fields; all v0.1.4 functions identical; four compiled report cases passed.')


def verify_input(original, diagnostic, controller, bindings, manager_bindings):
    """Execute the instrumented compiled entry event, not a source translation."""
    from pex_host import Host
    for key in ('name', 'parent', 'variables', 'properties'):
        if original[key] != diagnostic[key]:
            raise ValueError(f'Input diagnostic changed saved layout: {key}')
    if set(original['states']) != set(diagnostic['states']):
        raise ValueError('Input diagnostic changed script states')
    for state, functions in original['states'].items():
        if set(functions) != set(diagnostic['states'][state]):
            raise ValueError('Input diagnostic added or removed a function')
        for name, function in functions.items():
            if name.lower() != 'oneffectstart' and diagnostic['states'][state][name] != function:
                raise ValueError(f'Input diagnostic changed another function: {name}')
    cases = ('ready', 'cooldown', 'wrong-race', 'missing-spell',
             'missing-controller', 'start-failed', 'wrong-target')
    for case in cases:
        host = Host(diagnostic, controller, dict(bindings), manager_bindings)
        if case == 'cooldown':
            host.activate()
            host.advance(15)
            host.casts.clear()
            host.messages.clear()
            host.notifications.clear()
            host.traces.clear()
        elif case == 'wrong-race':
            host.race = 0x13746
        elif case == 'missing-spell':
            var = controller['properties']['DetectionSpell']['variable'].lower()
            host.manager.fields[var] = None
        elif case == 'missing-controller':
            host.effect_bindings['CooldownController'] = None
        elif case == 'start-failed':
            host.start_ok = False
        host.activate('npc' if case == 'wrong-target' else 'player', 'player')
        if host.messages or len(host.notifications) != 2 or host.notifications[0] != 'LKS: INPUT':
            raise ValueError(f'Input diagnostic messages missing: {case}')
        if len(host.casts) != int(case == 'ready') or host.registrations:
            raise ValueError(f'Input diagnostic cast/timer mismatch: {case}')
        errors = {'missing-controller': 'not bound', 'start-failed': 'Start failed',
                  'wrong-target': 'not PlayerRef'}
        expected = errors.get(case, 'ACCEPTED' if case == 'ready' else 'BLOCKED')
        if expected not in host.notifications[1]:
            raise ValueError(f'Input diagnostic result mismatch: {case}')
        if case not in errors and (len(host.traces) != 1 or
                f'TryActivate accepted: {case == "ready"}' not in host.traces[0]):
            raise ValueError(f'Input diagnostic trace mismatch: {case}')
    print('Power input diagnostic: saved layout unchanged; seven compiled entry/report/error cases passed.')


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
        effect = read_pex(z.read(f'Scripts/{EFFECT}.pex'))['objects'][0]
        effect_source = z.read(f'Scripts/Source/{EFFECT}.psc').decode('utf-8')
        original_source = z.read(f'Scripts/Source/{NAME}.psc').decode('utf-8')
        if original_source != (ROOT / 'scripts/source' / (NAME + '.psc')).read_text():
            raise ValueError('Source differs from published v0.1.4')
        esp = WORK / 'base.esp'
        esp.write_bytes(z.read('KhajiitKeenSenses.esp'))
    generated = source / (NAME + '.psc')
    generated.write_text(original_source + EXTRA, encoding='utf-8')
    trigger = source / (EFFECT + '.psc')
    trigger.write_text(effect_source.split('Event OnEffectStart(', 1)[0] + TRIGGER, encoding='utf-8')
    api = ROOT / 'tools/papyrus-api'
    verify_stubs(api)
    command = ([args.wine] if args.wine else []) + [str(compiler), '--game=skyrim',
        '--strict', '--champollion-compat=false', '--enable-debug-info=false',
        '--all-warnings-as-errors', '--flags=' + windows_path(api / 'TESV_Papyrus_Flags.flg', args.wine),
        '--import=' + windows_path(api, args.wine),
        '--output=' + windows_path(package / 'Scripts', args.wine), NAME + '.psc', EFFECT + '.psc']
    subprocess.run(command, cwd=source, check=True)
    for name in (NAME, EFFECT):
        pex = package / 'Scripts' / (name + '.pex')
        repair_caprica_skyrim_size(pex)
        normalize_pex(pex)
        subprocess.run([args.dotnet, 'run', '--project', str(ROOT / 'tools/PluginBuilder/PluginBuilder.csproj'),
            '--no-build', '--configuration', 'Release', '--', '--verify-pex', str(pex)], cwd=ROOT, check=True)
        shutil.copy2(source / (name + '.psc'), package / 'Scripts/Source')
    diagnostic = read_pex(package / 'Scripts' / (NAME + '.pex'))['objects'][0]
    diagnostic_effect = read_pex(package / 'Scripts' / (EFFECT + '.pex'))['objects'][0]
    checked = verify_pex_calls([diagnostic, diagnostic_effect])
    print(f'Independent vanilla API validation: {checked} native calls matched pinned signatures.')
    debug_calls = set()
    for obj in (diagnostic, diagnostic_effect):
        for functions in obj['states'].values():
            for function in functions.values():
                for instruction in function['code']:
                    operands = instruction['args']
                    if instruction['op'] == 25:
                        api, method = operands[0][1].lower(), operands[1][1].lower()
                        if (api, method) not in {('game', 'getplayer'), ('game', 'getrealhourspassed'),
                                                 ('debug', 'notification'), ('debug', 'trace')}:
                            raise ValueError(f'Unexpected global API: {api}.{method}')
                        if api == 'debug':
                            debug_calls.add(method)
                    if instruction['op'] == 23 and operands[0][1].lower() in {
                            'registerforupdate', 'registerforsingleupdate', 'equipspell', 'unequipspell'}:
                        raise ValueError('Diagnostic added a timer or equipment operation')
    if debug_calls != {'notification', 'trace'}:
        raise ValueError('Diagnostic must use nonmodal notifications and tracing only')
    records, _ = read_plugin(esp)
    forms = {r['id'] & 0xFFFFFF: r for r in records[1:]}
    bindings = vmad(forms[0x801])[EFFECT]['properties']
    manager_bindings = vmad(forms[0x804])[NAME]['properties']
    verify_behavior(original, diagnostic, effect, bindings, manager_bindings)
    verify_input(effect, diagnostic_effect, diagnostic, bindings, manager_bindings)
    shutil.copy2(ROOT / 'docs/RELOAD_DIAGNOSTIC.md', package / METADATA / 'README.md')
    shutil.copy2(ROOT / 'LICENSE', package / METADATA / 'LICENSE.txt')
    (package / METADATA / 'build-manifest.json').write_text(json.dumps({
        'version': '0.1.4-diagnostic5', 'requires': 'KhajiitKeenSenses 0.1.4',
        'base_sha256': BASE_SHA256, 'new_records': 0, 'new_saved_variables': 0,
        'controller_functions_unchanged': True, 'input_event_instrumented': True,
        'command_required': False, 'activation': 'Use the existing Keen Senses power once',
        'ui': 'Nonmodal notifications only; no MessageBox, menu or Wait call',
        'api_reference': 'BellCubeDev/papyrus-index@ec822650d44885707c01e90eeb569551f0ab8ddb',
        'notification_parameters': 1,
        'note': 'Probe attempts one normal activation; not a bug fix. Skyrim runtime/display unverified.'
    }, indent=2) + '\n')
    output = ROOT / 'dist/KhajiitKeenSenses-0.1.4-diagnostic5-MO2.zip'
    archive(package, output, checksum_path=METADATA + 'SHA256SUMS.txt')
    with zipfile.ZipFile(output) as z:
        expected = {f'Scripts/{name}.pex' for name in (NAME, EFFECT)} | {
            f'Scripts/Source/{name}.psc' for name in (NAME, EFFECT)} | {
            METADATA + n for n in ('README.md', 'LICENSE.txt', 'build-manifest.json', 'SHA256SUMS.txt')}
        if set(z.namelist()) != expected or z.testzip() is not None:
            raise ValueError('Invalid diagnostic-only archive')
        for line in z.read(METADATA + 'SHA256SUMS.txt').decode().splitlines():
            digest, name = line.split('  ', 1)
            if hashlib.sha256(z.read(name)).hexdigest() != digest:
                raise ValueError('Diagnostic checksum failure')
    source_archive(ROOT / 'dist/KhajiitKeenSenses-0.1.4-diagnostic5-source.zip')


if __name__ == '__main__':
    main()
