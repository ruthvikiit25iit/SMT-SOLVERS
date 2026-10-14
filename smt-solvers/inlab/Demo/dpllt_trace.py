#!/usr/bin/env python3
"""Step-by-step DPLL(T) trace in plain language.

Shows, for a formula given as clauses:
  1. the propositional encoding (each theory atom becomes a Boolean variable p1, p2, ...)
  2. the search: decisions, forced assignments, theory conflicts, lemmas, backtracking
  3. a cross-check against Z3's real answer

This is a simplified textbook DPLL(T): a tiny SAT engine written here, with Z3 acting as the
theory solver. Real Z3 is smarter (it learns better clauses, backjumps, and often solves small
formulas by preprocessing alone), so its exact order of steps differs.

Usage
    python demo/dpllt_trace.py                      # built-in example 1
    python demo/dpllt_trace.py --example 3
    python demo/dpllt_trace.py "Or(x > 5, y > 5)" "x < 0" "y < 0" --ints x y
Where Z3 checks consistency: every 'check' line in the trace is one call to Z3 on the literals assigned so far.
It happens after propagation finishes and before each new decision, not only when every variable is assigned.
On a conflict the learned clause is the negation of the decisions made so far.
Constraints must be clauses: an atom, Not(atom), or Or(...) of those (top-level And is split).
"""
import argparse
import sys

from z3 import *

EXAMPLES = {
    1: ("Needs backtracking, ends UNSAT",
        ["x", "y"], ["Or(x > 5, y > 5)", "x < 0", "y < 0"]),
    2: ("Backtracks once, then SAT",
        ["x", "y"], ["Or(x > 5, y > 5)", "x < 0"]),
    3: ("Wrong first guess, then SAT",
        ["x", "y"], ["Or(x > 5, x < -5)", "Or(y > 5, y < -5)", "x + y == 0"]),
}

LOGIC = (Z3_OP_AND, Z3_OP_OR, Z3_OP_NOT, Z3_OP_IMPLIES, Z3_OP_ITE, Z3_OP_XOR, Z3_OP_TRUE, Z3_OP_FALSE)


# ---------------------------------------------------------------------------
# Step 1: propositional encoding
# ---------------------------------------------------------------------------
class Encoding:
    def __init__(self, constraints):
        self.atoms = []           # atoms[i] is the theory atom for variable p(i+1)
        self.clauses = []         # each clause is a list of non-zero ints (negative = negated)
        for c in constraints:
            self._add(c)

    @staticmethod
    def _is_atom(e):
        return (is_app(e) and e.sort() == BoolSort() and e.decl().kind() not in LOGIC)

    def _var(self, atom):
        for i, a in enumerate(self.atoms):
            if eq(a, atom):
                return i + 1
        self.atoms.append(atom)
        return len(self.atoms)

    def _lit(self, e):
        if is_not(e) and self._is_atom(e.arg(0)):
            return -self._var(e.arg(0))
        if self._is_atom(e):
            return self._var(e)
        raise ValueError(f"not a literal: {e}")

    def _add(self, e):
        if is_and(e):
            for c in e.children():
                self._add(c)
        elif is_or(e):
            self.clauses.append([self._lit(c) for c in e.children()])
        elif is_implies(e):
            self.clauses.append([-self._lit(e.arg(0)), self._lit(e.arg(1))])
        else:
            self.clauses.append([self._lit(e)])


def lit_str(l):
    return ("¬" if l < 0 else "") + f"p{abs(l)}"


def clause_str(c):
    return " ∨ ".join(lit_str(l) for l in c) if c else "(empty)"


# ---------------------------------------------------------------------------
# Step 2: the search
# ---------------------------------------------------------------------------
class Tracer:
    def __init__(self, enc):
        self.enc = enc
        self.atoms = enc.atoms
        self.clauses = [list(c) for c in enc.clauses]
        self.value = {}                  # var -> bool
        self.trail = []                  # vars in assignment order
        self.model = None
        self.decisions = 0
        self.conflicts = 0
        self.checks = 0
        self.log = []                    # every printed line, as (level, text)
        self.observer = None             # optional callback(info) after each theory check
        self._prev_ok = {}               # assignment at the last consistent theory check

    # ----- helpers -----
    def name(self, v):
        return f"p{v} ({self.atoms[v - 1]})"

    def lit_value(self, l):
        v = self.value.get(abs(l))
        return None if v is None else (v if l > 0 else not v)

    def assign(self, v, val):
        self.value[v] = val
        self.trail.append(v)

    def undo_to(self, n):
        while len(self.trail) > n:
            del self.value[self.trail.pop()]

    def say(self, level, text):
        print("    " * level + text)
        self.log.append((level, text))

    def blank(self):
        print()
        self.log.append((0, ""))

    def event(self, level, label, text):
        self.say(level, f"{label:<10} {text}")

    # ----- Boolean propagation -----
    def propagate(self, level):
        """Returns ('conflict', clause_index) or ('ok', None)."""
        while True:
            progressed = False
            for ci, c in enumerate(self.clauses):
                vals = [self.lit_value(l) for l in c]
                if True in vals:
                    continue
                free = [l for l, v in zip(c, vals) if v is None]
                if not free:
                    return "conflict", ci
                if len(free) == 1:
                    l = free[0]
                    why = ("it is a unit clause" if len(c) == 1 else
                           "all other literals are False")
                    self.assign(abs(l), l > 0)
                    self.event(level, "propagate", f"{self.name(abs(l))} = {l > 0}"
                                              f"   [C{ci + 1}: {clause_str(c)} -- {why}]")
                    progressed = True
            if not progressed:
                return "ok", None

    # ----- theory check (Z3 plays the theory solver) -----
    def _infeasible(self, vs):
        s = Solver()
        for v in vs:
            atom = self.atoms[v - 1]
            s.add(atom if self.value[v] else Not(atom))
        return s.check() == unsat

    def _minimise(self, core):
        """Drop literals one by one while the rest is still contradictory (deterministic)."""
        core = list(core)
        i = 0
        while i < len(core):
            trial = core[:i] + core[i + 1:]
            if trial and self._infeasible(trial):
                core = trial
            else:
                i += 1
        return core

    def _notify(self, kind, level, core, model):
        if self.observer is None:
            return
        new = [v for v in self.trail if self._prev_ok.get(v) != self.value[v]]
        self.observer({"kind": kind, "level": level, "trail": list(self.trail),
                       "values": dict(self.value), "new": new, "core": core,
                       "model": model, "log_end": len(self.log)})

    def theory_check(self, level, stack):
        self.checks += 1
        s = Solver()
        tags = {}
        for v in self.trail:
            atom = self.atoms[v - 1]
            tag = Bool(f"t{v}")
            tags[str(tag)] = v
            s.assert_and_track(atom if self.value[v] else Not(atom), tag)
        shown_now = ", ".join(str(self.atoms[v - 1]) if self.value[v] else f"not({self.atoms[v - 1]})"
                              for v in self.trail)
        self.event(level, "check", f"Z3 consistency check #{self.checks} on: {shown_now}")
        r = s.check()
        if r == sat:
            self.model = s.model()
            self.event(level, "theory", "consistent")
            self._notify("ok", level, None, self.model)
            self._prev_ok = dict(self.value)
            return None
        core = self._minimise(sorted(tags[str(t)] for t in s.unsat_core()))
        shown = ", ".join(str(self.atoms[v - 1]) if self.value[v] else f"not({self.atoms[v - 1]})"
                          for v in core)
        decisions = [d for d in stack if not d["flipped"]]
        lemma = [-d["var"] if d["val"] else d["var"] for d in decisions]
        self.event(level, "theory", f"CONFLICT: {shown} cannot all hold")
        self.clauses.append(lemma)
        self.event(level, "learn", f"C{len(self.clauses)}: {clause_str(lemma)}   (negation of the decisions)")
        self._notify("conflict", level, core, None)
        return lemma

    # ----- main loop -----
    def run(self):
        stack = []          # decisions: dict(var, val, flipped, mark)
        level = 0
        self.say(0, "Level 0 (no decisions yet)")
        while True:
            status, ci = self.propagate(level)
            if status == "conflict":
                self.conflicts += 1
                self.event(level, "conflict", f"C{ci + 1} ({clause_str(self.clauses[ci])}) is False under the current assignment")
                bad = True
            else:
                bad = self.theory_check(level, stack) is not None
                if bad:
                    self.conflicts += 1

            if bad:
                while stack and stack[-1]["flipped"]:
                    stack.pop()
                if not stack:
                    self.event(level, "result", "no decision left to change  ->  UNSAT")
                    return "unsat"
                d = stack.pop()
                self.undo_to(d["mark"])
                level = d["level"]
                self.event(level, "backtrack", f"undo decision p{d['var']} = {d['val']} and everything after it")
                self.blank()
                self.say(level, f"Level {level}: flip p{d['var']} = {not d['val']}  (try the other value)")
                self.assign(d["var"], not d["val"])
                stack.append({**d, "val": not d["val"], "flipped": True, "mark": d["mark"]})
                continue

            if all(True in [self.lit_value(l) for l in c] for c in self.clauses):
                self.event(level, "result", "every clause is satisfied  ->  SAT")
                return "sat"
            free = [v for v in range(1, len(self.atoms) + 1) if v not in self.value]
            v = free[0]
            level += 1
            self.decisions += 1
            self.blank()
            self.say(level, f"Level {level}: decide  {self.name(v)} = True   (a guess)")
            stack.append({"var": v, "val": True, "flipped": False, "mark": len(self.trail), "level": level})
            self.assign(v, True)


# ---------------------------------------------------------------------------
def build_constraints(strings, ints, reals, bools):
    ns = {k: v for k, v in z3_namespace().items()}
    for n in ints:
        ns[n] = Int(n)
    for n in reals:
        ns[n] = Real(n)
    for n in bools:
        ns[n] = Bool(n)
    out = []
    for s in strings:
        try:
            out.append(eval(s, {"__builtins__": {}}, ns))
        except Exception as e:
            sys.exit(f"Could not read constraint {s!r}: {e}\n"
                     "Declare variables with --ints / --reals / --bools, e.g. --ints x y")
    return out


def z3_namespace():
    import z3
    return {k: getattr(z3, k) for k in dir(z3) if not k.startswith("_")}


def main():
    ap = argparse.ArgumentParser(description="Step-by-step DPLL(T) trace.")
    ap.add_argument("constraints", nargs="*", help='clauses, e.g. "Or(x > 5, y > 5)"')
    ap.add_argument("--ints", nargs="*", default=[])
    ap.add_argument("--reals", nargs="*", default=[])
    ap.add_argument("--bools", nargs="*", default=[])
    ap.add_argument("--example", type=int, choices=sorted(EXAMPLES))
    ap.add_argument("--dimacs", action="store_true", help="also print Z3's own Boolean encoding")
    a = ap.parse_args()

    names = []
    for opt, lst in (("--ints", a.ints), ("--reals", a.reals), ("--bools", a.bools)):
        expanded = [n for item in lst for n in item.split(",") if n]
        for n in expanded:
            if not n.isidentifier():
                sys.exit(f"{n!r} after {opt} is not a variable name. It looks like a constraint.\n"
                         "Put the constraints first and the options last, e.g.\n"
                         '  python demo/dpllt_trace.py "Or(x > 5, y > 5)" "x < 0" --ints x y')
        names.append(expanded)
    a.ints, a.reals, a.bools = names

    if a.constraints:
        title, strings = "Custom formula", a.constraints
        ints, reals, bools = a.ints, a.reals, a.bools
    elif a.ints or a.reals or a.bools:
        sys.exit("Variables were declared but no constraints were given.\n"
                 '  python demo/dpllt_trace.py "Or(x > 5, y > 5)" "x < 0" --ints x y')
    else:
        title, ints, strings = EXAMPLES[a.example or 1]
        reals, bools = [], []
    cs = build_constraints(strings, ints, reals, bools)

    print(f"{title}")
    print("Formula:")
    for c in cs:
        print(f"    {c}")

    try:
        enc = Encoding(cs)
    except ValueError as e:
        sys.exit(f"{e}\nWrite constraints as clauses: an atom, Not(atom) or Or(...) of those.")

    print("\n" + "=" * 70)
    print("STEP 1: Propositional encoding")
    print("=" * 70)
    print("Each theory atom becomes a Boolean variable the SAT engine can guess:")
    for i, atom in enumerate(enc.atoms, 1):
        print(f"    p{i}  :=  {atom}")
    print("The formula becomes a set of clauses over those variables:")
    for i, c in enumerate(enc.clauses, 1):
        print(f"    C{i}:  {clause_str(c)}")
    if a.dimacs:
        s = Solver()
        s.add(*cs)
        print("\nZ3's own Boolean abstraction (DIMACS):")
        print("    " + s.dimacs(True).strip().replace("\n", "\n    "))

    print("\n" + "=" * 70)
    print("STEP 2: Search  (decide, propagate, check the theory, backtrack)")
    print("=" * 70)
    t = Tracer(enc)
    result = t.run()

    print("\n" + "=" * 70)
    print("STEP 3: Result")
    print("=" * 70)
    print(f"Trace result: {result.upper()}   (decisions: {t.decisions}, conflicts: {t.conflicts}, "
          f"Z3 consistency checks: {t.checks})")
    if result == "sat" and t.model is not None:
        names = {}
        def collect(e):
            if is_const(e) and e.decl().kind() == Z3_OP_UNINTERPRETED:
                names[str(e)] = e
            elif is_app(e):
                for c in e.children():
                    collect(c)
        for atom in enc.atoms:
            collect(atom)
        vals = ", ".join(f"{n} = {t.model.eval(v, model_completion=True)}" for n, v in sorted(names.items()))
        print("Values that satisfy it (from the theory solver): " + vals)
    s = Solver()
    s.add(*cs)
    r = s.check()
    st = s.statistics()
    dec = st.get_key_value("decisions") if "decisions" in st.keys() else 0
    conf = st.get_key_value("conflicts") if "conflicts" in st.keys() else 0
    agree = "agrees" if str(r) == result else "DISAGREES"
    print(f"Real Z3 says: {r}  -> {agree}.  (Z3 itself: decisions {dec}, conflicts {conf};")
    print("it is smarter than this tracer, so its numbers can differ.)")


if __name__ == "__main__":
    main()
