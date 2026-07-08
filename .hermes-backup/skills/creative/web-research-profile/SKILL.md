---
name: web-research-profile
description: Research a person's online presence from web sources and build a professional profile or portfolio landing page as a single HTML file. Covers the full pipeline of search, extract, compile, design, and email delivery.
version: 1.0.0
author: agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [profile, research, landing-page, portfolio, html, creative, email, smtp]
    related_skills: [claude-design, smtp-email]
---

# Web Research + Profile Landing Page

Use this skill when the user asks you to research a person online (by name, company, title) and build a professional profile or portfolio landing page in HTML.

## When To Use

- User says "Research [name] from [company] and build a landing page"
- User says "Create an online presence report for [name]"
- User wants a professional profile page for themselves or someone else
- User asks for an HTML portfolio page based on web research

This skill covers the full pipeline: web research, information extraction, HTML page design, and email delivery.

## If Web Search Is Unavailable

Web search APIs (Firecrawl, Google, etc.) may occasionally be unavailable due to billing limits. When this happens:

1. Try alternative search engines via browser (DuckDuckGo, Bing, Yahoo)
2. Try direct source URLs (LinkedIn, The Org, ZoomInfo, RocketReach)
3. If all searches fail, build the page with what the user provided, include a prominent notice explaining the limitation, and send it anyway

**Fallback notice for the HTML page:**
```html
<div class="notice">Warning: Web search tools are temporarily unavailable. This profile was built from the information provided. For a fully enriched profile with detailed work history and skills, search capability needs to be restored.</div>
```

## The Pipeline

### Step 1: Research

Search for the person using name + company + title:

```
web_search(query='"First Last" "Company" "Title"')
```

If the search API is unavailable, try browser-based search on DuckDuckGo or Yahoo.

Target sources in priority order:
- LinkedIn (best for work history, education, skills)
- The Org (org chart data, role history, team context)
- ZoomInfo / RocketReach (professional contact info)
- Google / Bing search (general presence)

### Step 2: Extract Information

From the search results, extract:
- Current role and company with dates
- Previous roles with companies and dates
- Education (degrees, institutions)
- Skills and expertise areas
- Location
- Languages spoken

### Step 3: Build the HTML Profile Page

Design a dark-themed, single-file HTML profile page with this structure:

- Hero section: Initials avatar, full name, title, company, location
- Timeline: Professional experience in chronological order
- Skills: Tag cloud of expertise areas
- About cards: Company or industry context
- Education: Degrees and certifications
- Footer: Attribution with data source note

### Step 4: Email the HTML as Attachment

Use the smtp-email skill pattern to send the HTML file as an attachment via Python smtplib. Include a plain-text body explaining what was found and any limitations.

## Design Variants

### Teal Accent (default for engineer or tech profiles)
Use color values #4dd0e1, #80cbc4, #26a69a. Suitable for engineers, developers, and technical roles.

### Gold Accent (for business or finance profiles)
Use color values #c4782a, #e8a540, #ffd700. Suitable for executives, finance professionals, and Nomura profiles.

### Bronze Accent (for personal reports)
Use Hermes gold palette (#ffd700, #c4782a). Suitable for online presence reports about the user themselves.

## Common Pitfalls

1. **LinkedIn blocks scraping** - LinkedIn requires login. Use The Org, ZoomInfo, or RocketReach as alternatives.
2. **Search APIs can be down** - Have a fallback plan. Try browser-based searches if the API fails. Note the limitation in the HTML page.
3. **Name spelling matters** - The user may misspell the name. Try variations. Example: user said "Nikki Lloyd Corpus" but correct spelling was "Nikki Lloyd Corpuz."
4. **Do not guess details** - If you cannot verify a role, company, or date, do not invent it. Note it as unverified or leave it out.
5. **Email the file, not just the path** - The user asks to email the HTML. Do not just save it locally and tell them where it is.
6. **Dark theme by default** - All profile pages should default to dark theme (#0f0f1a background). Light mode is optional.

## Verification Checklist

- [ ] Searched for the person using name, company, and title
- [ ] Tried alternative search methods if primary API was down
- [ ] Extracted verifiable work history (not invented details)
- [ ] Built dark-themed HTML profile page
- [ ] Included fallback notice if search was limited
- [ ] Emailed the HTML as an attachment
- [ ] Confirmed email was sent successfully
