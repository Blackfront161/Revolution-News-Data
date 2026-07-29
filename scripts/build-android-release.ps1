[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$AndroidProject,

    [string]$Commit = "origin/main",
    [int]$VersionCode = 0,
    [string]$VersionName = "",

    [Parameter(Mandatory = $true)]
    [string]$Keystore,

    [string]$KeyAlias = "WRN_KEY",
    [string]$OutputDirectory = "",
    [switch]$SkipFetch
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Resolve-RequiredPath([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Label wurde nicht gefunden: $Path"
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

function Get-RelativeWebFiles([string]$Root) {
    $extensions = @(
        ".html", ".js", ".css", ".json", ".webp", ".png", ".jpg",
        ".jpeg", ".svg", ".ttf", ".woff", ".woff2", ".txt"
    )
    Get-ChildItem -LiteralPath $Root -File | Where-Object {
        $extensions -contains $_.Extension.ToLowerInvariant() -and
        $_.Name -notmatch "^(aggregate-errors|workflow-audit|INTEGRATION-REPORT|feature-audit)\.json$"
    } | Sort-Object Name
}

function Get-HashManifest([string]$Root) {
    $manifest = [ordered]@{}
    Get-RelativeWebFiles $Root | ForEach-Object {
        $manifest[$_.Name] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    }
    return $manifest
}

function Compare-HashManifest($Expected, $Actual) {
    $names = @($Expected.Keys + $Actual.Keys | Sort-Object -Unique)
    $differences = foreach ($name in $names) {
        $expectedHash = $Expected[$name]
        $actualHash = $Actual[$name]
        if ($expectedHash -ne $actualHash) {
            [pscustomobject]@{
                file = $name
                expected = $expectedHash
                actual = $actualHash
            }
        }
    }
    return @($differences)
}

function Get-WebVersion([string]$SourceRoot) {
    $configPath = Join-Path $SourceRoot "config.js"
    if (-not (Test-Path -LiteralPath $configPath)) { return "" }
    $content = Get-Content -LiteralPath $configPath -Raw
    $match = [regex]::Match(
        $content,
        "window\.WRN_CONFIG\s*=\s*Object\.freeze\(\{[\s\S]*?\bversion:\s*['""]([^'""]+)"
    )
    return $(if ($match.Success) { $match.Groups[1].Value } else { "" })
}

function Set-AndroidVersion(
    [string]$BuildGradle,
    [int]$RequestedCode,
    [string]$RequestedName
) {
    $content = Get-Content -LiteralPath $BuildGradle -Raw
    $codeMatch = [regex]::Match($content, "versionCode\s+(\d+)")
    $nameMatch = [regex]::Match($content, 'versionName\s+"([^"]+)"')
    if (-not $codeMatch.Success -or -not $nameMatch.Success) {
        throw "versionCode/versionName konnten in $BuildGradle nicht gelesen werden."
    }
    $oldCode = [int]$codeMatch.Groups[1].Value
    $nextCode = if ($RequestedCode -gt 0) { $RequestedCode } else { $oldCode + 1 }
    if ($nextCode -le $oldCode) {
        throw "Der neue Versionscode ($nextCode) muss größer als der vorhandene Code ($oldCode) sein."
    }
    $nextName = if ($RequestedName) { $RequestedName } else { $nameMatch.Groups[1].Value }
    $content = [regex]::Replace($content, "versionCode\s+\d+", "versionCode $nextCode", 1)
    $content = [regex]::Replace($content, 'versionName\s+"[^"]+"', "versionName `"$nextName`"", 1)
    [System.IO.File]::WriteAllText($BuildGradle, $content, [System.Text.UTF8Encoding]::new($false))
    return [pscustomobject]@{ code = $nextCode; name = $nextName; previousCode = $oldCode }
}

function Find-JavaTool([string]$Name) {
    $candidates = @()
    if ($env:JAVA_HOME) {
        $candidates += (Join-Path $env:JAVA_HOME "bin\$Name.exe")
    }
    $candidates += "C:\Program Files\Android\Android Studio\jbr\bin\$Name.exe"
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    throw "$Name wurde nicht gefunden. Android Studio oder ein JDK wird benötigt."
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) { throw "Dieses Skript muss innerhalb des WRN-Git-Repositories laufen." }
$androidRoot = Resolve-RequiredPath $AndroidProject "Android-Projekt"
$keystorePath = Resolve-RequiredPath $Keystore "Keystore"
$capacitorConfig = Resolve-RequiredPath (Join-Path $androidRoot "capacitor.config.json") "Capacitor-Konfiguration"
$androidDirectory = Resolve-RequiredPath (Join-Path $androidRoot "android") "Android-Verzeichnis"
$buildGradle = Resolve-RequiredPath (Join-Path $androidDirectory "app\build.gradle") "App build.gradle"

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $repoRoot "outputs"
}
[System.IO.Directory]::CreateDirectory($OutputDirectory) | Out-Null
$outputRoot = (Resolve-Path -LiteralPath $OutputDirectory).Path

$temporaryRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("wrn-release-" + [guid]::NewGuid().ToString("N"))
$sourceRoot = Join-Path $temporaryRoot "source"
$unpackRoot = Join-Path $temporaryRoot "aab"
[System.IO.Directory]::CreateDirectory($temporaryRoot) | Out-Null

$report = [ordered]@{
    schemaVersion = 1
    startedAt = (Get-Date).ToUniversalTime().ToString("o")
    requestedCommit = $Commit
    resolvedCommit = ""
    versionCode = 0
    versionName = ""
    capacitorSync = "pending"
    sourceFileCount = 0
    preBuildDifferences = @()
    packagedDifferences = @()
    signatureVerified = $false
    aab = ""
    aabSha256 = ""
    error = ""
}

try {
    if (-not $SkipFetch) {
        git fetch origin main | Out-Host
    }
    $resolvedCommit = (git rev-parse "$Commit^{commit}").Trim()
    if (-not $resolvedCommit) { throw "Git-Commit konnte nicht aufgelöst werden: $Commit" }
    $report.resolvedCommit = $resolvedCommit

    git worktree add --detach $sourceRoot $resolvedCommit | Out-Host
    $sourceManifest = Get-HashManifest $sourceRoot
    $report.sourceFileCount = $sourceManifest.Count

    $capacitor = Get-Content -LiteralPath $capacitorConfig -Raw | ConvertFrom-Json
    $webDirName = [string]$capacitor.webDir
    if (-not $webDirName) { $webDirName = "www" }
    $webRoot = Join-Path $androidRoot $webDirName
    $resolvedAndroidPrefix = [System.IO.Path]::GetFullPath($androidRoot).TrimEnd("\") + "\"
    $resolvedWebRoot = [System.IO.Path]::GetFullPath($webRoot)
    if (-not $resolvedWebRoot.StartsWith($resolvedAndroidPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsicheres webDir außerhalb des Android-Projekts: $resolvedWebRoot"
    }
    [System.IO.Directory]::CreateDirectory($webRoot) | Out-Null
    Get-ChildItem -LiteralPath $webRoot -File | Remove-Item -Force
    Get-RelativeWebFiles $sourceRoot | Copy-Item -Destination $webRoot -Force

    $copiedManifest = Get-HashManifest $webRoot
    $preBuildDifferences = @(Compare-HashManifest $sourceManifest $copiedManifest)
    $report.preBuildDifferences = $preBuildDifferences
    if ($preBuildDifferences.Count) {
        throw "Webdateien unterscheiden sich bereits vor Capacitor Sync."
    }

    $webVersion = Get-WebVersion $sourceRoot
    $effectiveVersionName = if ($VersionName) { $VersionName } else { $webVersion }
    $version = Set-AndroidVersion $buildGradle $VersionCode $effectiveVersionName
    if ($webVersion -and $version.name -ne $webVersion) {
        throw "Android-Version $($version.name) stimmt nicht mit der Webversion $webVersion überein."
    }
    $report.versionCode = $version.code
    $report.versionName = $version.name

    Push-Location $androidRoot
    try {
        if (Test-Path -LiteralPath (Join-Path $androidRoot "node_modules\@capacitor\cli")) {
            & npm.cmd run sync:android
            if ($LASTEXITCODE -ne 0) { throw "Capacitor Sync ist fehlgeschlagen." }
            $report.capacitorSync = "npm run sync:android"
        } else {
            throw "Capacitor CLI fehlt. Führe im Android-Projekt zuerst npm ci aus."
        }
    } finally {
        Pop-Location
    }

    $gradle = Join-Path $androidDirectory "gradlew.bat"
    if (-not (Test-Path -LiteralPath $gradle)) {
        throw "Gradle Wrapper wurde nicht gefunden: $gradle"
    }
    if (-not $env:JAVA_HOME) {
        $java = Find-JavaTool "java"
        $env:JAVA_HOME = Split-Path -Parent (Split-Path -Parent $java)
    }
    Push-Location $androidDirectory
    try {
        & $gradle bundleRelease --no-daemon
        if ($LASTEXITCODE -ne 0) { throw "Gradle bundleRelease ist fehlgeschlagen." }
    } finally {
        Pop-Location
    }

    $unsignedAab = Resolve-RequiredPath (Join-Path $androidDirectory "app\build\outputs\bundle\release\app-release.aab") "Release AAB"
    $finalName = "WorldRevolutionNews-$($version.name)-code$($version.code).aab"
    $finalAab = Join-Path $outputRoot $finalName
    $jarsigner = Find-JavaTool "jarsigner"
    $signArguments = @("-keystore", $keystorePath, "-signedjar", $finalAab)
    if ($env:WRN_KEYSTORE_PASSWORD) {
        $signArguments += @("-storepass:env", "WRN_KEYSTORE_PASSWORD")
    }
    if ($env:WRN_KEY_PASSWORD) {
        $signArguments += @("-keypass:env", "WRN_KEY_PASSWORD")
    }
    $signArguments += @($unsignedAab, $KeyAlias)
    & $jarsigner @signArguments
    if ($LASTEXITCODE -ne 0) { throw "AAB-Signierung ist fehlgeschlagen." }
    # Android upload keys are normally self-signed. Verify the archive's
    # cryptographic signature without requiring a public PKIX certificate chain.
    & $jarsigner -verify -verbose -certs $finalAab | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "AAB-Signaturprüfung ist fehlgeschlagen." }
    $report.signatureVerified = $true

    [System.IO.Directory]::CreateDirectory($unpackRoot) | Out-Null
    $zipCopy = Join-Path $temporaryRoot "release.zip"
    Copy-Item -LiteralPath $finalAab -Destination $zipCopy
    Expand-Archive -LiteralPath $zipCopy -DestinationPath $unpackRoot -Force
    $packagedWeb = Join-Path $unpackRoot "base\assets\public"
    $packagedManifest = Get-HashManifest $packagedWeb
    $packagedDifferences = @(Compare-HashManifest $sourceManifest $packagedManifest)
    $report.packagedDifferences = $packagedDifferences
    if ($packagedDifferences.Count) {
        throw "Die AAB enthält nicht denselben Webstand wie Git-Commit $resolvedCommit."
    }

    $report.aab = $finalAab
    $report.aabSha256 = (Get-FileHash -LiteralPath $finalAab -Algorithm SHA256).Hash
    $report.completedAt = (Get-Date).ToUniversalTime().ToString("o")
    $report.status = "passed"
} catch {
    $report.completedAt = (Get-Date).ToUniversalTime().ToString("o")
    $report.status = "failed"
    $report.error = $_.Exception.Message
    throw
} finally {
    $reportPath = Join-Path $outputRoot ("release-report-code" + $report.versionCode + ".json")
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    $markdownPath = Join-Path $outputRoot ("release-report-code" + $report.versionCode + ".md")
    @(
        "# World Revolution News – Android-Prüfbericht",
        "",
        "- Status: **$($report.status)**",
        "- Git-Commit: ``$($report.resolvedCommit)``",
        "- Version: **$($report.versionName)** (Code **$($report.versionCode)**)",
        "- Capacitor: $($report.capacitorSync)",
        "- Webdateien: $($report.sourceFileCount)",
        "- Abweichungen vor dem Build: $(@($report.preBuildDifferences).Count)",
        "- Abweichungen in der AAB: $(@($report.packagedDifferences).Count)",
        "- Signatur geprüft: $($report.signatureVerified)",
        "- AAB: ``$($report.aab)``",
        "- SHA-256: ``$($report.aabSha256)``",
        "",
        $(if ($report.error) { "Fehler: $($report.error)" } else { "Der eingebettete Webstand stimmt bytegenau mit dem gewählten Git-Commit überein." })
    ) | Set-Content -LiteralPath $markdownPath -Encoding UTF8
    if (Test-Path -LiteralPath $sourceRoot) {
        git worktree remove --force $sourceRoot 2>$null
    }
    if (Test-Path -LiteralPath $temporaryRoot) {
        Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
    }
}

Write-Host ""
Write-Host "Release erfolgreich: $($report.aab)" -ForegroundColor Green
Write-Host "Commit: $($report.resolvedCommit)"
Write-Host "Version: $($report.versionName) (Code $($report.versionCode))"
Write-Host "SHA-256: $($report.aabSha256)"
