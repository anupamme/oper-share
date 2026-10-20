[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [Parameter(Mandatory = $true, Position = 0, ValueFromRemainingArguments = $true)]
    [ValidateNotNullOrEmpty()]
    [string[]]$LiteralPath
)

$ErrorActionPreference = 'Stop'
$hadFailure = $false

# The Recycle Bin records the original path in its per-item $I metadata, which is
# MAX_PATH-sized. A path of 260+ characters therefore CANNOT be represented in
# the bin, and Microsoft.VisualBasic.FileIO does not report that as an error: it
# silently falls through to a PERMANENT delete (verified 2026-09-27: bin count
# and $I/$R records unchanged, marker bytes gone). That would break the Never
# Destroy rule, so long targets are moved to a short staging directory first and
# recycled from there. Consequence, by Windows design: the bin record for such an
# item holds the staging path, so "Restore" returns it to the staging directory,
# not to its original folder.
$maxPathLength = 260

function ConvertTo-PlainPath {
    param([string]$Path)
    if ($Path.StartsWith('\\?\UNC\', [System.StringComparison]::Ordinal)) {
        return '\\' + $Path.Substring(8)
    }
    if ($Path.StartsWith('\\?\', [System.StringComparison]::Ordinal)) {
        return $Path.Substring(4)
    }
    return $Path
}

function Test-LongPathItem {
    # Plain .NET path APIs are unreliable past MAX_PATH, so probe with the
    # verbatim prefix when the target is long.
    param([string]$Path)
    if ($Path.Length -ge $maxPathLength) {
        $verbatim = '\\?\' + $Path
        if ([System.IO.Directory]::Exists($verbatim)) { return 'Directory' }
        if ([System.IO.File]::Exists($verbatim)) { return 'File' }
    }
    else {
        if ([System.IO.Directory]::Exists($Path)) { return 'Directory' }
        if ([System.IO.File]::Exists($Path)) { return 'File' }
    }
    return $null
}

function Get-StagingParent {
    # Staging must sit on the target's own volume (Directory.Move is same-volume)
    # and be as SHORT as possible: the bin prefixes $R<id> before the staged path,
    # so every saved character is headroom for the deepest file inside the tree.
    param([string]$Target)
    $targetRoot = [System.IO.Path]::GetPathRoot($Target)
    $workspaceRoot = Split-Path -Parent $PSScriptRoot
    $candidates = @(
        (Join-Path $env:USERPROFILE '_ts'),
        (Join-Path $workspaceRoot '_tmp')
    )
    foreach ($candidate in $candidates) {
        if (-not $candidate) { continue }
        if ([System.IO.Path]::GetPathRoot($candidate) -ne $targetRoot) { continue }
        if (-not (Test-Path -LiteralPath $candidate -PathType Container)) {
            New-Item -ItemType Directory -Path $candidate -Force | Out-Null
        }
        return $candidate
    }
    return $env:TEMP
}

function Get-UniqueStagedPath {
    param([string]$StagingRoot, [string]$Leaf)
    $candidate = Join-Path $StagingRoot $Leaf
    if (-not (Test-Path -LiteralPath $candidate)) { return $candidate }
    $base = [System.IO.Path]::GetFileNameWithoutExtension($Leaf)
    $extension = [System.IO.Path]::GetExtension($Leaf)
    for ($n = 2; $n -lt 1000; $n++) {
        $candidate = Join-Path $StagingRoot ("$base-$n$extension")
        if (-not (Test-Path -LiteralPath $candidate)) { return $candidate }
    }
    throw "No free staging name available for '$Leaf'."
}

function Move-ToStaging {
    # Directory.Move only works inside one volume and requires the same path form
    # on both sides; File.Move handles cross-volume and mixed forms.
    param([string]$Source, [string]$Destination, [string]$Kind)
    if ($Kind -eq 'Directory') {
        [System.IO.Directory]::Move('\\?\' + $Source, '\\?\' + $Destination)
    }
    else {
        [System.IO.File]::Move('\\?\' + $Source, $Destination)
    }
}

function Move-FromStaging {
    param([string]$Staged, [string]$Original, [string]$Kind)
    if ($Kind -eq 'Directory') {
        [System.IO.Directory]::Move('\\?\' + $Staged, '\\?\' + $Original)
    }
    else {
        [System.IO.File]::Move($Staged, '\\?\' + $Original)
    }
}

try {
    Add-Type -AssemblyName Microsoft.VisualBasic
}
catch {
    Write-Error "Windows Recycle Bin support is unavailable: $($_.Exception.Message)"
    exit 1
}

$stagingRoot = $null

foreach ($requestedPath in $LiteralPath) {
    $stagedPath = $null
    $originalPath = $null
    $itemKind = $null
    try {
        $resolvedPaths = @(Resolve-Path -LiteralPath $requestedPath -ErrorAction Stop)
        foreach ($resolvedPath in $resolvedPaths) {
            $providerPath = ConvertTo-PlainPath $resolvedPath.ProviderPath

            if (-not $PSCmdlet.ShouldProcess($providerPath, 'Send to Windows Recycle Bin')) {
                continue
            }

            $itemKind = Test-LongPathItem -Path $providerPath
            if (-not $itemKind) {
                throw "Path disappeared before it could be recycled."
            }

            $recyclePath = $providerPath
            if ($providerPath.Length -ge $maxPathLength) {
                if (-not $stagingRoot) {
                    $stagingRoot = Join-Path (Get-StagingParent -Target $providerPath) ('ts-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
                    New-Item -ItemType Directory -Path $stagingRoot | Out-Null
                }
                $leaf = Split-Path -Leaf $providerPath
                $candidate = Get-UniqueStagedPath -StagingRoot $stagingRoot -Leaf $leaf
                if ($candidate.Length -ge $maxPathLength) {
                    throw "Leaf name too long to stage safely: '$leaf'."
                }
                Move-ToStaging -Source $providerPath -Destination $candidate -Kind $itemKind
                $stagedPath = $candidate
                $originalPath = $providerPath
                $recyclePath = $candidate
            }

            $recycleOne = {
                param([string]$PathToRecycle)
                if ([System.IO.Directory]::Exists($PathToRecycle)) {
                    [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory(
                        $PathToRecycle,
                        [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                        [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin
                    )
                }
                elseif ([System.IO.File]::Exists($PathToRecycle)) {
                    [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(
                        $PathToRecycle,
                        [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                        [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin
                    )
                }
                else {
                    throw "Path disappeared before it could be recycled."
                }
            }

            try {
                & $recycleOne $recyclePath
            }
            catch {
                # A tree whose INNER files are long fails with "access denied" even
                # when its own path is short: the bin prefixes $R before the whole
                # original path, so depth - not the top path - is what overflows.
                # Stage the tree at a short path and recycle it from there.
                if ($stagedPath) { throw }
                if (-not $stagingRoot) {
                    $stagingRoot = Join-Path (Get-StagingParent -Target $providerPath) ('ts-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
                    New-Item -ItemType Directory -Path $stagingRoot | Out-Null
                }
                $leaf = Split-Path -Leaf $providerPath
                $candidate = Get-UniqueStagedPath -StagingRoot $stagingRoot -Leaf $leaf
                if ($candidate.Length -ge $maxPathLength) {
                    throw
                }
                Move-ToStaging -Source $providerPath -Destination $candidate -Kind $itemKind
                $originalPath = $providerPath
                $stagedPath = $candidate
                $recyclePath = $candidate
                & $recycleOne $recyclePath
            }

            if (Test-Path -LiteralPath $recyclePath) {
                throw "Recycle Bin operation returned without moving the target."
            }

            if ($stagedPath) {
                Write-Host "Recycled: $originalPath"
                Write-Host "  (staged via $stagedPath - path was too long for the Recycle Bin to record)"
            }
            else {
                Write-Host "Recycled: $recyclePath"
            }
        }
    }
    catch {
        $hadFailure = $true
        $failure = $_.Exception.Message
        if ($stagedPath -and $originalPath -and (Test-Path -LiteralPath $stagedPath)) {
            try {
                Move-FromStaging -Staged $stagedPath -Original $originalPath -Kind $itemKind
                Write-Error "Failed to recycle '$requestedPath': $failure (item restored to its original location)"
            }
            catch {
                Write-Error "Failed to recycle '$requestedPath': $failure. The staged copy could not be restored automatically - it is at '$stagedPath'."
            }
        }
        else {
            Write-Error "Failed to recycle '$requestedPath': $failure"
        }
    }
}

# The staging directory is our own scaffolding; recycle it too, never erase it.
if ($stagingRoot -and (Test-Path -LiteralPath $stagingRoot)) {
    try {
        $leftover = @(Get-ChildItem -LiteralPath $stagingRoot -Force -ErrorAction Stop)
        if ($leftover.Count -eq 0) {
            [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory(
                $stagingRoot,
                [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin
            )
        }
        else {
            Write-Warning "Staging directory still holds items and was left in place: $stagingRoot"
        }
    }
    catch {
        Write-Warning "Could not recycle the staging directory; it was left in place: $stagingRoot"
    }
}

if ($hadFailure) {
    exit 1
}
