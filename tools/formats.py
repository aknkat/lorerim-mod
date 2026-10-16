"""Independent, bounded readers for this mod's TES5 and Skyrim PEX formats.

The ESP reader follows xEdit's TES5 schema. The PEX reader follows the
published Skyrim PEX layout; it does not import the ESP writer or compiler.
"""
import struct
from pathlib import Path


class Reader:
    def __init__(self, data, endian="<"):
        self.data, self.pos, self.endian = data, 0, endian

    def take(self, length):
        if length < 0 or self.pos + length > len(self.data):
            raise ValueError("Truncated binary")
        value = self.data[self.pos:self.pos + length]
        self.pos += length
        return value

    def number(self, fmt):
        return struct.unpack(self.endian + fmt, self.take(struct.calcsize(fmt)))[0]

    def string(self):
        return self.take(self.number("H")).decode("utf-8")

    def finish(self):
        if self.pos != len(self.data):
            raise ValueError("Unconsumed binary data")


def read_plugin(path):
    records, groups = [], []

    def walk(data):
        r = Reader(data)
        while r.pos < len(data):
            header = r.take(24)
            tag = header[:4].decode("ascii")
            size, = struct.unpack_from("<I", header, 4)
            if tag == "GRUP":
                if size < 24:
                    raise ValueError("Invalid GRUP length")
                groups.append((header[8:12].decode("ascii"),
                               struct.unpack_from("<I", header, 12)[0]))
                walk(r.take(size - 24))
                continue
            flags, form = struct.unpack_from("<II", header, 8)
            if flags & 0x40000:
                raise ValueError("Unexpected compressed record")
            sub = Reader(r.take(size))
            fields = []
            while sub.pos < len(sub.data):
                name = sub.take(4).decode("ascii")
                length = sub.number("H")
                if name == "XXXX":
                    raise ValueError("Unexpected extended subrecord")
                fields.append((name, sub.take(length)))
            sub.finish()
            records.append({"type": tag, "id": form, "flags": flags,
                            "version": struct.unpack_from("<H", header, 20)[0],
                            "fields": fields})
        r.finish()

    walk(Path(path).read_bytes())
    return records, groups


def fields(record, tag):
    return [data for name, data in record["fields"] if name == tag]


def field(record, tag):
    values = fields(record, tag)
    if len(values) != 1:
        raise ValueError(f"Expected one {tag}, found {len(values)}")
    return values[0]


def conditions(record):
    result = []
    for data in fields(record, "CTDA"):
        if len(data) != 32:
            raise ValueError("Invalid CTDA size")
        kind, comparison, function, p1, p2, run_on, reference, p3 = struct.unpack(
            "<B3xfH2xIIIIi", data)
        result.append({"operator": kind >> 5, "or": bool(kind & 1),
                       "value": comparison, "function": function,
                       "p1": p1, "p2": p2, "run_on": run_on,
                       "reference": reference, "p3": p3})
    return result


def vmad(record):
    r = Reader(field(record, "VMAD"))
    if (r.number("H"), r.number("H")) != (5, 2):
        raise ValueError("Unexpected VMAD version/object format")
    scripts = {}
    for _ in range(r.number("H")):
        name = r.string()
        flags = r.number("B")
        properties = {}
        for _ in range(r.number("H")):
            prop = r.string()
            if (r.number("B"), r.number("B")) != (1, 1):
                raise ValueError("Expected edited object property")
            unused, alias, form = r.number("H"), r.number("h"), r.number("I")
            if unused != 0 or alias != -1:
                raise ValueError("Unexpected alias binding")
            properties[prop] = form
        scripts[name] = {"flags": flags, "properties": properties}
    if record["type"] == "QUST" and r.pos < len(r.data):
        if r.number("B") != 2 or r.number("H") != 0 or r.string() != "" or r.number("H") != 0:
            raise ValueError("Unexpected quest fragments or aliases")
    r.finish()
    return scripts


def strings_table(path):
    data = Path(path).read_bytes()
    r = Reader(data)
    count, size = r.number("I"), r.number("I")
    entries = [(r.number("I"), r.number("I")) for _ in range(count)]
    body = r.take(size)
    r.finish()
    result = {}
    for key, offset in entries:
        if offset >= len(body) or key in result:
            raise ValueError("Invalid strings directory")
        if str(path).lower().endswith(".strings"):
            end = body.index(b"\0", offset)
            raw = body[offset:end]
        else:
            length, = struct.unpack_from("<I", body, offset)
            raw = body[offset + 4:offset + 4 + length]
            if len(raw) != length or not raw.endswith(b"\0"):
                raise ValueError("Invalid length-prefixed string")
            raw = raw[:-1]
        result[key] = raw.decode("utf-8")
    return result


def normalize_pex(path):
    """Replace only non-executable header metadata for reproducible output."""
    path = Path(path)
    data = path.read_bytes()
    if data[:8] != bytes.fromhex("fa57c0de03020001"):
        raise ValueError("Expected Skyrim PEX 3.2 / game 1")
    r = Reader(data, ">")
    r.take(16)
    for _ in range(3):
        r.string()
    names = [path.stem + ".psc", "aknkat", "reproducible-build"]
    header = data[:8] + bytes(8)
    for name in names:
        raw = name.encode("utf-8")
        header += struct.pack(">H", len(raw)) + raw
    path.write_bytes(header + data[r.pos:])


def repair_caprica_skyrim_size(path):
    """Normalize Caprica's object-size marker to the CK-compatible PEX layout.

    The upstream PexWriter.endObject writes a uint32 marker directly rather
    than through its endian-aware writer. Only the exact, single-object case
    with a matching little-endian BODY size is accepted. The canonical size
    includes the four-byte size field itself, as Mutagen PexObject confirms.
    Strictly parse the entire
    repaired candidate before writing; do not skip or relax validation.
    """
    path = Path(path)
    data = path.read_bytes()
    r = Reader(data, ">")
    if r.take(8) != bytes.fromhex("fa57c0de03020001"):
        raise ValueError("Expected Skyrim PEX 3.2")
    r.take(8)
    for _ in range(3):
        r.string()
    for _ in range(r.number("H")):
        r.string()
    if r.number("B") != 0:
        raise ValueError("Expected debug info disabled")
    r.take(r.number("H") * 3)
    if r.number("H") != 1:
        raise ValueError("Expected exactly one script object")
    r.take(2)
    position = r.pos
    raw = r.take(4)
    actual = len(data) - r.pos
    canonical = actual + 4
    changed = False
    if struct.unpack(">I", raw)[0] != canonical:
        if struct.unpack("<I", raw)[0] != actual:
            raise ValueError("Object size mismatch is not the known endian bug")
        data = data[:position] + struct.pack(">I", canonical) + data[position + 4:]
        changed = True
    read_pex(data)
    if changed:
        path.write_bytes(data)
    return changed


def read_pex(path):
    r = Reader(path if isinstance(path, bytes) else Path(path).read_bytes(), ">")
    if r.take(8) != bytes.fromhex("fa57c0de03020001"):
        raise ValueError("Not Skyrim PEX 3.2")
    timestamp = r.number("Q")
    metadata = [r.string() for _ in range(3)]
    table = [r.string() for _ in range(r.number("H"))]

    def indexed():
        index = r.number("H")
        if index >= len(table):
            raise ValueError("Invalid PEX string index")
        return table[index]

    def value():
        kind = r.number("B")
        if kind == 0:
            return kind, None
        if kind in (1, 2):
            return kind, indexed()
        if kind == 3:
            return kind, r.number("i")
        if kind == 4:
            return kind, r.number("f")
        if kind == 5:
            val = r.number("B")
            if val not in (0, 1):
                raise ValueError("Invalid PEX Boolean")
            return kind, bool(val)
        raise ValueError("Unsupported PEX value type")

    # Skyrim opcode arities, including only the Skyrim instruction set.
    arities = [0,3,3,3,3,3,3,3,3,3,2,2,2,2,2,3,3,3,3,3,1,2,2,
               3,2,3,1,3,3,3,2,2,3,3,4,4]

    def function():
        name, returns, doc = indexed(), indexed(), indexed()
        flags, native_flags = r.number("I"), r.number("B")
        params = [(indexed(), indexed()) for _ in range(r.number("H"))]
        locals_ = [(indexed(), indexed()) for _ in range(r.number("H"))]
        code = []
        for _ in range(r.number("H")):
            op = r.number("B")
            if op >= len(arities):
                raise ValueError("Non-Skyrim opcode")
            args = [value() for _ in range(arities[op])]
            variadic = []
            if op in (23, 24, 25):
                kind, count = value()
                if kind != 3 or not 0 <= count <= 128:
                    raise ValueError("Invalid call argument count")
                variadic = [value() for _ in range(count)]
            code.append({"op": op, "args": args, "variadic": variadic})
        for i, instruction in enumerate(code):
            if instruction["op"] in (20, 21, 22):
                kind, distance = instruction["args"][-1]
                if kind != 3 or not 0 <= i + distance <= len(code):
                    raise ValueError("Invalid branch destination")
        return name, {"parameters": params, "locals": locals_, "code": code,
                      "returns": returns, "native_flags": native_flags}

    if r.number("B") != 0:
        raise ValueError("Expected debug info disabled")
    user_flags = [(indexed(), r.number("B")) for _ in range(r.number("H"))]
    objects = []
    for _ in range(r.number("H")):
        name = indexed()
        size_offset = r.pos
        length = r.number("I")
        if length < 4:
            raise ValueError("Invalid PEX object size")
        end = r.pos + length - 4
        parent, doc, flags, state = indexed(), indexed(), r.number("I"), indexed()
        variables = {}
        for _ in range(r.number("H")):
            var, type_, flags = indexed(), indexed(), r.number("I")
            variables[var] = {"type": type_, "initial": value()}
        properties = {}
        for _ in range(r.number("H")):
            prop, type_, doc, flags = indexed(), indexed(), indexed(), r.number("I")
            kind = r.number("B")
            if kind != 7:
                raise ValueError("Expected auto read/write property")
            properties[prop] = {"type": type_, "variable": indexed()}
        states = {}
        for _ in range(r.number("H")):
            state_name = indexed()
            states[state_name] = dict(function() for _ in range(r.number("H")))
        if r.pos != end:
            raise ValueError("Invalid PEX object size")
        objects.append({"name": name, "parent": parent, "properties": properties,
                        "variables": variables, "states": states,
                        "size_offset": size_offset, "encoded_size": length})
    r.finish()
    return {"objects": objects, "metadata": metadata, "timestamp": timestamp}
