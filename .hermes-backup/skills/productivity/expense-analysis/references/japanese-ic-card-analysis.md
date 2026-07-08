# IC Card (PASMO/Suica) Charge Analysis

Patterns for analyzing Japanese transit IC card charges from credit card statements. Covers Mobile PASMO, Mobile Suica, and Apple Pay IC card top-ups.

## Merchant Name Variants

These all represent IC card top-ups and should be grouped together:

| PDF text | Standardized name | Notes |
|----------|------------------|-------|
| モバイルパスモチャージ | Mobile PASMO | Standard PASMO charge |
| モバイルパスモチヤ－ジ | Mobile PASMO | (alt. OCR: ヤ vs ャ) |
| ＡＰ／モバイルパスモチヤ－ジ | Mobile PASMO (Apple Pay) | Apple Pay PASMO charge |
| AP／モバイルパスモチャージ | Mobile PASMO (Apple Pay) | Same, different OCR |
| モバイルスイカ | Mobile Suica | Standard Suica charge |
| Suica | Suica | Possibly physical Suica |

**Matching strategy**: Match on `パスモ` or `スイカ` as substrings. Do NOT match on the full merchant name since OCR variations differ between statements (モチヤ－ジ vs モチャージ).

## Charge Amount Patterns

Typical charge amounts and what they suggest:

| Amount | Pattern name | Typical behavior |
|:------:|:-----------:|------------------|
| ¥500 | Micro top-up | Running low, adding just enough for one trip |
| ¥1,000 | Small top-up | Standard small recharge |
| ¥2,000 | Medium top-up | Planned ahead |
| ¥5,000 | Bulk top-up | Planned recharge (setup for 2-3 weeks) |
| ¥10,000 | Large top-up | Heavy commuter or family use |

## Analysis Techniques

### 1. Daily Frequency Analysis

Group charges by date and count per day. This reveals compulsive vs. planned behavior:

```python
from collections import defaultdict
daily = defaultdict(list)
for txn in pasmo_charges:
    daily[txn['date']].append(txn['amount'])

multi_days = {d: amts for d, amts in daily.items() if len(amts) > 1}
```

Present results as a table sorted by number of charges (highest first), **including per-charge breakdown and daily total**:

```plaintext
May 28:  5 charges  [¥1,000, ¥1,000, ¥1,000, ¥1,000, ¥500]  = ¥4,500  🔥 WORST
May 5:   4 charges  [¥500, ¥500, ¥1,000, ¥1,000]             = ¥3,000
May 26:  3 charges  [¥500, ¥500, ¥500]                        = ¥1,500
```

Also compute aggregate stats:

```python
total_multi_days = len(multi_days)
total_multi_charges = sum(len(v) for v in multi_days.values())
total_multi_amount = sum(sum(v) for v in multi_days.values())
pct_multi = total_multi_charges / total_all_charges * 100
```

**Present like:**
> "15 days had multiple charges. May 28 was the worst — **5 separate top-ups totaling ¥4,500**. That's running low, topping up ¥500, then running low again the same day... 5 times."

### 2. Threshold Analysis

Categorize charges as "small" (below a threshold) vs "bulk" (above):

```python
below_3000 = [a for a in all_amounts if a < 3000]
above_3000 = [a for a in all_amounts if a >= 3000]
```

For Japanese users, **¥3,000** is a good threshold — below that means the user is treating the IC card like pocket change rather than planning ahead.

Present:
- Count and total of small charges
- Percentage of all charges that are small
- Average amount per small charge
- Behavioral trend across months

### 3. Behavioral Shift Detection

Compare early vs. recent months. Users often shift from bulk charges to micro charges over time:

```
Nov-Feb:  0/17 charges below ¥3,000  (all ¥5,000 bulk top-ups)
Mar-Jun:  59/61 charges below ¥3,000 (mostly ¥500-¥1,000)
```

This is the most impactful finding to present — it shows a clear habit change the user may not have noticed.

### 4. Monthly Aggregation

Total PASMO/Suica spending per month, plus charges count:

```
Nov-Dec 2025:  ¥30,000  (6 charges)
Dec-Jan 2026:   ¥6,000  (2 charges)
Jan-Feb 2026:  ¥15,000  (3 charges)
...
```

### 5. The Simple Fix

Don't overcomplicate the recommendation:

> "If you had done one ¥5,000 charge once a week instead of these tiny top-ups, [X] charges across [Y] months would become [Z] charges. Same money, less hassle."

For truly heavy transit users (¥15,000+/month), also suggest evaluating a 定期券 (commuter pass).

## Common Pitfalls

- **Don't confuse Suica with PASMO** — both are transit IC cards but Mobile Suica and Mobile PASMO are separate apps. Group them for analysis purposes since the user cares about total transit spend.
- **Transaction lines may span multiple lines** in the PDF. The amount is often on the line immediately following the merchant name. Always check ±3 lines.
- **"ＡＰ／" prefix** — Apple Pay charges use a different merchant name format. Match on `パスモ`, not the full merchant string.
- **Suica Express charges** — Occasional ¥5,000 charges are normal bulk top-ups, not daily behavior. Don't flag a single ¥5,000 charge — flag the pattern of many tiny charges.
