# htmlpreview.github.io Limitations

Key constraints and workarounds when using htmlpreview to serve interactive HTML pages from GitHub.

## Inline Script Truncation

htmlpreview truncates inline `<script>` content at approximately **3,400 characters**. Scripts longer than this are cut off mid-content, causing runtime errors or silent failures.

**Fix:** Minify aggressively and stay under 3,400 chars. Also split JS across multiple lines (htmlpreview may also have per-line length limits).

## External Scripts via raw.githubusercontent.com

External `<script src="file.js">` references get rewritten by htmlpreview to point to `raw.githubusercontent.com`. However, that domain serves files with `Content-Type: text/plain`, which browsers block from executing as JavaScript. Result: external scripts silently fail to load.

**Fix:** Keep JavaScript inline and under the 3,400-char limit. Do NOT rely on external `.js` files when hosting through htmlpreview.

## Touch / Scrolling in Iframes

htmlpreview renders the page inside an iframe. Touch events (swipe, scroll) may not pass through properly. CSS-based scrollable containers (`overflow-x: auto`) may not respond to touch/swipe gestures.

**Fix:** Use JavaScript-based swipe detection (touchstart/touchmove/touchend + mousedown/mousemove/mouseup) instead of CSS overflow scrolling. Compute translateX transform manually based on touch deltas.

## Cache

htmlpreview aggressively caches. After pushing changes to GitHub, the old version may still be served. Force refresh or append a cache-busting query parameter.
