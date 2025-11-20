#!/bin/sh
set -e

# 获取flag优先级
if [ "$GZCTF_FLAG" ]; then
    INSERT_FLAG="$GZCTF_FLAG"
    export GZCTF_FLAG_BACKUP="$GZCTF_FLAG"
elif [ "$FLAG" ]; then
    INSERT_FLAG="$FLAG"
else
    INSERT_FLAG="flag{TEST_Dynamic_FLAG}"
fi

# 写入 /flag (使用root权限)
echo $INSERT_FLAG > /flag
chmod 644 /flag

# 切换到ctf用户并启动
exec su -c "socat -s TCP-LISTEN:9999,reuseaddr,fork EXEC:'python3 -u /home/ctf/server.py'" ctf
