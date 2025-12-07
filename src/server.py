import socketserver
import threading
import sys
import os
import signal
from Crypto.Util.number import getPrime, bytes_to_long, long_to_bytes

# 配置
HOST = '0.0.0.0'
PORT = 9999

# 从环境变量读取 FLAG，如果不存在则使用默认测试 Flag
# GZCTF 会在容器启动时将动态 Flag 注入到 GZCTF_FLAG 变量中
FLAG = os.getenv("GZCTF_FLAG", "sdpcsec{b_box_isez_f0r_y0u_[TEAM_HASH]}")

class Challenge:
    def __init__(self):
        print(f"[Init] Generating 512-bit RSA keys for Flag: {FLAG}")
        # 生成两个 256 位的素数，N 为 512 位
        # 512位对于现代工具(YAFU/CADO-NFS)是可分解的，符合题目难度定位
        self.p = getPrime(256)
        self.q = getPrime(256)
        self.N = self.p * self.q
        self.e = 65537 
        
        # 加密 Flag (即题目中的 intercepted message y)
        m = bytes_to_long(FLAG.encode())
        self.encrypted_flag = pow(m, self.e, self.N)

    def encrypt(self, plaintext_int):
        """
        Oracle 函数：Encr(x) = x^e mod n
        """
        if plaintext_int < 0:
            return None
        return pow(plaintext_int, self.e, self.N)

# 全局初始化挑战环境 (确保所有连接使用的是同一个 N 和 Flag)
chall = Challenge()

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # 设置超时，防止恶意占用连接
        self.request.settimeout(60)
        try:
            # 1. 发送欢迎信息和加密后的 Flag
            welcome_msg = (
                f"Welcome to the Hidden RSA Oracle!\n"
                f"I hold a secret modulus N and exponent e.\n"
                f"Here is the intercepted secret message (y): {chall.encrypted_flag}\n"
                f"You can encrypt any integer x using my system: Encr(x) = x^e mod N.\n"
                f"Please input x (integer):\n"
            )
            self.request.sendall(welcome_msg.encode('utf-8'))

            # 2. 交互循环
            while True:
                self.request.sendall(b"> ")
                data = self.request.recv(1024).strip()
                if not data:
                    break
                
                try:
                    x = int(data.decode())
                    # 限制输入大小，防止 DoS
                    if x.bit_length() > 2048: 
                        self.request.sendall(b"Input too large.\n")
                        continue
                    
                    # 执行 Oracle 加密
                    c = chall.encrypt(x)
                    response = f"{c}\n"
                    self.request.sendall(response.encode('utf-8'))
                    
                except ValueError:
                    self.request.sendall(b"Invalid input. Please enter an integer.\n")
        except Exception as e:
            # 连接断开或超时
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
    print(f"[+] Starting Hidden RSA Oracle on {HOST}:{PORT}")
    print(f"[+] Secret N (Log for Admin): {chall.N}")
    
    server.serve_forever()
