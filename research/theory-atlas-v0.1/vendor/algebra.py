"""Small exact rational-expression kernel. No eval, floating point or domain solver.

It checks algebra, dimensions and conservative boxes supplied by the caller.
Denominator obligations are retained even when an expression cancels to zero.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from fractions import Fraction as F

MAX_TERMS, MAX_DEGREE, MAX_NODES = 256, 24, 400


def merge_guards(*groups):
    unique = {}
    for group in groups:
        for guard in group:
            key = (tuple(sorted(guard.n.items())), tuple(sorted(guard.d.items())))
            unique[key] = guard
            if len(unique) > 128:
                raise ValueError('Domain obligation budget exceeded')
    return list(unique.values())


def clean(p):
    result = {m: c for m, c in p.items() if c}
    if len(result) > MAX_TERMS or any(sum(e for _, e in m) > MAX_DEGREE for m in result):
        raise ValueError('Polynomial budget exceeded')
    if any(max(abs(c.numerator).bit_length(), c.denominator.bit_length()) > 2048 for c in result.values()):
        raise ValueError('Coefficient budget exceeded')
    return result


def add(p, q):
    r = dict(p)
    for m, c in q.items():
        r[m] = r.get(m, F(0)) + c
    return clean(r)


def mul(p, q):
    if len(p) * len(q) > 65536:
        raise ValueError('Multiplication budget exceeded')
    r = {}
    for m, c in p.items():
        for n, d in q.items():
            powers = dict(m)
            for name, exponent in n:
                powers[name] = powers.get(name, 0) + exponent
            key = tuple(sorted(powers.items()))
            r[key] = r.get(key, F(0)) + c * d
    return clean(r)


def diff(p, name):
    r = {}
    for m, c in p.items():
        powers = dict(m)
        exponent = powers.get(name, 0)
        if not exponent:
            continue
        if exponent == 1:
            del powers[name]
        else:
            powers[name] -= 1
        key = tuple(sorted(powers.items()))
        r[key] = r.get(key, F(0)) + c * exponent
    return clean(r)


def polynomial_text(p):
    if not p:
        return '0'
    return ' + '.join(f'({c})' + ''.join(f'*{v}' + (f'**{e}' if e != 1 else '') for v,e in m)
                      for m,c in sorted(p.items()))


@dataclass
class Rational:
    n: dict
    d: dict

    def __post_init__(self):
        self.n, self.d = clean(self.n), clean(self.d)
        if not self.d:
            raise ValueError('Identically zero denominator')
        # Only constant normalization; preserve other denominator conditions.
        if set(self.d) == {()}:
            c = self.d[()]
            self.n = clean({m: a/c for m,a in self.n.items()})
            self.d = {(): F(1)}

    @classmethod
    def constant(cls, value):
        return cls({(): F(value)}, {(): F(1)})

    @classmethod
    def variable(cls, name):
        return cls({((name, 1),): F(1)}, {(): F(1)})

    def __add__(self, other):
        return Rational(add(mul(self.n, other.d), mul(other.n, self.d)), mul(self.d, other.d))

    def __neg__(self):
        return Rational({m:-c for m,c in self.n.items()}, self.d)

    def __sub__(self, other):
        return self + -other

    def __mul__(self, other):
        return Rational(mul(self.n, other.n), mul(self.d, other.d))

    def __truediv__(self, other):
        return Rational(mul(self.n, other.d), mul(self.d, other.n))

    def power(self, exponent):
        if type(exponent) is not int or not 0 <= exponent <= 12:
            raise ValueError('Only integer powers 0..12 are supported')
        result = Rational.constant(1)
        for _ in range(exponent):
            result = result * self
        return result

    def derivative(self, name):
        return Rational(add(mul(diff(self.n, name), self.d), {m:-c for m,c in mul(self.n,diff(self.d,name)).items()}), mul(self.d,self.d))

    def equal(self, other):
        return mul(self.n, other.d) == mul(other.n, self.d)

    def value(self, values):
        def evaluate(poly):
            out = F(0)
            for m,c in poly.items():
                for v,e in m:
                    c *= F(values[v]) ** e
                out += c
            return out
        denominator = evaluate(self.d)
        if not denominator:
            raise ValueError('Undefined at supplied values')
        return evaluate(self.n) / denominator

    def text(self):
        n = polynomial_text(self.n)
        return n if self.d == {():F(1)} else f'({n}) / ({polynomial_text(self.d)})'


def dimensions(left, right, sign=1):
    result = dict(left)
    for k,v in right.items():
        result[k] = result.get(k, 0) + sign*v
    return {k:v for k,v in result.items() if v}


@dataclass
class Expression:
    ratio: Rational
    units: dict
    guards: list

    def derivative(self, name, units):
        return Expression(self.ratio.derivative(name), dimensions(self.units, units, -1), list(self.guards))


class Compiler:
    def __init__(self, symbols, functions=None):
        self.symbols = symbols
        self.functions = functions or {}
        self.results = {}
        if len(self.functions) > 20:
            raise ValueError('Function budget exceeded')
        for name, definition in self.functions.items():
            body, arguments = definition.get('expression'), definition.get('arguments')
            if not name.isidentifier() or name.startswith('_') or name in symbols:
                raise ValueError('Invalid function name')
            if not isinstance(body, str) or len(body) > 4000 or not isinstance(arguments, list) or len(arguments) > 12:
                raise ValueError('Invalid function definition')
            if len(set(arguments)) != len(arguments) or any(not isinstance(x,str) or not x.isidentifier() for x in arguments):
                raise ValueError('Invalid function arguments')

    def compile(self, source):
        if not isinstance(source, str) or len(source) > 4000:
            raise ValueError('Expression must be a short string')
        tree = ast.parse(source, mode='eval')
        self.nodes = 0
        return self._visit(tree.body, {}, ())

    def _visit(self, node, local, stack):
        self.nodes += 1
        if self.nodes > MAX_NODES or len(stack) > 12:
            raise ValueError('Expression budget exceeded')
        if isinstance(node, ast.Constant) and type(node.value) is int and abs(node.value).bit_length() <= 512:
            return Expression(Rational.constant(node.value), {}, [])
        if isinstance(node, ast.Name):
            if node.id in local:
                return local[node.id]
            if node.id in self.results:
                return self.results[node.id]
            if node.id in self.symbols:
                return Expression(Rational.variable(node.id), self.symbols[node.id].get('units', {}), [])
            raise ValueError(f'Unknown symbol: {node.id}')
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            x = self._visit(node.operand, local, stack)
            return Expression(-x.ratio if isinstance(node.op, ast.USub) else x.ratio, x.units, list(x.guards))
        if isinstance(node, ast.BinOp):
            left = self._visit(node.left, local, stack)
            if isinstance(node.op, ast.Pow):
                if not isinstance(node.right, ast.Constant) or type(node.right.value) is not int:
                    raise ValueError('Power must be a literal integer')
                e = node.right.value
                return Expression(left.ratio.power(e), {k:v*e for k,v in left.units.items() if v*e}, list(left.guards))
            right = self._visit(node.right, local, stack)
            guards = merge_guards(left.guards, right.guards)
            if isinstance(node.op, (ast.Add, ast.Sub)):
                left_zero = not left.ratio.n and not left.units
                right_zero = not right.ratio.n and not right.units
                if left.units != right.units and not (left_zero or right_zero):
                    raise ValueError('Dimension mismatch in addition/subtraction')
                units = right.units if left_zero else left.units
                value = left.ratio + right.ratio if isinstance(node.op, ast.Add) else left.ratio - right.ratio
            elif isinstance(node.op, ast.Mult):
                units, value = dimensions(left.units, right.units), left.ratio * right.ratio
            elif isinstance(node.op, ast.Div):
                units, value = dimensions(left.units, right.units, -1), left.ratio / right.ratio
                guards = merge_guards(guards, [right.ratio])
            else:
                raise ValueError('Unsupported operator')
            return Expression(value, units, guards)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            name = node.func.id
            if name not in self.functions or name in stack:
                raise ValueError('Unknown or recursive function')
            fn = self.functions[name]
            if len(node.args) != len(fn['arguments']):
                raise ValueError('Wrong function arity')
            args = [self._visit(x, local, stack) for x in node.args]
            body = ast.parse(fn['expression'], mode='eval').body
            result = self._visit(body, dict(zip(fn['arguments'], args)), stack + (name,))
            return Expression(result.ratio, result.units, merge_guards(result.guards, *(arg.guards for arg in args)))
        raise ValueError('Unsupported expression syntax')


def interval_product(a, b):
    values = [x*y for x in a for y in b]
    return min(values), max(values)


def polynomial_interval(poly, boxes):
    result = (F(0), F(0))
    for monomial, coefficient in poly.items():
        term = (coefficient, coefficient)
        for name, exponent in monomial:
            lo, hi = map(F, boxes[name])
            if lo > hi:
                raise ValueError('Reversed interval')
            ends = (lo**exponent, hi**exponent)
            power = (F(0) if exponent % 2 == 0 and lo <= 0 <= hi else min(ends), max(ends))
            term = interval_product(term, power)
        result = result[0]+term[0], result[1]+term[1]
    return result


def interval(expr, boxes):
    n, d = polynomial_interval(expr.n, boxes), polynomial_interval(expr.d, boxes)
    if d[0] <= 0 <= d[1]:
        return None
    return interval_product(n, (F(1)/d[1], F(1)/d[0]))


def domain_report(expression, boxes):
    pending = []
    seen = set()
    for guard in expression.guards:
        label = guard.text()
        if label in seen:
            continue
        seen.add(label)
        value = interval(guard, boxes)
        if value is None or value[0] <= 0 <= value[1]:
            pending.append(label + ' != 0')
    return {'status': 'pending_nonzero_conditions' if pending else 'established_on_declared_box', 'conditions': pending}
