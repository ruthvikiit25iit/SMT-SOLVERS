from z3 import *
import time

ROUNDS = 4

PAIRS = {
    4: [((0xD75A, 0xFB57), (0x3272, 0x6E01)),
        ((0xE1D7, 0x7AD8), (0xD467, 0x03A0)),
        ((0x014C, 0x2954), (0x5BDD, 0xE9E5))],
    5: [((0x38B2, 0x9311), (0x314B, 0xF974)),
        ((0x3233, 0xE639), (0x3065, 0xA0C4)),
        ((0x05E1, 0xFB06), (0xBF5A, 0xAC63))],
}


def ror(x, r):
    return ((x >> r) | (x << (16 - r))) & 0xFFFF


def rol(x, r):
    return ((x << r) | (x >> (16 - r))) & 0xFFFF


def round_keys(key, rounds):
    # concrete key schedule on ordinary Python ints
    k = [key[0]]
    l = list(key[1:])
    for i in range(rounds - 1):
        l.append(((k[i] + ror(l[i], 7)) & 0xFFFF) ^ i)
        k.append(rol(k[i], 2) ^ l[-1])
    return k


def encrypt(x, y, key, rounds):
    # concrete encryption on ordinary Python ints (used by the checks in __main__)
    for rk in round_keys(key, rounds):
        x = ((ror(x, 7) + y) & 0xFFFF) ^ rk
        y = rol(y, 2) ^ x
    return x, y


def solve():
    # TODO: return a key (k0, l0, l1, l2) of four ints consistent with every pair in PAIRS[ROUNDS], or None.
    # Hint: write encrypt again over Z3 bit-vectors (RotateLeft / RotateRight are in syntax.pdf).
    pass


if __name__ == "__main__":
    assert encrypt(0x6574, 0x694C, [0x0100, 0x0908, 0x1110, 0x1918], 22) == (0xA868, 0x42F2)

    t = time.time()
    key = solve()
    print(f"key: {None if key is None else [hex(w) for w in key]}  ({time.time() - t:.2f}s)")
    assert key is not None
    for pt, ct in PAIRS[ROUNDS]:
        assert encrypt(*pt, key, ROUNDS) == ct
