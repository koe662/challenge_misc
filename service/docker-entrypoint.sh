#!/bin/sh
set -e

echo "=== Starting NTRU Decryption Oracle ===" >&2

# 处理 GZCTF 动态 FLAG
if [ "$GZCTF_FLAG" ]; then
    export FLAG="$GZCTF_FLAG"
    echo "Using GZCTF_FLAG from environment" >&2
else
    export FLAG="flag{local_test_flag_for_ntru}"
    echo "Using default flag template" >&2
fi

echo "Listening on port 9999 with socat..." >&2

# 使用 socat 监听 9999 端口，并让每一次连接都启动一个独立的 sage 进程处理
exec socat TCP-LISTEN:9999,fork,reuseaddr EXEC:"sage /home/ctf/server.sage",pty,stderr,echo=0
