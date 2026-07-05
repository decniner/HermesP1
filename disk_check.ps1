# Check largest folders on C drive
$targets = @(
    "C:\Users\decni\AppData\Local",
    "C:\Users\decni\AppData\Roaming",
    "C:\Program Files",
    "C:\Program Files (x86)",
    "C:\Windows\Temp",
    "C:\Users\decni\Downloads",
    "C:\Users\decni\Desktop"
)

Write-Host "`nTop space consumers:" -ForegroundColor Yellow
foreach ($path in $targets) {
    if (Test-Path $path) {
        $folder = Get-ChildItem $path -ErrorAction SilentlyContinue
        $size = ($folder | Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
        # Also count subdirectories
        $total = (Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        if ($total -gt 1GB) {
            Write-Host ("  {0,-30} {1,8:N2} GB" -f (Split-Path $path -Leaf), ($total/1GB))
        }
    }
}

# Biggest folders in Users
Write-Host "`nLargest items in C:\Users\decni\:" -ForegroundColor Yellow
$userItems = Get-ChildItem "C:\Users\decni" -Directory -ErrorAction SilentlyContinue
foreach ($item in $userItems) {
    $total = (Get-ChildItem $item.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    if ($total -gt 500MB) {
        Write-Host ("  {0,-30} {1,8:N2} GB" -f $item.Name, ($total/1GB))
    }
}
