#!/usr/bin/env python3
import os
import sys
import socketserver
import binascii
import random
import json

# ================= CONFIGURATION =================
FLAG = os.environ.get("GZCTF_FLAG", "flag{PH1GFS_M4tr1x_H4s_Inv4r1ant_Subsp4c3}")
ROUNDS_TO_WIN = 50  # 需要连续猜对的次数
QUERIES_PER_ROUND = 2  # 每轮允许的明文查询次数
# =================================================

class PHIGFS:
    def __init__(self):
        # 按照竞赛设定，S盒可以是随机但固定的
        self.sbox = list(range(256))
        random.seed(2022)
        random.shuffle(self.sbox)
        # 具有漏洞的 A'' 矩阵
        self.matrix = [
            [0, 1, 1, 1],
            [1, 1, 1, 0],
            [1, 1, 0, 1],
            [1, 0, 1, 1]
        ]

    def _apply_matrix(self, v):
        res = [0, 0, 0, 0]
        for i in range(4):
            for j in range(4):
                if self.matrix[i][j]:
                    res[i] ^= v[j]
        return res

    def encrypt(self, block, round_keys):
        """实现 PHIGFS 8轮加密"""
        state = list(block)
        for r in range(8):
            x3, x2, x1, x0 = state
            k1, k0 = round_keys[r]
            
            # 非线性层：y2 = x2 ⊕ b(x3 ⊕ k1), y0 = x0 ⊕ b(x1 ⊕ k0)
            y2 = x2 ^ self.sbox[x3 ^ k1]
            y0 = x0 ^ self.sbox[x1 ^ k0]
            
            # 矩阵扩散层
            state = self._apply_matrix([x3, y2, x1, y0])
        return bytes(state)

class TaskHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            chall = PHIGFS()
            self.send_line("=== PHIGFS Distinguisher Challenge: Hard Mode ===")
            self.send_line(f"Successfully identify the algorithm {ROUNDS_TO_WIN} times to get the Flag.")
            self.send_line("In each round, you can query 2 plaintexts (4-byte hex).")
            self.send_line("-" * 50)

            for i in range(ROUNDS_TO_WIN):
                self.send_line(f"[Round {i+1}/{ROUNDS_TO_WIN}]")
                
                # 随机决定本轮是真实算法还是随机置换
                is_real = random.getrandbits(1)
                # 为本轮生成随机轮密钥
                round_keys = [(random.getrandbits(8), random.getrandbits(8)) for _ in range(8)]
                
                # 查询阶段
                for q in range(QUERIES_PER_ROUND):
                    self.send_line(f"[-] Query {q+1} (Hex, 4 bytes): ")
                    line = self.request.recv(1024).strip().decode()
                    if not line: return
                    
                    try:
                        p = binascii.unhexlify(line)
                        if len(p) != 4: raise ValueError
                    except:
                        self.send_line("[!] Invalid input.")
                        return

                    if is_real:
                        res = chall.encrypt(p, round_keys)
                    else:
                        # 随机模式：返回真随机字节
                        res = os.urandom(4)
                    
                    self.send_line(f"Result: {res.hex()}")

                # 提交答案阶段
                self.send_line("[?] Is this [R]EAL PHIGFS or [F]AKE Random? (R/F): ")
                choice = self.request.recv(1024).strip().decode().upper()
                
                correct = (choice == 'R' and is_real) or (choice == 'F' and not is_real)
                
                if correct:
                    self.send_line("[+] Correct!")
                else:
                    self.send_line("[!] Wrong! Philip's cipher remains a mystery to you.")
                    return

            # 全部通过
            self.send_line("-" * 50)
            self.send_line(f"[***] Congratulations! Your Flag: {FLAG}")

        except Exception as e:
            # 避免泄露服务端错误，仅打印提示
            pass
        finally:
            self.request.close()

    def send_line(self, text):
        try:
            self.request.sendall((text + "\n").encode())
        except:
            pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    # 监听 9999 端口，GZCTF 映射此端口即可
    server = ThreadedTCPServer(("0.0.0.0", 9999), TaskHandler)
    server.serve_forever()
