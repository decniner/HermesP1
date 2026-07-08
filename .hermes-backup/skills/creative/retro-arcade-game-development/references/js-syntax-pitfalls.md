# JS Syntax Pitfalls in HTML Game Files

Common JavaScript syntax errors that produce a blank page in single-file HTML games. Always run a Node.js syntax check before delivery.

## Pitfall 1: Computed Property Names in Object Literals

**Symptom:** Game loads but canvas is blank. No errors in browser console (because the script tag error is swallowed).

**Broken syntax:**
```javascript
const m = {0:[200,'FROG×3'],[1]:[100,'BELL×3'],[5:[60,'STAR×3']]};
//                                          ^
//                               The bracket [5 starts a computed
//                               property name, but then the :
//                               is INVALID inside the brackets
```

**`[5:[60,'STAR×3']]` is parsed as:**
- `[5` — Start of a computed property name expression
- `:` — Syntax error! Colon is not valid inside `[...]` brackets

The correct syntax is either:
```javascript
// Option A: Simple numeric key (preferred — cleanest)
const m = {0:[200,'FROG×3'],1:[100,'BELL×3'],5:[60,'STAR×3']};

// Option B: Computed property name (brackets around the KEY only)
const m = {0:[200,'FROG×3'],[1]:[100,'BELL×3'],[5]:[60,'STAR×3']};
//                                                ^^ correct
```

**Rule:** For numeric keys, use them directly — no brackets needed. Brackets are for computed property names (expressions like `[someVariable]`).

## Verification: Node.js Syntax Check

Before delivering any HTML game file, run the extracted JavaScript through Node.js:

```bash
node -e "
const fs = require('fs');
let html = fs.readFileSync('path/to/game.html', 'utf8');
const m = html.match(/<script>([\\s\\S]*?)<\\/script>/);
if (!m) { console.log('No script found'); process.exit(1); }
let js = m[1];
try {
    new Function(js);
    console.log('OK');
} catch(e) {
    console.log('ERROR:', e.message);
    const lines = js.split('\n');
    const match = e.stack.match(/<anonymous>:(\\d+)/);
    if (match) {
        const ln = parseInt(match[1]) - 1;
        console.log('Line', ln+1 + ':', lines[ln]?.trim().substring(0, 120));
    }
}
"
```

This catches all syntax errors before the user ever sees a blank page.

## Pitfall 2: Trailing Comma in Object Method Contexts

```javascript
const obj = {
    method() {},  // fine in modern JS
}
```

Modern JS allows trailing commas, but only since ES2017. For maximum compatibility, omit trailing commas.

## Pitfall 3: Using `roundRect` Without Checking Browser Support

```javascript
ctx.beginPath();
ctx.roundRect(10, 10, 100, 50, 5); // Not supported in all browsers
ctx.fill();
```

`roundRect` was added relatively recently. On some mobile browsers, it throws a runtime error. Use `fillRect` + `strokeRect` instead.

## Pitfall 4: Balanced Braces Check

After any patch/edit to a game file, verify brace balance:

```python
import re
with open('game.html') as f:
    c = f.read()
m = re.search(r'<script>(.*?)</script>', c, re.DOTALL)
js = m.group(1) if m else ''
opens = js.count('{')
closes = js.count('}')
print(f'Balanced: {opens == closes}')
```
