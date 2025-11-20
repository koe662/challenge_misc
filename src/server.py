#!/usr/bin/env python3
import sys
import io
import ast
import re
import socket
import threading
from contextlib import redirect_stdout, redirect_stderr

# 设置flag
import os
FLAG = os.environ.get('GZCTF_FLAG', 'sdpcsec{pyth0n_j41l_br34k3r_[TEAM_HASH]}')

# 在flag路径写入flag
with open('/flag', 'w') as f:
    f.write(FLAG)

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

def safe_exec_wrapper(code, globals_vars, locals_vars):
    """安全的代码执行包装器，防止源码读取"""
    import os
    original_system = os.system
    original_popen = os.popen
    
    def safe_system(cmd):
        # 检查是否尝试读取源码
        blocked_patterns = ['.py', 'server', 'src', 'app', 'cat ', 'head ', 'tail ', 'less ', 'more ', 'vim ', 'nano ']
        if any(pattern in cmd.lower() for pattern in blocked_patterns):
            if 'flag' not in cmd.lower():  # 允许读取flag
                return 1  # 返回错误码
        return original_system(cmd)
    
    def safe_popen(cmd):
        # 检查是否尝试读取源码
        blocked_patterns = ['.py', 'server', 'src', 'app', 'cat ', 'head ', 'tail ', 'less ', 'more ']
        if any(pattern in cmd.lower() for pattern in blocked_patterns):
            if 'flag' not in cmd.lower():  # 允许读取flag
                class BlockedPopen:
                    def read(self):
                        return "Command blocked: source code protection"
                    def __iter__(self):
                        return iter([])
                    def close(self):
                        pass
                return BlockedPopen()
        return original_popen(cmd)
    
    # 替换系统函数
    os.system = safe_system
    os.popen = safe_popen
    
    try:
        exec(code, globals_vars, locals_vars)
    finally:
        # 恢复原始函数
        os.system = original_system
        os.popen = original_popen

def safe_eval(code, timeout=3):
    """在受限环境中执行代码"""
    
    # 检查代码长度
    if len(code) > 500:
        return "Code too long (max 500 characters)"
    
    # 检查危险字符串和源码读取
    dangerous_patterns = [
        r'open\s*\(', r'eval\s*\(', r'exec\s*\(', 
        r'compile\s*\(', r'import\s+os', r'from\s+os', 
        r'import\s+subprocess', r'from\s+subprocess',
        r'server\.py', r'src/', r'app/',  # 禁止读取源码路径
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return "Dangerous pattern detected!"
    
    # 检查命令中是否包含源码相关关键词（但允许flag）
    source_keywords = ['server.py', '.py', 'src', 'app']
    if any(keyword in code.lower() for keyword in source_keywords):
        if 'flag' not in code.lower():  # 只有不包含flag时才阻止
            return "Source code reading is not allowed!"
    
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
        '__import__': __import__,  # 允许使用__import__
    }
    
    # 执行代码
    local_vars = {}
    global_vars = {'__builtins__': safe_builtins}
    
    try:
        # 重定向输出
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            safe_exec_wrapper(code, global_vars, local_vars)
        result = output.getvalue()
        if not result:
            result = "Code executed successfully (no output)"
        return result
    except Exception as e:
        return f"Error during execution: {e}"

def handle_client(conn, addr):
    """处理客户端连接"""
    print(f"New connection from {addr}")
    
    # 为每个客户端连接单独设置被篡改的模块
    import sys
    original_os = sys.modules.get('os')
    original_subprocess = sys.modules.get('subprocess')
    
    sys.modules['os'] = 'not allowed'
    sys.modules['subprocess'] = 'not allowed'
    
    try:
        banner = b"""
    \xf0\x9f\x94\x90 Python Jail Break Challenge
    
    Welcome to the Python sandbox! 
    The 'os' and 'subprocess' modules have been tampered with.
    
    Your goal: Execute commands to read the flag at /flag!
    Hint: Think about how Python module importing works...
    
    Rules:
    - Maximum 500 characters per input
    - No direct imports of os, subprocess, sys, importlib
    - No reading source code files (.py files are protected)
    - But del and __import__ are allowed!
    
    Enter your Python code (or 'quit' to exit):
    >>> """
        conn.send(banner)
        
        while True:
            try:
                data = conn.recv(1024).decode().strip()
                if not data:
                    break
                    
                if data.lower() in ['quit', 'exit', 'q']:
                    conn.send(b"Goodbye!\n")
                    break
                
                result = safe_eval(data)
                
                # 检查是否获取到flag
                if FLAG in str(result):
                    result += f"\n\n🎉 Congratulations! You found the flag: {FLAG}"
                
                response = f"{result}\n>>> "
                conn.send(response.encode())
                
            except socket.error:
                break
            except Exception as e:
                conn.send(f"Error: {e}\n>>> ".encode())
            
    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        # 恢复原始模块
        if original_os:
            sys.modules['os'] = original_os
        if original_subprocess:
            sys.modules['subprocess'] = original_subprocess
        conn.close()
        print(f"Connection from {addr} closed")

def start_server(host='0.0.0.0', port=9999):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    print(f"Server listening on {host}:{port}")
    
    try:
        while True:
            conn, addr = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.close()

if __name__ == '__main__':
    start_server()
