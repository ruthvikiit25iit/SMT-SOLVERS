import argparse

from z3 import *

W1 = [[1, -1], [2, 1], [-1, 2]]
b1 = [0, -1, 1]
W2 = [[1, 1, -1], [-1, 2, 1]]
b2 = [1, 0]
w3 = [1, -2]
b3 = 9

x = Reals("x0 x1")


def task_a():
    # TODO: Task A
    pass


def task_b():
    # TODO: Task B
    pass


def task_c():
    # TODO: Task C
    pass


def task_d():
    # TODO: Task D
    pass


def task_e():
    # TODO: Task E
    pass


def task_f():
    # TODO: Task F
    pass


def task_g():
    # TODO: Task G
    pass


def task_h():
    # TODO: Task H
    pass


TASKS = {k: globals()["task_" + k.lower()] for k in "ABCDEFGH"}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k in TASKS:
        ap.add_argument("--" + k, action="store_true")
    args = ap.parse_args()
    chosen = [k for k in TASKS if getattr(args, k)] or list(TASKS)
    for k in chosen:
        print("Task", k)
        TASKS[k]()
