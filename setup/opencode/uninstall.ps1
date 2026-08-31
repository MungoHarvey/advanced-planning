# uninstall.ps1 — remove what install.ps1 installed for OpenCode, and nothing else.
#
# Usage:
#   .\uninstall.ps1 -Project [path]   Remove from a project (default: .)
#   .\uninstall.ps1 -Global           Remove from the global config
#   .\uninstall.ps1 ... -Yes          Actually delete. Without it, dry run.
#   .\uninstall.ps1 ... -ForceNoRegistry  Proceed without registry (DANGEROUS)
#
# -ForceNoRegistry: bypass the ownership registry check when the registry is
# missing or malformed. This will remove all skills and shared files including
# bin\ap.py and runtime.json, which may break other adapters. Only use when you
# are certain no other adapter shares this install.
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
# and only removes what OpenCode owns. Shared entries have this adapter's
# registration dropped but the files left. The registry is updated, not deleted.

[CmdletBinding()]
param(
    [string]$Project,
    [switch]$Global,
    [switch]$Yes,
    [switch]$ForceNoRegistry
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
# Set only by the ownership KEEP decision below.  Kept alone will not do: it is
# also incremented by Remove-ApDirIfEmpty for a directory that merely has files
# in it, which says nothing about who owns the runtime.
$script:SharedOwners = $false

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

# Remove AGENTS.md fence for opencode
function Remove-ApAgentsFence([string]$AgentsFile) {
    if (-not (Test-Path -LiteralPath $AgentsFile)) { return }

    $fenceStart = "<!-- advanced-planning:opencode:start -->"
    $fenceEnd = "<!-- advanced-planning:opencode:end -->"

    $content = [System.IO.File]::ReadAllText($AgentsFile)

    if ($content -notmatch [regex]::Escape($fenceStart)) { return }

    if ($Yes) {
        $pattern = [regex]::Escape($fenceStart) + ".*?" + [regex]::Escape($fenceEnd)
        $newContent = [regex]::Replace($content, $pattern, "", [System.Text.RegularExpressions.RegexOptions]::Singleline)
        $newContent = [regex]::Replace($newContent, "\n{3,}", "`n`n")
        [System.IO.File]::WriteAllText($AgentsFile, $newContent,
            [System.Text.UTF8Encoding]::new($false))
        Write-Host "  - AGENTS.md fence block removed"
        $script:Removed++
    } else {
        Write-Host "  [dry-run] remove AGENTS.md fence block"
    }
}

# Process ownership and perform removals
function Invoke-ApOwnershipRemoval([string]$SkillsDir, [string]$OwnershipFile) {
    $approvedSkills = @("advanced-planning", "phase-plan-creator", "ralph-loop-planner", "plan-todos", "plan-skill-identification", "plan-subagent-identification", "progress-report", "schema-design")

    # Read ownership file - fail closed on missing or malformed registry
    $data = @{schema_version = 1; skills = @{}}
    $fileExists = Test-Path -LiteralPath $OwnershipFile
    
    if (-not $fileExists) {
        if (-not $ForceNoRegistry) {
            Write-Error "uninstall.ps1: registry not found: $OwnershipFile"
            Write-Error "uninstall.ps1: cannot establish ownership without the registry."
            Write-Error "uninstall.ps1: this may mean the registry was never created, or it was deleted."
            Write-Error "uninstall.ps1: to proceed anyway (DANGEROUS: may delete shared files including bin\ap.py and runtime.json), re-run with -ForceNoRegistry."
            exit 1
        }
        # ForceNoRegistry=True: proceed with empty registry
        Write-Warning "uninstall.ps1: proceeding without registry. May remove files owned by other adapters."
    } else {
        try {
            $existingContent = [System.IO.File]::ReadAllText($OwnershipFile)
            $data = $existingContent | ConvertFrom-Json
            if (-not $data.skills) {
                $data | Add-Member -NotePropertyName "skills" -NotePropertyValue @{}
            }
        } catch {
            if (-not $ForceNoRegistry) {
                Write-Error "uninstall.ps1: $OwnershipFile is malformed JSON ($_)"
                Write-Error "uninstall.ps1: fix: repair the JSON so it parses, or re-run the adapter installer to regenerate the registry."
                Write-Error "uninstall.ps1: deleting the file does not help: a missing registry is refused for the same reason."
                Write-Error "uninstall.ps1: to proceed anyway (DANGEROUS: may delete shared files including bin\ap.py and runtime.json), re-run with -ForceNoRegistry."
                exit 1
            }
            # ForceNoRegistry=True: proceed with empty registry after warning
            Write-Warning "uninstall.ps1: registry is malformed ($_). Proceeding without ownership data."
            $data = @{schema_version = 1; skills = @{}}
        }
    }

    $decisions = @()

    # Process each skill
    foreach ($skill in $approvedSkills) {
        $owners = @()
        if ($data.skills.$skill) {
            $owners = @($data.skills.$skill)
        }

        # Remove "opencode" from owners
        $owners = $owners | Where-Object { $_ -ne "opencode" }

        $skillPath = Join-Path $SkillsDir $skill
        $skillExists = Test-Path -LiteralPath $skillPath

        if ($owners.Count -gt 0) {
            # Shared - keep files, update registration
            $decisions += @{Action = "KEEP"; Skill = $skill; Owners = $owners}
        } elseif ($skillExists) {
            # Sole owner - remove
            $decisions += @{Action = "REMOVE"; Skill = $skill; Owners = @()}
        }
    }

    # Output decisions and perform actions
    foreach ($decision in $decisions) {
        if ($decision.Action -eq "KEEP") {
            Write-Host "  - $($decision.Skill) (shared with another adapter - leaving files, updating registration)"
            $script:Kept++
            $script:SharedOwners = $true
        } else {
            Remove-ApPath (Join-Path $SkillsDir $decision.Skill) "skills\$($decision.Skill)"
        }
    }

    # Write updated ownership file
    if ($Yes) {
        # Build remaining skills from ALL entries with non-empty owner lists after pruning
        $skillsHash = @{}
        if ($data.skills) {
            foreach ($k in $data.skills.PSObject.Properties.Name) {
                $val = $data.skills.$k
                # Preserve arrays, wrap non-arrays
                if ($val -is [System.Array]) {
                    $skillsHash[$k] = $val
                } else {
                    $skillsHash[$k] = @($val)
                }
            }
        }

        $remainingSkills = @{}
        foreach ($skill in $approvedSkills) {
            if ($skillsHash.ContainsKey($skill)) {
                $owners = $skillsHash[$skill]
                # Filter out "opencode"
                $filtered = @($owners | Where-Object { $_ -ne "opencode" })
                $filtered = @($filtered | Where-Object { $null -ne $_ })
                if ($filtered.Count -gt 0) {
                    $remainingSkills[$skill] = $filtered
                }
            }
        }
        # Keep non-approved-skill entries from other adapters
        foreach ($k in $skillsHash.Keys) {
            if ($k -notin $approvedSkills) {
                $owners = $skillsHash[$k]
                $filtered = @($owners | Where-Object { $_ -ne "opencode" })
                $filtered = @($filtered | Where-Object { $null -ne $_ })
                if ($filtered.Count -gt 0) {
                    $remainingSkills[$k] = $filtered
                }
            }
        }

        if ($remainingSkills.Count -gt 0) {
            $newData = @{
                schema_version = 1
                skills = $remainingSkills
            }
            $jsonOut = $newData | ConvertTo-Json -Depth 5
            [System.IO.File]::WriteAllText($OwnershipFile, $jsonOut,
                [System.Text.UTF8Encoding]::new($false))
        } elseif (Test-Path -LiteralPath $OwnershipFile) {
            # No remaining owners - delete the file
            Remove-Item -LiteralPath $OwnershipFile -Force
        }
    }
}

function Invoke-ApUninstall([string]$AgentsDir, [string]$ApDir) {
    $SkillsDir = Join-Path $AgentsDir "skills"
    $OwnershipFile = Join-Path $ApDir "skill-ownership.json"

    Write-Host ""
    Write-Host "Removing OpenCode Advanced Planning adapter from:"
    Write-Host "  skills:   $SkillsDir"
    Write-Host "  runtime:  $ApDir"
    if (-not $Yes) {
        Write-Host ""
        Write-Host "  DRY RUN -- nothing will be deleted. Re-run with -Yes to act."
    }
    Write-Host ""

    Write-Host "Skills (with ownership check):"
    Invoke-ApOwnershipRemoval $SkillsDir $OwnershipFile

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
    if ($script:SharedOwners) {
        # Another adapter still owns a skill here, and every one of those
        # skills invokes .advanced-plans\bin\ap.py.  Removing the launcher
        # would leave that adapter installed but inert -- exactly the failure
        # the ownership check above exists to prevent.
        Write-Host "  keeping bin/ap.py and runtime.json (still owned by another adapter)"
    }
    else {
        Remove-ApPath (Join-Path $ApDir "bin\ap.py") "bin/ap.py"
        Remove-ApDirIfEmpty (Join-Path $ApDir "bin")
        Remove-ApPath (Join-Path $ApDir "runtime.json") "runtime.json"
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
