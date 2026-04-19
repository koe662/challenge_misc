#!/usr/bin/env sage
import os
import sys
import time
import traceback
from sage.all import *

# ==========================================
# 终极 IO 修复：重写 print 函数强制 flush
# 解决 socat/xinetd 环境下数据被憋在缓冲区导致直接断开的问题
# ==========================================
import builtins
def ctf_print(*args, **kwargs):
    kwargs['flush'] = True
    builtins._original_print(*args, **kwargs)
builtins._original_print = builtins.print
builtins.print = ctf_print

# 动态获取 GZCTF 平台的 FLAG
FLAG = os.environ.get("FLAG", "flag{test_guid_for_local_debugging}")

def get_phi2():
    """返回 2-同源模多项式"""
    R.<X, Y> = PolynomialRing(ZZ)
    Phi_2 = X^3 + Y^3 - X^2*Y^2 + 1488*(X^2*Y + X*Y^2) - 162000*(X^2 + Y^2) + \
            40773375*X*Y + 8748000000*(X + Y) - 157464000000000
    return Phi_2

def generate_challenge(round_num):
    """
    生成题目参数，并确保生成的 p 绝对是一个合法的素数。
    """
    if round_num == 1:
        smooth_base = 2**20 * 3**10   # 基础平滑度 (~35 bits)
        steps = 20
    elif round_num == 2:
        smooth_base = 2**30 * 3**15   # 基础平滑度 (~53 bits)
        steps = 40
    else:
        smooth_base = 2**40 * 3**20   # 基础平滑度 (~71 bits)
        steps = 60
        
    # 【核心修复】：动态寻找一个合法的素数 p
    # 保证 p = 3 mod 4 (为了后续扩张域 Fp2 中 x^2+1 不可约) 且 p 确实是素数
    f = 1
    while True:
        p = f * smooth_base - 1
        if p % 4 == 3 and is_prime(p):
            break
        f += 1
        
    # 定义有限域与初始超奇异椭圆曲线 (j=1728)
    Fp2.<i> = GF(p^2, modulus=x^2+1)
    E = EllipticCurve(Fp2, [1, 0])
    j_current = E.j_invariant()
    
    # 随机游走隐藏目标曲线
    Phi_2 = get_phi2()
    prev_j = j_current
    for _ in range(steps):
        f_poly = Phi_2(X=j_current)
        roots = [r[0] for r in f_poly.roots()]
        # 防止直接回退
        next_js = [r for r in roots if r != prev_j]
        if not next_js:
            next_js = roots
        prev_j = j_current
        j_current = choice(next_js)
        
    return p, j_current

def check_solution(submitted_seq, p, target_j):
    """验证选手提交的 j-不变量序列是否构成一条无回溯的闭合环路"""
    if len(submitted_seq) < 3: 
        return False
        
    Fp2.<i> = GF(p^2, modulus=x^2+1)
    
    try:
        j_seq = [Fp2(j_str.replace(' ', '')) for j_str in submitted_seq]
    except Exception:
        return False
        
    # 验证起点和终点
    if j_seq[0] != target_j or j_seq[-1] != target_j: 
        return False
        
    Phi_2 = get_phi2()
    for k in range(len(j_seq) - 1):
        j1 = j_seq[k]
        j2 = j_seq[k+1]
        
        # 拒绝立即回溯
        if k > 0 and j_seq[k+1] == j_seq[k-1]: 
            return False 
            
        # 验证 2-同源关系
        if Phi_2(X=j1, Y=j2) != 0: 
            return False
            
    return True

def main():
    print("Welcome to the Abyssal Splittings Challenge (PQCrypto 2026 Edition)!")
    print("Standard cycle-finding will melt your RAM. You need TRUE 2D Jacobian Splittings.\n")

    # 留给选手 300 秒的时间进行同源图游走计算
    start_time = time.time() 
    
    for round_num in range(1, 4):
        print(f"Generating Round {round_num} parameters... (This might take a few seconds)")
        p, target_j = generate_challenge(round_num)

        print(f"--- Round {round_num} ---")
        print(f"Prime p = {p}")
        print(f"Target j = {target_j}")
        print(f"Find a non-backtracking cycle for this curve.")

        try:
            ans = input("Submit j-invariant cycle (comma separated): ").strip()
            submitted_seq = ans.split(',')
        except EOFError:
            print("Connection closed by client.")
            sys.exit(1)
        except Exception:
            print("Invalid input format!")
            sys.exit(1)

        if not check_solution(submitted_seq, p, target_j):
            print("Wrong cycle or invalid path!")
            sys.exit(1)

        if time.time() - start_time > 300:
            print("Timeout! You are too slow. Splitting is much faster.")
            sys.exit(1)

        print("Correct!\n")

    print(f"Congratulations! Here is your flag: {FLAG}")

if __name__ == "__main__":
    try:
        # 强制标准输出与错误输出为行缓冲
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
        sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)
        main()
    except Exception as e:
        # 如果服务端因不可抗力崩溃，将其打印给客户端以便排错
        print(f"\n[SERVER FATAL ERROR] 靶机内部发生致命错误: {e}")
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
