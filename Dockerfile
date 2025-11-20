FROM python:3.9-slim

WORKDIR /app

# 创建目录结构
RUN mkdir -p /app/src /app/service

# 复制文件
COPY src/server.py /app/src/
COPY service/docker-entrypoint.sh /app/service/

# 设置权限
RUN chmod +x /app/service/docker-entrypoint.sh
RUN chmod +x /app/src/server.py

# 创建非root用户
RUN useradd -m -u 1000 ctf && \
    chown -R ctf:ctf /app

USER ctf

EXPOSE 9999

# 使用entrypoint脚本
ENTRYPOINT ["/app/service/docker-entrypoint.sh"]
