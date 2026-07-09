---
name: interactive-study-html
description: Build structured bilingual/interactive single-file HTML study tools with visibility toggles (language tracks, annotations, translations). Covers content generation to HTML compilation to GitHub deployment for mobile access.
category: creative
triggers:
  - user wants an interactive study or practice HTML page
  - compiling bilingual or multilingual content into a practice tool
  - language learning HTML with toggle-able romaji or translation tracks
  - Sensei and Pogi dual-role workflow
  - any request for an interactive single-file HTML that teaches
---

# Interactive Study HTML — Skill

Build interactive, single-file HTML study tools from structured educational content. This skill covers the **dual-role workflow**: one role generates structured pedagogical content, a second role compiles it into a responsive interactive HTML page.

## Workflow

### Phase 1 — Content Generation (e.g. "Sensei" role)
Generate structured content with **three parallel tracks** for every piece of text:

| Track | Purpose | CSS Class / Selector |
|-------|---------|---------------------|
| **Source (JP)** | Target language / primary content | `.jp` |
| **Phonetic (Romaji)** | Reading aid / pronunciation guide | `.romaji-line`, `.block-romaji` |
| **Translation (EN)** | Meaning / full translation | `.en`, `.block-en` |

**Content sections commonly included:**
- **Reference tables** — grammar rules, vocabulary, verb conjugations with columns for all 3 tracks
- **Dialogue scripts** — multi-line conversations, each line having JP + Romaji + EN
- **Document samples** — emails, reports, memos in full with all 3 tracks
- **Key insight boxes** — tips, bridge phrases, cultural notes (usually JP + EN only)

### Phase 2 — HTML Compilation (e.g. "Pogi" role)

**Toggle Bar (must-have):**
A sticky top bar with 3 toggle buttons controlling visibility of Romaji and English tracks:

| Button | CSS Class | Behavior |
|--------|-----------|----------|
| Show Japanese Only | `.jp-only` | Hides ALL non-Japanese content (both Romaji and English) — for pure reading practice |
| Toggle Romaji Track | `.romaji` | Shows/hides all `.romaji-line` / `.block-romaji` elements |
| Toggle English Track | `.english` | Shows/hides all `.en` / `.block-en` elements |

**State management pattern (JavaScript):**
```js
const state = { jpOnly: false, romaji: true, english: true };

function toggleMode(mode) {
  // jp-only: activate/deactivate, disable the other two visually
  // romaji/english: toggle class .hide-romaji / .hide-english on #main-content
  // status dots: update .on/.off classes
}
```

**Status indicator bar** beneath toggles showing live green/grey dots for each active track.

**CSS hiding classes:**
```css
.hide-romaji .romaji-line,
.hide-romaji .block-romaji,
.hide-romaji .romaji-info { display: none; }
.hide-english .en,
.hide-english .block-en { display: none; }
.jp-only-mode .romaji-line,
.jp-only-mode .block-romaji,
.jp-only-mode .romaji-info,
.jp-only-mode .en,
.jp-only-mode .block-en { display: none; }
```

**Design defaults (user preference):**
- Dark theme: `--bg: #1a1b2e; --card: #232540; --accent: #7c6df0` (purple)
- Romaji text: amber/warn color (`--warn: #ffa726`)
- English text: light blue (`--accent2: #4fc3f7`)
- Japanese text: off-white (`--text: #e8e8f0`)
- Sticky dark header with gradient

### Phase 3 — GitHub + Mobile Deployment
1. Create a **public GitHub repo** for the textbook/project (via GitHub API or git CLI)
2. Commit the HTML file and push to `main`
3. Generate the htmlpreview.github.io URL:
   `https://htmlpreview.github.io/?https://github.com/{user}/{repo}/blob/main/{filename}`
4. Deliver the URL to the user for mobile access

## User Preferences (Den Sanchez)
- Preferred stack: single-file HTML, no external dependencies
- Deployment: public GitHub repo + htmlpreview.github.io for phone access
- Workflow: generate content, compile, push, deliver URL
- Target audience: professional adult learners (IT/SRE context)

## Pitfalls

- **Redacted tokens**: GitHub tokens in git remote URLs get redacted by the output filter. Set the remote URL without embedding the token: `git remote set-url origin https://github.com/{user}/{repo}.git` — git uses the Windows Credential Manager automatically.
- **Branch name mismatch**: `git init` may create `master` not `main` — rename with `git branch -m master main` before pushing.
- **htmlpreview.github.io only works with public repos** — ensure the GitHub repo is `private: false`.
- **Content MUST be self-contained**: single HTML file with all CSS + JS inline — no CDN links that break offline.
- **Mobile-first**: test the toggle bar and tables at 640px viewport width; use `@media (max-width: 640px)` breakpoints.

## Related Skills
- `html-ebook-reader` — more about long-form publication-grade digital books with page-flip UI
