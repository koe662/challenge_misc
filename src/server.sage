#!/usr/bin/env sage
import socket
import signal
import re
from sage.all import *

# ================= 配置区 =================
PORT = 35654
TIMEOUT = 120  # 120秒限时
P_VAL = 185752092671 # 38-bit prime
FLAG = "flag{Sage_Verified_Isogeny_Cycle_2026}"
# =========================================

def verify_isogeny_cycle(p, path_list):
    """
    使用 SageMath 内置逻辑严格校验同源环路
    """
    try:
        Fp2.<i> = GF(p^2, modulus=x^2+1)
        # 将字符串解析为 Fp2 元素
        def parse_j(s):
            s = s.replace(' ', '').replace('*i', '*I').replace('i', 'I')
            return Fp2(eval(s, {'I': i}))

        js = [parse_j(n) for n in path_list]
        
        if len(js) < 5:
            return False, "路径太短，不符合环路要求。"
        if js[0] != js[-1]:
            return False, "首尾不一致，这不是一个环。"

        # 预载 2-阶模多项式 (Modular Polynomial)
        R.<X, Y> = PolynomialRing(Fp2, 2)
        Phi2 = sum(c * X^exp[0] * Y^exp[1] for exp, c in classical_modular_polynomial(2).dict().items())

        for k in range(len(js) - 1):
            # 1. 校验非回溯: j_{k+1} != j_{k-1}
            if k > 0 and js[k+1] == js[k-1]:
                return False, f"检测到回溯！位置: {k} -> {k+1}"
            
            # 2. 校验同源性: Phi_2(j_k, j_{k+1}) == 0
            if Phi2(js[k], js[k+1]) != 0:
                return False, f"无效同源跳跃！从 {js[k]} 到 {js[k+1]}"
        
        return True, "验证通过"
    except Exception as e:
        return False, f"校验过程出错: {str(e)}"

def handle_client(conn):
    def timeout_handler(signum, frame):
        raise TimeoutError()

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT)

    try:
        # 初始欢迎语
        welcome = (
            "[SERVER] Welcome to the Abyssal Splittings Challenge (PQCrypto 2026 Edition)!\n"
            "[SERVER] Standard cycle-finding will melt your RAM. You need TRUE 2D Jacobian Splittings.\n"
            f"[SERVER] --- Round 1 ---\n"
            f"[SERVER] Prime p = {P_VAL}\n"
            f"[SERVER] Target j = 140087322762*i + 41012056975\n"
            "[SERVER] Submit j-invariant cycle (comma separated): "
        )
        conn.sendall(welcome.encode())

        # 接收 Payload
        data = conn.recv(65536).decode().strip()
        if not data: return

        # 提取路径
        path_list = data.split(',')
        
        # 启动 Sage 校验
        print(f"[*] 正在验证来自客户端的路径 (长度: {len(path_list)})...")
        is_valid, reason = verify_isogeny_cycle(P_VAL, path_list)

        if is_valid:
            conn.sendall(f"\nCorrect!\nMAGNIFICENT! Flag: {FLAG}\n".encode())
            print("[+] 验证成功，已下发 Flag")
        else:
            conn.sendall(f"\nWrong! Reason: {reason}\n".encode())
            print(f"[-] 验证失败: {reason}")

    except TimeoutError:
        conn.sendall(b"\nTimeout! You are too slow.\n")
    except Exception as e:
        print(f"[!] 错误: {e}")
    finally:
        signal.alarm(0)
        conn.close()

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', PORT))
    s.listen(5)
    print(f"[*] Sage 靶机已启动，监听端口: {PORT} (限时 {TIMEOUT}s)")
    while True:
        conn, addr = s.accept()
        handle_client(conn)

if __name__ == "__main__":
    start_server()
