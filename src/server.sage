#!/usr/bin/env sage
import os
import sys
import time
import traceback
import builtins
import signal
from sage.all import *

# ==========================================
# 终极 IO 修复：重写 print 函数强制 flush
# ==========================================
def ctf_print(*args, **kwargs):
    kwargs['flush'] = True
    builtins._original_print(*args, **kwargs)
if not hasattr(builtins, '_original_print'):
    builtins._original_print = builtins.print
    builtins.print = ctf_print

# 环境变量获取 FLAG
FLAG = os.environ.get("FLAG", "flag{Ethan_Catch_Sage10_8_Speedrun_Success}")

def get_phi2():
    """返回经典的 2-同源模多项式 Phi_2(X, Y)"""
    R.<X, Y> = PolynomialRing(ZZ)
    Phi_2 = X^3 + Y^3 - X^2*Y^2 + 1488*(X^2*Y + X*Y^2) - 162000*(X^2 + Y^2) + \
            40773375*X*Y + 8748000000*(X + Y) - 157464000000000
    return Phi_2

def generate_challenge():
    """生成 Round 1 参数 (~38 bits)"""
    smooth_base = 2**20 * 3**10
    steps = 25 # 游走步数
    
    f = 1
    while True:
        p = f * smooth_base - 1
        if p % 4 == 3 and is_prime(p):
            break
        f += 1
        
    Fp2.<i> = GF(p^2, modulus=x^2+1)
    E = EllipticCurve(Fp2, [1, 0])
    j_current = E.j_invariant()
    
    Phi_2 = get_phi2()
    prev_j = j_current
    PR.<Y> = PolynomialRing(Fp2) 
    
    for _ in range(steps):
        f_poly = Phi_2(X=j_current, Y=Y) 
        roots = [r[0] for r in f_poly.roots()]
        next_js = [r for r in roots if r != prev_j]
        if not next_js:
            next_js = roots
        prev_j = j_current
        j_current = choice(next_js)
        
    return p, j_current

def check_solution(submitted_seq, p, target_j):
    """严格验证：闭合、非回溯、2-同源"""
    if len(submitted_seq) < 5: 
        return False, "Sequence too short."
        
    Fp2.<i> = GF(p^2, modulus=x^2+1)
    try:
        # 处理可能的格式问题
        j_seq = [Fp2(j_str.replace(' ', '').replace('*i','*I').replace('i','I')) for j_str in submitted_seq]
    except Exception:
        return False, "Invalid j-invariant format."
        
    if j_seq[0] != target_j or j_seq[-1] != target_j: 
        return False, "The path must start and end at the target j."
        
    Phi_2 = get_phi2()
    for k in range(len(j_seq) - 1):
        # 严格非回溯校验
        if k > 0 and j_seq[k+1] == j_seq[k-1]: 
            return False, f"Backtracking detected at index {k}."
            
        # 严格同源校验
        if Phi_2(X=j_seq[k], Y=j_seq[k+1]) != 0: 
            return False, f"Invalid 2-isogeny step at index {k}."
            
    return True, "Success"

def timeout_handler(signum, frame):
    print("\nTimeout! 120 seconds are up. Splitting is faster.")
    sys.exit(1)

def main():
    # 设置 120 秒强制闹钟
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(120)

    print("Welcome to the Abyssal Splittings Challenge (PQCrypto 2026 Edition)!")
    print("Standard cycle-finding will melt your RAM. You need TRUE 2D Jacobian Splittings.\n")

    print(f"Generating Round 1 parameters... (This might take a few seconds)")
    p, target_j = generate_challenge()

    print(f"--- Round 1 ---")
    print(f"Prime p = {p}")
    print(f"Target j = {target_j}")
    print(f"Find a non-backtracking cycle for this curve.")

    try:
        ans = input("Submit j-invariant cycle (comma separated): ").strip()
        submitted_seq = ans.split(',')
    except EOFError:
        sys.exit(1)

    is_ok, reason = check_solution(submitted_seq, p, target_j)
    if not is_ok:
        print(f"Wrong! {reason}")
        sys.exit(1)

    print("Correct!")
    print(f"Congratulations! Here is your flag: {FLAG}")

if __name__ == "__main__":
    try:
        # 设置行缓冲
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
        main()
    except Exception as e:
        print(f"\n[SERVER FATAL ERROR]: {e}")
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
