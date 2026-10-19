param([string]$LoreRimRoot = 'M:\LoreRim')
$ErrorActionPreference = 'Stop'
# Read source files only. Write a new report/ZIP beside this script.
$warnings = New-Object 'System.Collections.Generic.List[string]'
if (-not (Test-Path -LiteralPath $LoreRimRoot -PathType Container)) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = 'Select the LoreRim folder containing mods and profiles'
    if ($dialog.ShowDialog() -ne 'OK') { throw 'No folder selected. No changes made.' }
    $LoreRimRoot = $dialog.SelectedPath
}
function Read-IniValues([string]$Path) {
    $values = @{}
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        foreach ($line in [IO.File]::ReadAllLines($Path)) {
            if ($line -match '^\s*([^;#=\[][^=]*?)\s*=\s*(.*?)\s*$') {
                $values[$matches[1].Trim()] = $matches[2]
            }
        }
    }
    return $values
}
$iniPath = $null
foreach ($relative in @('ModOrganizer.ini', 'ModOrganizer\ModOrganizer.ini', 'MO2\ModOrganizer.ini')) {
    $candidate = Join-Path $LoreRimRoot $relative
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { $iniPath = $candidate; break }
}
$ini = @{}
if ($iniPath) { $ini = Read-IniValues $iniPath } else { $warnings.Add('MO2 INI not found; using conventional folders. Active profile not established.') }
function Resolve-Directory([string]$Value, [string]$Fallback, [string]$Base) {
    if (-not $Value) { return $Fallback }
    $Value = $Value.Trim('"').Replace('%BASE_DIR%', $Base).Replace('/', '\')
    if ($Value -match '^@' -or $Value -match '%[^%]+%') { throw "Unsupported configured directory: $Value" }
    if (-not [IO.Path]::IsPathRooted($Value)) { $Value = Join-Path $Base $Value }
    return $Value
}
$baseDir = Resolve-Directory $ini['base_directory'] $LoreRimRoot $LoreRimRoot
$modsDir = Resolve-Directory $ini['mod_directory'] (Join-Path $baseDir 'mods') $baseDir
$profilesDir = Resolve-Directory $ini['profiles_directory'] (Join-Path $baseDir 'profiles') $baseDir
$overwriteDir = Resolve-Directory $ini['overwrite_directory'] (Join-Path $baseDir 'overwrite') $baseDir
if (-not (Test-Path -LiteralPath $modsDir -PathType Container)) { throw "Mods directory missing: $modsDir" }
if (-not (Test-Path -LiteralPath $profilesDir -PathType Container)) { throw "Profiles directory missing: $profilesDir" }
$selected = $ini['selected_profile']
if ($selected -match '^@ByteArray\((.*)\)$') { $selected = $matches[1] }
$profiles = @()
foreach ($dir in Get-ChildItem -LiteralPath $profilesDir -Directory) {
    $list = Join-Path $dir.FullName 'modlist.txt'
    if (-not (Test-Path -LiteralPath $list -PathType Leaf)) { continue }
    $enabled = @([IO.File]::ReadAllLines($list) | Where-Object { $_.StartsWith('+') } | ForEach-Object { $_.Substring(1) })
    $plugins = Join-Path $dir.FullName 'plugins.txt'
    $relevant = @()
    if (Test-Path -LiteralPath $plugins -PathType Leaf) {
        $relevant = @([IO.File]::ReadAllLines($plugins) | Where-Object { $_ -match '^\*.*(EchoesofTamriel|TESL-LoadingScreens|Loading Screens|Loading Succ)' })
    }
    $archiveSettings = @()
    foreach ($name in @('Skyrim.ini', 'SkyrimCustom.ini')) {
        $p = Join-Path $dir.FullName $name
        if (Test-Path -LiteralPath $p -PathType Leaf) {
            $archiveSettings += @([IO.File]::ReadAllLines($p) | Where-Object { $_ -match '^\s*(bInvalidateOlderFiles|sResourceDataDirsFinal|sResourceArchiveList\d*)\s*=' } | ForEach-Object { "$name : $_" })
        }
    }
    $profiles += [pscustomobject]@{ Name=$dir.Name; EnabledHighestFirst=$enabled; RelevantPlugins=$relevant; ArchiveSettings=$archiveSettings }
}
if ($profiles.Count -eq 0) { throw 'No profile modlists found.' }
$allNames = @{}
foreach ($profile in $profiles) { foreach ($name in $profile.EnabledHighestFirst) { $allNames[$name] = $true } }
$inventory = New-Object 'System.Collections.Generic.List[object]'
$targets = @('textures\EchoesofTamriel\SkyrimWallpaper.dds', 'SKSE\Plugins\SSEDisplayTweaks.ini', 'SKSE\Plugins\SSEDisplayTweaks_custom.ini')
$locations = @()
foreach ($name in $allNames.Keys) { $locations += [pscustomobject]@{ Name=$name; Directory=(Join-Path $modsDir $name) } }
$locations += [pscustomobject]@{ Name='[MO2 overwrite]'; Directory=$overwriteDir }
$locations += [pscustomobject]@{ Name='[physical game Data]'; Directory=(Join-Path $LoreRimRoot 'Stock Game\Data') }
foreach ($location in $locations) {
    if (-not (Test-Path -LiteralPath $location.Directory -PathType Container)) { continue }
    Write-Progress -Activity 'Reading loading screen file providers' -Status $location.Name
    foreach ($relative in $targets) {
        $p = Join-Path $location.Directory $relative
        if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { continue }
        $settings = @()
        if ($relative.EndsWith('.ini')) {
            $settings = @([IO.File]::ReadAllLines($p) | Where-Object { $_ -match '^\s*(\[Miscellaneous\]|LoadScreen(Filter|Allow|Block)\s*=)' })
        }
        $inventory.Add([pscustomobject]@{ Provider=$location.Name; Path=$relative; SHA256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower(); Settings=$settings })
    }
    foreach ($relative in @('meshes\EchoesofTamriel', 'meshes\TESL-LoadingScreens')) {
        $folder = Join-Path $location.Directory $relative
        if (-not (Test-Path -LiteralPath $folder -PathType Container)) { continue }
        foreach ($file in Get-ChildItem -LiteralPath $folder -Filter '*.nif' -File -Recurse) {
            $path = $file.FullName.Substring($location.Directory.Length).TrimStart('\')
            $inventory.Add([pscustomobject]@{ Provider=$location.Name; Path=$path; SHA256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower(); Settings=@() })
        }
    }
}
Write-Progress -Activity 'Reading loading screen file providers' -Completed
$results = @()
foreach ($profile in $profiles) {
    $rank = @{}
    for ($i=0; $i -lt $profile.EnabledHighestFirst.Count; $i++) { $rank[$profile.EnabledHighestFirst[$i]] = $i }
    $rank['[MO2 overwrite]'] = -1
    $rank['[physical game Data]'] = 2147483647
    $visible = @($inventory | Where-Object { $rank.ContainsKey($_.Provider) })
    $groups = @()
    foreach ($group in ($visible | Group-Object -Property Path)) {
        $providers = @($group.Group | Sort-Object { $rank[$_.Provider] })
        $groups += [pscustomobject]@{ Path=$group.Name; ExpectedLooseWinner=$providers[0].Provider; SHA256=$providers[0].SHA256; Providers=$providers }
    }
    $results += [pscustomobject]@{ Profile=$profile.Name; EnabledModsHighestFirst=$profile.EnabledHighestFirst; RelevantPlugins=$profile.RelevantPlugins; ArchiveSettings=$profile.ArchiveSettings; LooseFileProviders=$groups }
}
$report = [pscustomobject]@{
    Version=1; Root=$LoreRimRoot; SelectedProfileAsRecordedInMO2=$selected; Warnings=@($warnings.ToArray());
    ExpectedNewDDS='5fb5beff8d548786806f72626fe7539bf57ec8ada86bfd8de285148c8ae24211';
    ExpectedOldDDS='6e61959b5b09f8ed9d13518656cc3207a628966b858ff30230c046d9afbac918';
    Profiles=$results;
    Limits=@('Loose winners are inferred from standard MO2 modlist order, not observed through the running VFS.', 'BSA contents, per-file hidden state, and actual rendering are not validated.', 'A running MO2 may have unsaved changes; close MO2 normally before collecting.', 'Only conventional Stock Game/Data is checked; custom game paths are not inferred.')
}
$out = Join-Path $PSScriptRoot ('LoadingScreenDiagnostics-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,6))
New-Item -ItemType Directory -Path $out | Out-Null
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $out 'report.json') -Encoding UTF8
Compress-Archive -LiteralPath (Join-Path $out 'report.json') -DestinationPath ($out + '.zip')
Write-Host ('Report saved: ' + $out + '.zip')
Write-Host 'Send this ZIP. No mod files or settings were changed.'
