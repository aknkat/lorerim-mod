using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Binary.Parameters;
using Mutagen.Bethesda.Plugins.Binary.Streams;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Mutagen.Bethesda.Strings.DI;
using System.Text.Json;

if (args.Length == 2 && args[0] == "--verify-pex")
{
    var pex = Mutagen.Bethesda.Pex.PexFile.CreateFromFile(args[1], GameCategory.Skyrim);
    if (pex.Objects.Count != 1 || pex.Objects[0].Name != "LKS_KeenSensesEffect")
        throw new InvalidDataException("Unexpected PEX script objects.");
    Console.WriteLine("Mutagen independent PEX readback: complete Skyrim file and object sizes passed.");
    return;
}

// External IDs checked against Mutagen.Bethesda.FormKeys.SkyrimSE/Skyrim.
// No game data, existing record payload, or master override is shipped.
static FormKey Vanilla(uint id) => new(ModKey.FromNameAndExtension("Skyrim.esm"), id);
var output = Path.GetFullPath(args.Length > 0 ? args[0] : "package");
Directory.CreateDirectory(output);
var key = ModKey.FromNameAndExtension("KhajiitKeenSenses.esp");
var mod = new SkyrimMod(key, SkyrimRelease.SkyrimSE);
mod.ModHeader.Flags = SkyrimModHeader.HeaderFlag.Small | SkyrimModHeader.HeaderFlag.Localized;
mod.ModHeader.Author = "aknkat";
mod.ModHeader.Description = "Keen Senses 0.1.2 - remove self-referential cooldown gate; game validation pending.";
mod.ModHeader.Stats.Version = 1.7f;

var power = new Spell(new FormKey(key, 0x800), SkyrimRelease.SkyrimSE);
var control = new MagicEffect(new FormKey(key, 0x801), SkyrimRelease.SkyrimSE);
var detect = new MagicEffect(new FormKey(key, 0x802), SkyrimRelease.SkyrimSE);
var detectionSpell = new Spell(new FormKey(key, 0x803), SkyrimRelease.SkyrimSE);
mod.Spells.Add(power);
mod.Spells.Add(detectionSpell);
mod.MagicEffects.Add(control);
mod.MagicEffects.Add(detect);

const SpellDataFlag safeSpellFlags = SpellDataFlag.ManualCostCalc
    | SpellDataFlag.IgnoreResistance | SpellDataFlag.NoAbsorbOrReflect
    | SpellDataFlag.NoDualCastModification;
TranslatedString Text(string english, string japanese)
{
    var text = new TranslatedString(Language.English, english);
    text.Set(Language.Japanese, japanese);
    return text;
}
void SetSpell(Spell spell, string editorId, string english, string japanese, SpellType type)
{
    spell.EditorID = editorId;
    spell.Name = Text(english, japanese);
    spell.Description = Text("", "");
    spell.Type = type;
    spell.CastType = CastType.FireAndForget;
    spell.TargetType = TargetType.Self;
    spell.EquipmentType.SetTo(Vanilla(0x25BEE)); // Voice
    spell.Flags = safeSpellFlags;
    spell.BaseCost = 0;
    spell.ChargeTime = 0;
    spell.CastDuration = 0;
    spell.Range = 0;
}
void SetEffect(MagicEffect effect, string editorId, string english, string japanese)
{
    effect.EditorID = editorId;
    effect.Name = Text(english, japanese);
    effect.BaseCost = 0;
    effect.MagicSkill = ActorValue.None;
    effect.ResistValue = ActorValue.None;
    effect.CastType = CastType.FireAndForget;
    effect.TargetType = TargetType.Self;
    effect.CastingSoundLevel = SoundLevel.Silent;
    effect.SkillUsageMultiplier = 0;
}
ConditionFloat Compare(ConditionData data, float value,
    CompareOperator op = CompareOperator.EqualTo, bool or = false)
    => new() { Data = data, ComparisonValue = value, CompareOperator = op,
        Flags = or ? Condition.Flag.OR : 0 };
GetIsReferenceConditionData IsPlayer()
{
    var data = new GetIsReferenceConditionData();
    data.Target.Link.SetTo(Vanilla(0x14));
    return data;
}
GetIsRaceConditionData IsRace(uint id)
{
    var data = new GetIsRaceConditionData();
    data.Race.Link.SetTo(Vanilla(id));
    return data;
}
HasKeywordConditionData Keyword(uint id)
{
    var data = new HasKeywordConditionData();
    data.Keyword.Link.SetTo(Vanilla(id));
    return data;
}

SetSpell(power, "LKS_KeenSensesPower", "Keen Senses", "鋭敏な感覚", SpellType.LesserPower);
power.Description = Text("Detect living creatures within about 8 metres for 2 seconds. 60-second cooldown. Khajiit only. Excludes undead, machines and corpses.",
    "半径約8mの生物を2秒間探知する。再使用まで60秒。カジート専用。アンデッド・機械・死体は対象外。");
SetEffect(control, "LKS_KeenSensesCooldownEffect", "Keen Senses: Cooldown", "鋭敏な感覚：再使用待ち");
control.Archetype = new MagicEffectArchetype(MagicEffectArchetype.TypeEnum.Script);
control.Flags = MagicEffect.Flag.NoMagnitude | MagicEffect.Flag.NoArea
    | MagicEffect.Flag.NoRecast | MagicEffect.Flag.NoHitEvent
    | MagicEffect.Flag.Painless | MagicEffect.Flag.NoDeathDispel;
control.Description = Text("Keen Senses can be used again when this effect expires.", "鋭敏な感覚は、この効果が終了すると再び使用できる。");
control.VirtualMachineAdapter = new VirtualMachineAdapter();
var script = new ScriptEntry { Name = "LKS_KeenSensesEffect" };
void Bind(string name, FormKey form)
{
    var property = new ScriptObjectProperty { Name = name };
    property.Object.SetTo(form);
    script.Properties.Add(property);
}
Bind("DetectionSpell", detectionSpell.FormKey);
Bind("KhajiitRace", Vanilla(0x13745));
Bind("KhajiitVampireRace", Vanilla(0x88845));
control.VirtualMachineAdapter.Scripts.Add(script);
var trigger = new Effect { Data = new EffectData
    { Magnitude = 0, Area = 0, Duration = 60 } };
trigger.BaseEffect.SetTo(control.FormKey);
trigger.Conditions.Add(Compare(IsPlayer(), 1));
trigger.Conditions.Add(Compare(IsRace(0x13745), 1, or: true));
trigger.Conditions.Add(Compare(IsRace(0x88845), 1));
// Do not condition this effect on its own absence, including on the SPEL
// entry: active-effect conditions can be reevaluated after application.
// The finite 60-second effect and NoRecast handle duplicate applications.
power.Effects.Add(trigger);

SetSpell(detectionSpell, "LKS_DetectionPulse", "LKS Internal Detection Pulse", "LKS Internal Detection Pulse", SpellType.Spell);
detectionSpell.Flags |= SpellDataFlag.AreaEffectIgnoresLOS;
SetEffect(detect, "LKS_DetectLivingEffect", "Keen Senses: Detection", "鋭敏な感覚：探知");
// Based on the actual exported native FF Detect Life records (001019D8-DB).
// The shader applies over EFIT.Area. NoArea/area=0 disables that distribution.
detect.Flags = MagicEffect.Flag.Recover | MagicEffect.Flag.NoMagnitude
    | MagicEffect.Flag.FXPersist | MagicEffect.Flag.NoRecast
    | MagicEffect.Flag.HideInUI | MagicEffect.Flag.NoHitEvent | MagicEffect.Flag.Painless;
detect.Archetype = new MagicEffectArchetype(MagicEffectArchetype.TypeEnum.DetectLife)
    { ActorValue = ActorValue.None };
detect.SpellmakingArea = 27;
detect.DualCastScale = 1;
// This shader rendered red in the user's working Aura Whisper comparison.
// A reference only: never override/copy a third-party winning shader record.
detect.HitShader.SetTo(Vanilla(0xDC209));
detect.Description = Text("Detect living creatures within about 8 metres for 2 seconds.", "半径約8mの生物を2秒間探知する。");
// Native-style target filters; no self-exclusion condition that can reject
// application to the caster before the area effect is distributed.
detect.Conditions.Add(Compare(new GetDeadConditionData(), 0));
detect.Conditions.Add(Compare(Keyword(0x13796), 0));
detect.Conditions.Add(Compare(Keyword(0x1397A), 0));
detect.Conditions.Add(Compare(Keyword(0xF82F4), 0)); // Respect native NoDetectLife.
detect.Conditions.Add(Compare(new IsUndeadConditionData(), 0));
var distance = new GetDistanceConditionData();
distance.Target.Link.SetTo(Vanilla(0x14));
detect.Conditions.Add(Compare(distance, 560, CompareOperator.LessThanOrEqualTo));
// Native SPELs use EFIT.Area, not Magnitude, for their detection radius.
// 27 feet covers 576 units; the distance condition clips that to 560 (~8 m).
var pulse = new Effect { Data = new EffectData
    { Magnitude = 0, Area = 27, Duration = 2 } };
pulse.BaseEffect.SetTo(detect.FormKey);
detectionSpell.Effects.Add(pulse);

var path = Path.Combine(output, key.FileName.String);
var encoding = new EncodingBundle(MutagenEncoding._utf8, MutagenEncoding._utf8);
mod.WriteToBinary(path, new BinaryWriteParameters { Encodings = encoding,
    Parallel = new ParallelWriteParameters { MaxDegreeOfParallelism = 1 } });
using var readback = SkyrimMod.CreateFromBinaryOverlay(path, SkyrimRelease.SkyrimSE);
var records = readback.EnumerateMajorRecords().ToArray();
if (records.Length != 4 || records.Any(r => r.FormKey.ModKey != key))
    throw new InvalidDataException("Unexpected record count or existing-record override.");
if (readback.ModHeader.MasterReferences.Count != 1
    || readback.ModHeader.MasterReferences[0].Master.FileName.String != "Skyrim.esm")
    throw new InvalidDataException("Unexpected runtime master dependency.");
foreach (var link in records.SelectMany(r => r.EnumerateFormLinks()))
{
    if (link.FormKey.IsNull) continue;
    if (link.FormKey.ModKey == key && !records.Any(r => r.FormKey == link.FormKey))
        throw new InvalidDataException($"Broken local link: {link.FormKey}");
}
var report = new { plugin = key.FileName.String, version = "0.1.2",
    status = "structural_validation_only_game_validation_pending",
    master = "Skyrim.esm", esl = true, overrides = 0,
    records = records.Select(r => new { id = $"{r.FormKey.ID:X6}", type = r.GetType().Name,
        editor_id = r.EditorID }).ToArray(),
    external_references = new Dictionary<string, string> {
        ["PlayerRef"] = "00000014", ["KhajiitRace"] = "00013745",
        ["KhajiitRaceVampire"] = "00088845", ["ActorTypeUndead"] = "00013796",
        ["ActorTypeDwarven"] = "0001397A", ["NoDetectLife"] = "000F82F4",
        ["LifeDetectedEnemy"] = "000DC209",
        ["Voice"] = "00025BEE" },
    native_detection_area_feet = 27, detection_magnitude = 0, distance_filter_units = 560,
    reference_data = "User-provided LKS-detection-records.txt; 3494 loaded files",
    detection_seconds = 2, cooldown_seconds = 60,
    cooldown_control = "Finite effect with NoRecast; no self-referential HasMagicEffect gate",
    languages = new[] { "English", "Japanese" },
    skse_required = false, requiem_master_required = false };
var metadata = Path.Combine(output, "KhajiitKeenSenses");
Directory.CreateDirectory(metadata);
File.WriteAllText(Path.Combine(metadata, "build-manifest.json"),
    JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }) + "\n");
Console.WriteLine($"Wrote {path}; Mutagen readback: 4 new records, 0 overrides, Skyrim.esm only.");
