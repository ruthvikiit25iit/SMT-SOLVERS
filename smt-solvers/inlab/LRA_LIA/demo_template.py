# Problem: find integers x, y and a real r such that
#   1. x + 2*y == 12, x is even, y > 0
#   2. x != y and |x - y| <= 3
#   3. max(x, y) == 5                      (use If)
#   4. r == x / 3, using real division     (use ToReal)
#   5. r < 1 or r > 2
# Then print r exactly, as a decimal, rounded down (ToInt), and check whether it is a whole number (IsInt).
# Finally, prove: for every integer n, if n is even then n + 2 is even.

from z3 import *

x, y = Ints("x y")
r = Real("r")

s = Solver()

#TODO:
s.add(x + 2*y == 12, x % 2 == 0, y > 0, x != y, Abs(x - y)<= 3,If(x>y,x,y)==5 ,r == ToReal(x) / 3, Or(r < 1, r > 2))

print(s.check())
m = s.model()
print("x =", m[x].as_long(), " y =", m[y].as_long())
print("r =", m[r].as_fraction(), "=", m[r].as_decimal(3))
print("ToInt(r) =", m.eval(ToInt(r)), " IsInt(r) =", m.eval(IsInt(r)))

p = Solver()
n=Int("n")
p.add(ForAll([n],Implies(n%2==0,(n+2)%2==2)))

print("claim:", "proved" if p.check() == unsat else "not proved")
