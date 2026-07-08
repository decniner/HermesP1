---
name: web-app-demo-video
description: Create short demo/promo videos from web applications by capturing clean browser screenshots, assembling a slideshow with ffmpeg crossfade transitions, and adding TTS narration. Produces a shareable MP4 file.
trigger: User asks for a demo video, walkthrough, or promo of a working web app, single-file HTML game, or browser-based tool.
---

# Web App Demo Video

## Workflow Overview

1. **Serve the app publicly** if it's local (push to GitHub, use `htmlpreview.github.io`)
2. **Capture clean screenshots** via `browser_navigate` → `browser_vision`
3. **Create individual video clips** from each screenshot with ffmpeg
4. **Crossfade clips** together
5. **Generate TTS narration** with `text_to_speech`
6. **Merge audio and video** with proper fade-out
7. **Deliver the MP4** to the user for review

---

## Step 1: Make the App Accessible

If the app is a local file, it must be accessible from the cloud browser (Browserbase runs remotely):

- **GitHub + htmlpreview.github.io** (preferred): Push to GitHub, then use:
  ```
  https://htmlpreview.github.io/?https://github.com/USER/REPO/blob/main/PATH/FILE.html
  ```
- **NOT localhost**: The browser runs in the cloud and cannot reach your local server or `file://` paths.
- **NOT raw.githubusercontent.com**: Serves as plain text, not rendered HTML.

See `html-preview-deployment` skill for detailed patterns.

## Step 2: Capture Clean Screenshots

Quality matters. The user's feedback when screenshots are cluttered or the video looks rough is: **"Make sure it's professionally made."**

### Rules for professional screenshots:

| Rule | Why |
|------|-----|
| **One feature per screenshot** | Close all other windows/scenes before capturing each feature |
| **Clean desktop state** | No overlapping windows, no Start menu bleed-through unless that's the scene's subject |
| **Show app in action** | Click a few cells in Minesweeper, start the game, reveal some state — don't show a blank fresh state |
| **Full viewport** | Capture the entire desktop/window, not cropped |

### Screenshot capture steps:

```
browser_navigate(url="https://htmlpreview.github.io/?...")
# Wait for page to load
# Interact to set up the scene (open Start menu, launch app, trigger feature)
browser_vision(question="Describe what you want to capture clearly")
```

Save paths from `browser_vision` results (the `screenshot_path` field).

## Step 3: Create Video Clips from Screenshots

Use ffmpeg's `-loop 1 -i` input pattern (NOT the concat demuxer with image files — it is unreliable):

```bash
mkdir -p /path/to/video/scenes
cp screenshot1.png /path/to/video/scenes/01-desktop.png
cp screenshot2.png /path/to/video/scenes/02-menu.png
# ...

cd /path/to/video

# Create each clip
ffmpeg -y -loop 1 -i scenes/01-desktop.png -c:v libx264 -t 4.0 \
  -pix_fmt yuv420p -vf "scale=W:H" clip01.mp4 2>&1 | tail -1
```

### Duration guidelines per scene:

| Scene type | Duration |
|-----------|----------|
| Establishing shot / desktop | 4-5s |
| Menu / navigation | 3-4s |
| Game/app in action | 5-6s |
| Easter egg / finale | 4-5s |

### CRITICAL PITFALL: h.264 even dimensions

h.264 encoder requires **both width AND height to be even** (divisible by 2). Browser screenshots may have odd dimensions (e.g., 1264×625).

**Fix:** Add a scale filter to force even dimensions:
```bash
-vf "scale=1264:626"
```
The 1-pixel difference is imperceptible. Without this, ffmpeg fails silently with:
```
height not divisible by 2 (1264x625)
[libx264 @ ...] Error while opening encoder
```

## Step 4: Crossfade Clips Together

Use ffmpeg's `xfade` filter with sequential chaining:

```bash
ffmpeg -y \
  -i clip01.mp4 -i clip02.mp4 -i clip03.mp4 -i clip04.mp4 -i clip05.mp4 \
  -filter_complex "\
    [0]format=yuv420p[v0];\
    [1]format=yuv420p[v1];\
    [2]format=yuv420p[v2];\
    [3]format=yuv420p[v3];\
    [4]format=yuv420p[v4];\
    [v0][v1]xfade=transition=fade:duration=0.8:offset=OFFSET1[x01];\
    [x01][v2]xfade=transition=fade:duration=0.8:offset=OFFSET2[x02];\
    [x02][v3]xfade=transition=fade:duration=0.8:offset=OFFSET3[x03];\
    [x03][v4]xfade=transition=fade:duration=0.8:offset=OFFSET4[out]\
  " -map "[out]" -pix_fmt yuv420p slideshow.mp4
```

### Calculating xfade offsets:

Each `xfade=offset=X` means: start the crossfade at X seconds into the CURRENT accumulated timeline.

```python
# Given clips with durations [d1, d2, d3, d4, d5]:
total = d1 + d2 + d3 + d4 + d5 - (4 * transition_duration)
# Offset for transition from clip N:
offset_N = sum(d[0:N]) - (N * transition_duration)
```

Example with 0.8s transitions and durations [4.5, 4.0, 5.0, 5.0, 4.5]:
- Offset 1: 4.5 - 0.8 = 3.7
- Offset 2: 4.5 + 4.0 - 1.6 = 6.9
- Offset 3: 4.5 + 4.0 + 5.0 - 2.4 = 11.1
- Offset 4: 4.5 + 4.0 + 5.0 + 5.0 - 3.2 = 15.3

## Step 5: Generate TTS Narration

Use `text_to_speech` for voiceover:

```python
text_to_speech(
    text="Professional narration describing each scene...",
    output_path="/path/to/narration.mp3"
)
```

### Narration script guidelines:

| The video is ~Xs | The narration should be... |
|-----------------|---------------------------|
| Under 15s | ~12-14s (tight, punchy) |
| 15-30s | ~match video length |
| Over 30s | ~match or slightly shorter |

**ALWAYS check the audio duration** after generation — this is a hard gate before merging:

```bash
# Linux/MSYS:
ffmpeg -y -i narration.mp3 -f null - 2>&1 | grep -oP "time=\K[0-9:.]+" | tail -1

# Windows PowerShell / Python fallback if ffprobe fails:
python -c "import subprocess; r=subprocess.run(['ffprobe','-v','quiet','-show_format','narration.mp3'],capture_output=True,text=True); print(r.stderr)"
```

**⚠️ First-generation TTS often runs 2-3x longer than expected.** A script that reads naturally at conversation pace may produce 30-40s of audio for a video that's only 15-20s. The correct fix is to write a tighter, faster-paced script — do not extend the video to match the first TTS generation.

Iteration pattern when audio is too long:
```text
1st try: 30-40s narration → Check duration → Too long
2nd try: Cut script in half, remove filler words → Check → Still 22s
3rd try: Tight, punchy bullet-point style → Check → ~18s ✅
```

If audio is still slightly longer than video:
- **Regenerate with a shorter script** (preferred — keeps the video concise)
- If extending video: add 1-2s to each clip's duration and recalculate xfade offsets
- Use `afade` with `-shortest` to fade out early only when duration mismatch is < 2s (catching a trailing millisecond, not cutting off a sentence)

## Step 6: Merge Audio with Video

```bash
ffmpeg -y -i slideshow.mp4 -i narration.mp3 \
  -filter_complex "\
    [1:a]volume=1.5[a1];\
    [a1]afade=t=out:st=VIDEO_LENGTH-2:d=2[audio]\
  " \
  -map 0:v:0 -map "[audio]" -c:v copy -c:a aac -shortest \
  Win95_Demo_Final.mp4
```

Parameters explained:
- `volume=1.5` — boost TTS volume (it's usually quiet)
- `afade=t=out:st=TOTAL-2:d=2` — fade audio over last 2 seconds
- `-shortest` — trim audio to match video duration
- `c:v copy` — no re-encode of video (lossless)
- `c:a aac` — encode audio stream

## Step 7: Deliver for Review

Copy the final file to the user's project directory and deliver via MEDIA: tag:

```bash
cp /path/to/video/Demo_Final.mp4 /path/to/project/Demo_Final.mp4
```

Then in your response:
```
MEDIA:C:\Users\USER\projects\APPNAME\Demo_Final.mp4
```

**⚠️ MEDIA: tag platform caveat:** On some messaging platforms (Discord, Telegram), the MEDIA: tag may render as visible path text rather than an actual inline video player. If the user says "send the actual video, not the path" or "it's not playing here", the MEDIA: tag is not being rendered as an attachment on that platform. Try:
- Sending the MEDIA: tag again in a fresh response (sometimes the rendering is a one-time glitch)
- If it persistently shows as text, tell the user the exact file path so they can locate and upload it manually
- Platform-specific rendering is outside the agent's control — do not claim the file was delivered if the user cannot see it

Always ask for review before declaring done. The user may want:
- Different screenshots
- Different timing per scene
- Different narration tone
- More/less scenes

## Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| h.264 odd dimensions | `height not divisible by 2` | `-vf "scale=W:H+1"` to make even |
| Browser cloud vs local | 404 on localhost | Push to GitHub, use htmlpreview |
| Audio too long | Narration cut off mid-sentence | Check audio duration, write shorter script, or extend video |
| Concat demuxer unreliable | `Impossible to open` / `Nothing was written` | Use `-loop 1 -i` per-image approach instead |
| Cluttered screenshots | User says "unprofessional" | One feature per screenshot, close other windows |
| Overlapping windows | Hard to see the feature | Close all apps first, then launch only what you're capturing |
| MSYS path issues on Windows | `No such file or directory` on paths that exist | Use `C:\Windows\style` paths in quotes, not `/c/` paths for ffmpeg inputs |
