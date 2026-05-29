#!/usr/bin/env python3
"""
Wafflez Algebra Calculator
Supports: algebra, equations, fractions, functions, calculus
"""

import sys
import re
from fractions import Fraction as PyFraction

try:
    from sympy import (
        symbols, solve, simplify, expand, factor, Symbol,
        sqrt, Rational, pi, E, I, oo, zoo,
        sin, cos, tan, asin, acos, atan, sinh, cosh, tanh,
        log, ln, exp, Abs, floor, ceiling,
        diff, integrate, limit, series,
        Eq, Ne, Lt, Le, Gt, Ge,
        Matrix, det, trace,
        cancel, together, apart, radsimp,
        gcd, lcm, factorint, isprime,
        nsolve, nsimplify,
        latex, pretty,
        sympify, SympifyError,
        Number, Float, Integer,
        pprint,
    )
    from sympy.parsing.sympy_parser import (
        parse_expr,
        standard_transformations,
        implicit_multiplication_application,
        convert_xor,
    )
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False

TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

BANNER = """
╔══════════════════════════════════════════════════════════╗
║         Wafflez Algebra Calculator  v1.0                ║
║  Algebra · Equations · Fractions · Functions · Calculus ║
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
  cancel((x^2-1)/(x-1))  →  cancel common factors

SOLVE EQUATIONS
  solve(2x + 4 = 0)  →  solve for x
  solve(x^2 - 4 = 0) →  solve quadratic
  solve(x^2 + x + 1 = 0)  →  complex solutions
  solve(2x + y = 5, x - y = 1)  →  system of equations

FRACTIONS
  1/3 + 2/5          →  exact fraction result
  simplify(6/8)      →  simplify fraction

FUNCTIONS & CALCULUS
  diff(x^3 + 2x, x)       →  derivative w.r.t. x
  integrate(x^2, x)        →  indefinite integral
  integrate(x^2, x, 0, 1)  →  definite integral 0→1
  limit(sin(x)/x, x, 0)   →  limit as x→0
  series(sin(x), x, 0, 5)  →  Taylor series

TRIG / MATH FUNCTIONS
  sin(pi/6), cos(pi), tan(pi/4)
  asin(1), acos(0), atan(1)
  log(100), ln(e), exp(2)

MATRICES
  matrix([[1,2],[3,4]])       →  define matrix
  det([[1,2],[3,4]])          →  determinant
  matrix([[1,2],[3,4]]) * matrix([[5,6],[7,8]])  → multiply

NUMBER THEORY
  factor_int(360)    →  prime factorization
  gcd(48, 18)        →  greatest common divisor
  lcm(12, 18)        →  least common multiple
  isprime(97)        →  primality test

SPECIAL VALUES
  pi, e, I (imaginary unit), oo (infinity)

COMMANDS
  help               →  show this help
  clear              →  clear screen
  quit / exit        →  exit calculator

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIPS:
  • Implicit multiplication works: 2x = 2*x, (x+1)(x-1) = product
  • Use ^ or ** for powers
  • Variables: x, y, z, a, b, c, n, t, k are auto-recognized
  • solve() auto-detects equations with '='
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

ALL_SYMBOLS = symbols('x y z a b c n t k m p q r s u v w')
SYMBOL_DICT = {str(s): s for s in ALL_SYMBOLS}

def _integrate_wrapper(*args):
    """Support both integrate(f, x) and integrate(f, x, a, b) syntax."""
    if len(args) == 3:
        return integrate(args[0], (args[1], args[2]))
    if len(args) == 4:
        return integrate(args[0], (args[1], args[2], args[3]))
    return integrate(*args)


BUILTIN_LOCALS = {
    **SYMBOL_DICT,
    'sqrt': sqrt, 'abs': Abs, 'Abs': Abs,
    'sin': sin, 'cos': cos, 'tan': tan,
    'asin': asin, 'acos': acos, 'atan': atan,
    'sinh': sinh, 'cosh': cosh, 'tanh': tanh,
    'log': log, 'ln': log, 'exp': exp,
    'floor': floor, 'ceiling': ceiling, 'ceil': ceiling,
    'diff': diff, 'integrate': _integrate_wrapper,
    'limit': limit, 'series': series,
    'simplify': simplify, 'expand': expand,
    'factor': factor, 'cancel': cancel,
    'together': together, 'apart': apart,
    'gcd': gcd, 'lcm': lcm,
    'isprime': isprime,
    'pi': pi, 'e': E, 'E': E, 'I': I,
    'oo': oo, 'inf': oo,
    'Rational': Rational,
    'Matrix': Matrix,
    'det': lambda m: Matrix(m).det(),
    'trace': lambda m: Matrix(m).trace(),
    'matrix': Matrix,
    'factor_int': factorint,
}


def clear_screen():
    import os
    os.system('clear' if os.name != 'nt' else 'cls')


def format_result(result):
    """Pretty-print a sympy result."""
    try:
        txt = pretty(result, use_unicode=True)
        # If multi-line, add spacing
        if '\n' in txt:
            return '\n' + txt
        return txt
    except Exception:
        return str(result)


def parse_equation(expr_str):
    """Detect and parse 'LHS = RHS' style equations."""
    if '=' in expr_str and '==' not in expr_str:
        parts = expr_str.split('=', 1)
        lhs = parse_expr(parts[0].strip(), local_dict=BUILTIN_LOCALS,
                         transformations=TRANSFORMATIONS)
        rhs = parse_expr(parts[1].strip(), local_dict=BUILTIN_LOCALS,
                         transformations=TRANSFORMATIONS)
        return Eq(lhs, rhs)
    return None


def detect_solve_vars(expr):
    """Pick which symbols to solve for (prefer x, then y, etc.)."""
    free = expr.free_symbols
    preference = [SYMBOL_DICT[s] for s in ['x','y','z','a','b','c','n','t','k']
                  if s in SYMBOL_DICT and SYMBOL_DICT[s] in free]
    return preference if preference else list(free)


def handle_solve_call(args_str):
    """Handle solve(...) with optional system-of-equations syntax."""
    # Split on top-level commas, respecting parentheses
    parts = []
    depth = 0
    current = []
    for ch in args_str:
        if ch == '(':
            depth += 1
            current.append(ch)
        elif ch == ')':
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append(''.join(current).strip())

    # Separate equations from variable specifications
    eqs = []
    var_syms = []
    for p in parts:
        if p in SYMBOL_DICT:
            var_syms.append(SYMBOL_DICT[p])
        else:
            eq = parse_equation(p)
            if eq is not None:
                eqs.append(eq)
            else:
                expr = parse_expr(p, local_dict=BUILTIN_LOCALS,
                                  transformations=TRANSFORMATIONS)
                eqs.append(expr)

    if not eqs:
        return "No equations found."

    if not var_syms:
        all_free = set()
        for eq in eqs:
            all_free |= eq.free_symbols
        var_syms = detect_solve_vars(eqs[0]) if len(eqs) == 1 else sorted(all_free, key=str)

    if len(eqs) == 1:
        result = solve(eqs[0], var_syms)
    else:
        result = solve(eqs, var_syms)

    if not result:
        return "No solution found."

    # Format nicely
    if isinstance(result, dict):
        lines = []
        for k, v in result.items():
            lines.append(f"  {k} = {format_result(v)}")
        return "\n".join(lines)
    elif isinstance(result, list):
        if len(result) == 1:
            return f"  {var_syms[0] if len(var_syms)==1 else ''} = {format_result(result[0])}"
        lines = []
        for i, sol in enumerate(result):
            if isinstance(sol, (list, tuple)):
                inner = ", ".join(f"{var_syms[j]} = {format_result(v)}"
                                  for j, v in enumerate(sol))
                lines.append(f"  Solution {i+1}: {inner}")
            else:
                lines.append(f"  {var_syms[0] if len(var_syms)==1 else ''} = {format_result(sol)}")
        return "\n".join(lines)
    return format_result(result)


def evaluate(user_input):
    """Main evaluation logic."""
    s = user_input.strip()

    # Strip trailing semicolons
    s = s.rstrip(';').strip()

    if not s:
        return None

    # Special commands
    low = s.lower()
    if low in ('quit', 'exit', 'q'):
        raise SystemExit(0)
    if low == 'help':
        return HELP_TEXT
    if low == 'clear':
        clear_screen()
        return None

    # Intercept solve(...) specially for multi-equation support
    solve_match = re.match(r'^solve\((.+)\)$', s, re.DOTALL | re.IGNORECASE)
    if solve_match:
        return handle_solve_call(solve_match.group(1))

    # Check if bare equation (has '=' but no leading function name)
    eq = parse_equation(s)
    if eq is not None:
        # Auto-solve it
        return handle_solve_call(s)

    # Otherwise evaluate as expression
    result = parse_expr(s, local_dict=BUILTIN_LOCALS, transformations=TRANSFORMATIONS)

    # Only auto-simplify plain expressions, not explicit function calls
    # (simplify can undo factor/expand/etc.)
    explicit_fns = ('simplify','expand','factor','cancel','together','apart',
                    'diff','integrate','limit','series','solve','matrix','det',
                    'trace','factor_int','gcd','lcm','isprime')
    is_explicit = any(s.lower().startswith(fn + '(') for fn in explicit_fns)
    if not is_explicit:
        result = simplify(result)

    return format_result(result)


def repl():
    print(BANNER)
    history = []

    while True:
        try:
            user_input = input("\033[96m calc> \033[0m").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        history.append(user_input)

        try:
            result = evaluate(user_input)
            if result is not None:
                print(f"\033[92m  = {result}\033[0m")
        except SystemExit:
            print("Goodbye!")
            break
        except ZeroDivisionError:
            print("\033[91m  Error: Division by zero.\033[0m")
        except SympifyError as e:
            print(f"\033[91m  Parse error: {e}\033[0m")
        except Exception as e:
            # Try to give a helpful message
            msg = str(e)
            if 'unexpected EOF' in msg or 'invalid syntax' in msg:
                print(f"\033[91m  Syntax error — check your expression.\033[0m")
            else:
                print(f"\033[91m  Error: {msg}\033[0m")


if __name__ == '__main__':
    if not SYMPY_AVAILABLE:
        print("Error: sympy is not installed. Run: pip install sympy")
        sys.exit(1)

    # Non-interactive single-expression mode: python calculator.py "2x+4=0"
    if len(sys.argv) > 1:
        expr = ' '.join(sys.argv[1:])
        try:
            result = evaluate(expr)
            if result:
                print(result)
        except SystemExit:
            pass
        except Exception as e:
            print(f"Error: {e}")
        sys.exit(0)

    repl()
