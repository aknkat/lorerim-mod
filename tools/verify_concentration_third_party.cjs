#!/usr/bin/env node
// Structural readback using an external, separately authored package.
// The package path is explicit: it is NOT bundled or required by the game.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {promisify} = require('node:util');

async function main() {
  const [modulePath, plugin] = process.argv.slice(2);
  if (!modulePath || !plugin) throw new Error('Usage: node verify_concentration_third_party.cjs MODULE_PATH PLUGIN');
  const tes = require(path.resolve(modulePath));
  const version = require(path.join(path.resolve(modulePath), 'package.json')).version;
  assert.equal(version, '0.0.1');
  const offsets = promisify(tes.getRecordOffsets);
  const bufferAt = promisify(tes.getRecordBuffer);
  const fd = fs.openSync(plugin, 'r');
  const context = {};
  const decoded = [];
  let roundtripped = 0;
  try {
    const roots = await offsets(fd, 0);
    assert.deepEqual(roots.map(([, type]) => type), ['TES4', 'GRUP', 'GRUP', 'GRUP']);
    async function readRecord(offset, expected) {
      const raw = await bufferAt(fd, offset);
      assert.equal(raw.toString('ascii', 0, 4), expected);
      const record = tes.getRecord(raw, context);
      assert.equal(record.recordType, expected);
      assert.ok(!record.compressed);
      const rewritten = tes.writeRecord(record, context);
      assert.deepEqual(rewritten, raw, `Third-party roundtrip differs: ${expected}`);
      roundtripped += 1;
      decoded.push(record);
    }
    await readRecord(roots[0][0], 'TES4');
    for (const [offset] of roots.slice(1)) {
      const children = await offsets(fd, offset);
      assert.equal(children[0][1], 'GRUP');
      assert.equal(children.length, 2);
      await readRecord(children[1][0], children[1][1]);
    }
    assert.deepEqual(decoded.map(r => r.recordType), ['TES4', 'EFSH', 'MGEF', 'SPEL']);
    const spell = decoded[3], effect = decoded[2], shader = decoded[1];
    assert.equal(Number(spell.id), 0x01000800);
    assert.equal(Number(effect.id), 0x01000801);
    assert.equal(Number(shader.id), 0x01000802);
    assert.equal(shader.subRecords.find(r => r.type === 'DATA').size, 400);
    assert.equal(spell.subRecords.filter(r => r.type === 'CTDA').length, 3);
    assert.equal(effect.subRecords.filter(r => r.type === 'CTDA').length, 6);
    assert.ok(!decoded.some(r => r.subRecords.some(s => s.type === 'VMAD')));
    console.log(JSON.stringify({reader: '@fcrick/tes-data', version,
      records: decoded.map(r => ({type:r.recordType, formId:Number(r.id || 0),
        subrecords:r.subRecords.length})), byte_exact_roundtrips:roundtripped,
      scope:'third-party structural readback only; Skyrim runtime not tested'}, null, 2));
  } finally {
    fs.closeSync(fd);
  }
}
main().catch(err => { console.error(err); process.exitCode = 1; });
