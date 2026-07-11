@echo off
REM ============================================================
REM  DEN_EA Backtest Automation Script
REM  Auto-generates .set file for MT5 Strategy Tester
REM  Usage:  double-click or run from command prompt
REM ============================================================
setlocal enabledelayedexpansion

REM ---- CONFIGURATION ----
set EA_NAME=BTCJPY_LowDDWithBoS_Opt_V5_1
set SYMBOL=BTCJPY
set TIMEFRAME=M15
set FROM_DATE=2025.07.01
set TO_DATE=2026.07.10
set TEST_MODE=0
REM  0 = Every tick, 1 = 1 minute OHLC, 2 = Open prices only

REM ---- Paths ----
set TERMINAL_DATA=%APPDATA%\MetaQuotes\Terminal
for /f "delims=" %%d in ('dir "%TERMINAL_DATA%" /b /ad ^| findstr /v "^Common$ ^Community$"') do set INSTANCE=%%d
if "%INSTANCE%"=="" (
    echo ERROR: Cannot find MetaTrader 5 terminal instance
    pause
    exit /b 1
)

set SET_DIR=%TERMINAL_DATA%\%INSTANCE%\MQL5\Experts\DEN_EA\Sets
set SET_FILE=%SET_DIR%\%EA_NAME%.set

if not exist "%SET_DIR%" mkdir "%SET_DIR%"

REM ---- Generate .set file (UTF-16LE) ----
echo Generating parameter set for %EA_NAME%...
(
echo ; DEN EA Backtest Parameters - Auto-generated
echo ; Expert: %EA_NAME%
echo ; Symbol: %SYMBOL%  Period: %TIMEFRAME%
echo ; Date: %FROM_DATE% - %TO_DATE%
echo.
echo ; name=value^|^|start^|^|step^|^|stop^|^|selected
echo MagicNumber=987659^|^|987659^|^|1^|^|987659^|^|Y
echo EMAPeriod=88^|^|88^|^|1^|^|88^|^|Y
echo UseRSIFilter=true^|^|true^|^|^|^|^|^|Y
echo RSIPeriod=14^|^|14^|^|1^|^|14^|^|Y
echo RSILongMin=30.0^|^|30.0^|^|5.0^|^|30.0^|^|Y
echo RSIShortMax=60.0^|^|60.0^|^|5.0^|^|60.0^|^|Y
echo ZoneTF=16388^|^|16388^|^|^|^|^|^|Y
echo BodyStrengthMin=50^|^|50^|^|5^|^|50^|^|Y
echo ZoneExpiryHours=24^|^|24^|^|4^|^|24^|^|Y
echo BaseLotSize=0.01^|^|0.01^|^|0.01^|^|0.01^|^|Y
echo StopLossATR=2.0^|^|2.0^|^|0.5^|^|2.0^|^|Y
echo TakeProfitATR=3.5^|^|3.5^|^|0.5^|^|3.5^|^|Y
echo MaxDailyLossPct=5.0^|^|5.0^|^|1.0^|^|5.0^|^|Y
echo MaxConsecutiveLosses=3^|^|3^|^|1^|^|3^|^|Y
echo UseTrailing=true^|^|true^|^|^|^|^|^|Y
echo TrailActivatePct=1.0^|^|1.0^|^|0.2^|^|1.0^|^|Y
echo TrailOffsetPct=0.6^|^|0.6^|^|0.1^|^|0.6^|^|Y
echo UsePartialTP=true^|^|true^|^|^|^|^|^|Y
echo PartialTP1Pct=3.0^|^|3.0^|^|0.5^|^|3.0^|^|Y
echo PartialClose1Pct=50.0^|^|50.0^|^|10.0^|^|50.0^|^|Y
echo PartialTP2Pct=6.0^|^|6.0^|^|1.0^|^|6.0^|^|Y
echo PartialClose2Pct=75.0^|^|75.0^|^|10.0^|^|75.0^|^|Y
) > "%SET_FILE%"

echo.
echo === SET FILE CREATED ===
echo Location: %SET_FILE%
echo.
echo === INSTRUCTIONS ===
echo 1. Open MetaTrader 5
echo 2. Go to View - Strategy Tester
echo 3. Select Expert: %EA_NAME%
echo 4. Symbol: %SYMBOL% / Period: %TIMEFRAME%
echo 5. Date: %FROM_DATE% - %TO_DATE%
echo 6. Mode: Real ticks (recommended)
echo 7. Go to Inputs tab - Load - select "%EA_NAME%.set"
echo 8. Click Start
echo.
echo === OPTIMIZATION MODE ===
echo To run optimization instead of single test:
echo  - In the Inputs tab, check the boxes next to parameters
echo    you want to optimize (already set with ranges above).
echo  - Click Start - MT5 will run through all combinations.
echo.
pause
