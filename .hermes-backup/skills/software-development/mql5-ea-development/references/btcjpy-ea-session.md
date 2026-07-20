# BTCJPY EA Development Session — Extended

## Session Overview
Extensive backtesting and optimization of BTCJPY Expert Advisors across multiple architectures. User runs EAs on XMTrading MT5, BTCJPY M15, ¥50K JPY, 1:1000 leverage. EAs stored in `DEN_EA/` folder.

## EAs Developed & Results

### V4.3 — Original BTCJPY_LowDDWithBoS
- BodyStrengthMin=60, EMAPeriod=579, RSI(105), fixed SL 3.48%/TP 8%
- 1yr: 43 trades, +¥32,638 (+65%), Win 38.3%, PF 1.12, DD 46%

### V5 — First Attempt
- BodyStrengthMin=70, EMAPeriod=88, RSI(14), ATR SL/TP 1.5/3.0, LongBias=true
- 0 trades (zone loop bug: `for(i=1; i<=2; i++)` loop overwrites r[1] zones with r[2])
- Fixed: 21 trades, -¥1,108, PF 0.89, DD 11.5%

### V5_1 — Dynamic Bias + Bugfixes
- 8,281-pass opt (SL/ATR × TP/ATR): Pass #2465 — SL=3.6, TP=12.95
- +¥10,248 (20.5%), PF 1.633, DD 8.8%, 35 trades, Sharpe 5.52

### V5_2 — Applied Best Params
- SL=3.6, TP=12.95 (from V5_1 opt). Proven best.

### V6 — Original EA + Pass 54 Optimized Params (19,000+ pass opt)
- SlowMA=317, SL=10.09%, TP=71.2%, PartialTP=true(8.5%), LTF=true, BoS=47
- +¥13,055 (26.1%), PF 2.073, DD 13.3%, 8 trades (too few for statistical confidence)

### Institutional Sniper Series — ALL FAILED
- **V1:** 1 trade in 1yr (forming-bar bug: used `m15[0]` instead of `m15[1]`)
- **V1_1:** -16.4% (lot formula blew up to 0.10 lots, too many filters)
- **V2:** Losing (over-engineered: zone + BoS + RSI + candle confirm + spread + directional lock)

## Key Bugs Discovered

| Bug | Symptom | Fix |
|-----|---------|-----|
| **Forming bar vs completed bar** | Single trade then never re-enters | Use `m15[1]` (completed), not `m15[0]` (forming) for candle confirm |
| **Lot size blowup** | 0.10 lot on ¥50K account | Hard-cap at 0.03, use fixed 0.01 |
| **H4 MA vs M15 price** | Wrong scale comparison | Remove H4 filter from M15 logic |
| **Zone loop overwrite** | `for(i=1; i<=2; i++)` overwrites zones | Only check last completed H4 bar (r[1]) |
| **Zone width too tight** | Price never touches zone | 38.2% → 50-60% of range |
| **EMA slope deadband** | Strict `> 0` blocks all trades on flat EMA | Use `> -0.5` for longs, `< 0.5` for shorts |
| **WebView Platform not initialized** | `ERR_UNKNOWN_URL_SCHEME` / crash | Register `AndroidWebViewPlatform` in `main()` |
| **GoRouter + pushNamed** | Silent no-op navigation | Use `context.push()` not `Navigator.pushNamed()` |
| **2embed TV URL format** | Wrong URL for TV shows | Per-source URL builder: path vs query params |

## Key Platform Fixes

### Flutter WebView Crash
The error `WebViewPlatform.instance != null` occurs when webview_flutter's Android platform isn't registered. Fix:
```dart
import 'package:webview_flutter_android/webview_flutter_android.dart';
// In main(), before runApp:
if (Platform.isAndroid) {
  WebViewPlatform.instance = AndroidWebViewPlatform();
}
```
**Note:** class name is `AndroidWebViewPlatform`, not `WebAndroidViewPlatform`.

### Android 11+ Intent Filters
Apps targeting API 31+ need explicit `<queries>` declarations in AndroidManifest.xml for custom URL schemes:
```xml
<queries>
    <intent>
        <action android:name="android.intent.action.VIEW"/>
        <data android:scheme="magnet"/>
    </intent>
</queries>
```

### Embed Sites vs WebView
Free streaming embed sites (vidsrc.to, 2embed.cc) **cannot play video in a WebView** — they rely on `intent://` URL schemes and JavaScript popups that WebView blocks. They **must** be opened in a real browser (Chrome Custom Tabs with `LaunchMode.platformDefault` or `LaunchMode.externalApplication`).

### Torrent Streaming (v2.0.0+)
The OnStream app switched to torrent streaming via **The Pirate Bay API** (`apibay.org`):
- Query: `https://apibay.org/q.php?q={search}&cat=0`
- Response: JSON array with `name`, `seeders`, `leechers`, `info_hash`, `size`
- Magnet format: `magnet:?xt=urn:btih:{HASH}&dn={NAME}&tr=...` (uppercase hash from API)
- No auth required. Reliable, returns 100 results per query.
- Sorted by seeders descending (most popular first).

## Verification Workflow: MT5 Reinstall Restoration

After MT5 reinstall, restore EAs from GitHub repos:
1. Clone/download `.mq5` files from `decniner/MQLBestStrat`, `decniner/mql5`, etc.
2. Copy to `{TerminalInstance}/MQL5/Experts/DEN_EA/`
3. Convert UTF-8 to UTF-16LE: `iconv -f UTF-8 -t UTF-16LE`
4. The CLI compile (`MetaEditor64.exe /compile:`) **does not work** in non-interactive shell — it hangs waiting for GUI. Must compile from within MetaEditor (F7).
5. `.set` files must be UTF-16LE encoded. Use PowerShell: `[System.IO.File]::WriteAllText(path, content, [System.Text.Encoding]::Unicode)`
6. Rebuild `.set` files for each EA from scratch.
