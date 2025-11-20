#!/usr/bin/env python3
import sys
import os
import re

# 强制立即输出
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# SDPCSEC Logo
print('''
\033[91m
   _____  ______   ______   _____  ______   _____ 
  / ___/ / ____/  / ____/  / ___/ / ____/  / ___/
 / __ \ / /___   / ___/   / __ \ / /___   / __ \ 
/ /_/ // ___/  / /___   / /_/ // ___/  / /_/ /
\____//_/     /_____/   \____//_/      \____/ 
\033[0m
''')
sys.stdout.flush()

print("🔒 Advanced PyJail Challenge")
print("============================")
print("Escape the jail by re-importing modules!")
print("Only module re-import technique is allowed.")
print("=" * 50)
sys.stdout.flush()

def get_flag():
    """从文件获取动态flag"""
    try:
        if os.path.exists('/flag'):
            with open("/flag", "r") as f:
                return f.read().strip()
        else:
            return "sdpcsec{4dv4nc3d_pyj41l_3sc4p3}"
    except:
        return "sdpcsec{3rr0r_r3tr13v1ng_fl4g}"

def setup_secure_environment():
    """设置安全环境"""
    # 删除危险的模块
    import sys
    dangerous_modules = ['os', 'subprocess', 'shutil', 'socket']
    for module in dangerous_modules:
        if module in sys.modules:
            del sys.modules[module]
    
    # 限制builtins
    safe_builtins = {
        'print': print,
        'len': len,
        'str': str,
        'int': int,
        'list': list,
        'dict': dict,
        'type': type,
        'dir': dir,
        'vars': vars,
        '__import__': __import__
    }
    
    return safe_builtins

def validate_code_safety(code):
    """严格验证代码安全性"""
    # 黑名单检查
    blacklist_patterns = [
        r'__',                      # 禁止双下划线
        r'\.',                      # 禁止点操作符
        r'\[', r'\]',               # 禁止中括号
        r'open\s*\(',               # 禁止open函数
        r'eval\s*\(',               # 禁止eval
        r'exec\s*\(',               # 禁止exec
        r'compile\s*\(',            # 禁止compile
        r'input\s*\(',              # 禁止input
        r'file\s*\(',               # 禁止file
        r'subprocess',              # 禁止subprocess
        r'shutil',                  # 禁止shutil
        r'socket',                  # 禁止socket
        r'commands',                # 禁止commands
        r'popen',                   # 禁止popen
        r'system',                  # 禁止system
        r'import\s+os',             # 禁止import os
        r'from\s+os',               # 禁止from os
    ]
    
    for pattern in blacklist_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return False, f"Security violation detected: {pattern}"
    
    # 检查代码长度限制（防止DoS）
    if len(code) > 500:
        return False, "Code too long (max 500 characters)"
    
    return True, "Code is safe"

def execute_secure_code(code, safe_env):
    """在安全环境中执行代码"""
    try:
        # 创建限制的执行环境
        restricted_globals = {
            '__builtins__': safe_env,
            '__name__': '__main__',
            '__doc__': None
        }
        
        # 执行代码
        exec(code, restricted_globals)
        return True, "Execution completed"
        
    except ImportError as e:
        return False, f"Import error: {e}"
    except Exception as e:
        return False, f"Execution error: {e}"

def pyjail_challenge():
    """PyJail挑战主函数"""
    HIDDEN_FLAG = get_flag()
    safe_env = setup_secure_environment()
    attempts = 5
    
    print("🔧 Challenge Setup:")
    print("- os, subprocess, shutil, socket modules have been removed from sys.modules")
    print("- You must re-import modules to escape")
    print("- Only __import__ function is available")
    print("- Many dangerous functions are blocked")
    print(f"- You have {attempts} attempts")
    print("\n💡 Hint: Think about how Python's import system works!")
    print("         What happens when you delete a module from sys.modules?")
    sys.stdout.flush()
    
    for attempt in range(attempts):
        try:
            print(f"\n🔄 Attempt {attempt + 1}/{attempts}")
            print("Enter your Python code:")
            sys.stdout.flush()
            
            user_code = sys.stdin.readline().strip()
            
            if not user_code:
                continue
                
            # 验证代码安全性
            is_safe, safety_message = validate_code_safety(user_code)
            if not is_safe:
                print(f"❌ {safety_message}")
                continue
            
            # 执行代码
            success, result_message = execute_secure_code(user_code, safe_env)
            
            if success:
                print(f"✅ {result_message}")
                # 检查是否成功获取了flag
                if 'os' in sys.modules:
                    print("🎉 You successfully re-imported os module!")
                    print("Now try to read the flag file...")
            else:
                print(f"❌ {result_message}")
                
        except KeyboardInterrupt:
            print("\n👋 Challenge interrupted!")
            break
        except Exception as e:
            print(f"💥 System error: {e}")
    
    # 显示答案
    print(f"\n🔓 Solution: The flag was: {HIDDEN_FLAG}")
    print("Expected solution: __import__('os').system('cat /flag')")
    sys.stdout.flush()

def main():
    pyjail_challenge()
    print("\nThanks for playing SDPCSEC Advanced PyJail!")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
