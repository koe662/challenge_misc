#!/usr/bin/env sage
import os
import sys
import time
from sage.all import *

# ==========================================
# 完美对接 GZCTF 平台动态 FLAG
# ==========================================
FLAG = os.environ.get("FLAG", "flag{test_guid_for_local_debugging}")

def get_phi2():
    """
    经典的 2-同源模多项式 Phi_2(X, Y)
    用于验证选手提交的相邻 j-不变量之间是否存在 2-同源关系。
    """
    R.<X, Y> = PolynomialRing(ZZ)
    Phi_2 = X^3 + Y^3 - X^2*Y^2 + 1488*(X^2*Y + X*Y^2) - 162000*(X^2 + Y^2) + \
            40773375*X*Y + 8748000000*(X + Y) - 157464000000000
    return Phi_2

def generate_challenge(round_num):
    """
    【生成挑战参数】
    根据轮次增加素数 p 的规模和图上的游走深度。
    第三轮将达到约 80-bit 规模，使得暴力 MITM 彻底失效。
    """
    if round_num == 1:
        p = 2**20 * 3**13 - 1   # ~40 bits
        steps = 20
    elif round_num == 2:
        p = 2**30 * 3**19 - 1   # ~60 bits
        steps = 40
    else:
        p = 2**40 * 3**25 - 1   # ~80 bits (The Abyssal Wall)
        steps = 60
        
    Fp2.<i> = GF(p^2, modulus=x^2+1)
    
    # 从基底曲线 j=1728 出发，进行随机游走隐藏目标曲线
    E = EllipticCurve(Fp2, [1, 0])
    j_current = E.j_invariant()
    
    Phi_2 = get_phi2()
    prev_j = j_current
    for _ in range(steps):
        f = Phi_2(X=j_current)
        roots = [r[0] for r in f.roots()]
        # 防止游走时直接回退
        next_js = [r for r in roots if r != prev_j]
        if not next_js:
            next_js = roots
        prev_j = j_current
        j_current = choice(next_js)
        
    return p, j_current

def check_solution(submitted_seq, p, target_j):
    """
    【基于密码学属性的验证】
    与你的模板一致：不验证中间过程，只验证数学结果。
    验证选手提交的 j-不变量序列是否构成一条无回溯的闭合环路 (自同态)。
    """
    if len(submitted_seq) < 3: 
        return False
        
    Fp2.<i> = GF(p^2, modulus=x^2+1)
    
    try:
        # 将选手提交的字符串转换为 Fp2 域元素
        j_seq = [Fp2(j_str.replace(' ', '')) for j_str in submitted_seq]
    except Exception:
        return False
        
    # 验证起点和终点是否都是目标曲线
    if j_seq[0] != target_j or j_seq[-1] != target_j: 
        return False
        
    Phi_2 = get_phi2()
    
    # 验证代数与图论约束
    for k in range(len(j_seq) - 1):
        j1 = j_seq[k]
        j2 = j_seq[k+1]
        
        # 1. 拒绝平凡的回溯路径 (例如 A -> B -> A)
        if k > 0 and j_seq[k+1] == j_seq[k-1]: 
            return False 
            
        # 2. 验证真正的 2-同源关系
        if Phi_2(X=j1, Y=j2) != 0: 
            return False
            
    return True

def main():
    print("Welcome to the Abyssal Splittings Challenge (PQCrypto 2026 Edition)!")
    print("Standard cycle-finding will melt your RAM. You need TRUE 2D Jacobian Splittings.\n")

    # Isogeny 计算需要选手在本地跑脚本，时间放宽到 300 秒 (总时间)
    start_time = time.time() 
    
    for round_num in range(1, 4):
        print(f"Generating Round {round_num} parameters...")
        p, target_j = generate_challenge(round_num)

        print(f"--- Round {round_num} ---")
        print(f"Prime p  = {p}")
        print(f"Target j = {target_j}")
        print(f"Find a non-backtracking cycle for this curve.")

        try:
            ans = input("Submit j-invariant cycle (comma separated): ").strip()
            submitted_seq = ans.split(',')
        except Exception:
            print("Invalid format!")
            sys.exit(1)

        # 调用验证逻辑
        if not check_solution(submitted_seq, p, target_j):
            print("Wrong cycle or invalid path!")
            sys.exit(1)

        # 超时检测机制 (保持你的模板风格)
        if time.time() - start_time > 300:
            print("Timeout! You are too slow. The Splitting algorithm is much faster.")
            sys.exit(1)

        print("Correct!\n")

    print(f"Congratulations! Here is your flag: {FLAG}")

if __name__ == "__main__":
    # 强制行缓冲，防止 GZCTF 的 socat/xinetd 吞掉前面的 print 输出
    sys.stdout.reconfigure(line_buffering=True)
    main()
