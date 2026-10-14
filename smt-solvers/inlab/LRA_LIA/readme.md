# Verifying Neural Networks with Z3

All the Z3 syntax you need is in `syntax.pdf` in this folder. Use `Real` variables throughout.

This folder has two exercises: a warm-up in `demo_template.py` (below), then the neural-network tasks.

## Warm-up: `demo_template.py`

Find integers `x, y` and a real `r` such that

1. `x + 2*y == 12`, `x` is even, `y > 0`
2. `x != y` and `|x - y| <= 3`
3. `max(x, y) == 5`
4. `r == x / 3`, using real division
5. `r < 1` or `r > 2`

Print `r` exactly, as a decimal, rounded down, and check whether it is a whole number. Then prove: for every integer `n`, if `n` is even then `n + 2` is even.

Run it with `python3 demo_template.py`.

---

## Background: what is a neural network?

A neural network is a function that takes some numbers in and returns some numbers out. It is built
from small units called **neurons**, arranged in **layers**.

### One neuron

A neuron with inputs `x1, ..., xn` does two steps:

1. **Weighted sum.** It computes `z = w1*x1 + ... + wn*xn + b`. The numbers `w1, ..., wn` are called
   the **weights** and `b` is the **bias**. They are fixed constants. Call `z` the neuron's
   *pre-activation*.
2. **ReLU.** It outputs `y = max(z, 0)`: the value `z` if `z` is at least 0, and `0` otherwise. This
   step is called the **ReLU activation**.

### A network

In a layer, every neuron reads the same inputs but has its own weights and bias. The outputs of one
layer are the inputs of the next. In a **fully connected** network:

```
layer 1:  z1[j] = sum_i W1[j][i] * x[i]  + b1[j]       h1[j] = max(z1[j], 0)
layer 2:  z2[j] = sum_i W2[j][i] * h1[i] + b2[j]       h2[j] = max(z2[j], 0)
output:   y     = sum_j w3[j] * h2[j] + b3             (no ReLU on the output)
```

`W1[j][i]` is the weight from input `i` to neuron `j` of layer 1, and so on.

### What does it mean to verify one?

Networks are used for decisions (is that a stop sign?), so we want guarantees such as "for every input
in this range, the output is never negative". Testing a few inputs cannot give that. Instead, we ask Z3
whether a **bad input exists**:

> Is there an input `x` in the allowed range such that the network output violates the property?

If Z3 says `unsat`, no bad input exists, so the property holds for every input in the range. If Z3 says
`sat`, its model is a concrete bad input, called a **counterexample**.

### Big-M encoding of a ReLU

A ReLU can also be written without a case split, using a 0/1 integer variable `p`. Suppose you know
bounds `l <= z <= u` on the pre-activation (with `l < 0 < u`). Then `y = max(z, 0)` holds exactly when

```
y >= 0,   y >= z,   y <= z - l*(1 - p),   y <= u*p,   p in {0, 1}
```

If `p` is allowed to be any real number in `[0, 1]` instead, this is called the **LP relaxation**: it
allows more outputs than the true ReLU does.

A neuron is **stable** over an input range if `l >= 0` or `u <= 0` (its ReLU is then just `z` or just
`0` and needs no case split). Otherwise it is **unstable**.

---

## Running your tasks

Each task is run separately from the command line with a flag named after the task:

```
python3 neuron_template.py --A          # run Task A only
python3 neuron_template.py --B --C      # run Tasks B and C
python3 neuron_template.py              # run every task
```

Put the code for each task in its own function in the template, so that `--A`, `--B`, ... run just that
task.

The same flags work for the whole-network tasks (Tasks A to H of the advanced problem) in `network_template.py`:

```
python3 network_template.py --A          # run Task A only
python3 network_template.py --E --F      # run Tasks E and F
python3 network_template.py              # run every task (A to H)
```

`network_template.py` already defines the weights (`W1`, `b1`, `W2`, `b2`, `w3`, `b3`) and the input
variables `x`. Fill in the `task_a` ... `task_h` functions; a task you have not written yet does nothing.

---

## Basic problem: one neuron

```
z = 2*x1 - x2 - 1
y = max(z, 0)
```

The inputs are restricted to the box `0 <= x1 <= 2`, `0 <= x2 <= 2`.

**Task A.** Encode the neuron and the input box in Z3. Find an input for which `y >= 3`.

**Task B.** Decide whether some input in the box gives `y >= 3.5`. What is the largest value `y` can
take on the box?

**Task C.** Find an input in the box with `x1 > 0`, `x2 > 0` and `y == 0`.

**Task D (optional).** Encode the neuron using the big-M encoding instead of `If`. Compute `l` and `u` for `z` over the
box by hand. Redo Tasks A and B with this encoding. Then repeat with `l = -100000` and `u = 100000`.

**Task E (optional).** Compute the smallest and largest value of `z` on the box. Is the neuron stable or unstable?

**Task F (optional, sensitivity).** Take the point `c = (1, 1/2)` and let `y0` be the neuron's output there. A
small change of the input should not cause a large change of the output. For `ε = 1/4, 1/2, 1` and
`δ = 1/2, 1, 2`, decide whether some input `x'` in the box with `|x1' - 1| <= ε` and `|x2' - 1/2| <= ε`
has `|y(x') - y0| >= δ`. If so, report such an `x'`.

---

## Advanced problem: a whole network

A fully connected network with 2 inputs, a first layer of 3 neurons, a second layer of 2 neurons, and 1
output:

```
W1 = [[ 1, -1],        b1 = [ 0, -1, 1]
      [ 2,  1],
      [-1,  2]]

W2 = [[ 1,  1, -1],    b2 = [ 1, 0]
      [-1,  2,  1]]

w3 = [1, -2]           b3 = 9
```

The inputs are `x = (x0, x1)`. Unless stated otherwise, the input box is `-1 <= x0, x1 <= 1`.

**Task A.** Write a function `layer(W, b, xs)` that takes a weight matrix, a bias vector and a list of
Z3 inputs, and returns the new pre-activation variables, the post-activation variables and the
constraints. It must work for any layer size. Use it to encode the whole network. Check your encoding
against a plain Python implementation of the network on a few inputs, including `x = (0.5, 0.5)`.

**Task B.** Find the smallest and largest value of the output `y` over the box, and an input that
attains each.

**Task C.** Property P: *for every input in the box, `y >= 0`.* Decide whether P is true. If it is false, give a
counterexample and check it with the plain Python implementation. Then find the smallest non-negative integer `c` for which the property `y >= -c` is true.

**Task D.** At `x = (0.5, 0.5)` the output is positive. Find the largest `ε` (to 3 decimals) such that `y > 0`
for every input with `|x0 - 0.5| <= ε` and `|x1 - 0.5| <= ε`.

**Task E.** For every neuron in both hidden layers, compute the tightest lower and upper bounds of its
pre-activation over the input box. Say which neurons are stable and which are unstable.

**Task F.** Re-encode the network with the big-M encoding for every unstable neuron, using the bounds from
Task E. Find the minimum of `y` over the box (a) with `p` an integer in `{0, 1}` and (b) with `p` a real in `[0, 1]`.
Compare the two minima. For each of `y >= 0`, `y >= -2`, `y >= -3`, say whether the relaxed (b)
encoding is enough to prove it.

**Task G (sensitivity).** Let `c = (0.5, 0.5)` and let `y0` be the network output at `c`. Given a
radius `ε` and a threshold `δ`, decide whether there is an input `x'` with `|x0' - 0.5| <= ε` and
`|x1' - 0.5| <= ε` such that `|y(x') - y0| >= δ`. Such an `x'` shows the network is *sensitive* around
`c`. For `ε = 1/20, 1/10, 1/4` and `δ = 1, 3, 6`, report the answer and, when one exists, the input
and its output (check it against the plain Python implementation). Then, for each `ε`, find the largest
change `|y(x') - y0|` that is possible.

**Task H (challenge).** Write a function that builds a random network with `k` hidden layers of width `w`
(small integer weights, fixed seed). Measure how long Z3 takes to minimise the output over `[-1, 1]^2`
for `w = 4, 8, 12, 16` with `k = 2`, and for `k = 1, 2, 3, 4` with `w = 8`. For each size, also print
the number of neurons and `2^(number of neurons)`.

---

## Source

Prof. Huan Zhang, *Integer and Linear Programming Formulations for Neural Network Verification*,
ECE/CS 584, Lecture 9.
