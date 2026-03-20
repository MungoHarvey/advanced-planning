# install.ps1
#
# Installs the Advanced Planning System into a Claude Code project or globally.
# PowerShell equivalent of install.sh — for Windows users.
#
# Usage:
#   .\setup\claude-code\install.ps1 -Project C:\path\to\your\project
#   .\setup\claude-code\install.ps1 -Global
#   .\setup\claude-code\install.ps1 -Project C:\path\to\your\project -DryRun
#   .\setup\claude-code\install.ps1 -Project C:\path\to\your\project -Symlink
#
# What is installed:
#   -Project : copies commands, skills, agents, schemas, settings into PROJECT\.claude\
#   -Global  : copies commands only into $HOME\.claude\commands\ (available in all projects)
#   -DryRun  : prints what would be copied without writing any files
#   -Symlink : creates a junction (directory symlink) to core\skills\ instead of copying

[CmdletBinding()]
param(
    [string]$Project  = "",
    [switch]$Global,
    [switch]$DryRun,
    [switch]$Symlink
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Resolve repo root (two levels up from this script)
# ---------------------------------------------------------------------------
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\.." )).Path

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

function Do-Junction([string]$link, [string]$target) {
    # Creates a directory junction (Windows equivalent of a symlink for directories).
    # Requires no elevated permissions on modern Windows.
    if ($DryRun) {
        Write-Host "  [dry-run] New-Item Junction $link -> $target"
    } else {
        if (Test-Path $link) { Remove-Item $link -Recurse -Force }
        New-Item -ItemType Junction -Path $link -Target $target | Out-Null
    }
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

# ---------------------------------------------------------------------------
# Global install
# ---------------------------------------------------------------------------
if ($Global) {
    $GlobalDir = Join-Path $HOME ".claude"
    $CommandsDir = Join-Path $GlobalDir "commands"
    $SkillsDest  = Join-Path $GlobalDir "skills"
    $AgentsDir   = Join-Path $GlobalDir "agents"
    $SchemasDir  = Join-Path $GlobalDir "schemas"

    Say "Installing Advanced Planning System globally to $GlobalDir"
    Say ""
    Do-MkDir $CommandsDir
    Do-MkDir $AgentsDir
    Do-MkDir $SchemasDir

    # Slash commands
    Say "Installing slash commands..."
    $cmds = Get-ChildItem -Path (Join-Path $RepoRoot "platforms\claude-code\commands") -Filter "*.md" -File
    foreach ($cmd in $cmds) {
        Do-Copy $cmd.FullName $CommandsDir
        Say "  + commands\$($cmd.Name)"
    }

    # Agent definitions
    Say "Installing agent definitions..."
    $agents = Get-ChildItem -Path (Join-Path $RepoRoot "core\agents") -Filter "*.md" -File
    foreach ($agent in $agents) {
        Do-Copy $agent.FullName $AgentsDir
        Say "  + agents\$($agent.Name)"
    }

    # Skills
    Say "Installing core skills..."
    $skillsSrc = Join-Path $RepoRoot "core\skills"
    if ($Symlink) {
        Do-Junction $SkillsDest $skillsSrc
        Say "  + skills\ -> $skillsSrc (junction)"
    } else {
        Do-MkDir $SkillsDest
        $skillDirs = Get-ChildItem -Path $skillsSrc -Directory
        foreach ($skillDir in $skillDirs) {
            Do-Copy $skillDir.FullName $SkillsDest
            Say ("  + skills\" + $skillDir.Name + "\")
        }
    }

    # Schemas
    Say "Installing schemas..."
    $schemas = Get-ChildItem -Path (Join-Path $RepoRoot "core\schemas") -File
    foreach ($schema in $schemas) {
        Do-Copy $schema.FullName $SchemasDir
        Say "  + schemas\$($schema.Name)"
    }

    Say ""
    Say "Global install complete."
    exit 0
}

# ---------------------------------------------------------------------------
# Project install
# ---------------------------------------------------------------------------
$ClaudeDir = Join-Path $Project ".claude"

Say "Installing Advanced Planning System"
Say "  repo:    $RepoRoot"
Say "  project: $Project"
Say "  target:  $ClaudeDir"
if ($DryRun)   { Say "  mode:    DRY RUN (no files written)" }
if ($Symlink)  { Say "  skills:  junction (symlink)" }
Say ""

# Create target directories
Do-MkDir (Join-Path $ClaudeDir "commands")
Do-MkDir (Join-Path $ClaudeDir "agents")
Do-MkDir (Join-Path $ClaudeDir "state")
Do-MkDir (Join-Path $ClaudeDir "schemas")

# ---------------------------------------------------------------------------
# Slash commands
# ---------------------------------------------------------------------------
Say "Installing slash commands..."
$cmds = Get-ChildItem -Path (Join-Path $RepoRoot "platforms\claude-code\commands") -Filter "*.md" -File
foreach ($cmd in $cmds) {
    Do-Copy $cmd.FullName (Join-Path $ClaudeDir "commands")
    Say "  + commands\$($cmd.Name)"
}

# ---------------------------------------------------------------------------
# Agent definitions
# ---------------------------------------------------------------------------
Say "Installing agent definitions..."
$agents = Get-ChildItem -Path (Join-Path $RepoRoot "core\agents") -Filter "*.md" -File
foreach ($agent in $agents) {
    Do-Copy $agent.FullName (Join-Path $ClaudeDir "agents")
    Say "  + agents\$($agent.Name)"
}

# ---------------------------------------------------------------------------
# Skills (copy or junction)
# ---------------------------------------------------------------------------
Say "Installing core skills..."
$skillsSrc  = Join-Path $RepoRoot "core\skills"
$skillsDest = Join-Path $ClaudeDir "skills"

if ($Symlink) {
    Do-Junction $skillsDest $skillsSrc
    Say "  + skills\ -> $skillsSrc (junction)"
} else {
    Do-MkDir $skillsDest
    $skillDirs = Get-ChildItem -Path $skillsSrc -Directory
    foreach ($skillDir in $skillDirs) {
        Do-Copy $skillDir.FullName $skillsDest
        Say "  + skills\$($skillDir.Name)\"
    }
}

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
Say "Installing schemas..."
$schemas = Get-ChildItem -Path (Join-Path $RepoRoot "core\schemas") -File
foreach ($schema in $schemas) {
    Do-Copy $schema.FullName (Join-Path $ClaudeDir "schemas")
    Say "  + schemas\$($schema.Name)"
}

# ---------------------------------------------------------------------------
# settings.json
# ---------------------------------------------------------------------------
$settingsPath = Join-Path $ClaudeDir "settings.json"
Say "Writing settings.json..."
if (-not $DryRun) {
    $settings = @{
        planning = @{
            state_dir   = ".claude/state"
            skills_dir  = ".claude/skills"
            agents_dir  = ".claude/agents"
            plans_dir   = "plans"
        }
    } | ConvertTo-Json -Depth 3
    # Use UTF-8 without BOM — Set-Content -Encoding UTF8 adds a BOM in Windows PowerShell 5.x
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($settingsPath, $settings, $utf8NoBom)
} else {
    Write-Host "  [dry-run] write $settingsPath"
}

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Say ""
Say "Installation complete."
Say ""
Say "Next steps:"
Say "  1. cd into your project folder"
Say "  2. claude"
Say "  3. /new-phase    # create your first phase plan"
Say "  4. /new-loop     # decompose phase into loops"
Say "  5. /next-loop    # run the first loop"
Say ""
Say 'See setup/claude-code/README.md for full documentation.'
