# DEN EA Backtest Runner
# Run this script in PowerShell to execute the backtest

$eaName = "BTCJPY_LowDDWithBoS_Opt_V5_1"
$symbol = "BTCJPY"
$timeframe = "M15"
$fromDate = "2025.07.01"
$toDate = "2026.07.10"
$setFile = "C:\Users\decni\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\DEN_EA\Sets\BTCJPY_LowDDWithBoS_Opt_V5_1.set"

Write-Host "=== DEN EA Backtest ===" -ForegroundColor Cyan
Write-Host "Expert: $eaName"
Write-Host "Symbol: $symbol  Period: $timeframe"
Write-Host "Date: $fromDate - $toDate"
Write-Host ""
Write-Host "Project: C:\Users\decni\projects\POGIBOT\backend"
Write-Host "Set file: $setFile" -ForegroundColor Green
Write-Host ""
Write-Host "=== MANUAL STEPS ===" -ForegroundColor Yellow
Write-Host "1. Open MetaTrader 5"
Write-Host "2. View -> Strategy Tester"
Write-Host "3. Expert: $eaName"
Write-Host "4. Symbol: $symbol / Period: $timeframe"
Write-Host "5. Date: $fromDate - $toDate"
Write-Host "6. Mode: Real ticks (recommended)"
Write-Host "7. Inputs tab -> Load -> Select $eaName.set"
Write-Host "8. Check boxes for parameters to optimize"
Write-Host "9. Click Start"
Write-Host ""

# Optional: Launch MT5
$mt5 = "C:\Program Files\MetaTrader 5\terminal64.exe"
if (Test-Path $mt5) {
    Write-Host "Launching MetaTrader 5..." -ForegroundColor Cyan
    Start-Process $mt5
} else {
    Write-Host "MT5 not found at $mt5" -ForegroundColor Red
    Write-Host "Launch it manually."
}

Read-Host "Press Enter to exit"
