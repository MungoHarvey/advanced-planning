# uninstall.ps1 — remove what install.ps1 installed for Codex, and nothing else.
#
# Usage:
#   .\uninstall.ps1 -Project [path]   Remove from a project (default: .)
#   .\uninstall.ps1 -Global           Remove from the global config
#   .\uninstall.ps1 ... -Yes          Actually delete. Without it, dry run.
#
# The reasoning is the same as uninstall.sh, which this mirrors: the mechanism
# shares .advanced-plans/ with the user's planning record, so uninstalling is a
# removal of a known set of names derived from this checkout, never a directory
# removal. Skills go first and the launcher last, because commands left
# without a launcher is the one broken state this system cannot diagnose —
# the interpreter fails to open the missing ap.py and exits before any guard
# can speak.
#
# The shared skill at .agents\skills\advanced-planning\ may be registered by
# both Codex and OpenCode. This script reads .advanced-plans\skill-ownership.json
# and only removes what Codex owns. Shared entries have this adapter's
# registration dropped but the files left.

[CmdletBinding()]
param(
    [string]$Project,
    [switch]$Global,
    [switch]$Yes
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# USERPROFILE before HOME, and $env:HOME before PowerShell's automatic $HOME —
# they are different variables and the automatic one is derived from
# HOMEDRIVE/HOMEPATH. Kept identical to install.ps1's Get-ApGlobalHome.
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

# Remove <Dest>\<name> for every <name> this checkout provides.
function Remove-ApInstalledFrom([string]$Src, [string]$Dest, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Dest)) { return }
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

# Check skill ownership and remove appropriately
# If skill has multiple owners (shared), leave files and only update registration
# If skill has only codex as owner, remove the files
function Remove-ApSkillWithOwnership([string]$SkillName, [string]$SkillsDir, [string]$OwnershipFile) {
    $skillPath = Join-Path $SkillsDir $SkillName

    if (-not (Test-Path -LiteralPath $skillPath)) { return }

    # Check ownership if metadata exists
    $isShared = $false
    $isOwner = $true
    if (Test-Path -LiteralPath $OwnershipFile) {
        try {
            $ownership = Get-Content $OwnershipFile -Raw | ConvertFrom-Json
            if ($ownership.skills -and $ownership.skills.$SkillName) {
                $owners = $ownership.skills.$SkillName
                if ($owners -is [array]) {
                    $isOwner = $owners -contains "codex"
                    # Shared if more than one owner
                    $isShared = $owners.Count -gt 1
                } else {
                    $isOwner = $owners -eq "codex"
                    $isShared = $false
                }
            }
        } catch {
            # JSON parse error or other issue - assume sole ownership
            $isOwner = $true
            $isShared = $false
        }
    }

    if (-not $isOwner) {
        Write-Host "  - $SkillName (not owned by codex - leaving in place)"
        $script:Kept++
        return
    }

    if ($isShared) {
        Write-Host "  - $SkillName (shared with another adapter - leaving files, will update registration)"
        $script:Kept++
        return
    }

    Remove-ApPath $skillPath "skills\$SkillName"
}

# Remove AGENTS.md fence for codex
function Remove-ApAgentsFence([string]$AgentsFile) {
    if (-not (Test-Path -LiteralPath $AgentsFile)) { return }

    $fenceStart = "<!-- advanced-planning:codex:start -->"
    $fenceEnd = "<!-- advanced-planning:codex:end -->"

    $content = [System.IO.File]::ReadAllText($AgentsFile)

    if ($content -notmatch [regex]::Escape($fenceStart)) { return }

    if ($Yes) {
        # Remove the fence block
        $pattern = [regex]::Escape($fenceStart) + ".*?" + [regex]::Escape($fenceEnd)
        $newContent = [regex]::Replace($content, $pattern, "", [System.Text.RegularExpressions.RegexOptions]::Singleline)
        # Clean up multiple consecutive blank lines
        $newContent = [regex]::Replace($newContent, "\n{3,}", "`n`n")
        [System.IO.File]::WriteAllText($AgentsFile, $newContent,
            [System.Text.UTF8Encoding]::new($false))
        Write-Host "  - AGENTS.md fence block removed"
        $script:Removed++
    } else {
        Write-Host "  [dry-run] remove AGENTS.md fence block"
    }
}

function Invoke-ApUninstall([string]$AgentsDir, [string]$ApDir) {
    $SkillsDir = Join-Path $AgentsDir "skills"
    $OwnershipFile = Join-Path $ApDir "skill-ownership.json"

    Write-Host ""
    Write-Host "Removing Codex Advanced Planning adapter from:"
    Write-Host "  skills:   $SkillsDir"
    Write-Host "  runtime:  $ApDir"
    if (-not $Yes) {
        Write-Host ""
        Write-Host "  DRY RUN -- nothing will be deleted. Re-run with -Yes to act."
    }
    Write-Host ""

    Write-Host "Skills (with ownership check):"
    # Remove shared routing skill
    Remove-ApSkillWithOwnership "advanced-planning" $SkillsDir $OwnershipFile
    # Remove approved core skills
    $approvedSkills = @("phase-plan-creator", "ralph-loop-planner", "plan-todos", "plan-skill-identification", "plan-subagent-identification", "progress-report", "schema-design")
    foreach ($skill in $approvedSkills) {
        Remove-ApSkillWithOwnership $skill $SkillsDir $OwnershipFile
    }
    Remove-ApDirIfEmpty $SkillsDir
    Remove-ApDirIfEmpty $AgentsDir

    # Remove AGENTS.md fence
    Write-Host "AGENTS.md:"
    $agentsFile = Join-Path $AgentsDir "..\AGENTS.md"
    $agentsFile = Resolve-Path $agentsFile -ErrorAction SilentlyContinue
    if ($agentsFile) {
        Remove-ApAgentsFence $agentsFile.Path
    }

    # Shared Python runtime
    Write-Host "Shared Python runtime:"
    Remove-ApPath (Join-Path $ApDir "bin\ap.py") "bin/ap.py"
    Remove-ApDirIfEmpty (Join-Path $ApDir "bin")
    Remove-ApPath (Join-Path $ApDir "runtime.json") "runtime.json"

    # Remove skill-ownership.json
    if (Test-Path -LiteralPath $OwnershipFile) {
        Remove-ApPath $OwnershipFile "skill-ownership.json"
    }

    Write-Host ""
    Write-Host "Left in place -- this is your planning record, not part of the install:"
    foreach ($keep in @("phases", "specs", "state", "logs", "PLANNING.md", "README.md", "gate-verdicts", "evidence")) {
        $p = Join-Path $ApDir $keep
        if (Test-Path -LiteralPath $p) { Write-Host "  $p" }
    }
    Write-Host ""
    if ($Yes) {
        Write-Host "Done. $($script:Removed) path(s) removed, $($script:Kept) kept."
    }
    else {
        Write-Host "Dry run complete. Re-run with -Yes to act."
    }
    Write-Host ""
}

if ($Global) {
    $home_ = Get-ApGlobalHome
    Invoke-ApUninstall (Join-Path $home_ ".agents") (Join-Path $home_ ".advanced-plans")
}
elseif ($PSBoundParameters.ContainsKey("Project") -or $Project) {
    $target = if ($Project) { $Project } else { "." }
    if (-not (Test-Path -LiteralPath $target)) {
        Write-Error "Directory not found: $target"
        exit 1
    }
    Invoke-ApUninstall (Join-Path $target ".agents") (Join-Path $target ".advanced-plans")
}
else {
    Write-Host "Specify -Project [path] or -Global."
    Write-Host "Dry run is the default; add -Yes to actually delete."
    exit 1
}
