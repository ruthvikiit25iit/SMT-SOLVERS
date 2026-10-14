import argparse
from fractions import Fraction

from z3 import *

x1, x2, z, y = Reals("x1 x2 z y")
p = Int("p")


# define neuron and box constraints # do not change varaible names
neuron = And(z==2*x1-x2+1,y== If(z>0,z,0))
box =And(x1>=0,x1<=2,x2>=0,x2<=2)


# helper: checks enc + box + any extra constraints, prints sat/unsat and the input found
def query(name, enc, *extra):
    s = Solver()
    s.add(enc, box, *extra)
    r = s.check()
    print(name, r)
    if r == sat:
        m = s.model()
        print("   x1 =", m[x1], " x2 =", m[x2], " y =", m[y])
    return r


# helper for the optional Task D: the big-M encoding of the ReLU for bounds l <= z <= u
def bigm(l, u):
    #TODO
    pass


def task_a():
    #TODO
    query("a",neuron,y>=3)

    pass

def task_b():
    #TODO
    pass


def task_c():
   #TODO
   pass


def task_d():
    #Optional TODO
    pass

def task_e():
    #Optional TODO
    pass

def task_f():
    # Optional TODO
    pass


TASKS = {k: globals()["task_" + k.lower()] for k in "ABCDEF"}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k in TASKS:
        ap.add_argument("--" + k, action="store_true")
    args = ap.parse_args()
    chosen = [k for k in TASKS if getattr(args, k)] or list(TASKS)
    for k in chosen:
        print("Task", k)
        TASKS[k]()
