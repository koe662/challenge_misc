import socketserver
import sys
import os
import signal
import random
from Crypto.Util.number import getPrime

# 配置
HOST = '0.0.0.0'
PORT = 9999
FLAG = os.getenv("GZCTF_FLAG", "sdpcsec{b_box_isez_f0r_y0u_[TEAM_HASH]}")

class Challenge:
    def __init__(self):
        # 1. 生成模数 N
        self.p = getPrime(256)
        self.q = getPrime(256)
        self.N = self.p * self.q
        
        # 2. 生成 e (3 ~ 10000)
        # 按照要求：不需要检查 gcd(e, phi) == 1
        # 这意味着 e 甚至可以是偶数，或者 phi 的因子，这对 "求N" 的逻辑没有影响
        self.e = random.randint(3, 10000)

    def encrypt(self, plaintext_int):
        """
        Oracle: x^e mod N
        """
        return pow(plaintext_int, self.e, self.N)

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(120)
        try:
            # 每次连接都实例化一个新的 Challenge，保证 N 和 e 是全新的
            current_chall = Challenge()
            
            # 欢迎信息 (不输出 y)
            welcome_msg = (
                f"Welcome to the RSA Modulus Challenge!\n"
                f"Settings: e is random (< 10000), and checks on GCD(e, phi) are REMOVED.\n"
                f"You have 2 chances to query: x -> x^e mod N\n"
                f"Then you must reveal N.\n"
                f"--------------------------------------------------\n"
            )
            self.request.sendall(welcome_msg.encode('utf-8'))

            # 2 次查询机会
            for i in range(2):
                try:
                    self.request.sendall(f"[{i+1}/2] Input x: ".encode('utf-8'))
                    data = self.request.recv(1024).strip()
                    if not data: return
                    
                    x = int(data.decode())
                    
                    # 限制输入大小
                    if x.bit_length() > 2048:
                        self.request.sendall(b"Input too large.\n")
                        return
                    
                    # 计算并返回结果
                    c = current_chall.encrypt(x)
                    self.request.sendall(f"Result: {c}\n".encode('utf-8'))
                    
                except ValueError:
                    self.request.sendall(b"Invalid integer.\n")
                    return

            # 验证环节
            self.request.sendall(b"\nQueries used up. Tell me N: ")
            data = self.request.recv(4096).strip()
            if not data: return
            
            try:
                user_n = int(data.decode())
                # 判定
                if user_n == current_chall.N:
                    self.request.sendall(f"\nCorrect! Flag: {FLAG}\n".encode('utf-8'))
                else:
                    self.request.sendall(b"\nWrong N! Bye.\n")
            except ValueError:
                pass

        except Exception:
            pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

def signal_handler(sig, frame):
    print("\n[!] Server stopping...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    print(f"[+] Starting Challenge on port {PORT}")
    print(f"[+] Constraints: e < 10000, No Coprime Check")
    server.serve_forever()
