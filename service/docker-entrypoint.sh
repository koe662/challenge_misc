#!/bin/sh
set -e

echo "=== Starting Container ===" >&2

# 获取flag优先级
if [ "$GZCTF_FLAG" ]; then
    INSERT_FLAG="$GZCTF_FLAG"
    echo "Using GZCTF_FLAG" >&2
elif [ "$FLAG" ]; then
    INSERT_FLAG="$FLAG"
    echo "Using FLAG" >&2
else
    # 使用正确的flag模板
    INSERT_FLAG="sdpcsec{pyth0n_j41l_br34k3r_test}"
    echo "Using default flag" >&2
fi

echo "Flag: $INSERT_FLAG" >&2

# 确保flag文件创建（使用root权限）
echo "$INSERT_FLAG" > /flag
chmod 644 /flag
echo "Flag file created at /flag" >&2

# 验证flag文件
if [ -f "/flag" ]; then
    echo "Flag file verified: $(cat /flag)" >&2
else
    echo "ERROR: Flag file not created!" >&2
    exit 1
fi

echo "Starting socat service..." >&2

# socat启动python
exec socat -s TCP-LISTEN:9999,reuseaddr,fork EXEC:"python3 -u /home/ctf/server.py"
