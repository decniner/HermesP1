# Building Visual Clones from Reference Images

When the user provides a reference image/screenshot of a UI they want cloned:

## Workflow

1. Use `vision_analyze` on the reference image to extract:
   - Color hex codes (cabinet, buttons, backgrounds, text)
   - Layout proportions (percentage-based, not pixel-based)
   - Symbol/icon details
   - Font styles and sizes
   - Button placement and labeling

2. Ask ONE clarifying question before coding:
   - "Which device/size should this fit first? (phone, desktop, both)"
   - If details are ambiguous, ask before guessing

3. Build the first version
4. QA immediately (do not skip)
5. If the user says "the X doesn't look right", use `vision_analyze` again to compare the real reference vs the current output, then adjust
6. Deliver file, then push to GitHub

## Session Examples

- **GOGO JUGGLER** (2026-07-05): User provided a KITAC cabinet screenshot. Initial build missed layout proportions and the GOGO lamp design. Required 3 iterations: first build → QA → user sent another reference → rebuilt → user asked to change reel stop mechanic → rebuilt again.
- **King Pulsar** (2026-07-05): User provided a Yamasa King Pulsar screenshot. Built from image alone. Had a JS syntax error (computed property bracket syntax) that caused a blank screen.
