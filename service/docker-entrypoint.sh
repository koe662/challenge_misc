#!/bin/sh
set -e

echo "=== Starting Post-Quantum NTRU Crypto Challenge ===" >&2

# 1. 适配 GZCTF 动态 FLAG 注入
if [ "$GZCTF_FLAG" ]; then
    export FLAG="$GZCTF_FLAG"
    echo "Using GZCTF_FLAG from environment" >&2
elif [ "$FLAG" ]; then
    echo "Using standard FLAG environment variable" >&2
else
    export FLAG="flag{local_test_flag_for_ntru_fail}"
    echo "Using default fallback flag" >&2
fi

echo "Listening on port 9999 with socat..." >&2

# 2. socat 接管端口，每次连入启动一个 sage 进程进行交互
exec socat TCP-LISTEN:9999,fork,reuseaddr EXEC:"sage /home/ctf/server.sage",pty,stderr,echo=0
