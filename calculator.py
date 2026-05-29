#!/usr/bin/env python3
"""
Wafflez Algebra Calculator
===========================

An interactive symbolic math calculator supporting algebra, equations,
fractions, functions, and calculus — powered by SymPy.

Usage:
    python3 calculator.py                 # interactive REPL
    python3 calculator.py "2x + 4 = 0"    # evaluate a single expression

Requires:
    sympy  (pip install sympy)
"""

import os
import sys
from tokenize import TokenError

__version__ = "1.0.0"

# ---------------------------------------------------------------------------
# Dependency check (fail gracefully before touching any SymPy names)
# ---------------------------------------------------------------------------
try:
    from sympy import (
        symbols, solve, simplify, expand, factor,
        sqrt, cbrt, root, Rational, pi, E, I, oo, nan, zoo, GoldenRatio, EulerGamma,
        sin, cos, tan, cot, sec, csc,
        asin, acos, atan, acot, asec, acsc, atan2,
        sinh, cosh, tanh, coth, sech, csch,
        asinh, acosh, atanh,
        log, exp, Abs, sign, floor, ceiling, frac,
        re as sym_re, im as sym_im, conjugate, arg, Add,
        diff, integrate, limit, series, summation, product,
        Eq, Matrix, eye, zeros, ones, diag,
        cancel, together, apart, radsimp, ratsimp, trigsimp, expand_trig,
        powsimp, logcombine, expand_log, nsimplify,
        gcd, lcm, factorint, isprime, prime, primepi, nextprime, prevprime,
        totient, divisors, divisor_count, mod_inverse, igcd, ilcm,
        factorial, binomial, ff, rf, fibonacci, lucas, catalan, bernoulli, harmonic,
        gamma, beta, erf, zeta,
        Min, Max,
        N, nsolve, dsolve, rsolve, Function, Derivative,
        degree, Poly, roots, real_roots,
        pretty, latex,
        SympifyError,
        FiniteSet, Interval, Union, Intersection, Complement, EmptySet,
        And, Or, Not, Implies, Equivalent, satisfiable,
    )
    from sympy.parsing.sympy_parser import (
        parse_expr,
        standard_transformations,
        implicit_multiplication_application,
        convert_xor,
    )
except ImportError:
    sys.stderr.write(
        "Error: SymPy is required but not installed.\n"
        "Install it with:  pip install sympy\n"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Parser configuration
# ---------------------------------------------------------------------------
TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,  # 2x  -> 2*x ,  (x+1)(x-1) -> product
    convert_xor,                          # ^   -> **
)

# Variables that are auto-recognized when typed.
ALL_SYMBOLS = symbols('x y z a b c n t k m p q r s u v w')
SYMBOL_DICT = {str(s): s for s in ALL_SYMBOLS}

# Undefined functions for differential / functional equations, e.g.
#   dsolve(diff(f(x), x) - f(x))
FUNCTION_DICT = {name: Function(name) for name in ('f', 'g', 'h', 'y_')}

# Preferred order when auto-detecting which variable to solve for.
SOLVE_PREFERENCE = ['x', 'y', 'z', 'a', 'b', 'c', 'n', 't', 'k']


def _integrate_wrapper(*args):
    """Support integrate(f, x), integrate(f, x, a, b) and the tuple form."""
    if len(args) == 3:
        return integrate(args[0], (args[1], args[2]))
    if len(args) == 4:
        return integrate(args[0], (args[1], args[2], args[3]))
    return integrate(*args)


def _matrix(rows):
    """Build a Matrix, tolerating both matrix([[...]]) and Matrix() forms."""
    return Matrix(rows)


# --- Statistics helpers (operate on plain lists of numbers) ----------------
def _as_list(data):
    """Accept a list/tuple/Matrix and return a flat Python list."""
    if isinstance(data, Matrix):
        return list(data)
    if isinstance(data, (list, tuple)):
        return list(data)
    return [data]


def _mean(data):
    d = _as_list(data)
    return Add(*d) / len(d)


def _median(data):
    d = sorted(_as_list(data), key=lambda v: float(v))
    n = len(d)
    if n == 0:
        return nan
    mid = n // 2
    if n % 2 == 1:
        return d[mid]
    return (d[mid - 1] + d[mid]) / 2


def _mode(data):
    d = _as_list(data)
    counts = {}
    for v in d:
        counts[v] = counts.get(v, 0) + 1
    best = max(counts.values())
    modes = [k for k, c in counts.items() if c == best]
    return modes[0] if len(modes) == 1 else FiniteSet(*modes)


def _variance(data, sample=False):
    d = _as_list(data)
    n = len(d)
    mu = _mean(d)
    total = Add(*[(v - mu) ** 2 for v in d])
    return total / (n - 1) if sample else total / n


def _stdev(data, sample=False):
    return sqrt(_variance(data, sample))


def _summation(expr, var, lo, hi):
    return summation(expr, (var, lo, hi))


def _product(expr, var, lo, hi):
    return product(expr, (var, lo, hi))


# --- Base conversion / display helpers -------------------------------------
def _to_base(n, base):
    """Return a string representation of integer n in the given base (2-36)."""
    n = int(n)
    base = int(base)
    if base < 2 or base > 36:
        raise ValueError("base must be between 2 and 36")
    if n == 0:
        return "0"
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    neg = n < 0
    n = abs(n)
    out = []
    while n:
        out.append(digits[n % base])
        n //= base
    return ("-" if neg else "") + "".join(reversed(out))


def _to_bin(n):
    return bin(int(n))


def _to_hex(n):
    return hex(int(n))


def _to_oct(n):
    return oct(int(n))


# Names exposed to the expression parser. This is an explicit allow-list:
# user input is only ever evaluated against these symbols/functions, never
# against arbitrary Python builtins.
BUILTIN_LOCALS = {
    **SYMBOL_DICT,
    **FUNCTION_DICT,

    # --- Roots & powers ----------------------------------------------------
    'sqrt': sqrt, 'cbrt': cbrt, 'root': root,
    'abs': Abs, 'Abs': Abs, 'sign': sign,

    # --- Trigonometry ------------------------------------------------------
    'sin': sin, 'cos': cos, 'tan': tan,
    'cot': cot, 'sec': sec, 'csc': csc,
    'asin': asin, 'acos': acos, 'atan': atan, 'atan2': atan2,
    'acot': acot, 'asec': asec, 'acsc': acsc,
    'sinh': sinh, 'cosh': cosh, 'tanh': tanh,
    'coth': coth, 'sech': sech, 'csch': csch,
    'asinh': asinh, 'acosh': acosh, 'atanh': atanh,
    'deg': lambda x: x * pi / 180, 'rad': lambda x: x * 180 / pi,

    # --- Exponential / logarithmic ----------------------------------------
    'log': log, 'ln': log, 'exp': exp,
    'log2': lambda x: log(x, 2), 'log10': lambda x: log(x, 10),
    'floor': floor, 'ceiling': ceiling, 'ceil': ceiling, 'frac': frac,

    # --- Calculus ----------------------------------------------------------
    'diff': diff, 'integrate': _integrate_wrapper,
    'limit': limit, 'series': series,
    'sum': _summation, 'Sum': _summation, 'summation': _summation,
    'product': _product, 'Product': _product,
    'dsolve': dsolve, 'rsolve': rsolve,
    'Function': Function, 'Derivative': Derivative,

    # --- Algebra / simplification -----------------------------------------
    'simplify': simplify, 'expand': expand,
    'factor': factor, 'cancel': cancel,
    'together': together, 'apart': apart,
    'radsimp': radsimp, 'ratsimp': ratsimp,
    'trigsimp': trigsimp, 'expand_trig': expand_trig,
    'powsimp': powsimp, 'logcombine': logcombine, 'expand_log': expand_log,
    'nsimplify': nsimplify,
    'degree': degree, 'roots': roots, 'real_roots': real_roots,
    'Poly': Poly,

    # --- Number theory -----------------------------------------------------
    'gcd': gcd, 'lcm': lcm, 'igcd': igcd, 'ilcm': ilcm,
    'isprime': isprime, 'prime': prime, 'primepi': primepi,
    'nextprime': nextprime, 'prevprime': prevprime,
    'totient': totient, 'divisors': lambda n: FiniteSet(*divisors(int(n))),
    'divisor_count': divisor_count, 'mod_inverse': mod_inverse,
    'factor_int': factorint, 'factorint': factorint,

    # --- Combinatorics -----------------------------------------------------
    'factorial': factorial,
    'binomial': binomial, 'nCr': binomial, 'C': binomial,
    'nPr': ff, 'P_perm': ff, 'ff': ff, 'rf': rf,
    'fibonacci': fibonacci, 'fib': fibonacci, 'lucas': lucas,
    'catalan': catalan, 'bernoulli': bernoulli, 'harmonic': harmonic,

    # --- Special functions -------------------------------------------------
    'gamma': gamma, 'beta': beta, 'erf': erf, 'zeta': zeta,

    # --- Statistics --------------------------------------------------------
    'mean': _mean, 'average': _mean, 'avg': _mean,
    'median': _median, 'mode': _mode,
    'variance': _variance, 'var': _variance,
    'stdev': _stdev, 'std': _stdev,
    'min': lambda *a: Min(*(_as_list(a[0]) if len(a) == 1 else a)),
    'max': lambda *a: Max(*(_as_list(a[0]) if len(a) == 1 else a)),
    'Min': Min, 'Max': Max,

    # --- Complex numbers ---------------------------------------------------
    're': sym_re, 'im': sym_im, 'conjugate': conjugate,
    'conj': conjugate, 'arg': arg,

    # --- Linear algebra ----------------------------------------------------
    'Matrix': _matrix, 'matrix': _matrix,
    'eye': eye, 'zeros': zeros, 'ones': ones, 'diag': diag,
    'det': lambda m: Matrix(m).det(),
    'trace': lambda m: Matrix(m).trace(),
    'transpose': lambda m: Matrix(m).T,
    'inv': lambda m: Matrix(m).inv(),
    'inverse': lambda m: Matrix(m).inv(),
    'rank': lambda m: Matrix(m).rank(),
    'rref': lambda m: Matrix(m).rref()[0],
    'eigenvals': lambda m: Matrix(m).eigenvals(),
    'eigenvects': lambda m: Matrix(m).eigenvects(),
    'nullspace': lambda m: Matrix(m).nullspace(),

    # --- Sets --------------------------------------------------------------
    'set': lambda *a: FiniteSet(*(_as_list(a[0]) if len(a) == 1 else a)),
    'FiniteSet': FiniteSet, 'Interval': Interval,
    'union': Union, 'Union': Union,
    'intersect': Intersection, 'Intersection': Intersection,
    'complement': Complement, 'Complement': Complement,
    'EmptySet': EmptySet,

    # --- Logic -------------------------------------------------------------
    'And': And, 'Or': Or, 'Not': Not,
    'Implies': Implies, 'Equivalent': Equivalent,
    'satisfiable': satisfiable,

    # --- Base conversions / numeric ---------------------------------------
    'to_base': _to_base, 'base': _to_base,
    'bin': _to_bin, 'hex': _to_hex, 'oct': _to_oct,
    'N': N, 'evalf': N, 'float': lambda x, n=15: N(x, n),
    'nsolve': nsolve, 'latex': latex,

    # --- Constants ---------------------------------------------------------
    'pi': pi, 'e': E, 'E': E, 'I': I, 'i': I,
    'oo': oo, 'inf': oo, 'nan': nan, 'zoo': zoo,
    'phi': GoldenRatio, 'golden': GoldenRatio, 'gamma_const': EulerGamma,
    'Rational': Rational,
}

# Function names that should NOT be auto-simplified after evaluation
# (simplify would undo their intent, return non-expr types, or be costly).
EXPLICIT_FNS = (
    'simplify', 'expand', 'factor', 'cancel', 'together', 'apart',
    'radsimp', 'ratsimp', 'trigsimp', 'expand_trig', 'powsimp',
    'logcombine', 'expand_log', 'nsimplify',
    'diff', 'integrate', 'limit', 'series', 'sum', 'summation', 'product',
    'dsolve', 'rsolve',
    'solve', 'nsolve', 'roots', 'real_roots', 'degree', 'poly', 'latex',
    'matrix', 'eye', 'zeros', 'ones', 'diag', 'det', 'trace', 'transpose',
    'inv', 'inverse', 'rank', 'rref', 'eigenvals', 'eigenvects', 'nullspace',
    'factor_int', 'factorint', 'gcd', 'lcm', 'igcd', 'ilcm', 'isprime',
    'prime', 'primepi', 'nextprime', 'prevprime', 'totient', 'divisors',
    'divisor_count', 'mod_inverse',
    'mean', 'average', 'avg', 'median', 'mode', 'variance', 'var',
    'stdev', 'std', 'min', 'max',
    'set', 'finiteset', 'interval', 'union', 'intersect', 'intersection',
    'complement', 'and', 'or', 'not', 'implies', 'equivalent', 'satisfiable',
    'to_base', 'base', 'bin', 'hex', 'oct', 'n', 'evalf', 'float',
)


# ---------------------------------------------------------------------------
# UI text
# ---------------------------------------------------------------------------
BANNER = f"""
╔══════════════════════════════════════════════════════════╗
║          Wafflez Algebra Calculator  v{__version__}              ║
║  Algebra · Equations · Fractions · Functions · Calculus  ║
╚══════════════════════════════════════════════════════════╝
Type 'help' for commands, 'quit' to exit.
"""

HELP_TEXT = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WAFFLEZ CALCULATOR — COMMAND REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BASIC ARITHMETIC
  3 + 4 * 2          →  standard math (use * for multiply)
  2^3  or  2**3      →  exponentiation (^ works too)
  1/3 + 1/6          →  exact fractions kept as fractions
  sqrt(16)           →  square root
  abs(-5)            →  absolute value

ALGEBRA / SIMPLIFY
  expand((x+1)^2)    →  expand expression
  factor(x^2-1)      →  factor expression
  simplify(...)      →  simplify expression
  cancel((x^2-1)/(x-1))   →  cancel common factors

SOLVE EQUATIONS
  2x + 4 = 0         →  auto-solves for x
  x^2 - 4 = 0        →  solve quadratic
  x^2 + x + 1 = 0    →  complex solutions
  solve(2x + y = 5, x - y = 1)   →  system of equations
  solve(a*x = b, x)  →  solve for a specific variable

FRACTIONS
  1/3 + 2/5          →  exact fraction result
  simplify(6/8)      →  reduce fraction

CALCULUS
  diff(x^3 + 2x, x)        →  derivative w.r.t. x
  diff(f, x, 2)            →  2nd derivative
  integrate(x^2, x)        →  indefinite integral
  integrate(x^2, x, 0, 1)  →  definite integral 0→1
  limit(sin(x)/x, x, 0)    →  limit as x→0
  series(sin(x), x, 0, 7)  →  Taylor series
  sum(k, k, 1, 100)        →  summation Σ
  product(k, k, 1, 5)      →  product Π

DIFFERENTIAL EQUATIONS  (f, g, h are functions)
  dsolve(diff(f(x), x) - f(x))        →  solve ODE
  dsolve(diff(f(x), x, 2) + f(x))     →  2nd-order ODE

TRIG / EXP / LOG  (rad by default; use deg(30) for degrees)
  sin, cos, tan, cot, sec, csc + inverses + hyperbolics
  log(100), log2(8), log10(1000), ln(e), exp(2)

COMBINATORICS
  factorial(10), binomial(10,3) / nCr(10,3)
  fibonacci(20), lucas(10), catalan(5)

STATISTICS  (pass a list)
  mean([1,2,3,4,5]), median([...]), mode([...])
  variance([...]), stdev([...])

LINEAR ALGEBRA
  det([[1,2],[3,4]])       →  determinant
  inv([[1,2],[3,4]])       →  inverse
  rref([[...],[...]])      →  reduced row echelon
  eigenvals(M), eigenvects(M), rank(M), transpose(M)
  matrix([[1,2]]) * matrix([[3],[4]])   →  multiply

NUMBER THEORY
  factor_int(360)    →  prime factorization
  gcd / lcm / igcd / ilcm
  totient(36), divisors(28), nextprime(100)
  mod_inverse(3, 11), isprime(97)

COMPLEX NUMBERS
  re(3+4I), im(3+4I), abs(3+4I), conjugate(3+4I), arg(I)

SETS & LOGIC
  union(set([1,2]), set([2,3])), intersect(...), Interval(0,1)
  And(x, y), Or(x, y), Not(x), satisfiable(...)

NUMERIC / BASES
  N(pi, 50)          →  50-digit decimal
  bin(10), hex(255), oct(8), to_base(255, 16)
  latex(x^2/2)       →  LaTeX source

SPECIAL VALUES
  pi, e, I (imaginary unit), oo (infinity), phi (golden ratio)

COMMANDS
  help               →  show this help
  clear              →  clear screen
  quit / exit        →  exit calculator

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIPS:
  • Implicit multiplication works: 2x = 2*x, (x+1)(x-1) = product
  • Use ^ or ** for powers
  • Variables x y z a b c n t k m p q r s u v w are auto-recognized
  • f, g, h are treated as functions (for calculus / ODEs)
  • A bare equation containing '=' is solved automatically
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ANSI colors (disabled automatically when output is not a TTY).
if sys.stdout.isatty() and os.environ.get('NO_COLOR') is None:
    C_PROMPT = '\033[96m'
    C_RESULT = '\033[92m'
    C_ERROR = '\033[91m'
    C_RESET = '\033[0m'
else:
    C_PROMPT = C_RESULT = C_ERROR = C_RESET = ''


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def format_result(result):
    """Pretty-print a SymPy result, indenting multi-line output."""
    try:
        txt = pretty(result, use_unicode=True)
    except Exception:
        return str(result)
    if '\n' in txt:
        return '\n' + txt
    return txt


def _parse(text):
    """Parse a single expression string into a SymPy object."""
    return parse_expr(text, local_dict=BUILTIN_LOCALS,
                      transformations=TRANSFORMATIONS)


def parse_equation(expr_str):
    """Parse 'LHS = RHS' into an Eq, or return None if not an equation."""
    # '=' but not '==', '<=', '>=', '!='
    if '=' not in expr_str:
        return None
    if '==' in expr_str or '<=' in expr_str or '>=' in expr_str or '!=' in expr_str:
        return None
    lhs, rhs = expr_str.split('=', 1)
    return Eq(_parse(lhs.strip()), _parse(rhs.strip()))


def detect_solve_vars(expr):
    """Choose which symbols to solve for, preferring x, y, z, ..."""
    free = expr.free_symbols
    preferred = [SYMBOL_DICT[s] for s in SOLVE_PREFERENCE
                 if s in SYMBOL_DICT and SYMBOL_DICT[s] in free]
    return preferred if preferred else sorted(free, key=str)


def _split_top_level(args_str):
    """Split on commas that are not nested inside (), [] or {}."""
    parts, depth, current = [], 0, []
    for ch in args_str:
        if ch in '([{':
            depth += 1
            current.append(ch)
        elif ch in ')]}':
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append(''.join(current).strip())
    return [p for p in parts if p]


def handle_solve_call(args_str):
    """Solve one equation or a system; supports trailing variable specs."""
    parts = _split_top_level(args_str)
    if not parts:
        return "No equations found."

    eqs, var_syms = [], []
    for p in parts:
        if p in SYMBOL_DICT:
            var_syms.append(SYMBOL_DICT[p])
            continue
        eq = parse_equation(p)
        eqs.append(eq if eq is not None else _parse(p))

    if not eqs:
        return "No equations found."

    if not var_syms:
        if len(eqs) == 1:
            var_syms = detect_solve_vars(eqs[0])
        else:
            all_free = set()
            for eq in eqs:
                all_free |= eq.free_symbols
            var_syms = sorted(all_free, key=str)

    result = solve(eqs[0], var_syms) if len(eqs) == 1 else solve(eqs, var_syms)

    if not result:
        return "No solution found."

    return _format_solutions(result, var_syms)


def _format_solutions(result, var_syms):
    """Render solve() output in a readable, consistent layout."""
    single_var = var_syms[0] if len(var_syms) == 1 else None

    if isinstance(result, dict):
        return "\n".join(f"  {k} = {format_result(v)}" for k, v in result.items())

    if isinstance(result, list):
        if len(result) == 1 and not isinstance(result[0], (list, tuple)):
            label = f"{single_var} = " if single_var is not None else ""
            return f"  {label}{format_result(result[0])}"
        lines = []
        for i, sol in enumerate(result, 1):
            if isinstance(sol, (list, tuple)):
                inner = ", ".join(f"{var_syms[j]} = {format_result(v)}"
                                  for j, v in enumerate(sol))
                lines.append(f"  Solution {i}: {inner}")
            else:
                label = f"{single_var} = " if single_var is not None else ""
                lines.append(f"  {label}{format_result(sol)}")
        return "\n".join(lines)

    return format_result(result)


def evaluate(user_input):
    """
    Evaluate one line of input.

    Returns a string to print, or None if there is nothing to display
    (e.g. blank input or a screen clear). Raises SystemExit on quit.
    """
    s = user_input.strip().rstrip(';').strip()
    if not s:
        return None

    low = s.lower()
    if low in ('quit', 'exit', 'q'):
        raise SystemExit(0)
    if low == 'help':
        return HELP_TEXT
    if low == 'clear':
        clear_screen()
        return None

    # Explicit solve(...) call — handle systems and variable specs.
    if low.startswith('solve(') and s.endswith(')'):
        return handle_solve_call(s[len('solve('):-1])

    # A bare equation (contains '=') is auto-solved.
    if parse_equation(s) is not None:
        return handle_solve_call(s)

    # Otherwise evaluate as an expression.
    result = _parse(s)

    # Auto-simplify plain expressions only; explicit calls keep their form.
    if not any(low.startswith(fn.lower() + '(') for fn in EXPLICIT_FNS):
        result = simplify(result)

    return format_result(result)


def _format_error(exc):
    """Turn an exception into a concise, user-friendly message."""
    msg = str(exc)
    if isinstance(exc, ZeroDivisionError):
        return "Division by zero."
    if isinstance(exc, SympifyError):
        return f"Could not parse expression: {msg}"
    syntax_markers = (
        'invalid syntax', 'unexpected EOF', 'EOF in multi-line',
        'EOF in multi-line statement', 'unbalanced', 'tokenize',
        'unmatched', 'was never closed',
    )
    if isinstance(exc, (SyntaxError, TokenError)) or any(m in msg for m in syntax_markers):
        return "Syntax error — check your expression (unbalanced parentheses?)."
    if isinstance(exc, (NameError, KeyError)):
        return f"Unknown name: {msg}"
    return f"Error: {msg}"


def repl():
    """Run the interactive read-eval-print loop."""
    print(BANNER)
    while True:
        try:
            user_input = input(f"{C_PROMPT} calc> {C_RESET}")
        except EOFError:
            print("\nGoodbye!")
            break
        except KeyboardInterrupt:
            # Ctrl-C cancels the current line rather than killing the app.
            print("\n(Use 'quit' or Ctrl-D to exit.)")
            continue

        if not user_input.strip():
            continue

        try:
            result = evaluate(user_input)
            if result is not None:
                print(f"{C_RESULT}  = {result}{C_RESET}")
        except SystemExit:
            print("Goodbye!")
            break
        except KeyboardInterrupt:
            print(f"\n{C_ERROR}  Cancelled.{C_RESET}")
        except RecursionError:
            print(f"{C_ERROR}  Expression too complex to evaluate.{C_RESET}")
        except Exception as exc:  # noqa: BLE001 - REPL must never crash
            print(f"{C_ERROR}  {_format_error(exc)}{C_RESET}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if argv:
        # Single-shot mode: python3 calculator.py "x^2 - 4 = 0"
        expr = ' '.join(argv)
        try:
            result = evaluate(expr)
            if result is not None:
                print(result)
            return 0
        except SystemExit:
            return 0
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(_format_error(exc) + "\n")
            return 1

    repl()
    return 0


if __name__ == '__main__':
    sys.exit(main())
