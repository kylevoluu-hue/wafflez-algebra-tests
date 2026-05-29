#!/usr/bin/env python3
"""
Wafflez Algebra Calculator - NO-JAVASCRIPT edition
==================================================

This is a server-rendered calculator. ALL the math runs on the server
(Python + SymPy). The browser only displays a plain HTML form and the
answer, so it works even when JavaScript is completely blocked
(e.g. a school-managed Chromebook).

Run locally:
    pip install flask sympy
    python3 app.py
    # then open http://localhost:5000

Deploy free (so you can use it from a locked Chromebook):
    See HOW_TO_HOST.md
"""

from flask import Flask, request
from markupsafe import Markup

from sympy import (
    Eq, solve, simplify, factor, expand, diff, integrate,
    pretty, symbols, sqrt, sin, cos, tan, log, exp, pi, E, I, Abs,
    Rational, oo,
)
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations,
    implicit_multiplication_application, convert_xor,
)

app = Flask(__name__)

TRANSFORMS = standard_transformations + (
    implicit_multiplication_application, convert_xor,
)

X, Y, Z = symbols("x y z")
LOCALS = {
    "x": X, "y": Y, "z": Z,
    "sqrt": sqrt, "sin": sin, "cos": cos, "tan": tan,
    "log": log, "ln": log, "exp": exp, "abs": Abs,
    "pi": pi, "e": E, "I": I, "oo": oo,
}


def _parse(text):
    return parse_expr(text, local_dict=LOCALS, transformations=TRANSFORMS)


def compute(raw, op):
    """Run one calculation on the server and return a plain-text answer."""
    raw = (raw or "").strip()
    if not raw:
        return ""

    # An explicit operation button was pressed
    if op == "factor":
        return pretty(factor(_parse(raw)), use_unicode=True)
    if op == "expand":
        return pretty(expand(_parse(raw)), use_unicode=True)
    if op == "simplify":
        return pretty(simplify(_parse(raw)), use_unicode=True)
    if op == "derivative":
        return pretty(diff(_parse(raw), X), use_unicode=True)
    if op == "integral":
        return pretty(integrate(_parse(raw), X), use_unicode=True) + "  + C"
    if op == "solve" or "=" in raw:
        if "=" in raw:
            lhs, rhs = raw.split("=", 1)
            eq = Eq(_parse(lhs), _parse(rhs))
        else:
            eq = _parse(raw)
        sols = solve(eq, X)
        if not sols:
            return "No solution."
        return "\n".join("x = " + pretty(s, use_unicode=True) for s in sols)

    # Plain expression
    return pretty(simplify(_parse(raw)), use_unicode=True)


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wafflez Algebra Calculator (No-JS)</title>
<style>
  body {{ font-family: Arial, sans-serif; background:#1b1f2a; color:#f4f6fb;
         display:flex; justify-content:center; padding:24px; }}
  .calc {{ width:560px; max-width:100%; }}
  h1 {{ font-size:20px; color:#6ee7ff; margin:0 0 4px; }}
  p.sub {{ color:#8a93a8; margin:0 0 18px; font-size:13px; }}
  .screen {{ background:#0e1320; border:1px solid #2a3550; border-radius:12px;
            padding:16px; min-height:60px; margin-bottom:16px;
            white-space:pre; font-family:"Consolas",monospace; font-size:18px;
            color:#20c997; overflow:auto; }}
  .screen .q {{ color:#8a93a8; font-size:13px; margin-bottom:8px; white-space:normal; }}
  .screen .err {{ color:#e74c3c; }}
  input[type=text] {{ width:100%; box-sizing:border-box; padding:14px;
            font-size:18px; border-radius:10px; border:none; margin-bottom:12px;
            font-family:"Consolas",monospace; }}
  .ops {{ display:grid; grid-template-columns:repeat(3,1fr); gap:8px;
         margin-bottom:10px; }}
  button {{ padding:12px; font-size:15px; font-weight:bold; border:none;
           border-radius:10px; cursor:pointer; color:#fff; }}
  button.go  {{ background:#20c997; color:#08231b; }}
  button.fn  {{ background:#4b5bd6; }}
  .hint {{ color:#8a93a8; font-size:12px; line-height:1.6; margin-top:14px; }}
  code {{ background:#2b303f; padding:1px 6px; border-radius:5px; color:#ffb066; }}
  .nojs {{ background:#13351f; border:1px solid #20c997; color:#9ff3d0;
          padding:8px 12px; border-radius:8px; font-size:12px; margin-bottom:16px; }}
</style>
</head>
<body>
<div class="calc">
  <h1>Wafflez Algebra Calculator</h1>
  <p class="sub">No-JavaScript edition &middot; all math runs on the server</p>
  <div class="nojs">&#10003; This page uses zero JavaScript &mdash; it works on a locked Chromebook.</div>

  <div class="screen">{result_block}</div>

  <!-- A plain HTML form. No JavaScript: the browser just submits it. -->
  <form method="get" action="/">
    <input type="text" name="q" value="{q_value}"
           placeholder="e.g.  x^2 - 5x + 6 = 0   or   1/3 + 1/6" autofocus>
    <div class="ops">
      <button class="fn" type="submit" name="op" value="solve">Solve for x</button>
      <button class="fn" type="submit" name="op" value="factor">Factor</button>
      <button class="fn" type="submit" name="op" value="expand">Expand</button>
      <button class="fn" type="submit" name="op" value="simplify">Simplify</button>
      <button class="fn" type="submit" name="op" value="derivative">d/dx</button>
      <button class="fn" type="submit" name="op" value="integral">&#8747; dx</button>
    </div>
    <button class="go" type="submit" name="op" value="auto" style="width:100%">= Calculate</button>
  </form>

  <div class="hint">
    <b>How to type:</b><br>
    &bull; Powers: <code>x^2</code> &nbsp; Multiply: <code>2*x</code> or <code>2x</code><br>
    &bull; Equation (auto-solves): <code>2x + 4 = 0</code><br>
    &bull; Fractions stay exact: <code>1/3 + 1/6</code> &rarr; 1/2<br>
    &bull; Functions: <code>sqrt sin cos tan log ln exp</code>, constants <code>pi e</code><br>
    &bull; Press a labeled button (Factor, d/dx&hellip;) or just <b>= Calculate</b>.
  </div>
</div>
</body>
</html>"""


@app.route("/")
def index():
    q = request.args.get("q", "")
    op = request.args.get("op", "")

    result_block = '<span class="q">Type an equation above and press a button.</span>'
    if q:
        try:
            answer = compute(q, op)
            safe_q = (q.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            safe_a = (answer.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            result_block = ('<span class="q">' + safe_q + '</span>' + safe_a)
        except Exception:
            result_block = ('<span class="q">' + q + '</span>'
                            '<span class="err">Could not read that. '
                            'Check the typing rules below.</span>')

    html = PAGE.format(
        result_block=Markup(result_block),
        q_value=q.replace('"', "&quot;"),
    )
    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
