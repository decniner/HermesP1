---
name: flutter-mobile-development
description: Build Flutter/Android mobile apps — navigation, WebView, video playback, build troubleshooting, and common platform pitfalls.
category: software-development
tags:
  - flutter
  - android
  - dart
  - webview
  - gorouter
  - build
version: 1.0.0
triggers:
  - "build / fix a Flutter mobile app"
  - "debug a Flutter APK build"
  - "implement video / WebView in Flutter"
  - "handle navigation / routing in Flutter"
  - "troubleshoot Android manifest or gradle"
---

# Flutter Mobile Development

## Navigation: GoRouter vs Navigator

**CRITICAL RULE:** If the app uses `GoRouter` (via `MaterialApp.router`), **all navigation must use GoRouter's API** — not the classic `Navigator` API.

| DO | DON'T |
|----|-------|
| `context.push('/detail/movie/550')` | `Navigator.pushNamed(context, '/detail/movie/550')` |
| `context.go('/')` | `Navigator.pop(context)` |
| `context.push('/player/movie/550/0/0')` | `Navigator.push(context, MaterialPageRoute(...))` |

**Why:** GoRouter registers routes with its own Router, not with Flutter's built-in Navigator. `Navigator.pushNamed()` silently does nothing (no route found → no-op). The app just freezes — no error, no crash, no navigation.

**Fix:** Every file that calls navigation must:
1. Import `package:go_router/go_router.dart`
2. Use `context.push()`, `context.go()`, or `context.replace()` from GoRouter

**Common victims:**
- Detail screens with "Watch Now" buttons
- Search results that open detail pages
- Player screens with back navigation
- Auth/logout flows

The error *"nothing happens when I tap the button"* + debug console shows no errors = almost certainly `Navigator.pushNamed` instead of `context.push`.

## WebView: Platform Initialization Required

The `webview_flutter` package requires explicit platform registration before first use. Without it, the app crashes immediately when navigating to a WebView screen:

```
WebViewPlatform.instance != null:
A platform implementation for webview_flutter has not been set.
```

**Fix in `main()`:**

```dart
import 'dart:io' show Platform;
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:webview_flutter_platform_interface/webview_flutter_platform_interface.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (Platform.isAndroid) {
    WebViewPlatform.instance = AndroidWebViewPlatform();
  }
  // ... rest of app setup
}
```

**Class name:** `AndroidWebViewPlatform` (NOT `WebAndroidViewPlatform` — that class doesn't exist).

**Package requirement:** `webview_flutter_android: ^4.0.0` in pubspec.yaml (separate from `webview_flutter`).

## Gradle / Android Build Issues

### WebView requires AGP 8.1.1+

When adding `webview_flutter`, gradle may fail with:
```
Dependency 'androidx.webkit:webkit:1.14.0' requires Android Gradle plugin 8.1.1 or higher.
```

**Fix:** Update AGP in `android/settings.gradle`:
```gradle
plugins {
    id "com.android.application" version "8.1.1" apply false  // was 8.1.0
    id "org.jetbrains.kotlin.android" version "1.8.22" apply false
}
```

### AndroidX must be enabled

If gradle fails with "contains AndroidX dependencies but `android.useAndroidX` is not enabled", add to `android/gradle.properties`:
```properties
android.useAndroidX=true
android.enableJetifier=true
```

### Android 11+ magnet:// URI queries

When using `url_launcher` to open `magnet:` URIs (torrents), add a `<queries>` entry to `AndroidManifest.xml`:
```xml
<queries>
    <intent>
        <action android:name="android.intent.action.VIEW"/>
        <data android:scheme="magnet"/>
    </intent>
</queries>
```

Without this, `launchUrl(Uri.parse('magnet:?...'))` returns `false` silently on Android 11+. Nothing visible happens — no error, no dialog.

### WebView Manifest Requirements

WebView embed sites (vidsrc.to, etc.) load content over mixed HTTP/HTTPS. Enable cleartext traffic:
```xml
<application
    android:usesCleartextTraffic="true"
    ...>
```

## Video Embeds: WebView is the Wrong Tool

Embed sites like vidsrc.to, 2embed.cc, and similar **do not work reliably in Android WebView**. They rely on:
- `intent://` URL scheme redirects (WebView can't handle)
- Cross-origin iframe navigation
- JavaScript popups for ad layers
- Canvas-based DRM video rendering

**net::ERR_UNKNOWN_URL_SCHEME** is the expected error — the embed page loaded, but it tried to redirect to an `intent://` URL that only a real browser can handle.

### The Fix: Use Chrome Custom Tabs

Replace WebView with `url_launcher` using `LaunchMode.platformDefault`:
```dart
import 'package:url_launcher/url_launcher.dart';

void openEmbedUrl(String url) {
  launchUrl(Uri.parse(url), mode: LaunchMode.platformDefault);
  // On Android: opens in Chrome Custom Tabs (overlays app, back button returns)
  // On iOS: opens in Safari
}
```

Chrome Custom Tabs:
- Shows the embed site in a browser tab **inside the app** (not a full browser switch)
- Handles ALL URL schemes correctly
- Supports full JavaScript, popups, DRM video
- User taps back → returns to the app

### Per-Source URL Format

Different embed sources use different URL formats for TV shows. **Each source must be handled individually:**

| Source | Movie URL | TV URL |
|--------|-----------|--------|
| vidsrc.to | `/embed/movie/ID` | `/embed/tv/ID/SEASON/EPISODE` (path segments) |
| 2embed.cc | `/embed/tmdb/movie?id=ID` | `/embed/tmdb/tv?id=ID&s=SEASON&e=EPISODE` (query params) |

**Wrong:** Appending `&s=1&e=1` to all TV URLs (vidsrc.to uses path segments).
**Fix:** Use a per-source URL builder function (not a single template string).

```dart
// Per-source approach
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

### WebView Use Cases That Do Work

WebView is still appropriate for:
- Loading local HTML content (charts, reports)
- Embedding iframe-based widgets that don't use `intent://` redirects
- OAuth login flows (well-defined redirect URIs)

## Torrent Streaming in Android Apps

### The Pirate Bay API (apibay.org)

For querying torrents without scraping:
```http
GET https://apibay.org/q.php?q=SEARCH_TERM&cat=0
```

Response: JSON array of torrents with `name`, `seeders`, `leechers`, `size`, `info_hash`.

Magnet URI format:
```
magnet:?xt=urn:btih:INFO_HASH&dn=URLENCODED_NAME&tr=udp://tracker.opentrackr.org:1337/announce&tr=...
```

### Android Manifest for magnet: URIs

Must add `<queries>` entry for Android 11+ (see section above).

### Torrent Client Required

Android doesn't have a built-in torrent handler. The app must:
1. Try `launchUrl(magnetUri, LaunchMode.externalApplication)` 
2. If it returns `false`, show a dialog to install a client
3. Recommended: Flud (`com.delphicoder.flud`) — supports sequential streaming

## OnStream App Architecture (Reference)

The OnStream app built in this session uses:
- **GoRouter** for navigation (splash → home → detail → player)
- **Material Design 3 dark theme** with deep blue background (#0A0E27) and purple accent (#6C63FF)
- **TMDb API** for movie/TV metadata and posters
- **The Pirate Bay API** for torrent search (replaced unreliable embed sites)
- **url_launcher** for playing magnet links in external torrent client
- **SQLite (sqflite)** for favorites and local storage
- **No auth required** — splash screen goes directly to home screen
