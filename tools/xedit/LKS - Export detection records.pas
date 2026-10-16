{
  Read-only export. No Add/Set/Remove/Copy operations on game records.
  Select any single record, Apply Script, then choose the text output path.
  "Winning" below means winning among the files loaded in this xEdit session.
}
unit LKSExportDetectionRecords;

var
  ReportLines, SeenRecords: TStringList;

function FindLoadedFile(filename: string): IInterface;
var
  i: integer;
  loadedFile: IInterface;
begin
  Result := nil;
  for i := 0 to Pred(FileCount) do begin
    loadedFile := FileByIndex(i);
    if SameText(GetFileName(loadedFile), filename) then begin
      Result := loadedFile;
      Exit;
    end;
  end;
end;

procedure DumpElement(e: IInterface; indent: string; depth: integer);
var
  i: integer;
begin
  if not Assigned(e) then Exit;
  if depth > 24 then begin
    ReportLines.Add(indent + '[Depth limit reached]');
    Exit;
  end;
  ReportLines.Add(indent + Name(e) + ' = ' + GetEditValue(e));
  for i := 0 to Pred(ElementCount(e)) do
    DumpElement(ElementByIndex(e, i), indent + '  ', depth + 1);
end;

procedure DumpRecord(rec: IInterface);
var
  key: string;
begin
  if not Assigned(rec) then Exit;
  key := GetFileName(GetFile(rec)) + ':' + IntToHex(GetLoadOrderFormID(rec), 8);
  if SeenRecords.IndexOf(key) >= 0 then Exit;
  SeenRecords.Add(key);
  ReportLines.Add('');
  ReportLines.Add('RECORD ' + key + ' ' + EditorID(rec));
  DumpElement(rec, '', 0);
end;

procedure DumpBaseAndWinner(rec: IInterface);
begin
  if not Assigned(rec) then Exit;
  DumpRecord(rec);
  DumpRecord(WinningOverride(rec));
end;

procedure DumpSpellEffects(spell: IInterface);
var
  effects, effect, baseEffect: IInterface;
  i: integer;
begin
  if not Assigned(spell) then Exit;
  effects := ElementByPath(spell, 'Effects');
  if not Assigned(effects) then Exit;
  for i := 0 to Pred(ElementCount(effects)) do begin
    effect := ElementByIndex(effects, i);
    baseEffect := LinksTo(ElementByPath(effect, 'EFID'));
    DumpBaseAndWinner(baseEffect);
  end;
end;

procedure DumpSpell(spell: IInterface);
begin
  if not Assigned(spell) then Exit;
  DumpBaseAndWinner(spell);
  DumpSpellEffects(spell);
  DumpSpellEffects(WinningOverride(spell));
end;

procedure DumpNative(masterFile: IInterface; formID: cardinal);
begin
  DumpBaseAndWinner(RecordByFormID(masterFile, formID, False));
end;

procedure DumpOwnGroup(plugin: IInterface; sig: string);
var
  group, rec: IInterface;
  i: integer;
begin
  group := GroupBySignature(plugin, sig);
  if not Assigned(group) then Exit;
  for i := 0 to Pred(ElementCount(group)) do begin
    rec := ElementByIndex(group, i);
    if sig = 'SPEL' then
      DumpSpell(rec)
    else
      DumpBaseAndWinner(rec);
  end;
end;

function Initialize: integer;
var
  skyrim, spell, ownPlugin: IInterface;
  dialog: TSaveDialog;
  outputPath: string;
begin
  Result := 0;
  skyrim := FindLoadedFile('Skyrim.esm');
  if not Assigned(skyrim) then begin
    AddMessage('LKS: Skyrim.esm must be loaded. No records changed.');
    Result := 1;
    Exit;
  end;
  spell := RecordByFormID(skyrim, $0008AFCC, False);
  if not Assigned(spell) then begin
    AddMessage('LKS: VoiceAuraWhisper1 0008AFCC not found. No records changed.');
    Result := 1;
    Exit;
  end;
  dialog := TSaveDialog.Create(nil);
  try
    dialog.Title := 'Save LKS read-only detection report';
    dialog.Filter := 'Text files (*.txt)|*.txt';
    dialog.DefaultExt := 'txt';
    dialog.FileName := 'LKS-detection-records.txt';
    dialog.Options := dialog.Options + [ofOverwritePrompt];
    if not dialog.Execute then begin
      Result := 1;
      Exit;
    end;
    outputPath := dialog.FileName;
  finally
    dialog.Free;
  end;

  ReportLines := TStringList.Create;
  SeenRecords := TStringList.Create;
  try
    ReportLines.Add('LKS read-only detection record export v1');
    ReportLines.Add('Loaded file count: ' + IntToStr(FileCount));
    ReportLines.Add('Winners apply only to files loaded in this xEdit session.');
    ReportLines.Add('Contains native reference records and their loaded winners.');
    DumpSpell(spell);
    // The normal Detect Life spell is a separate comparison, not a test cast.
    DumpSpell(RecordByFormID(skyrim, $000211EE, False));
    // Native fire-and-forget Detect Life configurations.
    DumpNative(skyrim, $001019D8);
    DumpNative(skyrim, $001019D9);
    DumpNative(skyrim, $001019DA);
    DumpNative(skyrim, $001019DB);
    DumpNative(skyrim, $0008AFCB);
    DumpNative(skyrim, $0010319E);
    // Shader definitions used by the native family, including loaded overrides.
    DumpNative(skyrim, $00000146);
    DumpNative(skyrim, $000DC209);
    DumpNative(skyrim, $000AAEB3);
    DumpNative(skyrim, $00016439);
    ownPlugin := FindLoadedFile('KhajiitKeenSenses.esp');
    if Assigned(ownPlugin) then begin
      DumpOwnGroup(ownPlugin, 'MGEF');
      DumpOwnGroup(ownPlugin, 'SPEL');
    end else
      ReportLines.Add('KhajiitKeenSenses.esp was not loaded.');
    ReportLines.SaveToFile(outputPath);
    AddMessage('LKS: report saved to ' + outputPath);
    AddMessage('LKS: no game records changed. Exported records: ' + IntToStr(SeenRecords.Count));
  finally
    SeenRecords.Free;
    ReportLines.Free;
  end;
end;

end.
