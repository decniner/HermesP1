# OnStream Clone — Full Session Notes

## Architecture Evolution
- **v1.x (failed):** GoRouter + TMDb + embed sites (vidsrc.to, 2embed.cc) via WebView
- **v2.0.0 (current):** TMDb + TPB API (apibay.org) for torrent magnet links → external torrent client

## Key Bugs Found & Fixed
1. Navigator.pushNamed doesn't work with GoRouter — use context.push() instead
2. WebView platform must be initialized: WebViewPlatform.instance = AndroidWebViewPlatform()
3. ERR_UNKNOWN_URL_SCHEME — embed sites use intent:// URLs that WebView can't handle
4. TV URL format varies per embed source (paths vs query params) — use callbacks per source
5. AGP version must match package requirements (8.1.0 to 8.1.1 for webview_flutter)
6. Lambda in const list — closures can't be static const, use static final

## Embed Sources Tested (July 2026)
- vidsrc.to: Working (ads+popups)
- 2embed.cc: Working (redirects to partner)
- embed.su: Dead (domain for sale)
- vidlink.pro: Dead (404)
- multiembed.mov: Dead
- autoembed.cc: Dead
- moviesapi.club: Dead
- player.smashy.stream: Dead

## Torrent Streaming (v2.0.0)
- API: https://apibay.org/q.php?q={query}&cat=0 (TPB, no auth)
- Fields: name, seeders, leechers, size (bytes), info_hash
- Magnet: magnet:?xt=urn:btih:{hash}&dn={name}&tr=trackers
- Client: External torrent app (Flud, LibreTorrent recommended)
- Install guide: Launch Play Store if no torrent client detected

## APK Delivery
- Final method: GitHub Releases on HermesP1 repo (avoid tmpfiles.org - too many ads)
- Upload: Create release tag → upload APK with curl → delete old tag first
