import os
import sys
import random
from sage.all import *

# 获取 GZCTF 动态注入的 FLAG，本地测试时回退到默认值
FLAG = os.getenv("FLAG", "flag{d3crypt10n_f41lur3_1s_f4t4l_t0_ntru}").encode()

N = 167
p = 3
q = 128
df = 61
dg = 45 
dr = 45

Zx.<x> = ZZ[]
Rq = PolynomialRing(Zmod(q), 'x').quotient(x^N - 1)
Rp = PolynomialRing(Zmod(p), 'x').quotient(x^N - 1)

def print_out(msg):
    """带 flush 的输出，防止 socat 缓冲导致客户端卡死"""
    print(msg, flush=True)

def gen_ternary(num_ones, num_neg_ones):
    poly = [1]*num_ones + [-1]*num_neg_ones + [0]*(N - num_ones - num_neg_ones)
    random.shuffle(poly)
    return Zx(poly)

def keygen():
    while True:
        f = gen_ternary(df, df - 1)
        try:
            Fq = Rq(f)^-1
            Fp = Rp(f)^-1
            break
        except ZeroDivisionError:
            continue
    g = gen_ternary(dg, dg)
    h = Rq(p) * Rq(g) * Fq
    return f, Fp, h

def encrypt(m_poly, h):
    r = gen_ternary(dr, dr)
    c = Rq(r) * h + Rq(m_poly)
    return c

def decrypt(c, f, Fp):
    a = Rq(c) * Rq(f)
    a_lifted = [((int(a[i]) + q//2) % q) - q//2 for i in range(N)]
    a_poly = Zx(a_lifted)
    m_dec = Rp(a_poly) * Fp
    m_lifted = [((int(m_dec[i]) + p//2) % p) - p//2 for i in range(N)]
    return Zx(m_lifted)

def flag_to_poly(flag: bytes):
    bits = ''.join([bin(b)[2:].zfill(8) for b in flag])
    poly = [1 if bit == '1' else -1 for bit in bits]
    poly += [0] * (N - len(poly))
    return Zx(poly)

def main():
    print_out("[*] Generating Post-Quantum Keys...")
    f, Fp, h = keygen()
    
    m_flag = flag_to_poly(FLAG)
    c_flag = encrypt(m_flag, h)
    
    print_out(f"[+] Public Key (h): {h.list()}")
    print_out(f"[+] Encrypted Flag: {c_flag.list()}")
    print_out("-" * 50)
    print_out("Welcome to the NTRU Decryption Oracle!")
    print_out("You can query up to 5000 times.")
    
    for _ in range(5000):
        try:
            print_out("Send ciphertext (comma separated integers) > ")
            req = sys.stdin.readline().strip()
            if not req:
                break
                
            c_list = [int(x.strip()) for x in req.split(",")]
            if len(c_list) > N:
                print_out("[-] Ciphertext too long.")
                continue
                
            c_query = Rq(c_list)
            
            if c_query == c_flag:
                print_out("[-] Oracle refuses to decrypt the intercepted flag!")
                continue
                
            m_prime = decrypt(c_query, f, Fp)
            print_out(f"Decrypted: {m_prime.list()}")
        except Exception as e:
            print_out("[-] Invalid input or connection closed.")
            break

if __name__ == "__main__":
    main()
