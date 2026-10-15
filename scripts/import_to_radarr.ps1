<#
.SYNOPSIS
    Imports Custom Formats and creates the 1080p IMAX HDR Quality Profile in Radarr via REST API.

.EXAMPLE
    .\import_to_radarr.ps1 -ApiKey "YOUR_API_KEY"
    .\import_to_radarr.ps1 -RadarrUrl "http://192.168.1.50:7878" -ApiKey "YOUR_API_KEY"
#>

[CmdletBinding()]
param(
    [string]$RadarrUrl = "http://127.0.0.1:7878",
    [Parameter(Mandatory=$true)][string]$ApiKey,
    [string]$CustomFormatsPath
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $CustomFormatsPath) {
    $CustomFormatsPath = Join-Path (Split-Path -Parent $scriptDir) "custom-formats"
}

$headers = @{
    "X-Api-Key" = $ApiKey
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}

Write-Host "Connecting to Radarr at $RadarrUrl..." -ForegroundColor Cyan
try {
    $status = Invoke-RestMethod -Uri "$RadarrUrl/api/v3/system/status" -Headers $headers -Method Get
    Write-Host "[+] Connected to Radarr v$($status.version)" -ForegroundColor Green
} catch {
    Write-Error "[-] Failed to connect to Radarr. Please check URL and API Key: $_"
}

# Fetch existing custom formats
$cfUrl = "$RadarrUrl/api/v3/customformat"
$existingCfs = Invoke-RestMethod -Uri $cfUrl -Headers $headers -Method Get
$cfMap = @{}
foreach ($cf in $existingCfs) {
    $cfMap[$cf.name] = $cf
}

$scores = @{
    "IMAX" = 300
    "English + Hindi Dual Audio" = 300
    "Blu-ray Remux" = 250
    "HDR" = 200
    "HDR10+" = 100
    "WEB-DL" = 100
    "HEVC / H.265" = 40
    "Low Quality Release" = -10000
    "Dolby Vision" = 150
    "Dolby Atmos" = 100
    "DTS-HD MA" = 80
    "Proper / Repack" = 50
}

$allowedQualities = @(
    "Remux-1080p",
    "Bluray-1080p",
    "WEBDL-1080p",
    "WEBRip-1080p",
    "Bluray-720p",
    "WEBDL-720p",
    "WEBRip-720p"
)

$syncedCfIds = @{}

Write-Host "`nImporting Custom Formats from $CustomFormatsPath..." -ForegroundColor Cyan
Get-ChildItem -Path $CustomFormatsPath -Filter "*.json" | ForEach-Object {
    if ($_.Name -eq "1080p-imax-hdr-complete.json") { return }

    $jsonContent = Get-Content $_.FullName -Raw | ConvertFrom-Json
    $name = $jsonContent.name
    if (-not $name) { return }

    $rawBody = Get-Content $_.FullName -Raw

    if ($cfMap.ContainsKey($name)) {
        $id = $cfMap[$name].id
        $jsonContent | Add-Member -MemberType NoteProperty -Name "id" -Value $id -Force
        $updatedJson = $jsonContent | ConvertTo-Json -Depth 10
        Invoke-RestMethod -Uri "$cfUrl/$id" -Headers $headers -Method Put -Body $updatedJson | Out-Null
        Write-Host "  [~] Updated: $name (ID: $id)" -ForegroundColor Yellow
        $syncedCfIds[$name] = $id
    } else {
        $created = Invoke-RestMethod -Uri $cfUrl -Headers $headers -Method Post -Body $rawBody
        Write-Host "  [+] Created: $name (ID: $($created.id))" -ForegroundColor Green
        $syncedCfIds[$name] = $created.id
    }
}

Write-Host "`nConfiguring Quality Profile '1080p IMAX HDR (English + Hindi)'..." -ForegroundColor Cyan
$profileUrl = "$RadarrUrl/api/v3/qualityprofile"
$profiles = Invoke-RestMethod -Uri $profileUrl -Headers $headers -Method Get
$targetName = "1080p IMAX HDR (English + Hindi)"
$target = $profiles | Where-Object { $_.name -eq $targetName }

if (-not $target) {
    $schema = Invoke-RestMethod -Uri "$RadarrUrl/api/v3/qualityprofile/schema" -Headers $headers -Method Get
    $target = $schema
}

$target.name = $targetName
$target.upgradeAllowed = $true

# Update allowed items and cutoff
$cutoffId = $null
foreach ($item in $target.items) {
    $qName = $item.quality.name
    if ($allowedQualities -contains $qName) {
        $item.allowed = $true
        if ($qName -eq "Bluray-1080p") {
            $cutoffId = $item.quality.id
        }
    } else {
        $item.allowed = $false
    }
}

if ($cutoffId) {
    $target.cutoff = $cutoffId
}

# Attach CF formatItems
$formatItems = @()
foreach ($entry in $syncedCfIds.GetEnumerator()) {
    $score = if ($scores.ContainsKey($entry.Key)) { $scores[$entry.Key] } else { 0 }
    $formatItems += @{
        format = $entry.Value
        name = $entry.Key
        score = $score
    }
}
$target.formatItems = $formatItems
$target.minFormatScore = 0
$target.cutoffFormatScore = 0

$payload = $target | ConvertTo-Json -Depth 10
if ($target.id) {
    Invoke-RestMethod -Uri "$profileUrl/$($target.id)" -Headers $headers -Method Put -Body $payload | Out-Null
    Write-Host "[+] Updated Profile '$targetName' (ID: $($target.id))" -ForegroundColor Green
} else {
    $res = Invoke-RestMethod -Uri $profileUrl -Headers $headers -Method Post -Body $payload
    Write-Host "[+] Created Profile '$targetName' (ID: $($res.id))" -ForegroundColor Green
}

Write-Host "`n[✓] Finished successfully!" -ForegroundColor Green
