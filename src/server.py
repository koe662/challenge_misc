#!/usr/bin/env python3
import os
import sys
import socketserver
import signal
import binascii
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# ================= CONFIGURATION =================
# 获取 Flag，如果本地测试没有环境变量则使用默认值
FLAG = os.environ.get("GZCTF_FLAG", "flag{test_flag_for_local_debug}")
TIMEOUT = 60  # 连接超时时间 (秒)
PORT = 9999   # 监听端口
# =================================================

class Challenge:
    def __init__(self):
        # 每次连接生成随机密钥，隔离不同选手的会话，防止重放
        self.key = os.urandom(16)
        
    def f(self, val_bytes):
        """内部压缩函数 f: 模拟题目中的随机函数 (使用 AES-ECB)"""
        if len(val_bytes) != 16:
            raise ValueError("Input length must be 16 bytes")
        cipher = AES.new(self.key, AES.MODE_ECB)
        return cipher.encrypt(val_bytes)

    def xor_bytes(self, a, b):
        return bytes(x ^ y for x, y in zip(a, b))

    def H(self, message):
        """迭代哈希函数 H"""
        state = b'\x00' * 16
        
        # 自动填充到 16 字节倍数 (Zero Padding)
        # 题目逻辑：如果不满16字节，补0。
        if len(message) % 16 != 0:
            padding_len = 16 - (len(message) % 16)
            message += b'\x00' * padding_len
            
        blocks = [message[i:i+16] for i in range(0, len(message), 16)]
        
        for block in blocks:
            # 核心公式: h_i = m_i ^ f(h_{i-1} ^ m_i)
            inner = self.xor_bytes(state, block)
            f_out = self.f(inner)
            state = self.xor_bytes(block, f_out)
            
        return state

class TaskHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            # 设置超时，防止挂起连接
            signal.alarm(TIMEOUT)
            
            # 初始化挑战环境
            chall = Challenge()
            
            # ==========================================
            # 1. 生成随机目标消息 m
            # ==========================================
            random_id = binascii.hexlify(os.urandom(4)).decode()
            target_msg_str = f"System: Access Granted [ID:{random_id}]"
            target_msg = target_msg_str.encode()
            
            # 计算目标哈希
            target_hash = chall.H(target_msg)
            
            # ==========================================
            # 2. 生成泄露数据对 (x, f(x))
            # 选手需要利用这一对数据构造追加攻击
            # ==========================================
            leak_x = os.urandom(16)
            leak_fx = chall.f(leak_x)
            
            # ==========================================
            # 3. 发送题目信息
            # ==========================================
            self.send_line("=" * 60)
            self.send_line("       [ Hash Second Preimage Challenge ]")
            self.send_line("=" * 60)
            self.send_line(f"Please find a second preimage (collision) for the target message.")
            self.send_line(f"You have {TIMEOUT} seconds.\n")
            
            # 输出 M
            self.send_line(f"[+] Target Message (Hex): {target_msg.hex()}")
            self.send_line(f"[+] Target Hash    (Hex): {target_hash.hex()}")
            self.send_line("-" * 50)
            
            # 输出 (x, f(x))
            self.send_line(f"[+] Leaked Internal Pair (x, f(x)):")
            self.send_line(f"    x    : {leak_x.hex()}")
            self.send_line(f"    f(x) : {leak_fx.hex()}")
            self.send_line("-" * 50)
            
            # ==========================================
            # 4. 等待用户输入
            # ==========================================
            self.send_line("[-] Input your forged message (Hex): ")
            data = self.request.recv(4096).strip()
            
            if not data:
                return

            try:
                user_msg = binascii.unhexlify(data)
            except binascii.Error:
                self.send_line("[!] Error: Invalid Hex encoding.")
                return

            # ==========================================
            # 5. 验证逻辑
            # ==========================================
            
            # 验证 1: 不能提交原始消息
            if user_msg == target_msg:
                self.send_line("[!] Error: You cannot submit the original message.")
                return
            
            # 验证 2: 长度检查 (防止空消息等)
            if len(user_msg) == 0:
                self.send_line("[!] Error: Empty message.")
                return

            # 计算用户提交消息的哈希
            user_hash = chall.H(user_msg)
            
            # 验证 3: 哈希碰撞检查
            if user_hash == target_hash:
                self.send_line(f"\n[+] Success! Collision found.")
                self.send_line(f"[+] Here is your flag: {FLAG}")
            else:
                self.send_line(f"\n[!] Fail. Hash mismatch.")
                self.send_line(f"    Your Hash: {user_hash.hex()}")
                self.send_line(f"    Target   : {target_hash.hex()}")
                
        except Exception as e:
            self.send_line(f"[!] Server Error: {e}")
        finally:
            self.request.close()

    def send_line(self, text):
        """辅助函数：发送一行文本并换行"""
        try:
            self.request.sendall((text + "\n").encode())
        except:
            pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    # 允许端口复用，防止重启容器时端口被占用
    socketserver.TCPServer.allow_reuse_address = True
    server = ThreadedTCPServer(("0.0.0.0", PORT), TaskHandler)
    print(f"[*] Server listening on 0.0.0.0:{PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[*] Server shutting down.")
        server.shutdown()
