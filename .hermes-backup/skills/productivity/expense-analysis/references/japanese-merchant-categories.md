# Japanese Merchant Categories

Curated keyword bank for categorizing Japanese credit card / bank transactions.
When a transaction contains ANY of these substrings, assign it to the corresponding category.

## 🛒 スーパー / Groceries & Hypermarkets

| Keyword | Store | Notes |
|---------|-------|-------|
| ベイシア | Beisia | Supercenter (Gunma-based) |
| ヤオコー | Yaoko | Supermarket (Saitama-based) |
| ベルク | Belc | Supermarket |
| ビッグマーケット | Big Market | Supermarket |
| タイラヤ | Tairaya | Supermarket |
| ドンキホーテ | Don Quijote | Discount store (mostly groceries/daily goods) |
| ライフ | Life | Supermarket |
| イオン | AEON | Supermarket / Shopping center |
| トップバリュ | TopValu | AEON house brand |
| サミット | Summit | Supermarket |
| マルエツ | Maruetsu | Supermarket |
| 西友 | Seiyu | Supermarket (Walmart Japan) |
| マックスバリュ | MaxValu | AEON supermarket |
| コープ | Co-op | Cooperative supermarket |
| 業務スーパー | Gyomu Super | Wholesale supermarket |
| ロピア | Lopia | Wholesale supermarket |
| オーケー | OK | Discount supermarket |
| メガドンキ | Mega Don Quijote | Large-format Don Quijote (東松山) |
| ギヨウムス－パ－ | Gyomu Super | (alt. OCR: ギヨウム vs 業務) |
| セイセンイチバ | Seisen Ichiba | Fresh/meat market (Kawagoe area) |
| カインズホーム | Cainz Home | Home center / hardware store |
| カインズ | Cainz | (shorthand for Cainz Home) |
| ビツグマ－ケツト | Big Market | (alt. OCR: ビツグ vs ビッグ) |
| メガドンキ | Mega Don Quijote | (Higashimatsuyama) |

## 🏪 コンビニ / Convenience Stores

| Keyword | Store | Notes |
|---------|-------|-------|
| セブンイレブン | 7-Eleven | Also matches PayPay＊セブンイレブン |
| ファミリーマート | FamilyMart | Also matches PayPay＊ファミリーマート |
| ローソン | Lawson | Also matches PayPay＊ローソン |
| セイジョウ | Seijo | Drugstore chain (often PayPay) |
| ミニストップ | Ministop | Convenience store |
| デイリーヤマザキ | Daily Yamazaki | Convenience store |
| セブン | 7-Eleven | Broad match |

**Pitfall**: A ¥6,200 charge at 7-Eleven is likely a utility payment (bill paid at the register), not 18 konbini snacks. Use amount heuristics — anything over ¥3,000 at a convenience store is suspicious and may be a bill payment.

## 🍽️ 外食 / Dining Out

| Keyword | Type |
|---------|------|
| マクドナルド / マック | McDonald's |
| スターバックス / スタバ | Starbucks |
| ガスト | Gusto (family restaurant) |
| サイゼリヤ | Saizeriya (Italian) |
| すき家 | Sukiya (gyudon) |
| 吉野家 / ヨシノヤ | Yoshinoya (gyudon) |
| 松屋 | Matsuya (gyudon) |
| ココス | Cocos (family restaurant) |
| デニーズ | Denny's |
| ロイヤルホスト | Royal Host |
| ラーメン | Ramen (matches many shops) |
| 居酒屋 | Izakaya (pub) |
| 焼肉 | Yakiniku (BBQ) |
| 寿司 / すし | Sushi |
| うどん | Udon |
| そば | Soba |
| カレー / Curry | Curry |
| サカバ | Sakaba (bar/tavern) — PayPay prefix |
| グルメキネヤ | Gourmet Kineya (udon chain) |
| フライングガーデン | Flying Garden (family restaurant) |
| アジアンダイニング | Asian Dining |
| アーバンドック | Urban Dock / Lalaport food court |
| タコズラ | Takozura |
| トヨスラーメン | Toyosu Ramen |
| サイセンカン | Saisankan (Chinese) |
| ウイーカーズ | Weekers (cafe) |
| コメダ | Komeda's Coffee |
| ドトール | Doutor Coffee |
| タリーズ | Tully's Coffee |
| トヨスサカバ | Toyosu Sakaba (bar/food) | PayPay prefix |
| ブラジルストア | Brazil Store (Rakuten Pay) | Latin grocery/shop |

## 🚃 交通 / Transport

| Keyword | Type |
|---------|------|
| モバイルパスモ | Mobile PASMO (IC card charge) |
| モバイルスイカ | Mobile Suica (IC card charge) |
| PASMO | PASMO |
| Suica / スイカ | Suica |
| ETC | Expressway toll |
| 高速道路 | Expressway |
| トヨタ | Toyota (rental/repair) |
| 日産 | Nissan |
| JR | Japan Rail |
| 東京メトロ | Tokyo Metro |
| 小田急 | Odakyu |
| 東急 | Tokyu |
| 京王 | Keio |
| 西武 | Seibu |
| タクシー | Taxi |

## ⛽ ガソリン / Gas

| Keyword | Station |
|---------|---------|
| エネオス / ENEOS | ENEOS |
| 出光 / Idemitsu | Idemitsu |
| コスモ | Cosmo Oil |
| シェル / Shell | Shell |
| モービル / Mobil | Mobil |
| エッソ / Esso | Esso |
| ガソリン | Gas (generic) |
| ＧＳ | Gas station |

## 💊 薬局・病院 / Pharmacy & Medical

| Keyword | Type |
|---------|------|
| ウエルシア | Welcia (drugstore) |
| ドラッグストア | Drugstore (generic) |
| ココカラファイン | Cocokara Fine (drugstore) |
| マツモトキヨシ / マツキヨ | Matsumoto Kiyoshi |
| クリニック | Clinic |
| 医院 | Clinic |
| 病院 | Hospital |
| 歯科 | Dentist |
| 薬局 | Pharmacy |
| ツルハ | Tsuruha Drug |
| スギ薬局 | Sugi Pharmacy |
| トモズ | Tomod's |
| セキ | Seki (drugstore chain, Saitama) |
| アイワレディ | Aiwa Ladies Clinic |

## 💡 光熱費・通信 / Utilities & Subscriptions

| Keyword | Type |
|---------|------|
| 東京電力 / TEPCO | Electricity (Tokyo) |
| 東京ガス | Gas (Tokyo) |
| ソフトバンク / SoftBank | Mobile carrier |
| ドコモ / docomo | Mobile carrier |
| au | Mobile carrier (KDDI) |
| ネットフリックス / Netflix | Streaming |
| Amazon Prime | Subscription |
| Spotify | Music streaming |
| U-NEXT | Streaming |
| Hulu | Streaming |
| Disney＋ / ディズニー | Disney+ |
| NHK | NHK broadcast fee |
| 水道 | Water bill |
| 電気 | Electricity (generic) |
| サクラショウガク | Sakura Shogaku insurance (SoftBank) |
| ポヴォ | Povo (au mobile plan) |

## 🛍️ 通販 / Online Shopping

| Keyword | Store |
|---------|-------|
| Amazon | Amazon.co.jp |
| 楽天 / Rakuten | Rakuten |
| メルカリ | Mercari (also appears under 分割/installments) |
| TEMU | TEMU (Chinese online shopping) |
| アゴダ / Agoda | Agoda (hotel booking) |
| ヤフー | Yahoo Shopping |
| PayPayモール | PayPay Mall |
| ユニクロ | UNIQLO online |
| ZOZO | ZOZO / ZOZOTOWN |
| ニトリ | Nitori online |
| 無印良品 / MUJI | Muji |

## 🎤 娯楽 / Entertainment

| Keyword | Type |
|---------|------|
| カラオケ | Karaoke |
| ツタヤ / TSUTAYA | Video/DVD rental |
| 映画 | Cinema |
| Toho / 東宝 | Cinema |
| イオンシネマ | AEON Cinema |
| ゲーム / Game | Gaming |
| 任天堂 / Nintendo | Nintendo eShop |
| Steam | Steam |
| クックワイ | Cook Y? (cooking class — Saitama area) |
| アネックス | Anex | Hobby/event (? Saitama area) |
| ファッションセンターシマムラ | Shimamura | Clothing store |
| ジ－ユ－ / GU | GU | Clothing (Uniqlo sister brand) |
| ブツクオフ / Book Off | Book Off | Used books/games |

## 📦 その他 / Other / Miscellaneous

| Keyword | Type |
|---------|------|
| ダイソー | Daiso (100 yen shop) |
| セリア | Seria (100 yen shop) |
| キャンドゥ | Can Do (100 yen shop) |
| ヤマトウンユ / ヤマト運輸 | Yamato Transport (delivery) |
| クロネコ | Kuroneko (Yamato) |
| 郵便 / ゆうパック | Japan Post |
| ドリンコ / DoDro | Drink vending |
| ペイペイ＊ヤマト | PayPay at Yamato Transport |
| ペイペイ＊セリア | PayPay at Seria |
| ペイペイ＊ツタヤ | PayPay at TSUTAYA |
| ペイペイ＊ベイシア | PayPay at Beisia (lower amounts: ¥200-¥600 suggest separate self-checkout purchases) |
| ペイペイ＊ローソン | PayPay at Lawson |
| ペイペイ＊ファミリーマート | PayPay at FamilyMart |
| ラクテンペイ | Rakuten Pay (online payment) |
| ペットアンドファミリー | Pet & Family Insurance (pet insurance) |
| アポツク | Apoc/U-Nix (? Saitama area) |
