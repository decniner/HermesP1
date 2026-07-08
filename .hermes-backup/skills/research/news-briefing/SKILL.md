---
name: news-briefing
description: "Fetch current news headlines from Japanese/global sources and produce a structured HTML report with ranked stories, category tags, and source attribution. Covers the full pipeline: source discovery, extraction via browser fallback, data compilation, HTML design, and local delivery."
version: 1.0.0
author: agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [news, headlines, briefing, japan, html, report, research, browser-fallback]
    related_skills: [web-research-profile, claude-design]
---

# News Briefing — HTML Report

Use this skill when the user asks you to fetch current news headlines (especially about Japan) and compile them into a formatted HTML report delivered locally.

## When To Use

- User says "Collate top 5 news headlines in Japan"
- User says "Give me a news briefing for today"
- User asks for an HTML report of current events
- User wants headlines from a specific region or country

## Primary Source: NHK WORLD-JAPAN

For Japan news, NHK World is the best first source. It's authoritative, free, and doesn't block automated access.

### Navigation Pattern

1. **Open the site**:
   `browser_navigate(url='https://www3.nhk.or.jp/nhkworld/en/news/')`

2. **Get all visible headlines**:
   `browser_vision(question='What are all the visible news headlines?')`
   This extracts headlines from the JS-rendered page — works even when accessibility tree is sparse.

3. **Switch to Japan-specific view** (if requested):
   The "Japan" nav link loads filtered Japan stories.

4. **Get article details**:
   Individual article URLs follow the pattern:
   `https://www3.nhk.or.jp/nhkworld/en/news/YYYYMMDD_NN/`
   Navigate to these and extract the article body from the snapshot.

### Fallback When web_search/web_extract Fails

Firecrawl billing issues can cause web_search and web_extract to fail with "Payment Required" or "Charge authorization failed". When this happens:

1. **Do NOT retry the failing tool** — it will fail again.
2. **Switch to browser tools immediately** — navigate directly to the news site.
3. **Use browser_vision for content extraction** — JS-heavy news sites render headlines visually even when the accessibility tree is empty. The vision tool captures all visible text.
4. **Use browser_navigate on article URLs** to get full story text from the page snapshot.

### Alternative Sources

If NHK is down or you need broader coverage:

| Source | URL | Notes |
|--------|-----|-------|
| Japan Times | japantimes.co.jp | English-language, paywall on some articles |
| BBC Asia | bbc.com/news/world/asia | Broader Asia coverage, may include Japan |
| Reuters Japan | reuters.com/world/japan | Quality wire service |
| Mainichi | mainichi.jp/english | Another major Japanese English paper |

## Compiling the Top 5

Curate from the full headline list. Criteria for ranking:

1. **Domestic significance** — stories that directly affect Japan (weather, politics, economy)
2. **Timeliness** — breaking or developing stories rank higher
3. **Impact** — stories with widespread effects (typhoons, policy changes)
4. **Human interest** — commemoration, cultural events

Avoid including non-Japan world news (e.g., unrelated Syria, Pakistan stories) unless the user asked for broader coverage.

## HTML Report Design

Build a single-file, dark-themed HTML page:

```
Structure:
+-- Header (title, date, source attribution)
+-- Headline cards (one per story, ranked #1-#5)
|   +-- Rank badge (#1, #2, etc.)
|   +-- Category tag (Weather, Infrastructure, etc.)
|   +-- Headline (h2)
|   +-- Summary paragraph (2-4 sentences)
|   +-- Location/topic tag
+-- Footer (generation timestamp, data source URL)
```

Design tokens (dark theme):
- Background: `#0f172a`
- Cards: `#1e293b` with `#3b82f6` left border
- Heading text: `#f1f5f9`
- Body text: `#cbd5e1`
- Muted text: `#64748b`
- Font: system sans-serif with Hiragino/Noto Sans JP fallback

Card layout (CSS):
```css
.headline-card {
  background: #1e293b;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.25rem;
  border-left: 4px solid #3b82f6;
}
```

## Delivery

On the CLI (no attachment channel), save the file and state the absolute path:
`C:\Users\decni\japan-top5-news-YYYYMMDD.html`

If the user also wants email delivery, use smtp-email to send the HTML as an attachment.

## Common Pitfalls

1. **Empty accessibility tree on JS-heavy sites** — NHK's news list is rendered client-side. The snapshot may show only navigation elements. Use browser_vision (screenshot) to extract visible headlines instead.
2. **Article URL guessing** — NHK uses sequential numeric IDs per day. Try `YYYYMMDD_NN` where NN = 01, 02, 03... If you get a 404, try the next number or check the Top Stories sidebar for working links.
3. **Terminal curl blocked** — The user may deny terminal curl commands for external fetches. Always use browser tools for web content by default on this setup.
4. **World news contamination** — NHK's "Top" page mixes Japan stories with international news. Filter to Japan-specific stories by clicking the "Japan" tab or manually curating based on story context.
5. **Date format** — NHK timestamps are relative ("8 hours ago"). Use the current date in the report header, not a parsed article date.
