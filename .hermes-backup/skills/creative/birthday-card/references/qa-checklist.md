# Birthday Card QA Checklist

Use this checklist when validating a birthday card after building or editing it. Run through each section systematically — the card touches multiple subsystems (audio, animation, layout, assets) that can break independently.

## Prerequisites

```bash
# Start a local HTTP server in the card directory (required for audio, images)
cd path/to/birthday-card/
python -m http.server 8128
```

Always serve via HTTP — `file://` URLs block audio playback in modern browsers.

---

## 1. Asset Verification

Check every asset file before looking at the rendered page:

| Check | Command / Method |
|---|---|
| Photo file exists | `file angel-photo.jpeg` → should report JPEG dimensions |
| Photo is valid JPEG | Confirm "JPEG image data, JFIF standard" in `file` output |
| Audio file exists | `file birthday-music.mp3` → should report MPEG layer III |
| Audio is real MP3, not placeholder | Confirm "MPEG ADTS, layer III" in `file` output — 0-byte or ~1KB files are synthesized dummies |
| Audio serves correctly | `curl -s -o /dev/null -w "%{http_code}, %{content_type}, %{size_download}" http://127.0.0.1:8128/birthday-music.mp3` → expect `200, audio/mpeg, >50000 bytes` |
| Photo serves correctly | Same curl check for `angel-photo.jpeg` → expect `200, image/jpeg` |

## 2. Console & JavaScript

Open the card in the browser and immediately check:

- **No JS errors**: `browser_console()` should return `"total_errors": 0`
- **No audio errors**: Audio load failures appear as non-fatal MediaError in console. If the audio file serves correctly (step 1), this shouldn't happen.
- **Intended log messages**: e.g., a "🎂 Happy Birthday!" console greeting is fine

## 3. Front Cover Inspection

Use `browser_vision(annotate=true)` to check:

- [ ] Background gradient renders (pink/soft tones)
- [ ] All text elements visible: recipient name, "Birthday", decorative lines
- [ ] Photo appears in the circular frame (not broken image icon)
- [ ] Gold sparkle dots are present and twinkling
- [ ] "tap to open" hint visible at bottom
- [ ] Music toggle button visible in corner
- [ ] No layout shifts or misaligned elements

## 4. Card Flip — Inside Message

Click the card (use `browser_click` on the card element), then after a ~1.5s delay for the animation:

- [ ] Card visibly flips with 3D perspective rotation
- [ ] Inside message animates in (fade + scale-up)
- [ ] All text fully visible — no clipping, no overflow past card borders
- [ ] Check specifically that bottom text (signature) isn't cut off
- [ ] Decorative borders and inside decorations visible
- [ ] Balloon emojis float upward inside the card
- [ ] Confetti pieces burst and fall from top of screen (`position: fixed`)
- [ ] Floating hearts/sparkles/flowers animate in the background

### Visual confirmation technique

Ask `browser_vision` specifically:
> "Is any text touching or being cut by the card borders? Look at all four edges carefully."

If text is clipped, the card-inside's `overflow: hidden` is too aggressive — reduce padding or shrink font sizes via media queries.

## 5. Responsive Layout

The card uses two media queries:
- `@media (max-width: 420px)` — smaller phone screens
- `@media (max-height: 600px)` — short viewports (landscape phones)

To test these, you can't easily resize in the browser tool. Instead, inspect the CSS directly:

```bash
# In the HTML, check these responsive rules are present:
# @media (max-width: 420px) — scales card from 360x520 → 300x460
# @media (max-height: 600px) — reduces height 520 → 380
```

If the message text is long (especially a multi-line sentence like "Wishing a very happy birthday to the woman who..."), verify it won't overflow on small screens by checking:
- Body text font size reduces to 14-15px on small screens
- Line height reduces to 1.5 on short screens
- Card container has `overflow: hidden` to contain the flip animation cleanly

## 6. Audio Playback

Audio is created via JS `new Audio()` (not an `<audio>` tag in DOM), so it won't appear in `document.querySelectorAll('audio')`.

Verify audio plays:
1. Click the card to open it → music should auto-start
2. Click the music toggle button → music should pause
3. Click again → music should resume
4. Check that `audioEl` uses the real MP3 path, not a Web Audio oscillator

## 7. htmlpreview Validation (CRITICAL)

**Always test through the actual htmlpreview URL that the user will use**, not just the local server. The local server and htmlpreview behave differently:

- **Local server** (`http://127.0.0.1:8128/`): All JS runs fully, no truncation, all click handlers work, audio plays
- **htmlpreview** (`https://htmlpreview.github.io/?https://github.com/...`): Inline scripts over ~3,400 chars are silently truncated, external script.js files don't load (MIME type blocked), audio may be sandbox-restricted

**This was learned the hard way this session** — a subagent tested the card on localhost and reported "no issues found," but the user reported it didn't work. The inline JS was 42 chars over htmlpreview's 3,400-char limit, so the carousel swipe handlers were silently dropped.

### Test flow:
1. Push changes to GitHub first
2. Open the htmlpreview URL for the card
3. Wait for the page to fully load (htmlpreview renders twice — initial load then re-renders in its own frame)
4. Click the card to open it
5. Check if the card actually flips open (JS test: `document.querySelector('.card').className` should contain "open")
6. Check the console for errors
7. If the card doesn't open or JS isn't running, the inline script was truncated — minify further

### Common htmlpreview failure modes:

| Symptom | Likely Cause | Fix |
|---|---|---|
| Card front renders but doesn't flip when tapped | Inline JS truncated — click handler code missing | Minify script to under 3,400 chars |
| No confetti / no music / no floating hearts | JS truncated before those functions | Minify further or remove dead code |
| Photo loads but audio doesn't play | Audio play() blocked by sandbox, or script truncated before Audio element creation | Ensure audio.play() is inside click/tap handler |
| External script.js has `len=0` in console | htmlpreview rewrote src to raw.githubusercontent.com → wrong MIME type | Inline ALL JS — external scripts are blocked |
| "subagent said it works" but user says it doesn't | Subagent tested locally (full JS) instead of through htmlpreview (truncated JS) | ALWAYS test through the actual htmlpreview URL |

### htmlpreview variable confirmation trick

After opening the card in htmlpreview, check if the JS is running:
```javascript
// Run this in browser_console:
try { typeof sC !== 'undefined' ? 'JS running: YES' : 'JS running: NO - truncated!' } catch(e) { 'JS error: ' + e.message; }
```

### htmlpreview JS truncation diagnosis

If the card doesn't respond to taps in htmlpreview:

1. **Check total script length** — if over ~3,400 chars, it WILL be truncated
   ```javascript
   // In browser console on the htmlpreview page:
   let sc = document.querySelectorAll('script'), last = '';
   sc.forEach(s => { if (s.textContent.includes('yourFunctionName')) last = s.textContent; });
   'Script length: ' + last.length;
   ```
2. **Check if script ends correctly** — truncated scripts cut off mid-expression
   ```javascript
   last.substring(last.length - 80);  // Should be valid JS ending (like `})();`)
   ```
3. **Check the ending pattern** — if you see extra `}})` brackets, the script was both truncated AND incorrectly reconstructed by htmlpreview's DOM injection

**HISTORICAL BUG:** This session's card had the script at 3,442 chars (42 over the 3,400 limit). The truncation caused:
- Carousel swipe handlers never registered
- `go(0)` init call never ran (transform stayed empty)
- Event listeners for touch/mouse events never attached
- Card appeared to open via CSS but no JS functionality worked
- The trimmed ending `'carousel-dot active':'carousel-dot'}})}})();` had 4 extra brackets from the truncation

## 8. Swipeable Carousel (if present)

- [ ] Swipe horizontally to scroll through messages
- [ ] Each slide snaps cleanly into view (scroll-snap)
- [ ] Navigation dots update to reflect current slide
- [ ] Tapping inside the carousel does NOT close the card (stopPropagation)
- [ ] ✕ close button closes the card
- [ ] Swiping backward (right to left) works correctly
- [ ] All slides are reachable (no stuck at first/last slide)

## 9. Common Pitfalls

| Problem | Likely Cause | Fix |
|---|---|---|
| Broken image icon on front | Photo path wrong or file missing | Check `src` attribute matches actual filename |
| Audio won't play | Browser blocks autoplay without user gesture | Audio.play() must be in a click/tap handler |
| Audio plays but no sound | Wrong file format or corrupt MP3 | Verify with `file` command, re-encode with ffmpeg |
| Text cut off at bottom | Card-inside `overflow: hidden` clips long content | Reduce padding, shrink font sizes, or set `overflow-y: auto` |
| No confetti visible | Confetti timeout may have expired (default: 5s cleanup) | Re-open the card and screenshot immediately |
| No balloons visible | Balloons may be above the card's visible area | Balloons animate from +80px to -220px translateY — ensure card height is enough |
| Music button not spinning | Missing the `note-spin` animation class | Ensure `.music-btn:not(.muted) .note-icon` has the animation rule |
| Card doesn't open / no JS runs via htmlpreview | Inline script truncated by htmlpreview's ~3,400 char limit | Minify the inline JS to fit under the limit, or enable GitHub Pages |
| Card works locally but not when shared | Relative paths broken by htmlpreview's DOM injection | All assets must be in the same directory; use relative `src="file.mp3"` paths |
| External `script.js` doesn't load via htmlpreview | htmlpreview rewrites src to raw.githubusercontent.com → wrong MIME type | Inline all JS instead of using `<script src="...">` |
| Audio doesn't play through htmlpreview | htmlpreview sandbox may block autoplay, or script truncated | Trigger audio in a click handler; keep inline JS under 3,400 chars |
| Subagent reports "all good" but user reports broken | Subagent tests via local server where JS runs fully; htmlpreview truncates | Add a new QA step: deploy and test via htmlpreview before marking done |
| Swiping carousel accidentally closes the card | Touch events bubble up to card-container's click handler | Add stopPropagation on carousel track touchstart and click events |
| Close button not visible | Needs `.card.open` ancestor to show | Ensure close button is inside `.card-inside` and has `.card.open .close-btn { opacity: 1; }` |
