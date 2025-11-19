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

# 创建测试文件验证脚本执行
echo "Entrypoint script started at $(date)" > /tmp/debug.log
echo "Flag written: $(cat /flag)" >> /tmp/debug.log

# 测试Python脚本是否能运行
echo "Testing Python script..." >> /tmp/debug.log
python3 /home/ctf/server.py >> /tmp/debug.log 2>&1 &

# 启动socat服务
echo "Starting socat on port 9999..." >> /tmp/debug.log
exec socat -v TCP-LISTEN:9999,reuseaddr,fork EXEC:"python3 -u /home/ctf/server.py" 2>> /tmp/socat.log
