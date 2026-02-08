#!/usr/bin/env python3
import os
import random
import sys

sys.stdout.reconfigure(line_buffering=True)

SBOX = list(range(256))
random.seed(2022)
random.shuffle(SBOX)

def matrix_op(v):
    m = [[0,1,1,1],[1,1,1,0],[1,1,0,1],[1,0,1,1]]
    res = [0]*4
    for i in range(4):
        for j in range(4):
            if m[i][j]: res[i] ^= v[j]
    return res

def phigfs_enc(p, ks):
    state = list(p)
    for r in range(8):
        x3, x2, x1, x0 = state
        y2 = x2 ^ SBOX[x3 ^ ks[r][0]]
        y0 = x0 ^ SBOX[x1 ^ ks[r][1]]
        state = matrix_op([x3, y2, x1, y0])
    return bytes(state)

def main():
    flag = os.getenv("FLAG", "flag{test_dummy}")
    print("Mode: [R]EAL PHIGFS or [F]AKE Random Permutation")
    
    for _ in range(50):
        is_real = random.getrandbits(1)
        ks = [(random.getrandbits(8), random.getrandbits(8)) for _ in range(8)]
        
        for _ in range(2):
            try:
                inp = bytes.fromhex(input("> ").strip())
                if len(inp) != 4: break
                if is_real:
                    print(phigfs_enc(inp, ks).hex())
                else:
                    print(os.urandom(4).hex())
            except:
                return

        ans = input("? ").strip().upper()
        if (ans == 'R' and is_real) or (ans == 'F' and not is_real):
            print("OK")
        else:
            print("FAIL")
            return
            
    print(flag)

if __name__ == "__main__":
    main()
