from z3 import *
import time

FNV_OFFSET = 0x811C9DC5
FNV_PRIME = 0x01000193
MASK = 0xFFFFFFFF # 32 bits


def hash_concrete(data):
    # here data is a string
    s = FNV_OFFSET
    for b in data:
        s = ((s ^ b) * FNV_PRIME) & MASK
    return s ^ (s >> 15) 


def hash_symbolic(data):

    # TODO : simulate hash_concrete on data 
    # (list of 8 bit bitvecs (8 bits is the ASCII char 
    # representation))
    # refer to syntax.pdf for help needed
    pass


    


def printable(b):
    ## A helper function to check whether b contains a printable ASCII character 
    return And(UGE(b, 0x20), ULE(b, 0x7E))


#
def find_preimage(target, length):
    # this function finds a printable string whose hash would give us this target
    data = [BitVec(f"b{i}", 8) for i in range(length)]
    s = Solver()

    #TODO : add constraints to s 

    if s.check() != sat:
        return None
    m = s.model()
    return bytes(m[b].as_long() for b in data)

#this function gives a pair of strings which map to the same target in the hash
def find_collision(length):
    a = [BitVec(f"a{i}", 8) for i in range(length)]
    b = [BitVec(f"b{i}", 8) for i in range(length)]
    s = Solver()

    #TODO: add constraints to s

    if s.check() != sat:
        return None
    m = s.model()
    return (bytes(m[x].as_long() for x in a), bytes(m[x].as_long() for x in b))


if __name__ == "__main__":
    secret = b"z3rocks!"
    target = hash_concrete(secret)
    print(f"target digest: {target:#010x}")

    t = time.time()
    found = find_preimage(target, len(secret))
    print(f"preimage: {found}  ({time.time() - t:.2f}s)")
    assert found is not None and hash_concrete(found) == target

    t = time.time()
    pair = find_collision(len(secret))
    print(f"collision: {pair}  ({time.time() - t:.2f}s)")
    assert pair is not None and pair[0] != pair[1]
    assert hash_concrete(pair[0]) == hash_concrete(pair[1])
