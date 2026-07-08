# Detecting Silent JS Failures in Single-File HTML Games

When auditing HTML/Canvas games, the most common failure mode is a **silent blank page** caused by a JavaScript syntax error in the `<script>` tag. Unlike Node.js or browser DevTools (which show red errors), the game simply renders nothing — no error visible to the user.

## Audit Step: Extract and Syntax-Check the JS

```bash
node -e "
const fs = require('fs');
let html = fs.readFileSync('game.html', 'utf8');
const m = html.match(/<script>([\\s\\S]*?)<\\/script>/);
if (!m) { console.log('No script found'); process.exit(1); }
let js = m[1];
try {
    new Function(js);
    console.log('JS OK');
} catch(e) {
    console.log('JS ERROR:', e.message);
    const lines = js.split('\n');
    const match = e.stack.match(/<anonymous>:(\\d+)/);
    if (match) {
        const ln = parseInt(match[1]) - 1;
        console.log('Line', ln+1 + ':', lines[ln]?.trim().substring(0, 120));
    }
}
"
```

## Common Silent Killers

| Issue | How to Detect |
|-------|---------------|
| Computed property name syntax (e.g. `[5:[60,'FOO']]` instead of `5:[60,'FOO']` or `[5]:[60,'FOO']`) | Node.js syntax check |
| `roundRect` not supported | Browser console — check for `ctx.roundRect is not a function` |
| Unbalanced braces after patching | Brace count check (`{` vs `}`) |
| Event listener `touch-action: none` missing (touch inputs don't fire) | CSS rule check |
| `canvas.width` set to 0 or viewport returns 0 on orientation change | Resize handler uses `window.innerWidth` not previous value |
