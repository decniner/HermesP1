# Curl Extraction Patterns for News Sources

When Firecrawl is unavailable (billing exhaustion), use `curl` via terminal to extract headlines and article summaries directly from news sites. This is faster than the browser and works for most major sources.

## Quick-Reference Table

| Source | Homepage | Headline Pattern | Summary Pattern | JS-rendered? |
|--------|----------|-----------------|-----------------|--------------|
| Kyodo News | english.kyodonews.net | `<h[23][^>]*>.*?</h[23]>` or `.top-news-main__ttl` | `<meta name="description"` or `og:description` | No |
| Inquirer | inquirer.net | `<h[1-4][^>]*>.*?</h[1-4]>` | `<meta name="description"` or `og:description` | No |
| PhilStar | philstar.com | `<h[1-4][^>]*>.*?</h[1-4]>` | `<meta name="description"` | No |
| BBC News | bbc.com/news | `<h2[^>]*data-testid="card-headline"[^>]*>.*?</h2>` | `<meta name="description"` | Partial |
| Rappler | rappler.com | `<h[23][^>]*>.*?</h[23]>` (limited) | `og:description` | Partial |
| NHK World | www3.nhk.or.jp/nhkworld/en/news/ | ❌ JS-rendered — use browser_vision | ❌ | Yes |
| AP News | apnews.com | ❌ JS-rendered | ❌ | Yes |
| Reuters | reuters.com/world | ❌ CAPTCHA-blocked | ❌ | Yes (blocked) |

## RSS Feed Extraction (Tier 0 — cleanest)

See the SKILL.md "Tier 0: RSS Feeds via curl" section for the full guide and common grep patterns. Key commands:

**BBC World RSS:**
```bash
curl -sL --max-time 10 "https://feeds.bbci.co.uk/news/world/rss.xml" | \
  grep -oP '<title><![CDATA[[^\]]+]]></title>' | \
  sed 's/<title><!\[CDATA\[//;s/\]\]><\/title>//' | head -15
```

**PhilStar RSS:**
```bash
curl -sL --max-time 10 "https://www.philstar.com/rss/headlines" | \
  grep -oP '<title>[^<]+</title>' | sed 's/<title>//;s/<\/title>//' | tail -n +2 | head -15
```

**NHK Japanese RSS (translation needed):**
```bash
curl -sL --max-time 10 "https://www3.nhk.or.jp/rss/news/cat0.xml"
# Extract Japanese headlines and descriptions
grep -oP '(?<=<title>)[^<]+|(?<=<description>)[^<]+' | head -20
```

## 🇯🇵 Japan Today

**Headlines from homepage (curl-friendly):**
```bash
curl -sL --max-time 15 "https://japantoday.com/" | \
  grep -oP '<h[1-6][^>]*>.*?</h[1-6]>' | \
  sed 's/<[^>]*>//g' | head -20
```

Note: dupes are common — pipe through `sort -u` if needed.

## 🇯🇵 Kyodo News

**Headlines from homepage:**
```bash
curl -sL --max-time 10 "https://english.kyodonews.net/" | \
  grep -oP '<h[23][^>]*>.*?</h[23]>' | \
  sed 's/<[^>]*>//g' | head -20
```

**Also get article links (for follow-up):**
```bash
curl -sL --max-time 10 "https://english.kyodonews.net/" | \
  grep -oP 'href="/articles/-/\d+"' | sort -u | head -10
```

**Article summary from meta description:**
```bash
curl -sL --max-time 10 "https://english.kyodonews.net/articles/-/79598" | \
  grep -oP '<meta[^>]*name="description"[^>]*content="[^"]*"' | \
  sed 's/<meta name="description" content="//;s/"//'
```

## 🇵🇭 Inquirer

**Headlines from homepage:**
```bash
curl -sL --max-time 10 "https://www.inquirer.net/" | \
  grep -oP '<h[1-4][^>]*>.*?</h[1-4]>' | \
  sed 's/<[^>]*>//g' | head -30
```

**Article URLs with class selector:**
```bash
curl -sL --max-time 10 "https://www.inquirer.net/" | \
  grep -oP '<a[^>]*href="([^"]*inquirer\.net[^"]*)"[^>]*class="optimize-track"[^>]*>([^<]*)</a>' | \
  head -15
```

**Article summary from meta:**
```bash
curl -sL --max-time 10 "https://newsinfo.inquirer.net/2260988/ashfall-from-kanlaon-blankets-negros-cebu" | \
  grep -oP '<meta[^>]*property="og:description"[^>]*content="[^"]*"' | \
  sed 's/<meta property="og:description" content="//;s/"//'
```

## 🇵🇭 PhilStar

**Headlines from homepage:**
```bash
curl -sL --max-time 10 "https://www.philstar.com/" | \
  grep -oP '<h[1-4][^>]*>.*?</h[1-4]>' | \
  sed 's/<[^>]*>//g' | head -25
```

**Headlines from dedicated /headlines page:**
```bash
curl -sL --max-time 10 "https://www.philstar.com/headlines" | \
  grep -oP '<h[1-4][^>]*>.*?</h[1-4]>' | \
  sed 's/<[^>]*>//g' | sed 's/^[[:space:]]*//' | grep -v '^$' | head -25
```

## 🌍 BBC News

**Headlines from main page (uses `data-testid="card-headline"` attribute):**
```bash
curl -sL --max-time 10 "https://www.bbc.com/news" | \
  grep -oP '<h2[^>]*data-testid="card-headline"[^>]*>.*?</h2>' | \
  sed 's/<[^>]*>//g' | head -15
```

**Article URLs from homepage:**
```bash
curl -sL --max-time 10 "https://www.bbc.com/news" | \
  grep -oP 'href="/news/articles/[^"]*"' | sort -u | head -15
```

**Article summary from meta:**
```bash
curl -sL --max-time 10 "https://www.bbc.com/news/articles/cz75zjj5wp8o" | \
  grep -oP '<meta[^>]*name="description"[^>]*content="[^"]*"' | \
  sed 's/<meta name="description" content="//;s/"//'
```

## Batch Article Summaries

When you have 5+ article URLs and need summaries for all of them:

```bash
for url in \
  "https://english.kyodonews.net/articles/-/79598" \
  "https://english.kyodonews.net/articles/-/79617" \
  "https://english.kyodonews.net/articles/-/79628"; do
  echo "=== $url ==="
  curl -sL --max-time 8 "$url" | \
    grep -oP '<meta[^>]*name="description"[^>]*content="[^"]*"' | \
    sed 's/<meta name="description" content="//;s/"//'
  echo ""
done
```

## When curl Fails

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Returns only `<script>` tags | JS-rendered site (NHK, AP) | Use browser_tools + browser_vision |
| Returns CAPTCHA page | Blocked (Reuters) | Use BBC or AP instead |
| Returns cookie consent page | Site requires cookie acceptance | Most news sites still serve content under the consent — grep for headline patterns anyway |
| Timeout | Slow server or rate limit | Increase `--max-time` to 15s, add `-L` for redirects |
| Empty output | Wrong URL or blocked user-agent | Append `-A "Mozilla/5.0"` to curl command |
