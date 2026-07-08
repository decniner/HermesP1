---
name: screenshot-demo-video
description: Create narrated slideshow demo videos from browser screenshots when real-time screen recording is unavailable. Uses browser_vision screenshots, ffmpeg slideshow with crossfade transitions, and TTS voiceover narration.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [video, demo, ffmpeg, screenshots, slideshow, tts]
    related_skills: [html-preview-deployment, retro-arcade-game-development]
---

# Screenshot Demo Video

Create short narrated walkthrough videos of web apps by stitching together browser screenshots with ffmpeg. This is the primary technique when real-time screen recording is unavailable — the browser_vision tool captures high-quality stills, and ffmpeg assembles them into a polished video with crossfades and voiceover.

## When to Use

- User wants a demo video of a web app / HTML artifact you built
- Screen recording tools are unavailable (browser runs in cloud)
- The app is interactive and you need to show multiple features in sequence
- You have browser_vision and ffmpeg available

## Workflow Overview

```
1. Deploy app to public URL (GitHub + htmlpreview.github.io)
2. Capture screenshots of each feature with browser_vision
3. Create video clips from screenshots with ffmpeg (even dimensions!)
4. Concatenate with crossfade transitions (xfade filter)
5. Generate TTS voiceover narration
6. Merge audio track with video
7. Deliver via MEDIA: path
```

## Step-by-Step

### Step 1: Deploy the App to a Public URL

The cloud browser cannot access `localhost` or `file://` paths. You must deploy the HTML artifact to a publicly accessible URL first.

**Pattern (GitHub + htmlpreview.github.io):**

```bash
cd /path/to/project
git add my-app.html
git commit -m "Add app"
git push origin main
```

Then navigate the cloud browser to:

```
https://htmlpreview.github.io/?https://github.com/USER/REPO/blob/main/path/to/file.html
```

See the `html-preview-deployment` skill for detailed deployment pitfalls (script truncation, asset paths, MIME types).

### Step 2: Capture Screenshots

Navigate to the deployed URL with `browser_navigate`, then use `browser_vision` to take screenshots of each feature. Click interactive elements between captures to show different states.

```javascript
browser_navigate(url)
// Take screenshot of initial state
browser_vision(question="Show the full desktop with My Computer window open")
// Click to open menus / launch features
browser_click(ref="@e3")  // Click Start button
// Take next screenshot
browser_vision(question="Show the Start menu with all items")
```

**Tips:**
- Use `browser_snapshot` between clicks to find the correct ref IDs for interactive elements
- Use `browser_vision(annotate=true)` to see numbered ref labels on the page
- Save at least 4-5 screenshots covering the key features
- Copy screenshots from cache to a working directory with numbered names

### Step 3: Create Video Clips from Screenshots

Convert each screenshot to a short MP4 clip using ffmpeg:

```bash
ffmpeg -y -loop 1 -i 01_desktop.png \
  -c:v libx264 -t 3.5 -pix_fmt yuv420p \
  -vf "scale=WIDTH:EVEN_HEIGHT" \
  clip1.mp4
```

**⚠️ CRITICAL: h.264 requires even dimensions.** Both width and height must be even numbers (divisible by 2). An odd height like 625 will fail silently with "height not divisible by 2" — always add a scale or pad filter to make dimensions even.

```bash
# If source is 1264x625, scale to 1264x626:
-vf "scale=1264:626"
```

**Typical durations per scene:**
| Scene type | Duration |
|------------|----------|
| Title / intro | 3s |
| Feature overview | 3.5s |
| Gameplay / interactive demo | 4s |
| End screen / easter egg | 3.5s |

### Step 4: Concatenate with Crossfade Transitions

Create individual clips (one per screenshot), then use the `xfade` filter for smooth transitions:

```bash
ffmpeg -y \
  -i clip1.mp4 -i clip2.mp4 -i clip3.mp4 -i clip4.mp4 -i clip5.mp4 \
  -filter_complex "\
    [0]format=yuv420p[v0];\
    [1]format=yuv420p[v1];\
    [2]format=yuv420p[v2];\
    [3]format=yuv420p[v3];\
    [4]format=yuv420p[v4];\
    [v0][v1]xfade=transition=fade:duration=0.8:offset=2.7[x01];\
    [x01][v2]xfade=transition=fade:duration=0.8:offset=5.4[x02];\
    [x02][v3]xfade=transition=fade:duration=0.8:offset=8.6[x03];\
    [x03][v4]xfade=transition=fade:duration=0.8:offset=12.8[out]\
  " -map "[out]" -pix_fmt yuv420p slideshow.mp4
```

**Offset calculation:** Each xfade offset = sum of previous clip durations minus the fade duration. E.g., with clips lasting 3.5, 3.5, 4.0, 4.0, 3.5s and fade duration 0.8s:
- offset 2.7 = 3.5 - 0.8
- offset 5.4 = 3.5 + 3.5 - 0.8 - 0.8 = 5.4
- offset 8.6 = 3.5 + 3.5 + 4.0 - 0.8 - 0.8 - 0.8 = 8.6
- offset 12.8 = 3.5 + 3.5 + 4.0 + 4.0 - 0.8 - 0.8 - 0.8 - 0.8 = 12.6 (round to 12.8)

### Step 5: Generate TTS Voiceover Narration

Use the `text_to_speech` tool to generate narration audio:

```
text_to_speech(text="Your narration script here...", output_path="narration.mp3")
```

**Script timing:** Keep the total narration to match the video length (typically 12-18 seconds for a 5-scene demo). Describe what each scene shows in sequence.

### Step 6: Merge Audio with Video

```bash
ffmpeg -y -i slideshow.mp3 -i narration.mp3 \
  -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest \
  Final_Demo_Narrated.mp4
```

**Notes:**
- Use `-shortest` to trim audio to video length (or vice versa)
- Use `-c:a aac` for YouTube-compatible audio codec
- Use Windows-native paths (backslashes) in MSYS/bash to avoid path resolution issues

### Step 7: Deliver the Video

Copy the final file to a convenient location and deliver via MEDIA: path:

```bash
cp video/Final_Demo_Narrated.mp4 project_folder/Final_Demo_Narrated.mp4
```

Then include `MEDIA:/absolute/path/to/video.mp4` in your response on Discord-compatible platforms.

## YouTube Upload

This toolchain cannot upload directly to YouTube — YouTube requires OAuth 2.0 authentication (interactive browser login flow). Two alternatives:

**A) User uploads manually:** Provide clear instructions:
1. Go to youtube.com/upload
2. Drag the MP4 file
3. Paste a pre-written title and description with the app link

**B) Browser automation:** If the user is already logged into YouTube in the browser session, you can navigate to youtube.com/upload and interact with the upload UI via browser tools. However, the HTML file upload dialog typically requires native OS file picker interaction which browser automation cannot handle.

## Pitfalls

1. **h.264 even dimensions** — Always verify even width AND height. Odd values cause silent failure. Add a `scale` or `pad` filter to fix.
2. **Browser runs in cloud** — Cannot access `localhost`, `file://`, or `127.0.0.1`. Must deploy to public URL first.
3. **ffmpeg concat demuxer format** — The last entry in a concat file must NOT have a `duration` line (ffmpeg uses the file's natural duration for the last entry).
4. **MSYS path resolution** — On Windows/MSYS2, paths like `/c/Users/...` may not work in all ffmpeg commands. Use Windows-native paths (`C:\Users\...`) when `-i` arguments fail.
5. **TTS timing mismatch** — If narration is longer than video, the video loops its last frame. Use `-shortest` to clip to video length, or extend the last clip duration.
6. **Snapshot ref IDs change** — After clicking elements, the DOM changes and previous ref IDs may no longer work. Take a fresh `browser_snapshot` after each interaction.
7. **Concat filter with image files** — The `ffmpeg concat demuxer` with `.png` files fails if the file's format can't be probed. Convert images to clips first (Step 3), then concat the clips (Step 4).
8. **Fontconfig errors on Windows** — ffmpeg's `drawtext` filter requires fontconfig which may not be configured on Windows. Avoid `drawtext` for titles; use an HTML title screen and screenshot it instead.
