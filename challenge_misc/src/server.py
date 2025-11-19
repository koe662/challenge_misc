#!/usr/bin/env python3
import sys
import os

# 强制立即输出
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("🚀 Factor Selection Game - Connected Successfully!")
print("================================================")
sys.stdout.flush()

# 简单回显测试
try:
    while True:
        print("Enter a number (or 'quit' to exit):", end=' ')
        sys.stdout.flush()
        
        user_input = sys.stdin.readline().strip()
        if not user_input:
            continue
            
        if user_input.lower() == 'quit':
            print("Goodbye!")
            sys.stdout.flush()
            break
            
        print(f"You entered: {user_input}")
        sys.stdout.flush()
        
except Exception as e:
    print(f"Error: {e}")
    sys.stdout.flush()
