# EPOS Card (エポスカード) Statement Format

EPOS is the house credit card for the Marui Group (マルイ／OIOI department stores).
Commonly used in Japan. Also available as EPOS Gold and EPOS Platinum.

## Document Structure

A typical EPOS statement PDF is 4 pages:

| Page | Content |
|------|---------|
| 1 | Header + first page of 1回払い transactions |
| 2 | Continuation of 1回払い transactions |
| 3 | 分割・ボーナス (installments) + リボ (revolving) summary |
| 4 | Point balance + credit limit + revolving course details |

## Key Japanese Terms to Extract

At the top of the statement, look for:

| Japanese | English | Example value |
|----------|---------|--------------|
| お名前 | Cardholder name | サンチェス　デンバーセラノ |
| カード種類 | Card type | エポスプラチナカード |
| 明細作成日 | Statement date | 2026年06月10日 |
| お支払日 | Payment due date | 2026年07月04日 |
| お支払金額合計 | Total amount due | 511,363円 |
| ご利用可能枠 | Credit limit | 500万円 |
| ご利用可能残額 | Available credit | 413万円 |

At the bottom:

| Japanese | English |
|----------|---------|
| リボお支払コース | Revolving payment course |
| 手数料率・融資利率 | Interest rate (APR) |
| お支払対象残高 | Revolving balance |
| 今回のお支払額 | This month's revolving payment |
| 今回お支払後リボ残高 | Remaining revolving balance |

## Transaction Line Format

Each transaction line follows this layout (fixed-width columns in the PDF):

```
[Date] [Merchant Name] [Amount] [Payment Type] [Installment Count] [This Payment Amount] [Notes]
```

### Date Format
`YY MM DD` — e.g., `26 06 04` means June 4, 2026

### Payment Types
- `１回` — One-time payment (full amount due this month)
- `分割` — Installment plan (split into multiple months)
- `ボーナス` — Bonus payment (tied to summer/winter bonus)
- `リボ` — Revolving credit

### Installment Detail
For 分割 entries, the detail appears on the right:
```
25000円× 2回（26年07月～26年08月）
```
This means ¥25,000/month for 2 months (July–August).

### Revolving Detail
For リボ, this month's amount is a fixed course payment:
```
100,000 うち手数料 4591円
```
¥100,000 total payment including ¥4,591 in interest.

### Payment Amount Column
The rightmost column (`お支払金額`) shows how much of this transaction is due **this month**:
- For 1回: same as the transaction amount
- For 分割: the installment portion (e.g., ¥25,000 of ¥50,000)
- For リボ: the fixed course amount (e.g., ¥100,000)

## Common EPOS-Specific Patterns

**PayPay transactions**: Many transactions appear as `ペイペイ＊<merchant>` — these are PayPay-linked payments that show the merchant name after the asterisk. e.g., `ペイペイ＊セブンイレブン` = PayPay payment at 7-Eleven.

**モバイルパスモチャージ** — Mobile PASMO top-up. These are ¥500 or ¥1,000 increments and happen very frequently (often multiple times per day). They're IC card recharges for transit.

**メルカリ** on 分割 (installments) — Mercari purchases that were split. These are buy-now-pay-later purchases on Mercari's installment plan.

**ETC高速道路** — Expressway tolls charged to the card via ETC (Electronic Toll Collection).

**ペイペイ＊ベイシア** — PayPay at Beisia registers. Lower amounts (¥200, ¥300, ¥600) suggest small separate purchases (e.g., drinking water, bread) rather than full grocery runs.

## Verification

Always cross-check your parsed one-time total against the statement's total. The relationship is:

```
Total Due = One-time (1回) total + Installments (分割) this month + Revolving (リボ) this month
```

If they don't match, you've likely missed some transactions or mis-parsed an installment entry.
