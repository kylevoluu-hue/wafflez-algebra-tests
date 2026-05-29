# Running the Calculator on Trinket & Google Sites

You have two scripts:

| File | What it is | Where it runs |
|------|------------|---------------|
| `trinket_calculator.py` | Pure-Python calculator (no libraries) | Trinket **Python**, repl.it, any Python 3 |
| `calculator.html` | Graphical button calculator | Trinket **HTML**, then embed in Google Sites |

> ⚠️ The big `calculator.py` uses **SymPy**, which Trinket **cannot** run.
> Use `trinket_calculator.py` for Trinket's Python instead — it needs no libraries.

---

## A) Python on Trinket

1. Go to **https://trinket.io** → sign in → **New Trinket** → **Python**.
2. Delete the sample code and **paste all of `trinket_calculator.py`**.
3. Click **▶ Run**. Type in the console on the right, e.g.:
   ```
   x^2 - 5x + 6 = 0
   1/3 + 1/6
   sqrt(16) + 2^3
   ```

---

## B) HTML calculator on Trinket

1. trinket.io → **New Trinket** → **HTML/CSS/JS**.
2. Open the `index.html` tab, delete its contents, and **paste all of `calculator.html`**.
3. Click **▶ Run** — the calculator with buttons appears on the right.
   - It loads its math engine from the internet, so keep a connection.

---

## C) Put it on a Google Site

**Easiest — embed the Trinket you made in step B:**

1. In your Trinket, click **Share** → **Embed** and copy the embed link.
2. In Google Sites: **Insert** → **Embed** → **By URL** (paste the Trinket
   share URL) or **Embed code** (paste the Trinket `<iframe>` code).
3. Resize the box and **Publish**.

**Or embed the raw HTML directly:**

1. Google Sites: **Insert** → **Embed** → **Embed code**.
2. Paste the entire contents of `calculator.html`.
3. Click **Next** → **Insert**, resize, then **Publish**.
   - Google Sites runs embeds in a sandboxed frame; the external math
     engine still loads fine over the internet.

---

### Quick reference (both versions)
- Powers: `^` or `**`  →  `x^2`
- Solve: include `=`  →  `2x + 4 = 0`
- Fractions stay exact: `1/3 + 1/6` → `1/2`
- In the **Python** version, use `*` for multiply in plain expressions
  (`3*x`); equations like `2x+4=0` are handled automatically.
- The **HTML** version has buttons, so you just click.
