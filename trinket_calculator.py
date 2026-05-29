# =====================================================================
#  Wafflez Algebra Calculator  —  Trinket / Skulpt edition
# ---------------------------------------------------------------------
#  Pure Python. No external libraries (no sympy/numpy), so it runs on
#  trinket.io, repl.it, Skulpt, and any plain Python 3.
#
#  Features:
#    * Arithmetic with fractions kept exact      e.g.  1/3 + 1/6  -> 1/2
#    * Scientific functions  sqrt sin cos tan log ln exp ...
#    * Solve LINEAR and QUADRATIC equations       e.g.  x^2 - 5x + 6 = 0
#    * Use ^ or ** for powers
#
#  How to use on Trinket:
#    1. Go to trinket.io  ->  New Trinket  ->  Python
#    2. Paste this whole file in
#    3. Press the ▶ Run button and type at the prompt
# =====================================================================

import math

# --- Functions / constants allowed inside an expression --------------
SAFE = {
    "sqrt": math.sqrt, "abs": abs,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "log": math.log, "ln": math.log, "log10": math.log10, "exp": math.exp,
    "floor": math.floor, "ceil": math.ceil,
    "pi": math.pi, "e": math.e, "tau": 2 * math.pi,
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def prep(text):
    """Turn friendly input into valid Python: ^ -> ** ."""
    return text.replace("^", "**")


def safe_eval(expr, xval=None):
    """Evaluate an expression string with only math names available."""
    names = dict(SAFE)
    if xval is not None:
        names["x"] = xval
    return eval(prep(expr), {"__builtins__": {}}, names)   # noqa: S307


def float_to_fraction(value, max_den=100000):
    """Approximate a float by a fraction using continued fractions.
    Returns (numerator, denominator) or None."""
    if value != value or value in (float("inf"), float("-inf")):
        return None
    sign = -1 if value < 0 else 1
    v = abs(value)
    h0, h1 = 0, 1     # numerators
    k0, k1 = 1, 0     # denominators
    b = v
    for _ in range(40):
        a = math.floor(b)
        h0, h1 = h1, a * h1 + h0
        k0, k1 = k1, a * k1 + k0
        if k1 > max_den:
            h1, k1 = h0, k0
            break
        if k1 != 0 and abs(h1 / k1 - v) < 1e-12:
            break
        frac = b - a
        if frac < 1e-12:
            break
        b = 1.0 / frac
    if k1 == 0:
        return None
    return sign * h1, k1


def show_number(value):
    """Format a number nicely: integers plain, exact fractions as a/b,
    otherwise a rounded decimal."""
    if isinstance(value, complex):
        return show_complex(value)
    # near-integer?
    if abs(value - round(value)) < 1e-12:
        return str(int(round(value)))
    fr = float_to_fraction(value)
    if fr is not None:
        num, den = fr
        if den != 1 and abs(num / den - value) < 1e-12 and den <= 100000:
            return str(num) + "/" + str(den)
    return str(round(value, 10))


def show_complex(z):
    re = z.real
    im = z.imag
    re_s = show_number(re) if abs(re) > 1e-12 else ""
    if abs(im) < 1e-12:
        return show_number(re)
    sign = "+" if im >= 0 else "-"
    im_s = show_number(abs(im))
    core = (im_s if im_s != "1" else "") + "i"
    if re_s:
        return re_s + " " + sign + " " + core
    return ("-" if im < 0 else "") + core


# ---------------------------------------------------------------------
# Equation solving (linear + quadratic) via coefficient sampling
# ---------------------------------------------------------------------
def poly_coeffs(expr):
    """Return (a, b, c) so expr == a*x^2 + b*x + c, or None if expr is
    not a polynomial in x of degree <= 2."""
    try:
        c = safe_eval(expr, 0.0)
        f1 = safe_eval(expr, 1.0)
        fm1 = safe_eval(expr, -1.0)
        f2 = safe_eval(expr, 2.0)
    except Exception:
        return None
    a = (f1 + fm1) / 2.0 - c
    b = (f1 - fm1) / 2.0
    # Confirm it really is degree <= 2 by checking another point.
    predicted = a * 4.0 + b * 2.0 + c
    if abs(predicted - f2) > 1e-6 * (1 + abs(predicted)):
        return None
    return a, b, c


def solve_equation(equation):
    """Solve 'LHS = RHS' for x (linear or quadratic)."""
    if "=" in equation:
        left, right = equation.split("=", 1)
        expr = "(" + left + ") - (" + right + ")"
    else:
        expr = equation

    coeffs = poly_coeffs(expr)
    if coeffs is None:
        return "Sorry — I can only solve linear/quadratic equations in x."

    a, b, c = coeffs

    # Linear:  b*x + c = 0
    if abs(a) < 1e-12:
        if abs(b) < 1e-12:
            return "No solution" if abs(c) > 1e-12 else "True for all x"
        return "x = " + show_number(-c / b)

    # Quadratic:  a*x^2 + b*x + c = 0
    disc = b * b - 4 * a * c
    if disc >= 0:
        root = math.sqrt(disc)
        x1 = (-b + root) / (2 * a)
        x2 = (-b - root) / (2 * a)
        if abs(x1 - x2) < 1e-12:
            return "x = " + show_number(x1)
        return "x = " + show_number(x1) + "   or   x = " + show_number(x2)
    else:
        root = math.sqrt(-disc)
        real = -b / (2 * a)
        imag = root / (2 * a)
        return ("x = " + show_complex(complex(real, imag)) +
                "   or   x = " + show_complex(complex(real, -imag)))


# ---------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------
BANNER = """
==========================================================
       WAFFLEZ ALGEBRA CALCULATOR  (Trinket edition)
==========================================================
 Examples:
   1/3 + 1/6           ->  fractions kept exact
   sqrt(16) + 2^3       ->  scientific functions
   2x + 4 = 0           ->  solves for x
   x^2 - 5x + 6 = 0     ->  solves quadratics
 Type 'help' for tips, or 'quit' to stop.
==========================================================
"""

HELP = """
 TIPS
 ----
 * Multiply must be explicit in plain expressions: use 3*x not 3x
   (Equations like '2x+4=0' are handled for you.)
 * Powers: use ^ or **        e.g.  x^2  or  x**2
 * Functions: sqrt sin cos tan log ln exp floor ceil abs
 * Constants: pi  e
 * Put an '=' in your input to solve an equation for x.
"""


def insert_mult(text):
    """Allow '2x' style in equations by inserting * between a digit and x."""
    out = []
    for i, ch in enumerate(text):
        out.append(ch)
        if ch.isdigit() and i + 1 < len(text) and text[i + 1] == "x":
            out.append("*")
        if ch == ")" and i + 1 < len(text) and (text[i + 1] == "x" or text[i + 1].isdigit()):
            out.append("*")
    return "".join(out)


def evaluate_line(line):
    line = line.strip()
    if not line:
        return None

    low = line.lower()
    if low in ("quit", "exit", "q"):
        raise SystemExit
    if low == "help":
        return HELP

    # Equation -> solve
    if "=" in line:
        return solve_equation(insert_mult(line))

    # Plain expression -> evaluate
    try:
        value = safe_eval(line)
        return "= " + show_number(value)
    except ZeroDivisionError:
        return "Error: division by zero"
    except Exception:
        return "Error: couldn't read that. (Use * for multiply, type 'help'.)"


def main():
    print(BANNER)
    while True:
        try:
            line = input("calc> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        try:
            result = evaluate_line(line)
        except SystemExit:
            print("Goodbye!")
            break
        if result is not None:
            print(result)


main()
