#!/usr/bin/env python3
import sys
import io
import resource
from contextlib import redirect_stdout, redirect_stderr

# 设置资源限制
resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
resource.setrlimit(resource.RLIMIT_AS, (64 * 1024 * 1024, 64 * 1024 * 1024))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))

# 设置flag
FLAG = "sdpcsec{pyth0n_j41l_br34k3r_[TEAM_HASH]}"

def safe_exec(code):
    """安全执行用户代码"""
    if len(code) > 200:
        return "Code too long (max 200 chars)"
    
    # 只禁止最危险的函数
    blocked = ['eval', 'exec', 'open', 'file']
    if any(word in code.lower() for word in blocked):
        return "Dangerous code detected!"
    
    # 安全的内置函数（不包含os模块）
    safe_builtins = {
        'print': print, 'len': len, 'str': str, 'int': int, 'chr': chr, 'ord': ord,
        'list': list, 'dict': dict, 'range': range, 'sum': sum, 'max': max, 'min': min,
        '__import__': __import__,  # 允许使用__import__
        'sys': sys  # 添加sys模块
    }
    
    # 执行代码
    local_vars = {}
    global_vars = {'__builtins__': safe_builtins, 'sys': sys}
    
    try:
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            # 为每次执行单独设置被篡改的模块
            original_os = sys.modules.get('os')
            sys.modules['os'] = 'not allowed'
            
            exec(code, global_vars, local_vars)
            
            # 恢复模块
            if original_os:
                sys.modules['os'] = original_os
                
        result = output.getvalue()
        return result if result else "Code executed (no output)"
        
    except Exception as e:
        # 确保恢复模块即使在异常情况下
        original_os = sys.modules.get('os')
        if original_os:
            sys.modules['os'] = original_os
        return f"Error: {e}"

def main():
    banner = """
\033[94m
╔══════════════════════════════════════════════╗
║                                              ║
║    ███████╗██████╗ ██████╗  ██████╗         ║
║    ██╔════╝██╔══██╗██╔══██╗██╔════╝         ║
║    ███████╗██║  ██║██████╔╝██║              ║
║    ╚════██║██║  ██║██╔══██╗██║              ║
║    ███████║██████╔╝██║  ██║╚██████╗         ║
║    ╚══════╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝         ║
║                                              ║
║         Python Jail Break Challenge          ║
║                                              ║
╚══════════════════════════════════════════════╝
\033[0m

\033[92mWelcome to the SDPC Python Sandbox!\033[0m

The 'os' module has been tampered with and is currently blocked.
Your mission is to bypass this restriction and execute system commands.

\033[93m📖 Challenge Rules:\033[0m
• Maximum 200 characters per input
• No eval/exec/open functions
• But del, import and __import__ are allowed!

\033[96m💡 Hint: Think about how Python module importing works...
        What happens when you delete a module from sys.modules?\033[0m

Enter your Python code below (type 'quit' to exit):
>>> """
    
    print(banner)
    
    while True:
        try:
            user_input = input("\033[95m>>> \033[0m").strip()
            if user_input.lower() in ['quit', 'exit']:
                print("\n\033[92mThank you for playing! Goodbye! 👋\033[0m")
                break
            if not user_input:
                continue
                
            result = safe_exec(user_input)
            print(f"\033[97m{result}\033[0m")
            
            # 检查是否获取到flag
            if FLAG in str(result):
                print(f"\n\033[92m🎉 CONGRATULATIONS! 🎉")
                print(f"🏁 Flag: {FLAG}")
                print("You successfully broke out of the Python jail! 🚀\033[0m")
                break
                
        except (EOFError, KeyboardInterrupt):
            print("\n\033[92mThank you for playing! Goodbye! 👋\033[0m")
            break
        except Exception as e:
            print(f"\033[91mUnexpected error: {e}\033[0m")

if __name__ == '__main__':
    main()
