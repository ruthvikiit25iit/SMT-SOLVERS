# Lab: Reversing a Hash with Bit-Vectors

All the Z3 bit-vector syntax you need is in **syntax.pdf** in this folder.

## The hash

Strings are hashed with an FNV-style function over a 32-bit state. For a string `b_1 ... b_n` (each `b_i` is one byte):

```
s_0 = 0x811C9DC5
s_i = ((s_{i-1} XOR b_i) * 0x01000193) mod 2^32
h   = s_n XOR (s_n >> 15)        (logical right shift)
```

`hash_concrete` in `hash_template.py` is this function on ordinary Python ints. Your job is to write the same function over Z3 bit-vectors and then use the solver to run it backwards.

## What to implement

Open `hash_template.py` and fill in the three `TODO`s.

1. **`hash_symbolic(data)`**: simulate `hash_concrete` on a list of 8-bit bit-vectors and return the 32-bit digest.
2. **`find_preimage(target, length)`**: add constraints so that any model is a printable string of `length` characters whose hash is `target`.
3. **`find_collision(length)`**: add constraints so that any model is a pair of **different** printable strings of `length` characters with the same hash.

"Printable" means an ASCII character between `0x20` and `0x7E`. The helper `printable(b)` is already provided.

## Running and checking

```
python3 hash_template.py
```

The script hashes the secret `b"z3rocks!"`, asks your solver for a preimage of that digest, then asks for a collision. The `assert`s check your answers with `hash_concrete`. The preimage you find is usually not `z3rocks!` itself, and that is fine: any string with the same digest is correct.

### Expected output

```
target digest: 0x5806d467
preimage: b',S&TfA8<'  (8.44s)
collision: (b'Ju+;FU=)', b'IaDQ$;u_')  (14.86s)
```

- The digest line is always exactly `0x5806d467` for `b"z3rocks!"`.
- The preimage and the two collision strings **will differ** from the ones above, and so will the times. Any strings that pass the `assert`s are correct. The program prints nothing else, so if it ends without an `AssertionError`, your answers are right.

### Try other inputs

Change this line in `hash_template.py`:

```python
secret = b"z3rocks!"
```

The length of `secret` sets the length of the strings the solver searches for. Here is what to expect (times are from my machine and vary):

| `secret` | Digest | Preimage | Collision |
|---|---|---|---|
| `b"a"` | `0xe40de134` | `b'a'` (instant) | `None` |
| `b"hi"` | `0x683a26ef` | `b'hi'` (instant) | `None` |
| `b"abc"` | `0x1a47dd84` | `b'abc'` (instant) | `None`, but it took about 90 s to prove |
| `b"hello"` | `0x4f9fb395` | `b'hello'` (about 1 s) | a pair, about 6 s |
| `b"z3rocks!"` | `0x5806d467` | another string, 3 to 8 s | a pair, 4 to 15 s |

Notice two things:

- **Short strings give back the original.** In my runs, `a`, `hi`, `abc` and `hello` each returned themselves. With few characters, very few printable strings share a digest. The 8-character secret returned a different string.
- **Short strings had no collision.** For 1 to 3 characters, `find_collision` returned `None`, so the final `assert pair is not None` in the script fails with an `AssertionError`. That is the correct behaviour, not a bug in your solution. Proving that no collision exists can take a long time (about 90 s for length 3), so only try that if you are willing to wait.

Try a longer secret too, and see how the time grows.

## Hints

- Each character is 8 bits wide but the hash state is 32 bits wide. Widen the byte before combining them.
- Multiplication in Z3 bit-vectors already wraps mod 2^32, so no masking is needed.
- In Python the final `>>` on a non-negative int is a logical shift. In Z3, `>>` is an *arithmetic* shift, so use the logical one.
- Compare bytes as *unsigned* values. A byte of `0xC8` is negative under signed comparison.
- To say two strings differ, it is enough that at least one position differs.
- Check the program with a short string first, then try longer ones and see how the solve time changes.

---

# Hard Problem: Recovering a SPECK Key

Syntax reference: **syntax.pdf**. The file to work on is `recovering_key.py`.

## Background

SPECK32/64 is a real lightweight block cipher. It encrypts a 32-bit block, written as two 16-bit words `(x, y)`, using a 64-bit key written as four 16-bit words `(k0, l0, l1, l2)`. It uses only addition, rotation and XOR, which is exactly the vocabulary of the bit-vector theory.

The real cipher runs 22 rounds. This lab uses a **reduced-round** version, so that the solver can finish.

## The cipher

All words are 16 bits and all additions are mod 2^16. `ROR` and `ROL` rotate right and left.

**Encryption.** Starting from the plaintext `(x, y)`, for each round key `rk`:

```
x = (ROR(x, 7) + y) XOR rk
y = ROL(y, 2) XOR x
```

The ciphertext is the final `(x, y)`.

**Key schedule.** The round keys `k[0], k[1], ...` come from the key words:

```
k[0] = k0,   l[0] = l0,   l[1] = l1,   l[2] = l2
for i = 0, 1, ..., rounds-2:
    l[i+3] = (k[i] + ROR(l[i], 7)) XOR i
    k[i+1] = ROL(k[i], 2) XOR l[i+3]
```

Round `i` uses `k[i]`.

`encrypt` and `round_keys` in `recovering_key.py` implement exactly this on ordinary Python ints. The `__main__` block checks them against the published 22-round test vector: key `1918 1110 0908 0100`, plaintext `6574 694c`, ciphertext `a868 42f2`.

## The problem

Someone encrypted several known plaintexts under the **same secret key**, using `ROUNDS` rounds. You are given the plaintext/ciphertext pairs in `PAIRS`. The key is not in the file.

**Recover a key that produces all of the given ciphertexts.**

## What to implement

Fill in `solve()`. It must return the key as a tuple of four ints `(k0, l0, l1, l2)`, or `None` if no key exists.


## Checking your answer

```
python3 recovering_key.py
```

`__main__` re-encrypts every plaintext with your key using the concrete `encrypt`, and asserts that you get the given ciphertexts. Any key that does this is correct, because several keys can fit a small number of pairs.

### Expected output

```
key: ['0x3cfd', '0xa393', '0x348c', '0x7252']  (0.67s)
```

The time will differ on your machine. The key you print may differ too, because any key that reproduces all the ciphertexts is correct. If the program ends without an `AssertionError`, your key is right.

### Try other inputs

**Different rounds.** Change this line:

```python
ROUNDS = 4
```

Set it to `5`. Expect it to run for a very long time (it did not finish within 100 seconds for me), and `solve()` returns the key only when it does. The time for 1 to 3 rounds is negligible.

**Your own secret key.** Pick any key and generate pairs for it with the concrete `encrypt`:

```python
mykey = [0x1234, 0x5678, 0x9ABC, 0xDEF0]
PAIRS[4] = [(p, encrypt(*p, mykey, 4)) for p in [(0x0001, 0x0002), (0x00FF, 0x1234)]]
```

Put these two lines just before `solve()` is called. With these two plaintexts, my solution printed `['0x1234', '0x5678', '0x9abc', '0xdef0']` in about 0.5 s, which is exactly `mykey`. With only one pair, many keys fit, so you will usually get a different key that still passes the assertions.

## Turning the difficulty up

Change `ROUNDS` at the top of the file (`4` and `5` have data in `PAIRS`).

In my tests with random keys and two pairs, the solve time grew from under 0.05 s for 1 to 3 rounds, to about 0.5 s for 4 rounds and about 12 s for 5 rounds. With the three pairs in this file, 4 rounds takes under a second, while 5 rounds had not finished after 100 seconds. Expect each extra round to cost much more than the one before.

Questions to think about:

- Why does each round make the problem so much harder? Look at what the additions and rotations do to the bits.
- How many keys fit one pair? Two pairs? How would you check that your key is the *only* one?
- Does it matter whether you build one large nested expression or name each intermediate value as its own variable?


