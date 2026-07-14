# Multi-Region News Sources Reference

## 🇯🇵 JAPAN

| Source | URL | Browser Access | Notes | RSS |
|--------|-----|----------------|-------|-----|
| **Kyodo News** | english.kyodonews.net | ✅ Full accessibility tree | **Preferred** — headlines and summaries visible in browser snapshot, no vision needed | ❌ |
| NHK World | www3.nhk.or.jp/nhkworld/en/news/ | ⚠️ Sparse tree; use browser_vision | JS-heavy; vision tool needed for headline extraction | ✅ (Japanese RSS: `https://www3.nhk.or.jp/rss/news/cat0.xml`) |
| **Japan Today** | japantoday.com | ✅ General access | Curl-friendly English headlines; simple `<h[1-6]>` grep works | ❌ |
| Japan Times | japantimes.co.jp | ⚠️ Paywall on some articles | Good for in-depth Japan analysis | ❌ |
| Mainichi | mainichi.jp/english | ✅ General access | Major Japanese English daily | ❌ |
| Asahi (Asia & Japan Watch) | asahi.com/ajw/ | ✅ General access | Liberal-leaning English edition | ❌ |

## 🇵🇭 PHILIPPINES

| Source | URL | Browser Access | Notes | RSS |
|--------|-----|----------------|-------|-----|
| **Rappler** | rappler.com (use `/latest/` for richest feed) | ✅ Full accessibility tree | **Preferred** — investigative journalism, impeachment coverage | ❌ |
| PhilStar | philstar.com | ✅ General access | Major English broadsheet | ✅ (`https://www.philstar.com/rss/headlines`) |
| Inquirer | inquirer.net | ✅ General access | Largest Philippine daily; curl-friendly | ❌ (limited) |
| ABS-CBN News | news.abs-cbn.com | ✅ General access | Broadcast network | ❌ |
| GMA News | gmanetwork.com/news | ✅ General access | Broadcast network | ❌ |
| Manila Bulletin | mb.com.ph | ✅ General access | Oldest English newspaper | ❌ |

## 🌍 GLOBAL

| Source | URL | Browser Access | Notes | RSS |
|--------|-----|----------------|-------|-----|
| **BBC News** | bbc.com/news (use `/world` for non-UK global) | ✅ Full content in tree | **Preferred** — no CAPTCHA, good formatting | ✅ (`https://feeds.bbci.co.uk/news/world/rss.xml`) |
| AP News | apnews.com | ✅ General access | Wire service, neutral tone | ❌ |
| Al Jazeera | aljazeera.com | ✅ General access | Good for Middle East / global South | ❌ |
| Reuters | reuters.com/world | ❌ DataDome CAPTCHA | **Avoid** — blocked by bot detection | ❌ |
| The Guardian | theguardian.com/international | ✅ General access | UK-based, global coverage | ✅ |
| DW (Deutsche Welle) | dw.com/en | ✅ General access | German international broadcaster | ❌ |
| France 24 | france24.com/en | ✅ General access | French international broadcaster | ❌ |

## ⚠️ Bot Detection Risk

| Risk Level | Source | Behavior |
|-----------|--------|----------|
| ❌ High | Reuters | DataDome CAPTCHA on reuters.com/world |
| ⚠️ Medium | Some Japan Times routes | May hit paywall after N articles |
| ✅ Low | BBC, Kyodo, Rappler, PhilStar, AP | Reliable browser access |

## Fallback Chain (when Firecrawl is down)

```
web_search / web_extract
    ↓ FAIL (Payment Required / billing error)
RSS feeds via curl (Tier 0 — cleanest, see SKILL.md)
    ↓ FAIL (no RSS available)
Terminal curl on HTML (Tier 1 — faster than browser, see curl-extraction-patterns.md)
    ↓ FAIL (JS-rendered, CAPTCHA, or empty)
browser_navigate to known source URL
    ↓ Read browser_snapshot
    ↓ Fall back to browser_vision if tree is empty
```

- **Japan fallback chain**: Japan Today (curl ✅) → Kyodo (curl ✅) → NHK RSS (Japanese) → NHK (browser/vision) → Mainichi
- **PH fallback chain**: Rappler (browser ✅) → Inquirer (curl ✅) → PhilStar (RSS ✅)
- **Global fallback chain**: BBC RSS (cleanest) → BBC (browser) → AP (browser) → Al Jazeera

## Article Detail URLs

Most news sites use standard paths for individual articles:
- **BBC**: bbc.com/news/articles/[slug]
- **Kyodo**: english.kyodonews.net/news/YYYY/MM/[hash].html
- **Rappler**: rappler.com/[category]/[slug]/
- **AP**: apnews.com/article/[hash]
- **Japan Today**: japantoday.com/category/[category]/[slug]
- **Inquirer**: newsinfo.inquirer.net/[id]/[slug]
