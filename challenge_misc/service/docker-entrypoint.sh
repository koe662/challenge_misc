#!/bin/sh

# 写入flag
echo "flag{test123}" > /flag

# 直接运行Python（不通过socat）
echo "Starting Python script directly..."
exec python3 /home/ctf/server.py
