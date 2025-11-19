#!/bin/sh

# 获取flag优先级
if [ "$GZCTF_FLAG" ]; then
    INSERT_FLAG="$GZCTF_FLAG"
    export GZCTF_FLAG_BACKUP="$GZCTF_FLAG"
elif [ "$FLAG" ]; then
    INSERT_FLAG="$FLAG"
else
    INSERT_FLAG="flag{TEST_Dynamic_FLAG}"
fi

# 写入 /flag
echo $INSERT_FLAG > /flag
chmod 600 /flag

# socat启动python
socat -s TCP-LISTEN:9999,reuseaddr,fork EXEC:"python3 -u /home/ctf/server.py"
