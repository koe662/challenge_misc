#!/usr/bin/env python3
import os
import random
import sys

# 禁用缓冲，确保输出实时传输
sys.stdout.reconfigure(line_buffering=True)

# PHIGFS 矩阵 A''
A_PRIME_PRIME = [
    [0, 1, 1, 1],
    [1, 1, 1, 0],
    [1, 1, 0, 1],
    [1, 0, 1, 1]
]

# 随机生成一个 S-box (8-bit)
SBOX = list(range(256))
random.shuffle(SBOX)

def matrix_mul(A, vec):
    res = [0, 0, 0, 0]
    for i in range(4):
        for j in range(4):
            if A[i][j]:
                res[i] ^= vec[j]
    return res

def encrypt_phigfs(state, round_keys, rounds=8):
    """实现 PHIGFS 加密逻辑 [cite: 22]"""
    curr_state = list(state)
    for r in range(rounds):
        x3, x2, x1, x0 = curr_state
        k1, k0 = round_keys[r]
        # 非线性层
        y2 = x2 ^ SBOX[x3 ^ k1]
        y0 = x0 ^ SBOX[x1 ^ k0]
        # 矩阵变换层
        curr_state = matrix_mul(A_PRIME_PRIME, [x3, y2, x1, y0])
    return tuple(curr_state)

def get_random_state():
    return tuple(random.getrandbits(8) for _ in range(4))

def main():
    FLAG = os.getenv("FLAG", "flag{phigfs_linear_layer_is_too_weak_12345}")
    ROUNDS_TO_WIN = 50
    
    print("=== PHIGFS Distinguisher Challenge ===")
    print("Philip thinks his new cipher is secure. Prove him wrong!")
    print(f"Correctly distinguish PHIGFS from a Random Permutation {ROUNDS_TO_WIN} times to get the Flag.")
    print("Each block is 4 bytes: (x3, x2, x1, x0). Input/Output in hex.\n")

    for i in range(ROUNDS_TO_WIN):
        print(f"--- Round {i+1}/{ROUNDS_TO_WIN} ---")
        is_real = random.getrandbits(1)
        
        # 为本轮生成随机密钥
        round_keys = [(random.getrandbits(8), random.getrandbits(8)) for _ in range(8)]
        
        # 允许用户询问有限次数的加密
        print("You can query 2 pairs of plaintexts.")
        for q in range(2):
            try:
                line = input(f"Query {q+1} (hex string, e.g., 00112233): ").strip()
                p_bytes = bytes.fromhex(line)
                if len(p_bytes) != 4: raise ValueError
                
                p = tuple(p_bytes)
                if is_real:
                    c = encrypt_phigfs(p, round_keys)
                else:
                    # 模拟随机置换（简化版）
                    c = tuple(random.getrandbits(8) for _ in range(4))
                
                print(f"Result: {bytes(c).hex()}")
            except:
                print("Invalid input. Game over.")
                return

        choice = input("Is this [R]EAL PHIGFS or [F]AKE random? (R/F): ").strip().upper()
        if (choice == 'R' and is_real) or (choice == 'F' and not is_real):
            print("Correct!\n")
        else:
            print("Wrong! Philip laughs at you.")
            return

    print(f"Congratulations! Here is your Flag: {FLAG}")

if __name__ == "__main__":
    main()
