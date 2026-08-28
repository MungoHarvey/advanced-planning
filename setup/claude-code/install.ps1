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

# $SelfInstall is set automatically when the project resolves to this repo root.
$SelfInstall = $false

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

# ---------------------------------------------------------------------------
# Global runtime record (mechanism B')
# ---------------------------------------------------------------------------
# USERPROFILE before HOME, matching install_audit.resolve_global_home and the
# launcher's own global_home(). Forward slashes in the embedded form so the
# path survives JSON and Python string literals with no backslash escaping.
function Get-ApGlobalHome {
    if ($env:USERPROFILE) { return $env:USERPROFILE }
    # USERPROFILE first, then the HOME *environment variable*, and only then
    # PowerShell's automatic $HOME. The order matters because the automatic
    # variable is not $env:HOME -- PowerShell derives it from HOMEDRIVE and
    # HOMEPATH -- so on a machine where Git Bash set HOME and USERPROFILE is
    # absent it is empty, while install_audit and the launcher both resolve
    # the HOME path. Join-Path then throws on the empty string and the install
    # aborts exactly where the other two implementations succeed.
    if ($env:HOME) { return $env:HOME }
    if ($HOME) { return $HOME }
    throw "Neither USERPROFILE nor HOME is set; refusing to resolve the global home to the filesystem root."
}

function ConvertTo-ApEmbeddedPath([string]$p) { return ($p -replace '\\', '/') }

# Point a copied command file at an absolute launcher. Only the two executable
# forms are rewritten; prose mentions describe the project install and stay true.
function Set-ApCallSites([string]$File, [string]$Launcher) {
    $text = [System.IO.File]::ReadAllText($File)
    # Only the PATH changes. The quoting and the r'' prefix are already in the
    # source form, so this is a pure substitution of one string for another --
    # which is what lets install_audit normalise it back and report no drift.
    $text = $text.Replace('python ".advanced-plans/bin/ap.py"', 'python "' + $Launcher + '"')
    $text = $text.Replace("runpy.run_path(r'.advanced-plans/bin/ap.py')",
                          "runpy.run_path(r'" + $Launcher + "')")
    [System.IO.File]::WriteAllText($File, $text,
        [System.Text.UTF8Encoding]::new($false))
}

if ($Global) {
    $ApGlobalHome = Get-ApGlobalHome
    $GlobalDir = Join-Path $ApGlobalHome ".claude"
    $ApGlobalDir = Join-Path $ApGlobalHome ".advanced-plans"
    $ApLauncher = ConvertTo-ApEmbeddedPath (Join-Path $ApGlobalDir "bin\ap.py")
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
        # Globally-installed commands run in projects that were never
        # project-installed, where .advanced-plans\bin\ap.py does not exist and
        # the interpreter dies before the launcher's diagnostic can fire.
        if (-not $DryRun) {
            Set-ApCallSites (Join-Path $CommandsDir $cmd.Name) $ApLauncher
        }
        Say "  + commands\$($cmd.Name)"
    }

    # Agent definitions
    Say "Installing agent definitions..."
    $agents = Get-ChildItem -Path (Join-Path $RepoRoot "core\agents") -Filter "*.md" -File
    foreach ($agent in $agents) {
        Do-Copy $agent.FullName $AgentsDir
        Say "  + agents\$($agent.Name)"
    }

    # Platform-specific agent definitions
    $platformAgents = Get-ChildItem -Path (Join-Path $RepoRoot "platforms\claude-code\agents") -Filter "*.md" -File
    foreach ($agent in $platformAgents) {
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
    Say "Recording the shared Python runtime globally..."
    Do-MkDir (Join-Path $ApGlobalDir "bin")
    Do-Copy (Join-Path $RepoRoot "platforms\python\ap_launcher.py") (Join-Path $ApGlobalDir "bin\ap.py")
    if (-not $DryRun) {
        $gVersionFile = Join-Path $RepoRoot "VERSION"
        $gVersion = if (Test-Path $gVersionFile) { (Get-Content $gVersionFile -Raw).Trim() } else { "unknown" }
        $gRuntime = [ordered]@{
            schema_version = 1
            source_root    = $RepoRoot
            version        = $gVersion
            written_by     = "setup/claude-code/install.ps1 -Global"
        } | ConvertTo-Json -Depth 3
        [System.IO.File]::WriteAllText((Join-Path $ApGlobalDir "runtime.json"),
            $gRuntime, [System.Text.UTF8Encoding]::new($false))
    }
    Say "  + $ApGlobalDir\bin\ap.py"
    Say "  + $ApGlobalDir\runtime.json"

    Say ""
    Say "Global install complete."
    exit 0
}

# ---------------------------------------------------------------------------
# Project install
# ---------------------------------------------------------------------------
$ClaudeDir = Join-Path $Project ".claude"

# Self-install detection: if --project resolves to the same git toplevel as
# the repo root, use junctions for runtime dirs so source edits surface immediately.
try {
    $projectGitTop = & git -C $Project rev-parse --show-toplevel 2>$null
    $repoGitTop    = & git -C $RepoRoot rev-parse --show-toplevel 2>$null
    if ($projectGitTop -and $repoGitTop -and ($projectGitTop -eq $repoGitTop)) {
        $SelfInstall = $true
        Say "Self-install detected: project is the source repo root"
        Say "Runtime dirs will be junctions so source edits surface immediately"
    }
} catch {
    # git not available or not a repo — continue without self-install detection
}

Say "Installing Advanced Planning System"
Say "  repo:    $RepoRoot"
Say "  project: $Project"
Say "  target:  $ClaudeDir"
if ($DryRun)        { Say "  mode:    DRY RUN (no files written)" }
if ($SelfInstall)   { Say "  mode:    SELF-INSTALL (junctions for runtime dirs)" }
elseif ($Symlink)   { Say "  skills:  junction (symlink)" }
Say ""

# Create target directories
Do-MkDir (Join-Path $ClaudeDir "commands")
Do-MkDir (Join-Path $ClaudeDir "agents")
Do-MkDir (Join-Path $ClaudeDir "schemas")

# ---------------------------------------------------------------------------
# .advanced-plans/ scaffold -- idempotent skip if data already exists
# ---------------------------------------------------------------------------
$ApDir = Join-Path $Project ".advanced-plans"
if (Test-Path $ApDir) {
    Say "Preserving existing planning data at $ApDir -- skipping scaffold"
} else {
    Say "Creating .advanced-plans\ scaffold..."
    Do-MkDir (Join-Path $ApDir "phases")
    Do-MkDir (Join-Path $ApDir "specs")
    Do-MkDir (Join-Path $ApDir "state")
    Do-MkDir (Join-Path $ApDir "logs")

    # Idempotent migration: move legacy layouts into .advanced-plans\ if present
    if (-not $DryRun) {
        $legacyPlans = Join-Path $Project "plans"
        if ((Test-Path $legacyPlans) -and -not (Test-Path (Join-Path $ApDir "PLANS-INDEX.md"))) {
            Say "Migrating legacy plans\ -> .advanced-plans\ ..."
            Copy-Item -Path (Join-Path $legacyPlans "*") -Destination $ApDir -Recurse -Force -ErrorAction SilentlyContinue
        }
        $legacyState = Join-Path $ClaudeDir "state"
        if (Test-Path $legacyState) {
            Say "Migrating legacy .claude\state\ -> .advanced-plans\state\ ..."
            Copy-Item -Path (Join-Path $legacyState "*") -Destination (Join-Path $ApDir "state") -Recurse -Force -ErrorAction SilentlyContinue
        }
        $legacyLogs = Join-Path $ClaudeDir "logs"
        if (Test-Path $legacyLogs) {
            Say "Migrating legacy .claude\logs\ -> .advanced-plans\logs\ ..."
            Copy-Item -Path (Join-Path $legacyLogs "*") -Destination (Join-Path $ApDir "logs") -Recurse -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "  [dry-run] migrate plans\ and .claude\state|logs\ -> .advanced-plans\ if present"
    }
}

# ---------------------------------------------------------------------------
# Shared Python runtime: launcher + recorded source path
#
# The commands shell out to platforms\python\<module>, which no install ships.
# Rather than copy that tree into every project, record where the checkout is
# and hand the project a launcher that reads the record. See
# platforms/python/ap_launcher.py for why this shape and not the other three.
#
# Deliberately OUTSIDE the scaffold guard above: that guard skips everything
# when .advanced-plans\ already exists, and an upgrade-in-place is exactly the
# case where the recorded path most needs refreshing.
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
        source_root    = $RepoRoot
        version        = $apVersion
        written_by     = "setup/claude-code/install.ps1"
        written_at     = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    } | ConvertTo-Json -Depth 3
    # UTF-8 without BOM: json.loads tolerates a BOM only via utf-8-sig, and the
    # launcher deliberately reads plain utf-8 so a BOM here would be a stale
    # manifest that reports itself as malformed JSON.
    $utf8NoBomRt = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText((Join-Path $ApDir "runtime.json"), $runtime, $utf8NoBomRt)
    Say "  + .advanced-plans\runtime.json -> $RepoRoot"
    Say "  + .advanced-plans\bin\ap.py"
} else {
    Write-Host "  [dry-run] write $(Join-Path $ApDir 'runtime.json') recording $RepoRoot"
}

# ---------------------------------------------------------------------------
# Runtime dirs: self-install uses junctions; normal install copies
# ---------------------------------------------------------------------------
if ($SelfInstall) {
    Say "Installing runtime dirs as junctions (self-install mode)..."
    $commandsSrc = Join-Path $RepoRoot "platforms\claude-code\commands"
    $skillsSrc   = Join-Path $RepoRoot "core\skills"
    $schemasSrc  = Join-Path $RepoRoot "core\schemas"

    if ($DryRun) {
        Write-Host "  [dry-run] New-Item Junction $($ClaudeDir)\commands -> $commandsSrc"
        Write-Host "  [dry-run] New-Item Junction $($ClaudeDir)\skills -> $skillsSrc"
        Write-Host "  [dry-run] New-Item Junction $($ClaudeDir)\schemas -> $schemasSrc"
        Write-Host "  [dry-run] symlink agents from core\agents and platforms\claude-code\agents"
    } else {
        # Remove existing dirs/junctions before creating new ones
        foreach ($dirName in @("commands", "skills", "schemas")) {
            $target = Join-Path $ClaudeDir $dirName
            if (Test-Path $target) { Remove-Item $target -Recurse -Force }
        }
        Do-Junction (Join-Path $ClaudeDir "commands") $commandsSrc
        Say "  + commands -> platforms\claude-code\commands"
        Do-Junction (Join-Path $ClaudeDir "skills") $skillsSrc
        Say "  + skills -> core\skills"
        Do-Junction (Join-Path $ClaudeDir "schemas") $schemasSrc
        Say "  + schemas -> core\schemas"

        # Agents: individual symlinks from both core\agents and platforms\claude-code\agents
        $agentsDir = Join-Path $ClaudeDir "agents"
        if (Test-Path $agentsDir) { Remove-Item $agentsDir -Recurse -Force }
        New-Item -ItemType Directory -Path $agentsDir -Force | Out-Null
        $coreAgents = Get-ChildItem -Path (Join-Path $RepoRoot "core\agents") -Filter "*.md" -File
        foreach ($agent in $coreAgents) {
            New-Item -ItemType SymbolicLink -Path (Join-Path $agentsDir $agent.Name) -Target $agent.FullName -ErrorAction SilentlyContinue | Out-Null
            # Fallback to copy if SymbolicLink fails (insufficient privileges)
            if (-not (Test-Path (Join-Path $agentsDir $agent.Name))) {
                Copy-Item $agent.FullName (Join-Path $agentsDir $agent.Name)
            }
            Say "  + agents\$($agent.Name) -> core\agents"
        }
        $platformAgents = Get-ChildItem -Path (Join-Path $RepoRoot "platforms\claude-code\agents") -Filter "*.md" -File
        foreach ($agent in $platformAgents) {
            New-Item -ItemType SymbolicLink -Path (Join-Path $agentsDir $agent.Name) -Target $agent.FullName -ErrorAction SilentlyContinue | Out-Null
            if (-not (Test-Path (Join-Path $agentsDir $agent.Name))) {
                Copy-Item $agent.FullName (Join-Path $agentsDir $agent.Name)
            }
            Say "  + agents\$($agent.Name) -> platforms\claude-code\agents"
        }
    }
} else {
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

    # Platform-specific agent definitions
    $platformAgents = Get-ChildItem -Path (Join-Path $RepoRoot "platforms\claude-code\agents") -Filter "*.md" -File
    foreach ($agent in $platformAgents) {
        Do-Copy $agent.FullName (Join-Path $ClaudeDir "agents")
        Say "  + agents\$($agent.Name)"
    }

    # ---------------------------------------------------------------------------
    # Skills (copy or junction)
    # All subdirectories of core\skills\ are included automatically.
    # Current skills: companion-detection, phase-plan-creator, plan-skill-identification,
    #   plan-subagent-identification, plan-todos, ralph-loop-planner, progress-report,
    #   schema-design, permission-config
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
}

# ---------------------------------------------------------------------------
# settings.json
# ---------------------------------------------------------------------------
$settingsPath = Join-Path $ClaudeDir "settings.json"
Say "Writing settings.json..."
if (-not $DryRun) {
    $settings = @{
        permissions = @{
            allow = @(
                "Read(.advanced-plans/**)",
                "Write(.advanced-plans/**)",
                "Edit(.advanced-plans/**)",
                "MultiEdit(.advanced-plans/**)"
            )
        }
        planning = @{
            state_dir   = ".advanced-plans/state"
            skills_dir  = ".claude/skills"
            agents_dir  = ".claude/agents"
            plans_dir   = ".advanced-plans"
        }
    } | ConvertTo-Json -Depth 4
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
Say "  3. /new-phase        # create your first phase plan"
Say "  4. /decompose-phase  # decompose phase into loops"
Say "  5. /next-loop    # run the first loop"
Say ""
Say 'See setup/claude-code/README.md for full documentation.'
