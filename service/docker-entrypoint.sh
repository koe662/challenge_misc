#!/bin/sh
set -e

echo "=== Starting Guess Number Game ===" >&2

# 设置flag（猜数字游戏不需要写入文件，直接从环境变量读取）
if [ "$GZCTF_FLAG" ]; then
    echo "Using GZCTF_FLAG from environment" >&2
elif [ "$FLAG" ]; then
    export GZCTF_FLAG="$FLAG"
    echo "Using FLAG from environment" >&2
else
    export GZCTF_FLAG="sdpcsec{gu3ss_numb3r_g4m3_[TEAM_HASH]}"
    echo "Using default flag template" >&2
fi

echo "Starting Python server on port 9999..." >&2

# 切换到工作目录
cd /home/ctf

# 直接启动Python服务（猜数字游戏不需要socat）
exec python server.py
