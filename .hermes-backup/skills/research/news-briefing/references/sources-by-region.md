# Multi-Region News Sources Reference

## 🇯🇵 JAPAN

| Source | URL | Browser Access | Notes |
|--------|-----|----------------|-------|
| **Kyodo News** | english.kyodonews.net | ✅ Full accessibility tree | **Preferred** — headlines and summaries visible in browser snapshot, no vision needed |
| NHK World | www3.nhk.or.jp/nhkworld/en/news/ | ⚠️ Sparse tree; use browser_vision | JS-heavy; vision tool needed for headline extraction |
| Japan Times | japantimes.co.jp | ⚠️ Paywall on some articles | Good for in-depth Japan analysis |
| Mainichi | mainichi.jp/english | ✅ General access | Major Japanese English daily |
| Asahi (Asia & Japan Watch) | asahi.com/ajw/ | ✅ General access | Liberal-leaning English edition |

## 🇵🇭 PHILIPPINES

| Source | URL | Browser Access | Notes |
|--------|-----|----------------|-------|
| **Rappler** | rappler.com | ✅ Full accessibility tree | **Preferred** — investigative journalism, impeachment coverage |
| PhilStar | philstar.com | ✅ General access | Major English broadsheet |
| Inquirer | inquirer.net | ✅ General access | Largest Philippine daily |
| ABS-CBN News | news.abs-cbn.com | ✅ General access | Broadcast network |
| GMA News | gmanetwork.com/news | ✅ General access | Broadcast network |
| Manila Bulletin | mb.com.ph | ✅ General access | Oldest English newspaper |

## 🌍 GLOBAL

| Source | URL | Browser Access | Notes |
|--------|-----|----------------|-------|
| **BBC News** | bbc.com/news | ✅ Full content in tree | **Preferred** — no CAPTCHA, good formatting |
| AP News | apnews.com | ✅ General access | Wire service, neutral tone |
| Al Jazeera | aljazeera.com | ✅ General access | Good for Middle East / global South |
| Reuters | reuters.com/world | ❌ DataDome CAPTCHA | **Avoid** — blocked by bot detection |
| The Guardian | theguardian.com/international | ✅ General access | UK-based, global coverage |
| DW (Deutsche Welle) | dw.com/en | ✅ General access | German international broadcaster |
| France 24 | france24.com/en | ✅ General access | French international broadcaster |

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
Terminal curl (faster — see curl-extraction-patterns.md)
    ↓ FAIL (JS-rendered, CAPTCHA, or empty)
browser_navigate to known source URL
    ↓ Read browser_snapshot
    ↓ Fall back to browser_vision if tree is empty
```

- **Japan fallback chain**: Kyodo (curl ✅) → NHK (browser/vision) → Mainichi
- **PH fallback chain**: Rappler (curl partial) → Inquirer (curl ✅) → PhilStar (curl ✅)
- **Global fallback chain**: BBC (curl ✅) → AP (browser) → Al Jazeera

## Article Detail URLs

Most news sites use standard paths for individual articles:
- **BBC**: bbc.com/news/articles/[slug]
- **Kyodo**: english.kyodonews.net/news/YYYY/MM/[hash].html
- **Rappler**: rappler.com/[category]/[slug]/
- **AP**: apnews.com/article/[hash]
