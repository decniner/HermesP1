---
name: news-briefing
description: "Fetch current news headlines from Japan, Philippines, and global sources and produce a structured digest (plain-text or HTML). Covers the full pipeline: source discovery, extraction via browser fallback, multi-region compilation, output formatting, and delivery."
version: 1.2.0
author: agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [news, headlines, briefing, japan, philippines, html, digest, report, research, browser-fallback, cron]
    related_skills: [web-research-profile, claude-design]
---

# News Briefing — Multi-Region Digest / HTML Report

Use this skill when the user asks you to fetch current news headlines — from Japan, the Philippines, or globally — and compile them into a structured digest. Supports both plain-text (for CLI/delivery channels) and HTML (for rich local files) output formats.

## When To Use

- User says "Collate top 5 news headlines in Japan"
- User says "Give me a news briefing for today"
- User says "Daily news digest from Japan, Philippines, and world"
- User asks for an HTML report of current events
- User wants headlines from a specific region or country
- User asks for a cron job that delivers a news briefing automatically

## Primary Sources

### 🇯🇵 Japan: Kyodo News (preferred for browser extraction)

Kyodo News loads its full content into the accessibility tree — no screenshot/vision needed. Use this as the first Japan source.

**Navigation Pattern:**

1. **Open the site**:
   `browser_navigate(url='https://english.kyodonews.net/')`

2. **Read headlines directly from the snapshot**:
   The accessibility tree contains full article headings, summaries, and links. Use `browser_snapshot()` after navigation — no vision call needed.

3. **Get article details**:
   Each article heading is a clickable link (`ref=eNN`). Click to navigate, then read the article body from the snapshot.

4. **Scroll for more**:
   If you need more stories than the initial view, use `browser_scroll(direction='down')` then `browser_snapshot()`.

### 🇯🇵 Japan: NHK WORLD-JAPAN

NHK World is authoritative and free but JS-heavy — the accessibility tree is often sparse.

**Navigation Pattern** (when Kyodo is unavailable):

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

#### Tier 1: Terminal curl (preferred — faster than browser)

Many news sites serve headlines and metadata in server-rendered HTML that curl can extract directly, bypassing both Firecrawl and the browser overhead entirely.

**Basic pattern:**
```bash
# Fetch the homepage and grep for headlines
curl -sL --max-time 15 "https://english.kyodonews.net/" | grep -oP '<h[23][^>]*>.*?</h[23]>' | sed 's/<[^>]*>//g' | head -30

# Extract article-level summaries from meta tags
curl -sL --max-time 10 "https://english.kyodonews.net/articles/-/79598" | \
  grep -oP '<meta[^>]*name="description"[^>]*content="[^"]*"' | \
  sed 's/<meta name="description" content="//;s/"//'
```

**Working grep selectors per source (see `references/curl-extraction-patterns.md`):**
| Source | Headline selector | Summary selector |
|--------|-------------------|------------------|
| Kyodo News | `<h[23][^>]*>.*?</h[23]>` | `<meta name="description"` |
| BBC News | `<h2[^>]*data-testid="card-headline"[^>]*>.*?</h2>` | `<meta name="description"` |
| Inquirer.net | `<h[1-4][^>]*>.*?</h[1-4]>` | `<meta name="description"` or `og:description` |
| PhilStar | `<h[1-4][^>]*>.*?</h[1-4]>` | `<meta name="description"` |
| AP News | JS-heavy — curl not useful | Use browser or BBC instead |

**Meta-tag trick for article summaries:**
After finding headlines, open each article URL with curl and extract its `<meta name="description" content="...">` or `<meta property="og:description" content="...">` for a ready-made 1-2 sentence summary — no full-page parsing needed.

**Caveat:** Reuters (reuters.com) blocks curl with a CAPTCHA wall. BBC and AP work fine.

#### Tier 2: Browser fallback (when curl is blocked or the site is JS-only)

If curl returns only `<script>` tags, empty content, or a CAPTCHA wall:

1. **Switch to browser tools** — navigate directly to the news site.
2. **Use browser_vision for content extraction** — JS-heavy news sites render headlines visually even when the accessibility tree is empty. The vision tool captures all visible text.
3. **Use browser_navigate on article URLs** to get full story text from the page snapshot.

Sources that require browser (JS-rendered): NHK World, Reuters, AP News headline pages.

### Alternative Sources

If Kyodo and NHK are down or you need broader coverage:

| Source | URL | Notes |
|--------|-----|-------|
| Japan Times | japantimes.co.jp | English-language, paywall on some articles |
| Mainichi | mainichi.jp/english | Another major Japanese English paper |

### 🇵🇭 Philippines: Rappler (preferred)

Rappler loads headlines and summaries into the accessibility tree — no vision needed.

**Navigation Pattern:**

1. **Open the site**:
   `browser_navigate(url='https://www.rappler.com/')`

2. **Read headlines from snapshot**:
   The accessibility tree shows article headings with category links, summaries, and timestamps. Scroll for more stories.

3. **Get article details**:
   Click article links (visible as `ref=eNN` in the snapshot) to navigate to full articles.

**Alternative PH sources:**
| Source | URL | Notes |
|--------|-----|-------|
| PhilStar | philstar.com | Major English-language broadsheet |
| Inquirer | inquirer.net | Largest Philippine daily |

### 🌍 Global: BBC News

BBC News loads well via browser. It has a CAPTCHA wall on reuters.com, so prefer BBC.

**Navigation Pattern:**

1. **Open the site**:
   `browser_navigate(url='https://www.bbc.com/news')`

2. **Scroll and snapshot**:
   The top section contains the lead story and 5-7 secondary headlines. Scroll down and call `browser_snapshot()` to reveal more articles.

3. **Read full articles**:
   Click any headline link in the snapshot to navigate to the article page.

**Note on Reuters:** reuters.com/world hits a DataDome CAPTCHA via the browser tool. Avoid using Reuters; use BBC or AP instead.

**Alternative global sources:**
| Source | URL | Notes |
|--------|-----|-------|
| AP News | apnews.com | Associated Press, free |
| Al Jazeera | aljazeera.com | Good for Middle East / global South coverage |

## Multi-Region Workflow

When the user asks for a digest covering multiple countries/regions (e.g., Japan, Philippines, and World):

1. **Parallel browsing**: Navigate to each source in sequence, gathering headlines from each. Independent sources don't depend on each other, so batch the work.
2. **Extract region-by-region**: Note which headlines belong to which region. BBC's World section may include Asia stories — attribute them appropriately.
3. **Compile section-by-section**: Build the digest with clear section headers per region.
4. **Rank within each section**: Apply the curation criteria independently per region. The top Japan story and top PH story are determined within their respective sections.

## Compiling the Top 5 (per region)

Curate from the full headline list. Criteria for ranking:

1. **Domestic significance** — stories that directly affect the country (weather, politics, economy)
2. **Timeliness** — breaking or developing stories rank higher
3. **Impact** — stories with widespread effects (typhoons, policy changes)
4. **Human interest** — commemoration, cultural events

Avoid including unrelated world news in a single-region briefing. For multi-region digests, keep stories within their correct regional section.

---

## Output Formats

### Option A: Plain-Text Digest (for CLI / cron delivery)

Use this when the user wants the output in their chat/delivery channel (not a file). Template:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📰 DAILY NEWS DIGEST
📅 [Date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🇯🇵 JAPAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. [Headline]
   Summary: [2-3 sentence summary]
   Source: [URL]

(3-6 headlines per section)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🇵🇭 PHILIPPINES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

(3-6 headlines, same format)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌍 GLOBAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

(3-6 headlines, same format)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 TOP STORY: [highlight the most significant story of the day]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Option B: HTML Report

Build a single-file, dark-themed HTML page (use when user asks for a report or HTML specifically):

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

### Plain-text digest (cron / CLI delivery):
When running as a cron job, just output the plain-text digest as your final response — the system delivers it automatically. No file save needed.

### HTML report (explicit request):
On the CLI (no attachment channel), save the file and state the absolute path:
`C:\Users\decni\news-briefing-YYYYMMDD.html`

If the user also wants email delivery, use smtp-email to send the HTML as an attachment.

## References

See `references/sources-by-region.md` for a comprehensive multi-region news source reference table with URL patterns, accessibility notes, and bot-handling behavior.
See `references/curl-extraction-patterns.md` for source-specific curl+grep selectors and batch-summary workflows when Firecrawl is unavailable.

## Common Pitfalls

1. **Empty accessibility tree on JS-heavy sites** — NHK's news list is rendered client-side. The snapshot may show only navigation elements. Use browser_vision (screenshot) to extract visible headlines instead. **Prefer Kyodo News** for Japan — it loads its full content into the accessibility tree.
2. **Article URL guessing** — NHK uses sequential numeric IDs per day. Try `YYYYMMDD_NN` where NN = 01, 02, 03... If you get a 404, try the next number or check the Top Stories sidebar for working links.
3. **Terminal curl blocked** — The user may deny terminal curl commands for external fetches. Always use browser tools for web content by default on this setup.
4. **Reuters CAPTCHA** — reuters.com hits a DataDome CAPTCHA via the browser tool. Do not use Reuters. Use BBC News (bbc.com/news) for global coverage instead.
5. **Date handling** — News site timestamps are often relative ("8 hours ago"). Use the current date in the report header. For cron jobs, use the actual run date.
6. **Firecrawl billing exhaustion** — web_search and web_extract may fail with "Payment Required" / "Charge authorization failed". Do NOT retry — switch immediately to terminal curl on known news URLs, or to browser_navigate as a second fallback. See the "Fallback" section above for the two-tier fallback chain.
7. **curl timeout** — Some news sites are slow (BBC, Inquirer). Always set `--max-time 10` to 15 seconds per URL. Batch article-summary fetches in a single terminal call using a loop for speed.
8. **Multi-article summary gathering** — When you have 5+ article URLs from the same domain, batch them in a single terminal call: `for url in ...; do curl ...; done`. This is much faster than reading each article individually.
7. **Multi-region attribution** — BBC's World section includes Asia stories that overlap with Japan/PH coverage. Attribute stories to the correct regional section in your digest.
8. **Cron job silence** — If a cron news briefing finds nothing new to report, respond with exactly `[SILENT]` and nothing else to suppress empty deliveries.
