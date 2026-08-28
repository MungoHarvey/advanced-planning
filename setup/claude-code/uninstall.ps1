# uninstall.ps1 — remove what install.ps1 installed, and nothing else.
#
# Usage:
#   .\uninstall.ps1 -Project [path]   Remove from a project (default: .)
#   .\uninstall.ps1 -Global           Remove from the global Claude Code config
#   .\uninstall.ps1 ... -Yes          Actually delete. Without it, dry run.
#
# The reasoning is the same as uninstall.sh, which this mirrors: the mechanism
# shares .advanced-plans/ with the user's planning record, so uninstalling is a
# removal of a known set of names derived from this checkout, never a directory
# removal. Commands go first and the launcher last, because commands left
# without a launcher is the one broken state this system cannot diagnose --
# the interpreter fails to open the missing ap.py and exits before any guard
# can speak.
#
# One case is specific to Windows and is the reason this file is not a thin
# translation. install.ps1 creates .claude\skills and .claude\schemas as
# JUNCTIONS into the source checkout, so what "remove this directory" means
# depends on whether the reparse point is followed. Every removal here checks
# for one and unlinks it with Directory.Delete($path, $false), which removes
# the link and cannot touch what it points at.
#
# The widely-repeated claim that `Remove-Item -Recurse` follows a junction and
# deletes the target's contents did NOT reproduce here: tested on PowerShell
# 7.6.5 and on Windows PowerShell 5.1.26100, a junction with three files in its
# target was removed and all three survived. So this guard is not closing a
# demonstrated hole on these versions. It is kept anyway, because unlinking is
# what is actually meant -- the target is the user's checkout and was never
# part of the install -- and because a delete whose blast radius depends on the
# host's patch level is not one to leave to inference.

[CmdletBinding()]
param(
    [string]$Project,
    [switch]$Global,
    [switch]$Yes
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# USERPROFILE before HOME, and $env:HOME before PowerShell's automatic $HOME --
# they are different variables and the automatic one is derived from
# HOMEDRIVE/HOMEPATH. Kept identical to install.ps1's Get-ApGlobalHome and
# pinned by platforms/python/tests/test_home_resolution_agreement.py. Removing
# from a different home than the install wrote to would remove nothing and
# report success.
function Get-ApGlobalHome {
    if ($env:USERPROFILE) { return $env:USERPROFILE }
    if ($env:HOME) { return $env:HOME }
    if ($HOME) { return $HOME }
    throw "Neither USERPROFILE nor HOME is set; refusing to guess the global home."
}

$script:Removed = 0
$script:Kept = 0

function Test-IsReparsePoint([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $item = Get-Item -LiteralPath $Path -Force
    return [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
}

function Remove-ApPath([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    Write-Host "  - $Label"
    if (-not $Yes) { return }

    if (Test-IsReparsePoint $Path) {
        # Unlink only. Never recurse through a junction: the target is the
        # source checkout.
        [System.IO.Directory]::Delete($Path, $false)
    }
    elseif ((Get-Item -LiteralPath $Path -Force) -is [System.IO.DirectoryInfo]) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
    else {
        Remove-Item -LiteralPath $Path -Force
    }
    $script:Removed++
}

# Remove <Dest>\<name> for every <name> this checkout provides, and nothing
# else. A file the checkout does not provide was not installed from here.
function Remove-ApInstalledFrom([string]$Src, [string]$Dest, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Dest)) { return }
    # The destination may itself be a junction INTO the source checkout, and
    # this has to be checked before anything walks it. install.ps1 replaces
    # .claude\commands, skills and schemas wholesale with junctions in
    # self-install mode, and -Symlink does it for skills alone. Get-ChildItem
    # and Test-Path both traverse a junction, so without this the loop below
    # would resolve each name THROUGH it and Remove-Item the source file --
    # deleting the user's checkout rather than their install. Note the
    # individual files inside are not themselves reparse points, so
    # Remove-ApPath's own guard would not save it.
    if (Test-IsReparsePoint $Dest) {
        Remove-ApPath $Dest "$Label (junction -- unlinking, not following)"
        return
    }
    if (-not (Test-Path -LiteralPath $Src)) { return }
    foreach ($item in Get-ChildItem -LiteralPath $Src -Force) {
        $target = Join-Path $Dest $item.Name
        if (Test-Path -LiteralPath $target) {
            Remove-ApPath $target "$Label/$($item.Name)"
        }
    }
}

function Remove-ApDirIfEmpty([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    if (Test-IsReparsePoint $Path) { return }
    if (-not $Yes) {
        Write-Host "  [dry-run] remove $Path, if the removals above leave it empty"
        return
    }
    if (-not (Get-ChildItem -LiteralPath $Path -Force)) {
        Remove-Item -LiteralPath $Path -Force
    }
    else {
        Write-Host "  keeping $Path (not empty -- contains files this installer did not write)"
        $script:Kept++
    }
}

function Invoke-ApUninstall([string]$ClaudeDir, [string]$ApDir) {
    Write-Host ""
    Write-Host "Removing Advanced Planning from:"
    Write-Host "  adapter:  $ClaudeDir"
    Write-Host "  runtime:  $ApDir"
    if (-not $Yes) {
        Write-Host ""
        Write-Host "  DRY RUN -- nothing will be deleted. Re-run with -Yes to act."
    }
    Write-Host ""

    Write-Host "Slash commands:"
    Remove-ApInstalledFrom (Join-Path $RepoRoot "platforms\claude-code\commands") `
        (Join-Path $ClaudeDir "commands") "commands"
    Remove-ApDirIfEmpty (Join-Path $ClaudeDir "commands")

    Write-Host "Agent definitions:"
    Remove-ApInstalledFrom (Join-Path $RepoRoot "core\agents") `
        (Join-Path $ClaudeDir "agents") "agents"
    Remove-ApInstalledFrom (Join-Path $RepoRoot "platforms\claude-code\agents") `
        (Join-Path $ClaudeDir "agents") "agents"
    Remove-ApDirIfEmpty (Join-Path $ClaudeDir "agents")

    foreach ($pair in @(@("skills", "core\skills"), @("schemas", "core\schemas"))) {
        $name = $pair[0]
        $dest = Join-Path $ClaudeDir $name
        Write-Host "$($name.Substring(0,1).ToUpper() + $name.Substring(1)):"
        Remove-ApInstalledFrom (Join-Path $RepoRoot $pair[1]) $dest $name
        Remove-ApDirIfEmpty $dest
    }

    # Reported, never removed. install.ps1 writes settings.json only when none
    # exists and saves settings.planning.json otherwise, so this file may be
    # entirely the user's, may be ours, or may be theirs with our hooks merged
    # in by hand. Nothing records which, and deleting a Claude Code settings
    # file on a guess is not a recoverable mistake.
    $settings = Join-Path $ClaudeDir "settings.json"
    if (Test-Path -LiteralPath $settings) {
        Write-Host "Settings:"
        Write-Host "  keeping $settings -- remove the planning hooks by hand if you want them gone."
        $script:Kept++
    }
    $planningSettings = Join-Path $ClaudeDir "settings.planning.json"
    if (Test-Path -LiteralPath $planningSettings) {
        Remove-ApPath $planningSettings "settings.planning.json"
    }

    # Last, for the reason at the top of this file.
    Write-Host "Shared Python runtime:"
    Remove-ApPath (Join-Path $ApDir "bin\ap.py") "bin/ap.py"
    Remove-ApDirIfEmpty (Join-Path $ApDir "bin")
    Remove-ApPath (Join-Path $ApDir "runtime.json") "runtime.json"

    Write-Host ""
    Write-Host "Left in place -- this is your planning record, not part of the install:"
    foreach ($keep in @("phases", "specs", "state", "logs", "PLANNING.md",
                        "README.md", "gate-verdicts", "evidence")) {
        $p = Join-Path $ApDir $keep
        if (Test-Path -LiteralPath $p) { Write-Host "  $p" }
    }
    Write-Host ""
    if ($Yes) {
        Write-Host "Done. $($script:Removed) path(s) removed."
    }
    else {
        Write-Host "Dry run complete. Re-run with -Yes to act."
    }
    Write-Host ""
}

if ($Global) {
    $home_ = Get-ApGlobalHome
    Invoke-ApUninstall (Join-Path $home_ ".claude") (Join-Path $home_ ".advanced-plans")
}
elseif ($PSBoundParameters.ContainsKey("Project") -or $Project) {
    $target = if ($Project) { $Project } else { "." }
    if (-not (Test-Path -LiteralPath $target)) {
        Write-Error "Directory not found: $target"
        exit 1
    }
    Invoke-ApUninstall (Join-Path $target ".claude") (Join-Path $target ".advanced-plans")
}
else {
    Write-Host "Specify -Project [path] or -Global."
    Write-Host "Dry run is the default; add -Yes to actually delete."
    exit 1
}
