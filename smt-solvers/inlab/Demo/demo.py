from z3 import *

x, y = Ints('x y')
s = Solver()
# s.add(x > 0, y == x - 10, y < 0)
#TODO:
s.add(x>=1,y>=1,x+y<=5,Or(x>=4,y>=4))

if s.check() == sat:
    print("sat")
    print(s.model())
else:
    print("unsat")
