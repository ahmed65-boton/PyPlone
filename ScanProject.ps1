<#
.SYNOPSIS
  Universal project structure scanner for any framework / platform

.DESCRIPTION
  Scans a project directory and generates a detailed file listing.
  Excludes common system / build folders and binary artifacts by default,
  but can be customized via parameters.
#>

[CmdletBinding()]
param(
    [string]$ProjectPath = ".",             # Default to current directory
    [string]$OutputFile = "ProjectStructure.txt",

    # Folder names to exclude (case-insensitive, leaf names only)
    [string[]]$ExcludeFolders = @(
        'node_modules',
        '.expo',
        'dist',
        'build',
        '.git',
        '.vscode',
        '.idea',
        '__pycache__',
        'bin',
        'obj',
        '.gradle',
        '.svn',
        '.hg',
        '.vs'
    ),

    # File extensions to exclude (case-insensitive, include the dot)
    [string[]]$ExcludeFileExtensions = @(
        '.dll',
        '.exe',
        '.pdb',
        '.obj',
        '.log',
        '.tmp'
    )
)

# Normalized versions for faster / consistent checks
$ExcludedFoldersNormalized       = $ExcludeFolders | ForEach-Object { $_.ToLowerInvariant() }
$ExcludedFileExtensionsNormalized = $ExcludeFileExtensions | ForEach-Object { $_.ToLowerInvariant() }

function Get-SizeInMB {
    param([long]$Bytes)
    if (-not $Bytes) { return 0 }
    return [math]::Round($Bytes / 1MB, 2)
}

function Should-ExcludeFolder {
    param(
        [System.IO.DirectoryInfo]$Directory
    )
    $name = $Directory.Name.ToLowerInvariant()
    return $ExcludedFoldersNormalized -contains $name
}

function Should-ExcludeFile {
    param(
        [System.IO.FileInfo]$File
    )
    $ext = $File.Extension.ToLowerInvariant()
    return $ExcludedFileExtensionsNormalized -contains $ext
}

function PathContainsExcludedFolder {
    param(
        [string]$FullPath
    )

    # Split path into segments and check each against excluded folder names
    $segments = $FullPath -split '[\\/]'
    foreach ($seg in $segments) {
        if ($ExcludedFoldersNormalized -contains $seg.ToLowerInvariant()) {
            return $true
        }
    }
    return $false
}

function Write-FileStructure {
    param(
        [string]$Path,
        [string]$Indent = "",
        [System.IO.StreamWriter]$Writer
    )

    try {
        $items = Get-ChildItem -Path $Path -Force -ErrorAction Stop |
                 Sort-Object Name

        foreach ($item in $items) {

            if ($item.PSIsContainer) {
                # Skip excluded folders
                if (Should-ExcludeFolder -Directory $item) {
                    continue
                }
            }
            else {
                # Skip excluded files by extension
                if (Should-ExcludeFile -File $item) {
                    continue
                }
            }

            # Calculate display size
            if ($item.PSIsContainer) {
                $sizeDisplay = "DIR"
            }
            else {
                $sizeDisplay = "{0} MB" -f (Get-SizeInMB -Bytes $item.Length)
            }

            # Write line
            $line = "{0}{1} | Size: {2} | Modified: {3} | Attributes: {4}" -f `
                    $Indent,
                    $item.Name,
                    $sizeDisplay,
                    $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"),
                    $item.Attributes

            $Writer.WriteLine($line)

            # Recurse into subdirectories
            if ($item.PSIsContainer) {
                Write-FileStructure -Path $item.FullName -Indent ($Indent + "  ") -Writer $Writer
            }
        }
    }
    catch {
        Write-Warning "Cannot access path: $Path - $($_.Exception.Message)"
    }
}

# ===================== MAIN EXECUTION =====================

try {
    # Validate project path
    if (-not (Test-Path $ProjectPath)) {
        Write-Error "Project path '$ProjectPath' does not exist!"
        exit 1
    }

    # Resolve full path
    $ProjectPath = (Resolve-Path $ProjectPath).Path

    # Get full output path
    $OutputFullPath = $OutputFile
    if (-not [System.IO.Path]::IsPathRooted($OutputFile)) {
        $OutputFullPath = Join-Path (Get-Location).Path $OutputFile
    }

    Write-Host "Scanning project at: $ProjectPath" -ForegroundColor Green
    Write-Host "Excluding folders: $($ExcludeFolders -join ', ')" -ForegroundColor Yellow
    Write-Host "Excluding file extensions: $($ExcludeFileExtensions -join ', ')" -ForegroundColor Yellow
    Write-Host "Output file: $OutputFullPath" -ForegroundColor Cyan

    # Create output file and write header
    $streamWriter = [System.IO.StreamWriter]::new($OutputFullPath, $false)
    $streamWriter.WriteLine("Project Structure Report")
    $streamWriter.WriteLine("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
    $streamWriter.WriteLine("Project Path: $ProjectPath")
    $streamWriter.WriteLine("Excluded Folders: $($ExcludeFolders -join ', ')")
    $streamWriter.WriteLine("Excluded File Extensions: $($ExcludeFileExtensions -join ', ')")
    $streamWriter.WriteLine("=" * 80)
    $streamWriter.WriteLine()

    # Generate file structure
    Write-FileStructure -Path $ProjectPath -Writer $streamWriter

    # Write summary
    $streamWriter.WriteLine()
    $streamWriter.WriteLine("=" * 80)
    $streamWriter.WriteLine("Scan completed successfully!")

    # Calculate total size (respecting excludes and nested excluded folders)
    $files = Get-ChildItem -Path $ProjectPath -File -Recurse -Force -ErrorAction SilentlyContinue |
             Where-Object {
                 -not (PathContainsExcludedFolder -FullPath $_.FullName) -and
                 -not (Should-ExcludeFile -File $_)
             }

    $totalSizeBytes = ($files | Measure-Object -Property Length -Sum).Sum
    if (-not $totalSizeBytes) { $totalSizeBytes = 0 }

    $totalSizeMb = Get-SizeInMB -Bytes $totalSizeBytes
    $streamWriter.WriteLine("Total Project Size (excluding excluded folders/extensions): {0} MB" -f $totalSizeMb)

}
catch {
    Write-Error "An error occurred: $($_.Exception.Message)"
}
finally {
    if ($streamWriter) {
        $streamWriter.Close()
        $streamWriter.Dispose()
    }
}

# Display completion message with full path
Write-Host ""
Write-Host "=== SCAN COMPLETED ===" -ForegroundColor Green
Write-Host "Project structure report generated at:" -ForegroundColor White
Write-Host "  $OutputFullPath" -ForegroundColor Yellow

# IMPORTANT: fix the ForegroundColor / -f issue by formatting FIRST, then passing to Write-Host
$sizeMessage = "Total size: {0} MB (excluding excluded folders/extensions)" -f $totalSizeMb
Write-Host $sizeMessage -ForegroundColor Cyan

# Option to open the file
$openFile = Read-Host "`nDo you want to open the file now? (y/n)"
if ($openFile -eq 'y' -or $openFile -eq 'Y') {
    try {
        Invoke-Item $OutputFullPath
        Write-Host "File opened successfully!" -ForegroundColor Green
    }
    catch {
        Write-Host "Could not open the file automatically. Please open it manually." -ForegroundColor Red
    }
}
