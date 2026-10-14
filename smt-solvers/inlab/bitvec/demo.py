# Problem: find an 8-bit value x such that
#   1. (x + 200) XOR (NOT 0x0F) == 0xFD          (8-bit arithmetic, wraps mod 256)
#   2. x zero-extended to 16 bits, plus 100, shifted right (logical) by 4,
#      is either 0x0A or 0x0B                    (no 8-bit overflow in the extended sum)
#   3. x is a printable ASCII character (0x20..0x7E)

from z3 import *

#TODO
