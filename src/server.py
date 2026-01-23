#!/usr/bin/env python3
import os
import sys
import socketserver
import binascii
import json
from Crypto.Cipher import AES

# ================= CONFIGURATION =================
FLAG = os.environ.get("GZCTF_FLAG", "flag{Matr1x_M4ster_Beat5_App3nd_Att4ck}")
# 块大小 128 bits (16 bytes)
BLOCK_SIZE = 16
# 限制最大块数量 (Target Message Length)
# 矩阵攻击通常需要约 128 个块来生成任意哈希
MAX_BLOCKS = 135 
# 提供足够多的已知对，确保满秩 (256 > 128)
PAIRS_COUNT = 300 
# =================================================

class Challenge:
    def __init__(self):
        self.key = os.urandom(16)
        
    def f(self, val_bytes):
        if len(val_bytes) != 16:
            raise ValueError("Input length must be 16 bytes")
        cipher = AES.new(self.key, AES.MODE_ECB)
        return cipher.encrypt(val_bytes)

    def xor_bytes(self, a, b):
        return bytes(x ^ y for x, y in zip(a, b))

    def H(self, message):
        state = b'\x00' * 16
        # Zero Padding
        if len(message) % 16 != 0:
            message += b'\x00' * (16 - (len(message) % 16))
            
        blocks = [message[i:i+16] for i in range(0, len(message), 16)]
        
        for block in blocks:
            # h_i = m_i ^ f(h_{i-1} ^ m_i)
            inner = self.xor_bytes(state, block)
            f_out = self.f(inner)
            state = self.xor_bytes(block, f_out)
            
        return state

class TaskHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            chall = Challenge()
            
            # 1. 生成一个较长的随机目标消息 (接近 MAX_BLOCKS)
            # 这样 Append Attack 必然超长
            target_blocks = MAX_BLOCKS
            target_msg = os.urandom(target_blocks * BLOCK_SIZE)
            target_hash = chall.H(target_msg)
            
            # 2. 生成大量泄露数据 (供矩阵求解)
            known_pairs = []
            seen_x = set()
            while len(known_pairs) < PAIRS_COUNT:
                x = os.urandom(16)
                if x in seen_x: continue
                seen_x.add(x)
                known_pairs.append({"x": x.hex(), "fx": chall.f(x).hex()})
            
            # 3. 交互
            self.send_line("=== Hash Collision: Hard Mode (Length Restricted) ===")
            self.send_line(f"Find a second preimage with LENGTH <= {MAX_BLOCKS * BLOCK_SIZE} bytes.")
            self.send_line("Hint: The simple append strategy will make the message too long!")
            self.send_line("-" * 50)
            
            self.send_line(f"[+] Target Hash (Hex): {target_hash.hex()}")
            # 注意：这里不需要发 Target Message 的原文，
            # 因为矩阵攻击根本不需要原文，只需要 Hash 值。
            # 如果你发了原文，append 攻击者会发现追加后长度变长了。
            
            self.send_line(f"[+] Leaked Pairs ({len(known_pairs)}):")
            self.send_line(json.dumps(known_pairs))
            self.send_line("-" * 50)
            
            self.send_line("[-] Input your forged message (Hex): ")
            data = self.request.recv(65536).strip()
            
            try:
                user_msg = binascii.unhexlify(data)
            except:
                self.send_line("[!] Invalid Hex.")
                return

            # === 核心限制：长度检查 ===
            # Append Attack 构造的消息长度是 len(target) + 32
            # 我们这里限制必须 <= len(target)
            if len(user_msg) > target_blocks * BLOCK_SIZE:
                self.send_line(f"[!] Fail: Message too long! Max {target_blocks} blocks.")
                self.send_line(f"    Your length: {len(user_msg)//16} blocks.")
                return

            # 验证哈希
            user_hash = chall.H(user_msg)
            if user_hash == target_hash:
                self.send_line(f"[+] Flag: {FLAG}")
            else:
                self.send_line(f"[!] Fail. Hash mismatch.")
                
        except Exception as e:
            self.send_line(f"[!] Error: {e}")
        finally:
            self.request.close()

    def send_line(self, text):
        try:
            self.request.sendall((text + "\n").encode())
        except: pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    server = ThreadedTCPServer(("0.0.0.0", 9999), TaskHandler)
    server.serve_forever()
