#!/usr/bin/env node
// External parser readback and byte-exact roundtrip, no game execution.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {promisify} = require('node:util');

async function main() {
  const [modulePath, plugin] = process.argv.slice(2);
  if (!modulePath || !plugin) throw new Error('Usage: node verify_emerald_third_party.cjs MODULE_PATH PLUGIN');
  const tes = require(path.resolve(modulePath));
  assert.equal(require(path.join(path.resolve(modulePath), 'package.json')).version, '0.0.1');
  const offsets = promisify(tes.getRecordOffsets);
  const bufferAt = promisify(tes.getRecordBuffer);
  const fd = fs.openSync(plugin, 'r');
  const context = {}, decoded = [];
  try {
    const roots = await offsets(fd, 0);
    assert.deepEqual(roots.map(([, type]) => type), ['TES4', 'GRUP', 'GRUP', 'GRUP']);
    async function readRecord(offset, expected) {
      const raw = await bufferAt(fd, offset);
      const record = tes.getRecord(raw, context);
      assert.equal(record.recordType, expected);
      assert.deepEqual(tes.writeRecord(record, context), raw);
      decoded.push(record);
    }
    await readRecord(roots[0][0], 'TES4');
    for (const [offset] of roots.slice(1)) {
      const children = await offsets(fd, offset);
      assert.equal(children.length, 2);
      await readRecord(children[1][0], children[1][1]);
    }
    assert.deepEqual(decoded.map(r => r.recordType), ['TES4', 'TXST', 'HDPT', 'FLST']);
    assert.deepEqual(decoded.slice(1).map(r => Number(r.id)), [0x01000801, 0x01000800, 0x01000802]);
    console.log(JSON.stringify({reader:'@fcrick/tes-data@0.0.1',
      byte_exact_roundtrips:decoded.length, records:decoded.map(r => r.recordType),
      scope:'structural readback only'}, null, 2));
  } finally { fs.closeSync(fd); }
}
main().catch(err => { console.error(err); process.exitCode = 1; });
