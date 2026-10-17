"""Execute emitted Papyrus instructions against a deliberately small mock host.

The saved deadline is actual compiled-script state. The native play-time clock
and its save/load are mocked; this does not validate Skyrim's clock semantics.
No source-language translation or reimplementation of TryActivate is used.
"""
import json
import struct


def float32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


class ScriptInstance:
    def __init__(self, obj, bindings, form=None):
        self.obj, self.form = obj, form
        self.fields = {name.lower(): info["initial"][1]
                       for name, info in obj["variables"].items()}
        for name, info in obj["properties"].items():
            self.fields[info["variable"].lower()] = bindings.get(name)

    def invoke(self, name, args, host):
        functions = self.obj["states"][""]
        function = next(f for key, f in functions.items() if key.lower() == name.lower())
        local = {key.lower(): None for key, _ in function["locals"]}
        local.update({key.lower(): arg for (key, _), arg in zip(function["parameters"], args)})
        local["self"] = self
        variable_types = {key.lower(): info['type'].lower()
                          for key, info in self.obj['variables'].items()}
        variable_types.update({key.lower(): kind.lower()
                               for key, kind in function['locals'] + function['parameters']})

        def get(value):
            kind, raw = value
            if kind != 1:
                return raw
            key = raw.lower()
            return local[key] if key in local else self.fields[key]

        def put(value, data):
            if value[0] != 1:
                raise ValueError("Nonvariable destination")
            key = value[1].lower()
            if isinstance(data, float):
                data = float32(data)
            if key in self.fields:
                self.fields[key] = data
            else:
                local[key] = data

        code, pc, steps = function["code"], 0, 0
        while pc < len(code):
            steps += 1
            if steps > 2000:
                raise ValueError("Unexpected loop")
            inst = code[pc]
            op, a, extra = inst["op"], inst["args"], inst["variadic"]
            if op == 0:
                pass
            elif op in (2, 4, 6, 8):
                left, right = get(a[1]), get(a[2])
                operation = {2: lambda: left + right, 4: lambda: left - right,
                             6: lambda: left * right, 8: lambda: left / right}[op]
                put(a[0], operation())
            elif op == 10:
                put(a[0], not get(a[1]))
            elif op == 13:
                put(a[0], get(a[1]))
            elif op == 14:
                value = get(a[1])
                if variable_types.get(a[0][1].lower()) == 'string':
                    if value is None:
                        value = 'None'
                    elif isinstance(value, bool):
                        value = 'True' if value else 'False'
                    elif isinstance(value, float):
                        value = f'{value:.6f}'
                    else:
                        value = str(value)
                put(a[0], value)
            elif op == 15:
                put(a[0], get(a[1]) == get(a[2]))
            elif op in (16, 17, 18, 19):
                left, right = get(a[1]), get(a[2])
                operation = {16: lambda: left < right, 17: lambda: left <= right,
                             18: lambda: left > right, 19: lambda: left >= right}[op]
                put(a[0], operation())
            elif op == 20:
                pc += get(a[0])
                continue
            elif op in (21, 22):
                if bool(get(a[0])) == (op == 21):
                    pc += get(a[1])
                    continue
            elif op == 23:
                result = host.method(get(a[1]), a[0][1], [get(x) for x in extra])
                put(a[2], result)
            elif op == 25:
                if a[0][1].lower() == 'debug' and a[1][1].lower() == 'messagebox' and len(extra) == 1:
                    host.messages.append(get(extra[0]))
                    put(a[2], None)
                    pc += 1
                    continue
                if a[0][1].lower() != "game" or extra:
                    raise ValueError("Unexpected global API")
                if a[1][1].lower() == "getplayer":
                    put(a[2], "player")
                elif a[1][1].lower() == "getrealhourspassed":
                    hook, host.clock_hook = host.clock_hook, None
                    if hook:
                        hook(host)
                    put(a[2], host.play_hours)
                else:
                    raise ValueError("Unexpected Game API")
            elif op == 26:
                return get(a[0])
            elif op == 27:
                put(a[0], get(a[1]) + get(a[2]))
            elif op == 28:
                receiver = get(a[1])
                prop = next(info for key, info in receiver.obj["properties"].items()
                            if key.lower() == a[0][1].lower())
                put(a[2], receiver.fields[prop["variable"].lower()])
            else:
                raise ValueError(f"Unsupported opcode {op}")
            pc += 1
        return None


class Host:
    CONTROLLER = 0x01000804
    PULSE = 0x01000803

    def __init__(self, effect, manager, effect_bindings, manager_bindings):
        self.effect, self.manager_object = effect, manager
        self.effect_bindings, self.manager_bindings = effect_bindings, manager_bindings
        self.manager = ScriptInstance(manager, manager_bindings, self.CONTROLLER)
        self.running, self.start_ok = False, True
        self.race = 0x13745
        self.now, self.due = 0.0, None
        self.play_hours = 100.0
        self.registrations, self.starts, self.casts = [], 0, []
        self.messages = []
        self.getrace_hook = None
        self.register_hook = None
        self.clock_hook = None
        self.cast_hook = None

    def activate(self, target="player", caster="player"):
        # A fresh trigger object for every press: state must never live here.
        trigger = ScriptInstance(self.effect, self.effect_bindings)
        return trigger.invoke("OnEffectStart", [target, caster], self)

    def method(self, receiver, name, args):
        method = name.lower()
        if receiver == self.CONTROLLER:
            if method == "isrunning" and not args:
                return self.running
            if method == "start" and not args:
                self.starts += 1
                self.running = self.start_ok
                return self.start_ok
            if any(key.lower() == method for key in self.manager.obj['states']['']):
                if not self.running:
                    raise ValueError("Controller called before quest start")
                return self.manager.invoke(name, args, self)
        elif receiver == "player" and method == "getrace" and not args:
            hook, self.getrace_hook = self.getrace_hook, None
            if hook:
                hook(self)
            return self.race
        elif receiver == self.PULSE and method == "cast":
            self.casts.append((self.now, receiver, *args))
            hook, self.cast_hook = self.cast_hook, None
            if hook:
                hook(self)
            return None
        elif receiver is self.manager and method == 'isrunning' and not args:
            return self.running
        elif receiver is self.manager and any(key.lower() == method for key in self.manager.obj['states']['']):
            return self.manager.invoke(name, args, self)
        elif receiver is self.manager and method == "registerforsingleupdate":
            self.due = self.now + args[0]
            self.registrations.append((self.now, args[0], self.due))
            hook, self.register_hook = self.register_hook, None
            if hook:
                hook(self)
            return None
        raise ValueError(f"Unexpected native/member call: {receiver} {method} {args}")

    def advance(self, seconds):
        end = self.now + seconds
        if self.due is not None and self.due <= end:
            self.now, self.due = self.due, None
            self.manager.invoke("OnUpdate", [], self)
        self.now = end
        self.play_hours += seconds / 3600.0

    def save(self):
        return json.dumps({"fields": self.manager.fields, "running": self.running,
                           "race": self.race,
                           "play_hours": self.play_hours,
                           "remaining_update": None if self.due is None else self.due - self.now})

    def load(self, snapshot):
        saved = json.loads(snapshot)
        # A newly added PEX variable has its initial value in an old save.
        self.manager.fields.update(saved["fields"])
        self.running, self.race = saved["running"], saved["race"]
        # Deliberately reset the session clock but restore the character's
        # native play-time counter. This is an assumption to test in-game.
        self.now = 0.0
        self.play_hours = saved["play_hours"]
        # Simulate update registrations being absent after load.
        self.due = None
