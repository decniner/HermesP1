---
name: flutter-app-development
description: Build, debug, and deploy Flutter mobile apps — project setup, navigation, WebView/media integration, Android config, and caching patterns.
category: software-development
triggers:
  - "build a Flutter app"
  - "create a mobile app for Android"
  - "debug a Flutter app"
  - "embed video player in Flutter"
  - "WebView not working / ERR_UNKNOWN_URL_SCHEME"
  - "GoRouter navigation not working"
  - "add search with caching to Flutter app"
version: 1.0.0
---
# Flutter / Android App Development

## Core Patterns

### 1. Navigation: Use GoRouter, Not Navigator.pushNamed

If the app uses `MaterialApp.router` with GoRouter, **every** navigation must use GoRouter's `context.push()` or `context.go()`. The classic `Navigator.pushNamed()` operates on a separate Navigator stack that has no routes registered.

**Bug symptom:** Tapping a button that should navigate does nothing — no error, no crash, no log.

**Files to check:**
- `app.dart` — where routes are defined with `GoRoute`
- Any screen with `Navigator.pushNamed(...)` — replace with `context.push(...)`
- Missing `import 'package:go_router/go_router.dart'`

**Before:**
```dart
onTap: () => Navigator.pushNamed(context, '/detail/${item.type}/${item.id}'),
```

**After:**
```dart
onTap: () => context.push('/detail/${item.type}/${item.id}'),
```

### 2. WebView Platform Must Be Initialized

`webview_flutter` 4.x requires explicit platform registration before first use. Without it, the app crashes with:

```
WebViewPlatform.instance != null
A platform implementation for webview_flutter has not been set.
```

**Fix in `main.dart`:**
```dart
import 'dart:io' show Platform;
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:webview_flutter_platform_interface/webview_flutter_platform_interface.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  if (Platform.isAndroid) {
    WebViewPlatform.instance = AndroidWebViewPlatform();
  }
  runApp(const MyApp());
}
```

The class name is `AndroidWebViewPlatform` (NOT `WebAndroidViewPlatform` — that class doesn't exist).

### 3. WebView + Video Embed Sites Don't Mix

Video embed sites (vidsrc.to, 2embed.cc, embed.su, etc.) rely on **custom URL schemes** (`intent://`, `custom://`) that Android WebView cannot handle. The error surfaced is:

```
net::ERR_UNKNOWN_URL_SCHEME  (Error: -10)
```

**These sites require a real browser.** Attempting in-app WebView will always fail for streams protected by `intent://` redirects, DRM, cross-origin iframes, or JS popups.

**Solutions (in order of reliability):**

| Approach | Result |
|----------|--------|
| ❌ WebView (webview_flutter) | Always fails for commercial embed sites |
| ✅ Chrome Custom Tabs (url_launcher `platformDefault`) | Opens in Chrome overlay — handles all URL schemes, feels in-app |
| ✅ External browser (`LaunchMode.externalApplication`) | Opens full browser — most reliable |

**Implementation with url_launcher:**
```dart
import 'package:url_launcher/url_launcher.dart';

// Opens in Chrome Custom Tabs (Android) — overlays the app
await launchUrl(Uri.parse(url), mode: LaunchMode.platformDefault);

// Opens in full external browser
await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
```

### 4. AndroidManifest Configuration for WebView

If you do use WebView, the Android manifest needs:
```xml
<uses-permission android:name="android.permission.INTERNET"/>
<application
    android:usesCleartextTraffic="true"
    ...>
```

Cleartext traffic is needed for HTTP embed sources that video sites proxy through.

### 5. Search Caching Pattern

For instant search results, implement an in-memory cache with debounce:

```dart
class _SearchState extends State<SearchWidget> {
  final Map<String, List<Result>> _cache = {};
  Timer? _deb;

  void _onChanged(String q) {
    _deb?.cancel();
    final trimmed = q.trim();
    if (trimmed.isEmpty) { setState(() => _results = null); return; }

    // Check cache first — instant response
    if (_cache.containsKey(trimmed)) {
      setState(() => _results = _cache[trimmed]);
      return;
    }

    // Debounce then fetch
    _deb = Timer(const Duration(milliseconds: 200), () async {
      final r = await fetchResults(trimmed);
      _cache[trimmed] = r;  // Store for next time
      if (mounted) setState(() => _results = r);
    });
  }
}
```

Also preload trending/popular results so the search page shows content immediately when opened.

### 6. Version Display Pattern

Show version on the Profile/Settings page:
```dart
Text('AppName v1.0.0', style: TextStyle(fontSize: 12, color: Colors.grey[600]))
```

Keep the version number in `pubspec.yaml`'s `version:` field as the single source of truth.

## Per-Source URL Format (Embed Sites)

**Critical finding:** Different embed sources use **different URL formats** for the same content type (TV shows). Applying a single template to all sources breaks TV playback.

| Source | Movie URL | TV URL |
|--------|-----------|--------|
| vidsrc.to | `/embed/movie/ID` | `/embed/tv/ID/SEASON/EPISODE` (path segments) |
| 2embed.cc | `/embed/tmdb/movie?id=ID` | `/embed/tmdb/tv?id=ID&s=SEASON&e=EPISODE` (query params) |

**Wrong approach:** A single string template with query params appended:
```dart
final tvUrl = src.tvUrl + id.toString();
return '$tvUrl&s=$season&e=$episode';  // BROKEN for vidsrc.to (uses paths)
```

**Right approach:** Per-source URL builder function:
```dart
class _Source {
  final String name;
  final String movieUrl;
  final String Function(int id, int s, int e) tvUrl;
}

static final _sources = [
  _Source(
    name: 'vidsrc.to',
    movieUrl: 'https://vidsrc.to/embed/movie/',
    tvUrl: (id, s, e) => 'https://vidsrc.to/embed/tv/$id/$s/$e',
  ),
  _Source(
    name: '2embed.cc',
    movieUrl: 'https://www.2embed.cc/embed/tmdb/movie?id=',
    tvUrl: (id, s, e) => 'https://www.2embed.cc/embed/tmdb/tv?id=$id&s=$s&e=$e',
  ),
];
```

**Note:** Lambdas/closures can't be in `static const` lists. Use `static final` instead:
```dart
static final _sources = [...];  // NOT static const
```

## DOM Cleanup Bug: Orphaned Function Calls

When removing an HTML element (e.g., replacing a history card with a chart), **all JavaScript function calls that reference that element must also be removed or null-checked**.

**Bug symptom:** After analysis completes, the app crashes with:
```
Cannot set properties of null (setting 'innerHTML')
```

**Root cause:** `renderHistory(data)` (still called from analyzeVideo) calls `document.getElementById('historyContainer')` which no longer exists in the DOM.

**Fix:** Remove or null-guard the function call alongside the DOM element removal. Search for ALL references to the deleted element's ID across the entire script.

## Backend API: Column Mapping Off-by-One

When building a `/history` endpoint that returns SQLite data, **verify column indices match the `SELECT` order**, not the table schema order.

**Bug symptom:** History endpoint returns wrong data in fields (e.g., `overall_score` contains technique ratings JSON string instead of integer score).

**Root cause:** SQL `SELECT` reorders columns, but endpoint code uses old index positions:
```python
# SQL: SELECT date, video_url, overall_score, technique_ratings, ...
#      row[0]      row[1]    row[2]        row[3]

# WRONG mapping: rows[3] gets technique_ratings, not overall_score
sessions.append({
    "overall_score": row[3],
})

# RIGHT mapping - match SELECT order left to right:
sessions.append({
    "session_order": row[0],    # date
    "video_url": row[1],        # video_url
    "overall_score": row[2],    # overall_score
    "technique_ratings": row[3], # technique_ratings
})
```

**Fix:** Count columns left to right in your SELECT statement. Index 0 = first column.

## Android Gradle Issues

### AGP Version Mismatch

When adding packages that require newer Android Gradle Plugin:
```
Dependency 'androidx.webkit:webkit:X.Y.Z' requires Android Gradle plugin 8.1.1 or higher.
```

**Fix** in `android/settings.gradle`:
```groovy
id "com.android.application" version "8.1.1" apply false
```

Update from 8.1.0 → 8.1.1 is safe and fixes webview/webkit dependency conflicts.

### java.io.tmpdir / Hermes Sandbox Issue

When building in restricted environments (like Hermes), Gradle may fail with:
```
java.io.IOException: java.io.tmpdir is set to a directory that doesn't exist
```

**Fix** in `android/gradle.properties`:
```properties
org.gradle.jvmargs=-Djava.io.tmpdir=/tmp
```

This overrides the sandbox's incorrect tmpdir path.

## Debug Logging Pattern

Add an in-app debug log viewer for flows that are hard to test (WebView, video playback, API calls):

```dart
final List<String> _logs = [];
void _log(String msg) { _logs.add(msg); debugPrint(msg); }

// Show logs in a bottom sheet
void _showDebugLog(BuildContext context) {
  showModalBottomSheet(context: context, builder: (_) =>
    Column(children: _logs.map((l) => Text(l, style: TextStyle(fontSize: 10, fontFamily: 'monospace'))).toList()));
}
```

## Pitfalls

### `flutter pub get` Fails in Sandbox → Use `dart pub get`

In restricted environments (Hermes, CI), `flutter pub get` fails with `.hermes-tmp` creation errors. **Run `dart pub get` directly instead** — it works in the same project without the Flutter tool's sandbox interference. After it resolves, `flutter build apk` works normally.

Set `PUB_CACHE=/tmp/pub-cache` and `TMPDIR=/tmp` before running.

### Java 17 Required for Android SDK Tools

`sdkmanager` needs Java 17+. Install via `winget install EclipseAdoptium.Temurin.17.JDK` or portable download. Set `JAVA_HOME` with no trailing space (use `&&` not `;`).

## See Also

- `references/onstream-clone-session.md` — Complete session notes: video embed sources tested, WebView debugging steps, search implementation details.
- `references/flutter-windows-setup.md` — Full Windows setup guide: Flutter SDK install, Java 17, Android cmdline-tools, SDK components, common pitfalls.

## Torrent Streaming Architecture

When embed sites prove unreliable (dead domains, aggressive ads, broken WebView compat), torrent streaming via magnet links is the fallback.

### API: The Pirate Bay

TPB has a free, open JSON API at `apibay.org` that requires no auth:

```
https://apibay.org/q.php?q={query}&cat=0
```

Returns JSON array with `name`, `seeders`, `leechers`, `size` (bytes), `info_hash`. Items with `id == "0"` mean no results.

### Magnet Link Construction

```dart
String makeMagnet(String hash, String name) {
  const tr = '&tr=udp://tracker.opentrackr.org:1337/announce'
      '&tr=udp://tracker.coppersurfer.tk:6969/announce'
      '&tr=udp://tracker.leechers-paradise.org:6969/announce';
  return 'magnet:?xt=urn:btih:$hash&dn=${Uri.encodeComponent(name)}$tr';
}
```

### Playing Magnets on Android

Android does not handle magnet: URLs natively. Open magnet links externally via `launchUrl(magnetUri, mode: LaunchMode.externalApplication)`. If that fails, guide the user to install a torrent client (Flud, LibreTorrent) via Play Store.

### Architecture Decision

When embed sites fail: Phase 1 (WebView with vidsrc.to/2embed.cc) → Phase 2 (TPB API + magnet links to external torrent client). Bump major version (1.x → 2.0.0) on this architectural pivot.

### Result Display

Show quality, title, size, seeds/peers in a compact Card+ListTile. Sort by seeds descending, pull title from TMDb API for the search query.

### Android 11+ Manifest: Custom URL Schemes (Critical)

Android 11+ requires apps to **declare** what URL schemes they want to open via `<queries>` in `AndroidManifest.xml`. Without this, `launchUrl()` for custom schemes like `magnet:` silently returns `false` and nothing happens.

**Symptom:** The user sees the torrent list, taps a result, and **nothing happens** — no error, no dialog, no crash. The `launchUrl` call completes but returns `false`.

**Fix in `android/app/src/main/AndroidManifest.xml`:**
```xml
<queries>
    <intent>
        <action android:name="android.intent.action.VIEW"/>
        <data android:scheme="magnet"/>
    </intent>
    <intent>
        <action android:name="android.intent.action.VIEW"/>
        <data android:scheme="intent"/>
    </intent>
</queries>
```

**Common schemes to declare:** `magnet` (torrent streaming), `intent` (app redirects), `market` (Play Store links).

**Diagnosis when `launchUrl` fails silently:** Check if the scheme needs `<queries>` declaration for Android 11+. Test with `launchUrl(uri, mode: LaunchMode.externalApplication)` and check the returned boolean. If false, show an install/fallback dialog instead of failing silently.
