# =====================================================================
#  Wafflez Algebra Calculator  -  Trinket / Skulpt edition
# ---------------------------------------------------------------------
#  Pure Python. No external libraries and NO eval(), so it runs on
#  trinket.io (Skulpt), repl.it, and any plain Python 3.
#
#  Features:
#    * Arithmetic with fractions kept exact      e.g.  1/3 + 1/6  -> 1/2
#    * Scientific functions  sqrt sin cos tan log ln exp ...
#    * Solve LINEAR and QUADRATIC equations       e.g.  x^2 - 5x + 6 = 0
#    * Use ^ or ** for powers, and 2x means 2*x
#
#  How to use on Trinket:
#    1. trinket.io  ->  New Trinket  ->  Python
#    2. Paste this whole file in
#    3. Press the > Run button and type at the prompt on the right
# =====================================================================

import math

# --- Functions / constants allowed inside an expression --------------
FUNCS = {
    "sqrt": math.sqrt, "abs": abs,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "log": math.log, "ln": math.log, "log10": math.log10, "exp": math.exp,
    "floor": math.floor, "ceil": math.ceil,
}
CONSTS = {"pi": math.pi, "e": math.e, "tau": 2 * math.pi}


# =====================================================================
#  A tiny expression evaluator (tokenizer + recursive-descent parser).
#  No eval() is used, so Skulpt/Trinket can run it.
# =====================================================================
class ParseError(Exception):
    pass


def tokenize(text):
    """Break the text into numbers, names, operators and parentheses."""
    text = text.replace("**", "^")
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == " ":
            i += 1
            continue
        if ch.isdigit() or ch == ".":
            j = i
            while j < n and (text[j].isdigit() or text[j] == "."):
                j += 1
            tokens.append(("num", float(text[i:j])))
            i = j
        elif ch.isalpha() or ch == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            tokens.append(("name", text[i:j]))
            i = j
        elif ch in "+-*/^(),":
            tokens.append(("op", ch))
            i += 1
        else:
            raise ParseError("bad character: " + ch)
    return tokens


class Parser:
    """Grammar (with implicit multiplication, e.g. 2x or (x+1)(x-1)):
        expr  := term (('+'|'-') term)*
        term  := power ( ('*'|'/') power | implicit power )*
        power := unary ('^' power)?           # right associative
        unary := ('+'|'-') unary | primary
        primary := number | const | var | func '(' expr ')' | '(' expr ')'
    """

    def __init__(self, tokens, xval):
        self.tokens = tokens
        self.pos = 0
        self.xval = xval

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (None, None)

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect_op(self, ch):
        kind, val = self.peek()
        if kind == "op" and val == ch:
            self.advance()
            return
        raise ParseError("expected '" + ch + "'")

    def parse(self):
        value = self.expr()
        if self.pos != len(self.tokens):
            raise ParseError("unexpected extra input")
        return value

    def expr(self):
        value = self.term()
        while True:
            kind, val = self.peek()
            if kind == "op" and val in ("+", "-"):
                self.advance()
                rhs = self.term()
                value = value + rhs if val == "+" else value - rhs
            else:
                return value

    def term(self):
        value = self.power()
        while True:
            kind, val = self.peek()
            if kind == "op" and val in ("*", "/"):
                self.advance()
                rhs = self.power()
                if val == "*":
                    value = value * rhs
                else:
                    value = value / rhs
            elif kind == "num" or kind == "name" or (kind == "op" and val == "("):
                # implicit multiplication:  2x , 3(x+1) , (x+1)(x-1)
                rhs = self.power()
                value = value * rhs
            else:
                return value

    def power(self):
        base = self.unary()
        kind, val = self.peek()
        if kind == "op" and val == "^":
            self.advance()
            exponent = self.power()    # right associative
            return base ** exponent
        return base

    def unary(self):
        kind, val = self.peek()
        if kind == "op" and val == "+":
            self.advance()
            return self.unary()
        if kind == "op" and val == "-":
            self.advance()
            return -self.unary()
        return self.primary()

    def primary(self):
        kind, val = self.peek()
        if kind == "num":
            self.advance()
            return val
        if kind == "op" and val == "(":
            self.advance()
            value = self.expr()
            self.expect_op(")")
            return value
        if kind == "name":
            self.advance()
            name = val
            if name == "x":
                if self.xval is None:
                    raise ParseError("unknown variable x")
                return self.xval
            if name in CONSTS:
                return CONSTS[name]
            if name in FUNCS:
                self.expect_op("(")
                arg = self.expr()
                self.expect_op(")")
                return FUNCS[name](arg)
            raise ParseError("unknown name: " + name)
        raise ParseError("unexpected input")


def evaluate_expr(text, xval=None):
    return Parser(tokenize(text), xval).parse()


# ---------------------------------------------------------------------
# Number formatting (exact fractions when possible)
# ---------------------------------------------------------------------
def is_nan(v):
    return v != v


def float_to_fraction(value, max_den=100000):
    """Approximate a float by a fraction using continued fractions."""
    if is_nan(value) or abs(value) > 1e15:
        return None
    sign = -1 if value < 0 else 1
    v = abs(value)
    h0, h1 = 0, 1
    k0, k1 = 1, 0
    b = v
    count = 0
    while count < 40:
        a = math.floor(b)
        h0, h1 = h1, a * h1 + h0
        k0, k1 = k1, a * k1 + k0
        if k1 > max_den:
            h1, k1 = h0, k0
            break
        if k1 != 0 and abs(h1 / float(k1) - v) < 1e-12:
            break
        frac = b - a
        if frac < 1e-12:
            break
        b = 1.0 / frac
        count += 1
    if k1 == 0:
        return None
    return int(sign * h1), int(k1)


def show_number(value):
    """Integers plain, exact fractions as a/b, else a rounded decimal."""
    if isinstance(value, complex):
        return show_complex(value)
    if abs(value - round(value)) < 1e-12:
        return str(int(round(value)))
    fr = float_to_fraction(value)
    if fr is not None:
        num, den = fr
        if den != 1 and abs(num / float(den) - value) < 1e-12:
            return str(num) + "/" + str(den)
    return str(round(value, 10))


def show_complex(z):
    re = z.real
    im = z.imag
    if abs(im) < 1e-12:
        return show_number(re)
    re_s = show_number(re) if abs(re) > 1e-12 else ""
    sign = "+" if im >= 0 else "-"
    im_abs = show_number(abs(im))
    core = ("" if im_abs == "1" else im_abs) + "i"
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
        c = evaluate_expr(expr, 0.0)
        f1 = evaluate_expr(expr, 1.0)
        fm1 = evaluate_expr(expr, -1.0)
        f2 = evaluate_expr(expr, 2.0)
    except Exception:
        return None
    a = (f1 + fm1) / 2.0 - c
    b = (f1 - fm1) / 2.0
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
        return "Sorry - I can only solve linear/quadratic equations in x."

    a, b, c = coeffs

    if abs(a) < 1e-12:                       # linear:  b*x + c = 0
        if abs(b) < 1e-12:
            return "No solution" if abs(c) > 1e-12 else "True for all x"
        return "x = " + show_number(-c / b)

    disc = b * b - 4 * a * c                  # quadratic
    if disc >= 0:
        root = math.sqrt(disc)
        x1 = (-b + root) / (2 * a)
        x2 = (-b - root) / (2 * a)
        if abs(x1 - x2) < 1e-12:
            return "x = " + show_number(x1)
        return "x = " + show_number(x1) + "   or   x = " + show_number(x2)
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
 * 2x means 2*x, and (x+1)(x-1) multiplies - implicit mult works.
 * Powers: use ^ or **        e.g.  x^2  or  x**2
 * Functions: sqrt sin cos tan log ln exp floor ceil abs
 * Constants: pi  e
 * Put an '=' in your input to solve an equation for x.
"""


def evaluate_line(line):
    line = line.strip()
    if not line:
        return None

    low = line.lower()
    if low in ("quit", "exit", "q"):
        raise SystemExit
    if low == "help":
        return HELP

    if "=" in line:
        return solve_equation(line)

    try:
        value = evaluate_expr(line)
        return "= " + show_number(value)
    except ZeroDivisionError:
        return "Error: division by zero"
    except ParseError:
        return "Error: couldn't read that. Type 'help' for the rules."
    except Exception:
        return "Error: couldn't compute that. Type 'help' for the rules."


def main():
    print(BANNER)
    while True:
        try:
            line = input("calc> ")
        except (EOFError, KeyboardInterrupt):
            print("")
            print("Goodbye!")
            break
        try:
            result = evaluate_line(line)
        except SystemExit:
            print("Goodbye!")
            break
        if result is not None:
            print(result)


main()
