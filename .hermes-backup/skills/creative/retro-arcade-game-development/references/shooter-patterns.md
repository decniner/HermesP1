# Space Shooter Pattern Reference

The most requested retro game pattern. This reference documents the complete implementation for a mobile-friendly space shooter (like Star Fury or Space Invaders).

## Entity Architecture

### Player
```javascript
const player = { x: 0, y: 0, w: 22, h: 18, speed: 1 };
let playerLives = 3;
let invuln = 0;       // Invulnerability frames after being hit
let fireRate = 10;    // Frames between shots
let fireCD = 0;       // Cooldown counter
let rapidFire = false;
let rapidTimer = 0;
```

### Bullets (Player)
```javascript
let bullets = [];
// Fire: bullets.push({ x: player.x - 1.5, y: player.y - 14 });
// Update: bullets[i].y -= 8;
// Remove off-screen: if (bullets[i].y < -12) bullets.splice(i, 1);
```

### Enemies
```javascript
let enemies = [];
const ENEMY_COLS = 8;
const ENEMY_ROWS = 5;

// Spawn: grid of enemies with position, type, alive flag, fire rate
enemies.push({
    x: startX + col * spacing, y: startY + row * spacing,
    w: 28, h: 20, alive: true, type: 'red',  // red/orange/green
    fireRate: 0.005 + wave * 0.001,
    anim: 0,  // animation frame toggle
});
```

### Enemy Bullets
```javascript
let enemyBullets = [];
// Max bullets on screen: 4 + wave (prevents bullet hell)
```

### Power-ups
```javascript
let powerups = [];
// 5% chance to drop on enemy kill
// Types: 'rapid' — 300 frames of rapid fire
```

### Particles
```javascript
let particles = [];
// Spawned on enemy death and player hit
// Each: { x, y, vx, vy, life } — fades out over 25-30 frames
```

## Wave System

```javascript
function spawnWave() {
    wave++;
    const cols = Math.min(6 + wave, 10);
    const rows = Math.min(3 + Math.floor(wave/2), 6);
    // Difficulty scaling
    enemyMoveDelay = Math.max(10, 25 - wave);  // Moves faster each wave
    enemyShootRate = 0.005 + wave * 0.001;      // Shoots more
}
```

## Collision Detection

### Bullets vs Enemies (Backward Iteration Pattern)
```javascript
for (let i = bullets.length - 1; i >= 0; i--) {
    let used = false;
    for (let j = enemies.length - 1; j >= 0; j--) {
        if (!enemies[j].alive) continue;
        if (rectCollide(bullets[i], enemies[j])) {
            enemies[j].alive = false; used = true;
            score += points; explosionSound();
            break;
        }
    }
    if (used) bullets.splice(i, 1);  // Remove AFTER inner loop
}
```

### Enemy Bullets vs Player
```javascript
if (invuln <= 0) {  // Skip if invulnerable
    for (let i = enemyBullets.length - 1; i >= 0; i--) {
        if (rectCollide(enemyBullets[i], player)) {
            enemyBullets.splice(i, 1);
            playerLives--;
            invuln = 90;  // 1.5 seconds
            if (playerLives <= 0) gameOver();
        }
    }
}
```

### rectCollide Helper
```javascript
function rectCollide(a, b) {
    return a.x < b.x + b.w && a.x + a.w > b.x &&
           a.y < b.y + b.h && a.y + a.h > b.y;
}
```

## Enemy Movement

### Grid March Pattern (Space Invaders)
```javascript
let enemyDir = 1;
let enemyMoveCount = 0;

enemyMoveCount++;
if (enemyMoveCount >= enemyMoveDelay) {
    enemyMoveCount = 0;
    let hitEdge = false;
    enemies.forEach(e => {
        if (!e.alive) return;
        if (e.x + enemyDir * 2 < 5 || e.x + e.w + enemyDir * 2 > W - 5) hitEdge = true;
    });
    if (hitEdge) {
        enemyDir *= -1;
        enemies.forEach(e => { if (e.alive) e.y += 8; });  // Drop down
    } else {
        enemies.forEach(e => { if (e.alive) { e.x += enemyDir * 2; e.anim ^= 1; } });
    }
}
```

## Enemy Shooting (Capped)
```javascript
enemies.forEach(e => {
    if (!e.alive || enemyBullets.length > 4 + wave) return;  // Cap
    if (Math.random() < e.fireRate) {
        enemyBullets.push({ x: e.x + e.w/2 - 2, y: e.y + e.h, w: 4, h: 10 });
        beep(200, 0.05);  // Quiet beep
    }
});
```

## Game Over Conditions

1. **Player lives reach 0** — hit by enemy bullet or collision
2. **Enemy reaches bottom of screen** — they've invaded
3. **All enemies killed** → Wave complete → Spawn harder wave

## Visual Polish

### Retro Ship (Pixel Art)
Draw using `fillRect()` calls arranged to form a ship shape. No image assets needed.

### Explosion Particles
```javascript
for (let k = 0; k < 8; k++) {
    particles.push({
        x: enemy.x + enemy.w/2, y: enemy.y + enemy.h/2,
        vx: (Math.random() - 0.5) * 4, vy: (Math.random() - 0.5) * 4,
        life: 30
    });
}
// Draw: rgba(255, 255, 0, life/30) — fades from yellow to transparent
```

### Stars (Parallax Background)
```javascript
for (let i = 0; i < 60; i++) {
    stars.push({ x: Math.random()*W, y: Math.random()*H, s: 0.5+Math.random()*1.5, b: 0.2+Math.random()*0.5 });
}
// Update: stars[i].y += stars[i].s (drifts down, wraps around)
// Draw: rgba(0, 255, 0, b * 0.3)
```

### Power-up Indicator
Yellow box with "R" character inside. Floats downward. Collected on overlap.

## HUD
```html
<div id="hud" style="position:absolute;top:2vh;left:3vw;right:3vw;display:flex;justify-content:space-between;">
    <span>SCORE: 0</span>
    <span>WAVE 1</span>
</div>
```

## Difficulty Curve Reference

| Wave | Cols | Rows | Move Delay | Total Enemies | Fire Rate |
|:----:|:----:|:----:|:----------:|:-------------:|:---------:|
| 1 | 6 | 3 | 25 frames | 18 | 0.006 |
| 3 | 7 | 4 | 20 frames | 28 | 0.008 |
| 5 | 8 | 5 | 15 frames | 40 | 0.010 |
| 10 | 10 | 6 | 10 frames | 60 | 0.015 |
