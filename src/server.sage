#!/usr/bin/env sage
import socket
import signal
import re
import sys
from sage.all import *

# ================= 题目核心配置 =================
PORT = 35654
TIMEOUT = 120
P_ROUND1 = 185752092671
# 题目给出的目标 j 不变量 (j = 140087322762*i + 41012056975)
TARGET_J_STR = "140087322762*i + 41012056975"
FLAG = "flag{Ethan_Catch_Sage10_8_GZCTF_Verified_2026}"
# ===============================================

def verify_cycle(p, path_str):
    """
    严格按照同源图规则校验：
    1. 每一跳必须是 degree-2 同源 (满足 Phi_2 模多项式)
    2. 严禁回溯: j_{k+1} != j_{k-1}
    3. 闭环: j_0 == j_n
    """
    try:
        Fp2.<i> = GF(p^2, modulus=x^2+1)
        # 清洗并解析输入
        raw_js = path_str.split(',')
        js = []
        for s in raw_js:
            s_clean = s.replace(' ', '').replace('*i', '*I').replace('i', 'I')
            js.append(Fp2(eval(s_clean, {'I': i})))

        if len(js) < 10: return False, "路径太短，这不是一个有效的自同态环。"
        if js[0] != js[-1]: return False, "首尾不连贯，这不是一个闭合环路。"

        # 加载 2-阶模多项式: $$\Phi_2(X, Y) = 0$$
        R.<X, Y> = PolynomialRing(Fp2, 2)
        Phi2 = sum(c * X^exp[0] * Y^exp[1] for exp, c in classical_modular_polynomial(2).dict().items())

        for k in range(len(js) - 1):
            # 1. 非回溯校验
            if k > 0 and js[k+1] == js[k-1]:
                return False, f"检测到回溯跳转: 节点 {k} 到 {k+1}"
            
            # 2. 同源性校验: Phi2(j_k, j_{k+1}) == 0
            if Phi2(js[k], js[k+1]) != 0:
                return False, f"非法跳转: 节点 {js[k]} 与 {js[k+1]} 之间不存在 2-同源边"
        
        return True, "Success"
    except Exception as e:
        return False, f"解析异常: {str(e)}"

def handle_connection(conn):
    # 强制超时处理
    def timeout_handler(signum, frame):
        raise TimeoutError("Timeout! Splitting is faster.")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT)

    try:
        welcome = (
            "Welcome to the Abyssal Splittings Challenge (PQCrypto 2026 Edition)!\n"
            "Standard cycle-finding will melt your RAM. You need TRUE 2D Jacobian Splittings.\n"
            "Generating Round 1 parameters... (This might take a few seconds)\n"
            "--- Round 1 ---\n"
            f"Prime p = {P_ROUND1}\n"
            f"Target j = {TARGET_J_STR}\n"
            "Find a non-backtracking cycle for this curve.\n"
            "Submit j-invariant cycle (comma separated): "
        )
        conn.sendall(welcome.encode())

        # 接收答案
        ans = conn.recv(65536).decode().strip()
        if not ans: return

        print(f"[*] 收到 Payload，长度: {len(ans)}。正在调用 Sage 引擎校验...")
        ok, reason = verify_cycle(P_ROUND1, ans)

        if ok:
            conn.sendall(f"\nCorrect!\nMAGNIFICENT! Flag: {FLAG}\n".encode())
            print("[+] 验证通过，已发送 Flag。")
        else:
            conn.sendall(f"\nWrong! Reason: {reason}\n".encode())
            print(f"[-] 验证失败: {reason}")

    except TimeoutError:
        conn.sendall(b"\nTimeout! You are too slow.\n")
    except Exception as e:
        print(f"[!] 处理异常: {e}")
    finally:
        signal.alarm(0)
        conn.close()

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 强制开启端口重用 (解决 Address already in use)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        s.bind(('0.0.0.0', PORT))
        s.listen(5)
        print(f"[*] GZCTF 风格 Sage 靶机启动成功，监听端口: {PORT}")
        print(f"[*] 算力环境: SageMath 10.8 / Python 3.14")
    except Exception as e:
        print(f"[!] 绑定端口失败: {e}")
        return

    while True:
        conn, addr = s.accept()
        print(f"[+] 收到攻击连接: {addr}")
        handle_connection(conn)

if __name__ == "__main__":
    start_server()
