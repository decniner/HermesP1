---
name: personal-finance-analysis
description: "Analyze personal credit card / bank statements from PDF exports, categorize spending, identify trends, and give tailored saving advice."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, budgeting, pdf-parsing, japan]
    related_skills: [ocr-and-documents]
---

# Personal Finance Analysis

Analyze bank/credit card statements imported as PDFs. Categorize spending, compare month-over-month, and produce actionable saving advice.

## Trigger Conditions

User sends a bank statement PDF (credit card, debit card, bank account) and asks for spending analysis, budget review, or saving tips. Also fires when a user asks for recurring monthly spending reviews.

## Workflow

### Step 1: Extract PDF Text

Use `pymupdf` (via the `ocr-and-documents` skill). Install if missing:

```bash
pip install pymupdf
```

Extract:

```python
import pymupdf
doc = pymupdf.open("statement.pdf")
for page in doc:
    text = page.get_text()
```

### Step 2: Parse Transactions

For Japanese EPOS/MUFG statements, the format is:

```
YY MM DD MerchantName(Japanese)
Amount
PaymentType(1回/分割/リボ)
```

Key parsing tips:
- Dates are in Reiwa/Heisei year format (e.g. `26 06 04` = 2026-06-04, where 26 = year 2026)
- Amount appears on the line after the merchant name, or whitespace-separated at end of line
- `１回` = one-time payment, `分割` = installment, `リボ` = revolving

For non-Japanese statements, parse based on the statement's format (date, description, amount columns).

### Step 3: Categorize Merchants

For Japanese statements, use the mapping in `references/epos-merchants.md`. Key categories:

| Category | Japanese Keywords |
|----------|------------------|
| Groceries | ベイシア, ヤオコー, ベルク, ビッグマーケット, タイラヤ, ギョウスーパー, ドンキホーテ |
| Convenience | セブンイレブン, ファミリーマート, ローソン, セイジョウ |
| Dining Out | マクドナルド, スターバックス, ラーメン, サカバ, フライングガーデン, タコズラ, サイセンカン, ヨシノヤ, アジアンダイニング, アーバンドック |
| Transit | モバイルパスモ, モバイルスイカ, ETC高速 |
| Gas | エネオス |
| Pharmacy/Clinic | ウエルシア, ドラッグストア, ココカラファイン, アイワレディスクリニック |
| Utilities & Bills | 東京電力, ソフトバンクＭ, ネットフリックス, サクラショウガク |
| Shopping / Online | AMAZON, TEMU, メルカリ |
| Entertainment | カラオケ, ツタヤ, クックワイ |
| Other | ダイソー, セリア, カインズホーム |

For non-Japanese statements, create category rules based on merchant name keywords.

### Step 4: Compute Summary

- Sum one-time (１回) transactions per category
- Report installment (分割) payments separately
- Report revolving (リボ) balance, interest charges, and APR
- Calculate percentages per category
- Track month-over-month trends if multiple statements are available

### Step 5: Identify Saving Opportunities (priority order)

1. **Revolving/credit card debt** — APR × balance. Calculate yearly interest waste. Recommend lump-sum payoff first.
2. **Convenience store spending** — Small transactions that accumulate. Recommend weekly grocery runs instead.
3. **Dining out** — Recommend replacing 1-2 meals out/week with home cooking.
4. **Transit IC charges** — Frequent small top-ups. Recommend larger monthly charges or commuter passes.
5. **Subscriptions** — Check for unused recurring charges.

### Step 6: Present Results

- **Always respond in English** unless user explicitly requests Japanese.
- Use a Markdown table for category breakdown (Category | Amount | %).
- Bullet-list saving tips with estimated monthly/yearly impact.
- If multiple months available, show a trend table.
- Keep it scannable — the user wants actionable advice, not a lecture.

### PASMO/Suica Deep Dive

This is the most common follow-up. When the user asks about transit IC charges:

1. **Extract all PASMO/Suica transactions** with their dates and amounts:
   - `モバイルパスモチャージ` / `モバイルパスモチヤ－ジ` → Mobile PASMO
   - `ＡＰ／モバイルパスモチヤ－ジ` → Apple Pay PASMO
   - `モバイルスイカ` → Mobile Suica

2. **Sub-¥3,000 analysis** — Count how many charges were below ¥3,000 and what percentage of total charges they represent. Tiny charges (¥500) indicate habitual daily top-ups.

3. **Multi-charge-per-day analysis** — Group transactions by date. Days with 2+ charges are "multi-charge days." Flag the worst day (most charges). Example output:
   ```
   May 28: 5 charges [¥1,000×4 + ¥500] = ¥4,500 🔥
   ```

4. **Compare behavior over time** — Older statements may show ¥5,000 charges (sensible) while newer ones show ¥500-¥1,000 (habitual). This behavioral shift is worth pointing out clearly.

5. **Quick savings tip** — If they'd charged ¥5,000 once weekly instead of daily ¥500:
   ```
   Apr-May: 27 charges → ~4 charges (saves 23 transactions)
   ```

### Other Follow-Up Deep Dives

When the user asks about a specific category (e.g. "how much did I spend on dining"), drill into individual transactions and look for patterns:
- **Frequency**: Count number of transactions in the period
- **Sub-threshold analysis**: How many were below a certain amount?
- **Daily patterns**: Were there multiple charges on the same day?
- **Trend**: Is it getting better or worse over time?
- **Top merchants**: Which specific stores/restaurants within the category cost the most?

## Pitfalls

- **DO NOT** ask for bank login credentials or attempt to access financial accounts directly — advise the user to export PDF/CSV and share the file instead.
- Japanese PDFs may have embedded spaces in merchant names that break regex — use flexible matching.
- The total amount is context-dependent. Look for the large number near the name line (サンチェス デンバーセラノ 様) — that's the statement total.
- Revolving debt interest rates in Japan are typically 18.0% APR for shopping revolving. Check the statement for the specific rate.
- Some files may be supplementary statements for the same period (overlapping dates). Ask the user if they want them combined or treated separately.
- When presenting saving advice, be specific with yen amounts — "¥4,591/month in interest" is more impactful than "high interest costs."
