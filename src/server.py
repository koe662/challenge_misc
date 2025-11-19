#!/usr/bin/env python3
import sys
import os

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

print("🔓 Welcome to SDPCSEC Python Challenge!")
print("========================================")
print("Find the hidden flag to win!")
print("=" * 50)
sys.stdout.flush()

def get_flag():
    """从文件或环境变量获取动态flag"""
    try:
        # 优先从文件读取
        if os.path.exists('/flag'):
            with open("/flag", "r") as f:
                return f.read().strip()
        # 从环境变量读取
        elif os.environ.get('GZCTF_FLAG_BACKUP'):
            return os.environ.get('GZCTF_FLAG_BACKUP')
        elif os.environ.get('GZCTF_FLAG'):
            return os.environ.get('GZCTF_FLAG')
        else:
            return "sdpcsec{pyth0n_j41l_br34k3r_default}"
    except:
        return "sdpcsec{pyth0n_j41l_br34k3r_error}"

def simple_challenge():
    """简单Python挑战"""
    # 获取动态flag
    HIDDEN_FLAG = get_flag()
    
    print("You can run Python commands to find the flag.")
    print("Try to discover the HIDDEN_FLAG variable!")
    print("Enter your Python code (or 'quit' to exit):")
    sys.stdout.flush()
    
    try:
        while True:
            print("\n>>> ", end='')
            sys.stdout.flush()
            
            user_input = sys.stdin.readline().strip()
            
            if user_input.lower() == 'quit':
                print("👋 Goodbye!")
                break
                
            if not user_input:
                continue
                
            # 安全执行用户代码
            try:
                # 创建安全环境
                safe_env = {
                    'print': print,
                    'len': len,
                    'str': str,
                    'int': int,
                    'list': list,
                    'dict': dict,
                    'HIDDEN_FLAG': HIDDEN_FLAG  # 动态flag在环境中
                }
                
                # 执行用户代码
                exec(user_input, safe_env)
                
            except NameError as e:
                print(f"❌ Name error: {e}")
            except Exception as e:
                print(f"💥 Error: {e}")
                
    except KeyboardInterrupt:
        print("\n\n👋 Challenge ended!")
    except Exception as e:
        print(f"💥 System error: {e}")

def main():
    simple_challenge()
    print("\nThank you for playing SDPCSEC Challenge!")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
