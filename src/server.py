#!/usr/bin/env python3
import sys
import io
import ast
import re
from contextlib import redirect_stdout, redirect_stderr

# 打印启动信息
print("=== Python Jail Challenge ===", file=sys.stderr)

# 检查flag文件
try:
    with open('/flag', 'r') as f:
        FLAG = f.read().strip()
    print(f"Flag loaded", file=sys.stderr)
except:
    FLAG = "sdpcsec{pyth0n_j41l_br34k3r_[TEAM_HASH]}"
    print("Using default flag", file=sys.stderr)

# 篡改sys.modules中的os模块
import sys
sys.modules['os'] = 'not allowed'
sys.modules['subprocess'] = 'not allowed'

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

def main():
    banner = """
    🔐 Python Jail Break Challenge
    
    Welcome to the Python sandbox! 
    The 'os' and 'subprocess' modules have been tampered with.
    
    Your goal: Execute commands to read the flag at /flag!
    Hint: Think about how Python module importing works...
    
    Rules:
    - Maximum 500 characters per input
    - No direct imports of os, subprocess, sys, importlib
    - But del and __import__ are allowed!
    
    Enter your Python code (or 'quit' to exit):
    """
    
    print(banner)
    
    while True:
        try:
            user_input = input(">>> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
                
            result = safe_eval(user_input)
            print(result)
            
            # 秘密检查：如果成功执行了系统命令并获取了flag
            if FLAG in str(result):
                print(f"\n🎉 Congratulations! You found the flag: {FLAG}")
                break
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == '__main__':
    main()
