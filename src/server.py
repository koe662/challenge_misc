#!/usr/bin/env python3
import sys
import io
import ast
import re
import socket
import threading
from contextlib import redirect_stdout, redirect_stderr

# 打印启动信息到stderr（GZCTF日志可见）
print("=== Python Jail Challenge Server Starting ===", file=sys.stderr)
print(f"Python version: {sys.version}", file=sys.stderr)

# 检查flag文件
try:
    with open('/flag', 'r') as f:
        FLAG = f.read().strip()
    print(f"Flag loaded: {FLAG[:20]}...", file=sys.stderr)
except Exception as e:
    FLAG = "sdpcsec{pyth0n_j41l_br34k3r_[TEAM_HASH]}"
    print(f"Using default flag, error: {e}", file=sys.stderr)

print("Server initialization complete", file=sys.stderr)

# 危险的函数和属性
DANGEROUS_BUILTINS = {
    'eval', 'exec', 'compile', 'open', 'file',
    'exit', 'quit', 'input', 'help', 'globals', 'locals',
    'breakpoint', 'memoryview', 'bytes', 'bytearray'
}

DANGEROUS_ATTRIBUTES = {
    '__class__', '__bases__', '__subclasses__', '__globals__',
    '__code__', '__func__', '__self__', '__builtins__',
    '__getattribute__', '__getattr__', '__setattr__', '__delattr__',
    '__call__', '__init__', '__new__', '__module__', '__name__',
    '__dict__', '__mro__', '__base__', '__subclasses__'
}

class SandboxError(Exception):
    pass

class SandboxVisitor(ast.NodeVisitor):
    def __init__(self):
        self.dangerous_calls = set()
    
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in DANGEROUS_BUILTINS:
                self.dangerous_calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in DANGEROUS_ATTRIBUTES:
                self.dangerous_calls.add(node.func.attr)
        self.generic_visit(node)
    
    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in ['os', 'subprocess', 'sys', 'importlib']:
                raise SandboxError(f"Import of {alias.name} is not allowed directly")
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module in ['os', 'subprocess', 'sys', 'importlib']:
            raise SandboxError(f"Import from {node.module} is not allowed directly")
        self.generic_visit(node)

def safe_eval(code):
    """在受限环境中执行代码"""
    
    # 检查代码长度
    if len(code) > 500:
        return "Code too long (max 500 characters)"
    
    # 检查危险字符串
    dangerous_patterns = [
        r'open\s*\(', r'eval\s*\(', r'exec\s*\(', 
        r'compile\s*\(', r'import\s+os', r'from\s+os', 
        r'import\s+subprocess', r'from\s+subprocess',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return "Dangerous pattern detected!"
    
    # AST解析和检查
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax error: {e}"
    
    visitor = SandboxVisitor()
    try:
        visitor.visit(tree)
    except SandboxError as e:
        return f"Security check failed: {e}"
    
    # 限制内置函数（但保留__import__）
    safe_builtins = {
        'print': print,
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'list': list,
        'dict': dict,
        'tuple': tuple,
        'set': set,
        'range': range,
        'sum': sum,
        'max': max,
        'min': min,
        'abs': abs,
        'round': round,
        'sorted': sorted,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'all': all,
        'any': any,
        'bool': bool,
        'chr': chr,
        'ord': ord,
        'hex': hex,
        'oct': oct,
        'bin': bin,
        '__import__': __import__,
    }
    
    # 执行代码
    local_vars = {}
    global_vars = {'__builtins__': safe_builtins}
    
    try:
        # 为每个执行单独设置被篡改的模块
        original_os = sys.modules.get('os')
        original_subprocess = sys.modules.get('subprocess')
        
        sys.modules['os'] = 'not allowed'
        sys.modules['subprocess'] = 'not allowed'
        
        # 重定向输出
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            exec(code, global_vars, local_vars)
        result = output.getvalue()
        
        # 恢复模块
        if original_os:
            sys.modules['os'] = original_os
        if original_subprocess:
            sys.modules['subprocess'] = original_subprocess
            
        if not result:
            result = "Code executed successfully (no output)"
        return result
        
    except Exception as e:
        # 确保恢复模块即使在异常情况下
        if original_os:
            sys.modules['os'] = original_os
        if original_subprocess:
            sys.modules['subprocess'] = original_subprocess
        return f"Error during execution: {e}"

def handle_client(conn, addr):
    """处理客户端连接"""
    print(f"New connection from {addr}", file=sys.stderr)
    
    try:
        banner = b"""\nPython Jail Break Challenge\n\nWelcome to the Python sandbox!\nThe 'os' and 'subprocess' modules have been tampered with.\n\nYour goal: Execute commands to read the flag!\nHint: Think about how Python module importing works...\n\nRules:\n- Max 500 characters per input\n- No direct imports of os, subprocess, sys, importlib\n- But del and __import__ are allowed!\n\nEnter your Python code (or 'quit' to exit):\n>>> """
        conn.send(banner)
        
        while True:
            try:
                data = conn.recv(1024).decode('utf-8', errors='ignore').strip()
                if not data:
                    print(f"Client {addr} disconnected", file=sys.stderr)
                    break
                    
                if data.lower() in ['quit', 'exit', 'q']:
                    conn.send(b"Goodbye!\n")
                    break
                
                print(f"Received from {addr}: {data}", file=sys.stderr)
                result = safe_eval(data)
                print(f"Result for {addr}: {result}", file=sys.stderr)
                
                # 检查是否获取到flag
                if FLAG in str(result):
                    result += f"\n\n🎉 Congratulations! You found the flag: {FLAG}"
                    print(f"Flag captured by {addr}", file=sys.stderr)
                
                response = f"{result}\n>>> "
                conn.send(response.encode('utf-8'))
                
            except socket.error as e:
                print(f"Socket error with {addr}: {e}", file=sys.stderr)
                break
            except Exception as e:
                print(f"Error with {addr}: {e}", file=sys.stderr)
                try:
                    conn.send(f"Error: {e}\n>>> ".encode('utf-8'))
                except:
                    break
            
    except Exception as e:
        print(f"Connection error with {addr}: {e}", file=sys.stderr)
    finally:
        try:
            conn.close()
        except:
            pass
        print(f"Connection from {addr} closed", file=sys.stderr)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 9999))
    server.listen(5)
    print("Server listening on 0.0.0.0:9999", file=sys.stderr)
    
    try:
        while True:
            conn, addr = server.accept()
            print(f"Accepted connection from {addr}", file=sys.stderr)
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\nShutting down server...", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
    finally:
        server.close()

if __name__ == '__main__':
    start_server()
