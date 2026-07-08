# Yamasa King Pulsar Cabinet Design (from session)

Built from a reference image of a King Pulsar (YAMASA) pachislot machine.

## Cabinet Layout (proportional)

```
🟫 Dark cabinet with green/gold ornate frame (4 alternating strokes)
┌────────────────────────────────────┐
│ YAMASA  YAMASA-NEXT (white on black)│  h=18px
│ 🔶🔶🔶🔶🔶 (orange honeycomb lamps) │  Flash on bonus (gflash)
├────────────────────────────────────┤
│ 🟢 GREEN BACKGROUND (#0a3a0a)       │  Gold filigree arcs at bottom
│ BIG BONUS (red, top-left)           │  
│ REGULAR BONUS (orange, below BIG)   │
│ 🟡 GOLDEN SUNBURST w/ 🐸 frog face  │  Center-top mascot
│   ┌─────┐ ┌─────┐ ┌─────┐          │
│   │ 🐸  │ │ 🔔  │ │ 7   │          │  3 reels (rw=80, rh=170)
│   │ 🔔  │ │ 🐸  │ │ 🐸  │          │
│   │ BAR │ │ 🔔  │ │ 🔔  │          │
│   └─────┘ └─────┘ └─────┘          │
│ WIN lamp (right side, yellow glow)  │
│ BAT TYPE - HAVE A GOOD TIME...      │
├────────────────────────────────────┤
│ Control panel (#0a0505, gold border)│
│ 🕹️ Lever (left, black+silver ball)  │
│ CHANCE badge (purple circle w/ "C") │
│ Credit / Count / Pay Out (LED red)  │
│ Medals display                      │
│ INSERT MEDAL button (right)         │
├────────────────────────────────────┤
│ [🛑STOP🛑] [🛑STOP🛑] [🛑STOP🛑]     │  3 oval STOP buttons under reels
│ [      PULL LEVER      ]           │  Oval button at bottom
│ Stats: BIG/REG/GAMES                │
├────────────────────────────────────┤
│ 👑 KING (red, small)               │
│ PULSAR (gold 3D serif, massive)    │
│ The fuyu revolution (script)       │
│ Crown icons on each side           │
├────────────────────────────────────┤
│ 🔊 Speaker grilles (bottom tray)    │
└────────────────────────────────────┘
```

## Key Visual Differences from Juggler

| Feature | Juggler | King Pulsar |
|---------|---------|-------------|
| **Theme** | Clown/circus (pink, gold) | Frog/nature (green, gold) |
| **Mascot** | 🤡 clown face | 🐸 green frog in sunburst |
| **Top lamps** | Row of 12 red lamps | Orange honeycomb pattern |
| **Reel BG** | Dark blue with text | Green with gold filigree |
| **Main color** | Deep pink #E91E63 | Green #0a3a0a |
| **Controls** | 4× GO buttons in arc | 2× oval buttons + lever + silver button |
| **Logo font** | GOGO (block), JUGGLER (3D gold) | KING (red serif), PULSAR (3D gold serif) |
| **Side panels** | Text only (Game Over / Wait) | Digital display (left), WIN lamp (right) |
| **Frame** | Gold/brown border | Green/gold ornate frame |

## Build Order

1. Cabinet frame (dark brown + green/gold borders)
2. Top YAMASA bar + orange honeycomb lamps
3. Main screen: green BG + gold filigree
4. BIG BONUS / REGULAR BONUS text (top left)
5. Frog mascot in golden sunburst (center top)
6. Side panels: digital display (left), WIN lamp (right)
7. 3 reels (Frog, Bell, 7, BAR, Cherry symbols)
8. STOP buttons under each reel
9. BAT TYPE banner text
10. Control panel with lever, CHANCE badge, LED displays
11. PULL LEVER button (oval)
12. KING PULSAR logo (bottom)
13. Speaker grilles

## Reel Symbols

```javascript
const S = ['🐸','🔔','7','BAR','🍒','⭐','🔔','7'];
const WGT = [18, 16, 14, 16, 14, 8, 7, 7]; // Frog most common
```

## Frame Drawing

```javascript
// Green/gold ornate frame
for (let i = 0; i < 4; i++) {
    ctx.strokeStyle = i%2===0 ? '#0a5a0a' : '#c80';
    ctx.lineWidth = 3 - i;
    ctx.strokeRect(4+i*2, 4+i*2, W-8-i*4, H-8-i*4);
}
```
