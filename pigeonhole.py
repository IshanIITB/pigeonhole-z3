#!/usr/bin/env python3
"""Pigeonhole principle with Z3: place m pigeons into n holes,
every pigeon gets a hole and no hole holds two pigeons.

Satisfiable  <=>  m <= n.  The interesting side is UNSAT (m > n):
the pigeonhole principle has no short resolution proof, so runtimes
explode exponentially as m,n grow.

Encodings compared:
  bool : x[i][j] = Bool("pigeon i sits in hole j") -- CNF style,
         one clause per pigeon, pairwise clauses per hole
  int  : h[i] = Int hole index in [0, n) + Distinct -- SMT style

Usage:  venv/bin/python pigeonhole.py
"""

import itertools
import time

from z3 import Bool, Distinct, Int, Not, Or, Solver

TIMEOUT_MS = 20_000


def encode_bool(m, n):
    s = Solver()
    s.set("timeout", TIMEOUT_MS)
    x = [[Bool(f"p{i}_{j}") for j in range(n)] for i in range(m)]
    for i in range(m):                            # pigeon i needs a hole
        s.add(Or(x[i]))
    for j in range(n):                            # hole j holds <= 1 pigeon
        for i, k in itertools.combinations(range(m), 2):
            s.add(Or(Not(x[i][j]), Not(x[k][j])))
    return s, {"vars": m * n, "cons": len(s.assertions())}, x


def encode_int(m, n):
    s = Solver()
    s.set("timeout", TIMEOUT_MS)
    h = [Int(f"h{i}") for i in range(m)]
    for i in range(m):
        s.add(0 <= h[i], h[i] < n)
    s.add(Distinct(h))
    return s, {"vars": m, "cons": len(s.assertions())}, h


def run(m, n, encoding):
    s, stats, _ = encoding(m, n)
    t0 = time.perf_counter()
    res = s.check()
    dt = time.perf_counter() - t0
    return res, dt, stats


def show_model(m, n):
    s, _, x = encode_bool(m, n)
    assert str(s.check()) == "sat"
    model = s.model()
    placement = [next(j for j in range(n) if model.eval(x[i][j])) for i in range(m)]
    print(f"example model, m={m} pigeons into n={n} holes:")
    for i, j in enumerate(placement):
        print(f"  pigeon {i} -> hole {j}")
    print()


CASES = [(4, 4), (5, 4), (6, 4), (4, 5), (8, 8), (9, 8), (10, 9), (11, 10), (12, 11)]


def main():
    show_model(8, 8)

    hdr = (f"{'m':>3} {'n':>3}  {'expect':<6} {'enc':<5} "
           f"{'result':<8} {'vars':>5} {'cons':>6} {'time':>10}")
    print(hdr)
    print("-" * len(hdr))
    for m, n in CASES:
        expect = "sat" if m <= n else "unsat"
        for enc in (encode_bool, encode_int):
            res, dt, stats = run(m, n, enc)
            name = "bool" if enc is encode_bool else "int"
            print(f"{m:>3} {n:>3}  {expect:<6} {name:<5} "
                  f"{str(res):<8} {stats['vars']:>5} {stats['cons']:>6} "
                  f"{dt:>9.3f}s", flush=True)
    print("\nresult 'unknown' = solver hit the 20 s timeout")


if __name__ == "__main__":
    main()
