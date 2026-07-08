# Win95 Desktop Simulator Demo — Session Reference

## Context
Built a demo video for a Windows 95 desktop simulator HTML app (single file, served via htmlpreview.github.io). Two iterations: V1 (12.6s, cluttered screenshots) rejected as "cut off" and "not professional"; V2 (19.8s, clean screenshots, proper narration) was the final deliverable.

## URL
```
https://htmlpreview.github.io/?https://github.com/decniner/HermesP1/blob/main/win95/Win95.html
```

## V1 (Rejected) — What Went Wrong
- **Cluttered screenshots**: Multiple windows overlapping in each shot (My Computer + Solitaire + Minesweeper all visible at once)
- **Too short**: 12.6s felt rushed
- **Narration synced poorly**: First TTS was 38s for 12.6s video → audio got abruptly cut off
- **Concat demuxer failed**: Had to switch from concat demuxer to `-loop 1 -i` per-clip approach

## V2 (Delivered) — Correct Approach

### Screenshots Captured (clean, one feature per shot)
1. Clean desktop (teal bg, My Computer + Recycle Bin icons, taskbar — no windows open)
2. Start menu open (showing Minesweeper, Solitaire, Space Invaders '86, Shut Down — no other windows)
3. Minesweeper in progress (3 cells clicked via browser_click, timer started)
4. Space Invaders '86 title screen (SCORE: 0000, LIVES: 3, WAVE: 1 — no other windows visible)
5. BSOD / Fatal Exception 0E error screen (full screen)

### Clip Durations
| Scene | Duration | Crossfade offset |
|-------|----------|-----------------|
| Desktop | 4.5s | 3.7s |
| Start Menu | 4.0s | 6.9s |
| Minesweeper | 5.0s | 11.1s |
| Space Invaders | 5.0s | 15.3s |
| BSOD | 4.5s | — |

Total video: ~19.8s (with 4 × 0.8s crossfades)

### Narration Script
"The Windows 95 Desktop Simulator recreates the classic OS in your browser. Click Start for Minesweeper, Solitaire, and Space Invaders. Play Minesweeper with the classic nine by nine grid. Blast aliens in Space Invaders 86 with full touch support. And yes — the Blue Screen of Death easter egg is included. Try it at the link below."

Duration: ~22s → faded out with 2s afade at `st=18`, trimmed with `-shortest`

### Key ffmpeg Commands Used

#### Create clip from screenshot:
```bash
ffmpeg -y -loop 1 -i scenes/00-desktop.png -c:v libx264 -t 4.5 \
  -pix_fmt yuv420p -vf "scale=1264:626" clip00.mp4
```

#### Crossfade 5 clips:
```bash
ffmpeg -y \
  -i clip00.mp4 -i clip01.mp4 -i clip02.mp4 -i clip03.mp4 -i clip04.mp4 \
  -filter_complex "\
    [0]format=yuv420p[v0];\
    [1]format=yuv420p[v1];\
    [2]format=yuv420p[v2];\
    [3]format=yuv420p[v3];\
    [4]format=yuv420p[v4];\
    [v0][v1]xfade=transition=fade:duration=0.8:offset=3.7[x01];\
    [x01][v2]xfade=transition=fade:duration=0.8:offset=6.9[x02];\
    [x02][v3]xfade=transition=fade:duration=0.8:offset=11.1[x03];\
    [x03][v4]xfade=transition=fade:duration=0.8:offset=15.3[out]\
  " -map "[out]" -pix_fmt yuv420p slideshow.mp4
```

#### Merge audio:
```bash
ffmpeg -y -i slideshow.mp4 -i narration.mp3 \
  -filter_complex "[1:a]volume=1.5[a1];[a1]afade=t=out:st=18:d=2[audio]" \
  -map 0:v:0 -map "[audio]" -c:v copy -c:a aac -shortest \
  Win95_Demo_V2.mp4
```

## User Quality Feedback
- **V1 feedback**: "It seems cut off. Make sure its professionally made."
- **Root causes**:
  - Cluttered screenshots (multiple windows overlapping — hard to see individual features)
  - Video too short (12.6s for 5 scenes)
  - Narration cut off (38s audio on 12.6s video)
- **V2 fixes**:
  - Clean screenshots: close other windows between each capture
  - Longer per-scene timing (3.5s → 4-5s)
  - Tight narration script (38s → 22s → matched better)
  - Smooth audio fade-out at video end
  - Professional voiceover via TTS

## MEDIA: Tag Delivery Issue
On Discord, the `MEDIA:` tag sometimes renders as visible path text rather than an inline video player attachment. The user repeatedly said "send the actual video, not the path" and "it's not playing here." The file exists at the specified path but the platform did not render it as an attachment. This is a platform rendering limitation — not a file creation failure.
