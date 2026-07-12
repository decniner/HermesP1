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

## See Also

- `references/onstream-clone-session.md` — Complete session notes: video embed sources tested, WebView debugging steps, search implementation details.

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
