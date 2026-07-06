# Scan C: drive for top files by size
Write-Host "Scanning C: drive for largest files (this may take a while)..." -ForegroundColor Yellow
Write-Host ""

$results = Get-ChildItem -Path 'C:\' -Recurse -ErrorAction SilentlyContinue -Force |
    Where-Object { -not $_.PSIsContainer } |
    Sort-Object Length -Descending |
    Select-Object -First 30 |
    ForEach-Object {
        [PSCustomObject]@{
            SizeGB = [math]::Round($_.Length / 1GB, 2)
            SizeMB = [math]::Round($_.Length / 1MB, 0)
            Path   = $_.FullName
        }
    }

$results | Format-Table -AutoSize -Property @{N='Size(GB)';E={$_.SizeGB}}, @{N='Size(MB)';E={$_.SizeMB}}, Path

Write-Host ""
Write-Host "--- Top folders by total size ---" -ForegroundColor Cyan
Write-Host ""

# Also check top-level folders by size
Get-ChildItem -Path 'C:\' -Directory -ErrorAction SilentlyContinue -Force |
    ForEach-Object {
        $size = (Get-ChildItem -Path $_.FullName -Recurse -ErrorAction SilentlyContinue -Force |
            Measure-Object -Property Length -Sum).Sum
        [PSCustomObject]@{
            SizeGB = [math]::Round($size / 1GB, 2)
            SizeMB = [math]::Round($size / 1MB, 0)
            Path   = $_.FullName
        }
    } |
    Sort-Object SizeGB -Descending |
    Select-Object -First 20 |
    Format-Table -AutoSize -Property @{N='Size(GB)';E={$_.SizeGB}}, @{N='Size(MB)';E={$_.SizeMB}}, Path
