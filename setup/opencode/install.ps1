# install.ps1
#
# Installs the Advanced Planning System for OpenCode into a project or globally.
# PowerShell equivalent of install.sh — for Windows users.
#
# Usage:
#   .\setup\opencode\install.ps1 -Project C:\path\to\your\project
#   .\setup\opencode\install.ps1 -Global
#   .\setup\opencode\install.ps1 -Project C:\path\to\your\project -DryRun
#
# What is installed:
#   -Project : shared routing skill + approved core skills to PROJECT\.agents\skills\
#   -Global  : skills to $HOME\.agents\skills\, runtime to $HOME\.advanced-plans\
#   AGENTS.md merge in project root (idempotent fence)
#   No .opencode/ content - OpenCode discovers skills automatically

[CmdletBinding()]
param(
    [string]$Project = "",
    [switch]$Global,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Resolve repo root (two levels up from this script)
# ---------------------------------------------------------------------------
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\.." )).Path

# Approved core skills to install (excludes companion-detection, permission-config)
# The shared routing skill "advanced-planning" is installed alongside these.
$ApprovedSkills = @("phase-plan-creator", "ralph-loop-planner", "plan-todos", "plan-skill-identification", "plan-subagent-identification", "progress-report", "schema-design")
$AllInstalledSkills = @("advanced-planning") + $ApprovedSkills

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Say([string]$msg) { Write-Host "[install] $msg" }

function Do-MkDir([string]$path) {
    if ($DryRun) {
        Write-Host "  [dry-run] mkdir $path"
    } else {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}

function Do-Copy([string]$src, [string]$dest) {
    if ($DryRun) {
        Write-Host "  [dry-run] Copy-Item $src -> $dest"
    } else {
        Copy-Item -Path $src -Destination $dest -Recurse -Force
    }
}

function Get-FileHash256([string]$path) {
    return (Get-FileHash -Path $path -Algorithm SHA256).Hash
}

function Test-FilesIdentical([string]$f1, [string]$f2) {
    if (-not (Test-Path $f1) -or -not (Test-Path $f2)) { return $false }
    $h1 = Get-FileHash256 $f1
    $h2 = Get-FileHash256 $f2
    return $h1 -eq $h2
}

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------
if (-not $Global -and $Project -eq "") {
    Write-Error "Provide -Project C:\path\to\project or -Global. Run Get-Help .\install.ps1 for usage."
    exit 1
}

if (-not (Test-Path (Join-Path $RepoRoot "core"))) {
    Write-Error "Cannot find core\ in $RepoRoot. Run this script from the advanced-planning root or check your path."
    exit 1
}

if (-not (Test-Path (Join-Path $RepoRoot "platforms\shared\agent-skills\advanced-planning"))) {
    Write-Error "Cannot find platforms\shared\agent-skills\advanced-planning in $RepoRoot."
    exit 1
}

# ---------------------------------------------------------------------------
# Global runtime record (Contract 6)
# ---------------------------------------------------------------------------
function Get-ApGlobalHome {
    if ($env:USERPROFILE) { return $env:USERPROFILE }
    if ($env:HOME) { return $env:HOME }
    if ($HOME) { return $HOME }
    throw "Neither USERPROFILE nor HOME is set; refusing to resolve the global home to the filesystem root."
}

function ConvertTo-ApEmbeddedPath([string]$p) { return ($p -replace '\\', '/') }

# Point a copied command file at an absolute launcher. Only the two executable
# forms are rewritten; prose mentions describe the project install and stay true.
function Set-ApCallSites([string]$File, [string]$Launcher) {
    $text = [System.IO.File]::ReadAllText($File)
    $text = $text.Replace('python ".advanced-plans/bin/ap.py"', 'python "' + $Launcher + '"')
    $text = $text.Replace("runpy.run_path(r'.advanced-plans/bin/ap.py')",
                          "runpy.run_path(r'" + $Launcher + "')")
    [System.IO.File]::WriteAllText($File, $text,
        [System.Text.UTF8Encoding]::new($false))
}

# Note: owner token ("opencode") and fence markers ("advanced-planning:opencode:")
# are handled in the Merge-ApAgentsMd and Write-ApOwnership functions below.

# ---------------------------------------------------------------------------
# Collision check for shared skills
# ---------------------------------------------------------------------------
# $Launcher is optional.  When set, the destination was rewritten to point
# at that absolute launcher when it was installed, so the raw source can
# never match it and every second global install would report a fork of a
# file it actually agrees with.  Compare what THIS installer would write.
# The project branch passes nothing and keeps a raw-vs-raw comparison.
function Test-ApCollision([string]$Src, [string]$Dst, [string]$SkillName, [string]$Launcher = "") {
    if (-not (Test-Path $Dst)) {
        return 0  # No collision - destination absent
    }

    # Check each file in the skill directory
    $srcFiles = Get-ChildItem -Path $Src -File -Recurse
    foreach ($srcFile in $srcFiles) {
        $relPath = $srcFile.FullName.Substring($Src.Length).TrimStart('\')
        $dstFile = Join-Path $Dst $relPath
        if (Test-Path $dstFile) {
            $cmpFile = $srcFile.FullName
            $tmpFile = $null
            if ($Launcher) {
                $tmpFile = [System.IO.Path]::GetTempFileName()
                Copy-Item $srcFile.FullName $tmpFile -Force
                Set-ApCallSites $tmpFile $Launcher
                $cmpFile = $tmpFile
            }
            if (-not (Test-FilesIdentical $cmpFile $dstFile)) {
                $srcHash = Get-FileHash256 $cmpFile
                $dstHash = Get-FileHash256 $dstFile
                if ($tmpFile) { Remove-Item $tmpFile -Force }
                Write-Host "ERROR: collision detected for skill '$SkillName'" -ForegroundColor Red
                Write-Host "  Source:      $($srcFile.FullName) (SHA-256: $srcHash)"
                if ($Launcher) {
                    Write-Host "  (source hashed as it would be installed, call sites rewritten)"
                }
                Write-Host "  Installed:   $dstFile (SHA-256: $dstHash)"
                Write-Host "  Refusing to overwrite - silent divergence is the defect this check exists to catch."
                return 1  # Collision error
            }
            if ($tmpFile) { Remove-Item $tmpFile -Force }
        }
    }

    # Identical - report shared; unchanged
    Say "  shared; unchanged: $SkillName"
    return 2  # Signal: identical, skip copy
}

# ---------------------------------------------------------------------------
# AGENTS.md merge
# ---------------------------------------------------------------------------
function Merge-ApAgentsMd([string]$ProjectPath) {
    $agentsFile = Join-Path $ProjectPath "AGENTS.md"
    $fenceStart = "<!-- advanced-planning:opencode:start -->"
    $fenceEnd = "<!-- advanced-planning:opencode:end -->"

    $fenceContent = @"
$fenceStart
## Advanced Planning for OpenCode

This project uses the Advanced Planning framework for structured, multi-loop execution.

**Triggers:**
- `` `$advanced-planning phase <goal> `` - Create a new phase plan
- `` `$advanced-planning loop next `` - Execute the next loop
- `` `$advanced-planning gate current `` - Run gate review on completed phase
- `` `$advanced-planning resume `` - Recover from interruption
- `` `$advanced-planning compact current `` - Compact phase artefacts

**Runtime:** Commands use the shared Python launcher at `.advanced-plans/bin/ap.py`. Exit code 3 means the runtime is unreachable - run the installer again.

**Skills:** Installed to `.agents/skills/` - OpenCode discovers them automatically.

$fenceEnd
"@

    if (-not (Test-Path $agentsFile)) {
        if ($DryRun) {
            Write-Host "  [dry-run] create $agentsFile with fence block"
        } else {
            [System.IO.File]::WriteAllText($agentsFile, $fenceContent + "`n",
                [System.Text.UTF8Encoding]::new($false))
            Say "  + AGENTS.md (created with fence)"
        }
        return
    }

    $existingContent = [System.IO.File]::ReadAllText($agentsFile)

    # Check if fence already exists
    if ($existingContent -match [regex]::Escape($fenceStart)) {
        # Count occurrences
        $matches = [regex]::Matches($existingContent, [regex]::Escape($fenceStart))
        if ($matches.Count -gt 1) {
            Write-Error "malformed AGENTS.md - multiple advanced-planning:opencode:start fences"
            exit 1
        }
        if ($existingContent -notmatch [regex]::Escape($fenceEnd)) {
            Write-Error "malformed AGENTS.md - fence started but not closed"
            exit 1
        }
        # Idempotent - fence exists and is well-formed, skip
        Say "  AGENTS.md fence already present - unchanged"
        return
    }

    # Append fence to existing file
    if ($DryRun) {
        Write-Host "  [dry-run] append fence block to $agentsFile"
    } else {
        $newContent = $existingContent + "`n" + $fenceContent + "`n"
        [System.IO.File]::WriteAllText($agentsFile, $newContent,
            [System.Text.UTF8Encoding]::new($false))
        Say "  + AGENTS.md (appended fence)"
    }
}

# ---------------------------------------------------------------------------
# Write ownership metadata - merges with existing, does not overwrite
# ---------------------------------------------------------------------------
function Write-ApOwnership([string]$ProjectPath) {
    $ownerFile = Join-Path $ProjectPath ".advanced-plans\skill-ownership.json"

    if ($DryRun) {
        Write-Host "  [dry-run] merge/write $ownerFile"
        return
    }

    # Read existing or start fresh - always work with hashtables
    $skillsHash = @{}
    if (Test-Path -LiteralPath $ownerFile) {
        try {
            $existingContent = [System.IO.File]::ReadAllText($ownerFile)
            $parsed = $existingContent | ConvertFrom-Json
            # Convert PSCustomObject skills to hashtable, ensuring array values
            if ($parsed.skills) {
                foreach ($k in $parsed.skills.PSObject.Properties.Name) {
                    $val = $parsed.skills.$k
                    # Convert to array - handle both single values and arrays
                    if ($val -is [System.Array]) {
                        $skillsHash[$k] = $val
                    } else {
                        $skillsHash[$k] = @($val)
                    }
                }
            }
        } catch {
            Write-Error "install.ps1: $ownerFile is malformed JSON ($_)"
            Write-Error "install.ps1: fix: repair the file or delete it and re-install."
            exit 1
        }
    }

    # Merge: for each skill this adapter installs, add "opencode" to owners
    foreach ($skill in $AllInstalledSkills) {
        # Force array context - PowerShell unwraps single-element arrays from hashtables
        $existing = if ($skillsHash.ContainsKey($skill)) { , $skillsHash[$skill] } else { @() }
        if ("opencode" -notin $existing) {
            $existing = $existing + @("opencode")
        }
        $skillsHash[$skill] = $existing
    }

    # Write back
    $data = @{
        schema_version = 1
        skills = $skillsHash
    }
    $jsonOut = $data | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($ownerFile, $jsonOut,
        [System.Text.UTF8Encoding]::new($false))
}

# ---------------------------------------------------------------------------
# Global install
# ---------------------------------------------------------------------------
if ($Global) {
    $ApGlobalHome = Get-ApGlobalHome
    $GlobalDir = Join-Path $ApGlobalHome ".agents"
    $ApGlobalDir = Join-Path $ApGlobalHome ".advanced-plans"
    $ApLauncher = ConvertTo-ApEmbeddedPath (Join-Path $ApGlobalDir "bin\ap.py")
    $SkillsDest = Join-Path $GlobalDir "skills"

    Say "Installing globally to $GlobalDir"
    Say ""
    Do-MkDir $SkillsDest

    # Install shared routing skill
    Say "Installing shared routing skill..."
    $src = Join-Path $RepoRoot "platforms\shared\agent-skills\advanced-planning"
    $dstParent = $SkillsDest
    $collisionResult = Test-ApCollision $src (Join-Path $dstParent "advanced-planning") "advanced-planning" $ApLauncher
    if ($collisionResult -eq 0) {
        Do-Copy $src $dstParent
        Say "  + skills\advanced-planning\"
    } elseif ($collisionResult -eq 1) {
        exit 1
    }

    # Rewrite call sites in global install
    if (-not $DryRun) {
        $skillDir = Join-Path $dstParent "advanced-planning"
        Get-ChildItem -Path $skillDir -Filter "*.md" -File | ForEach-Object {
            Set-ApCallSites $_.FullName $ApLauncher
        }
        Get-ChildItem -Path (Join-Path $skillDir "references") -Filter "*.md" -File | ForEach-Object {
            Set-ApCallSites $_.FullName $ApLauncher
        }
        Say "  (rewrote launcher call sites to $ApLauncher)"
    }

    # Install approved core skills
    Say "Installing approved core skills..."
    foreach ($skill in $ApprovedSkills) {
        $src = Join-Path $RepoRoot "core\skills\$skill"
        if (-not (Test-Path $src)) {
            Write-Host "WARNING: core\skills\$skill not found - skipping" -ForegroundColor Yellow
            continue
        }
        $collisionResult = Test-ApCollision $src (Join-Path $dstParent $skill) $skill $ApLauncher
        if ($collisionResult -eq 0) {
            Do-Copy $src $dstParent
            Say "  + skills\$skill\"
        } elseif ($collisionResult -eq 1) {
            exit 1
        }

        # Rewrite call sites if skill has any
        if (-not $DryRun) {
            $skillDestPath = Join-Path $dstParent $skill
            Get-ChildItem -Path $skillDestPath -Filter "*.md" -File | ForEach-Object {
                Set-ApCallSites $_.FullName $ApLauncher
            }
        }
    }

    Say ""
    Say "Recording the shared Python runtime globally..."
    Do-MkDir (Join-Path $ApGlobalDir "bin")
    Do-Copy (Join-Path $RepoRoot "platforms\python\ap_launcher.py") (Join-Path $ApGlobalDir "bin\ap.py")
    if (-not $DryRun) {
        $gVersionFile = Join-Path $RepoRoot "VERSION"
        $gVersion = if (Test-Path $gVersionFile) { (Get-Content $gVersionFile -Raw).Trim() } else { "unknown" }
        $gRuntime = [ordered]@{
            schema_version = 1
            source_root    = ConvertTo-ApEmbeddedPath $RepoRoot
            version        = $gVersion
            written_by     = "setup/opencode/install.ps1 -Global"
            written_at     = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        } | ConvertTo-Json -Depth 3
        [System.IO.File]::WriteAllText((Join-Path $ApGlobalDir "runtime.json"), $gRuntime,
            [System.Text.UTF8Encoding]::new($false))
    }
    Say "  + $ApGlobalDir\bin\ap.py"
    Say "  + $ApGlobalDir\runtime.json"

    Say ""
    # The global skills are shared with the other adapter, so the ownership
    # registry has to exist here too.  Without it a global uninstall reads an
    # empty owner list and removes the shared skill the other adapter needs.
    Say ""
    Say "Recording skill ownership globally..."
    Write-ApOwnership $ApGlobalHome

    Say "Global install complete."
    exit 0
}

# ---------------------------------------------------------------------------
# Project install
# ---------------------------------------------------------------------------
$AgentsDir = Join-Path $Project ".agents"
$ApDir = Join-Path $Project ".advanced-plans"

Say "Installing Advanced Planning System for OpenCode"
Say "  repo:    $RepoRoot"
Say "  project: $Project"
Say "  target:  $AgentsDir\skills\"
if ($DryRun) { Say "  mode:    DRY RUN (no files written)" }
Say ""

# Create target directories
Do-MkDir (Join-Path $AgentsDir "skills")

# ---------------------------------------------------------------------------
# Shared Python runtime - OUTSIDE any scaffold guard
# ---------------------------------------------------------------------------
Say "Recording the shared Python runtime..."
$ApBinDir = Join-Path $ApDir "bin"
Do-MkDir $ApBinDir
Do-Copy (Join-Path $RepoRoot "platforms\python\ap_launcher.py") (Join-Path $ApBinDir "ap.py")
if (-not $DryRun) {
    $apVersionFile = Join-Path $RepoRoot "VERSION"
    $apVersion = if (Test-Path $apVersionFile) { (Get-Content $apVersionFile -Raw).Trim() } else { "unknown" }
    $runtime = [ordered]@{
        schema_version = 1
        source_root    = ConvertTo-ApEmbeddedPath $RepoRoot
        version        = $apVersion
        written_by     = "setup/opencode/install.ps1"
        written_at     = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    } | ConvertTo-Json -Depth 3
    [System.IO.File]::WriteAllText((Join-Path $ApDir "runtime.json"), $runtime,
        [System.Text.UTF8Encoding]::new($false))
    Say "  + .advanced-plans\runtime.json -> $RepoRoot"
    Say "  + .advanced-plans\bin\ap.py"
} else {
    Write-Host "  [dry-run] write $(Join-Path $ApDir 'runtime.json') recording $RepoRoot"
}

# ---------------------------------------------------------------------------
# .advanced-plans/ scaffold - idempotent skip if data already exists
# ---------------------------------------------------------------------------
if ((Test-Path $ApDir) -and (Test-Path (Join-Path $ApDir "PLANNING.md"))) {
    Say "Preserving existing planning data at $ApDir - skipping scaffold"
} else {
    Say "Creating .advanced-plans\ scaffold..."
    Do-MkDir (Join-Path $ApDir "phases")
    Do-MkDir (Join-Path $ApDir "specs")
    Do-MkDir (Join-Path $ApDir "state")
    Do-MkDir (Join-Path $ApDir "logs")

    if (-not $DryRun) {
        if (-not (Test-Path (Join-Path $ApDir "PLANNING.md"))) {
            @"
---
programme: ""
status: not_started
last_updated: ""
current_phase: ""
current_loop: ""
gate_status: ""
next_action: "Run `$advanced-planning phase <goal> to create the first phase plan"
active_branches: @()
phases:
  complete: []
  pending: []
  failed: []
state_files:
  ready: .advanced-plans/state/loop-ready.json
  complete: .advanced-plans/state/loop-complete.json
  history: .advanced-plans/state/history.jsonl
notes: ""
---

# Planning

This directory holds all planning artefacts. See README.md for the layout.
"@ | Out-File -FilePath (Join-Path $ApDir "PLANNING.md") -Encoding UTF8 -NoNewline
        }
        if (-not (Test-Path (Join-Path $ApDir "README.md"))) {
            @"
# .advanced-plans/

Platform-agnostic planning data home.

- `PLANNING.md` -- live programme dashboard (YAML frontmatter)
- `PLANS-INDEX.md` -- index of all phases and loops
- `phases/phase-N/` -- `plan.md` + `loops.md` per phase
- `specs/` -- design specs
- `state/` -- filesystem state bus (loop-ready/complete, history.jsonl)
- `logs/` -- execution log
"@ | Out-File -FilePath (Join-Path $ApDir "README.md") -Encoding UTF8 -NoNewline
        }
    } else {
        Write-Host "  [dry-run] create .advanced-plans\ scaffold"
    }
}

# ---------------------------------------------------------------------------
# Install shared routing skill
# ---------------------------------------------------------------------------
Say "Installing shared routing skill..."
$src = Join-Path $RepoRoot "platforms\shared\agent-skills\advanced-planning"
$dstParent = Join-Path $AgentsDir "skills"
$collisionResult = Test-ApCollision $src (Join-Path $dstParent "advanced-planning") "advanced-planning"
if ($collisionResult -eq 0) {
    Do-Copy $src $dstParent
    Say "  + skills\advanced-planning\"
} elseif ($collisionResult -eq 1) {
    exit 1
}

# ---------------------------------------------------------------------------
# Install approved core skills
# ---------------------------------------------------------------------------
Say "Installing approved core skills..."
foreach ($skill in $ApprovedSkills) {
    $src = Join-Path $RepoRoot "core\skills\$skill"
    if (-not (Test-Path $src)) {
        Write-Host "WARNING: core\skills\$skill not found - skipping" -ForegroundColor Yellow
        continue
    }
    $collisionResult = Test-ApCollision $src (Join-Path $dstParent $skill) $skill
    if ($collisionResult -eq 0) {
        Do-Copy $src $dstParent
        Say "  + skills\$skill\"
    } elseif ($collisionResult -eq 1) {
        exit 1
    }
}

# ---------------------------------------------------------------------------
# Merge AGENTS.md
# ---------------------------------------------------------------------------
Say "Merging AGENTS.md..."
Merge-ApAgentsMd $Project

# ---------------------------------------------------------------------------
# Write ownership metadata
# ---------------------------------------------------------------------------
Say "Recording skill ownership..."
Write-ApOwnership $Project

Say ""
Say "Installation complete."
Say ""
Say "Next steps:"
Say "  1. cd into your project folder"
Say "  2. Start a new OpenCode session (skills are discovered on session start)"
Say '  3. Use: $advanced-planning phase <goal>'
Say ""
Say "See setup/opencode/README.md for full documentation."
