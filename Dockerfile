FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 创建非特权用户
RUN useradd -m -u 1000 ctf

# 复制文件
COPY --chown=ctf:ctf src/server.py /app/src/
COPY --chown=ctf:ctf service/docker-entrypoint.sh /app/service/

# 设置权限
RUN chmod +x /app/service/docker-entrypoint.sh

USER ctf

WORKDIR /app/src

EXPOSE 9999

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD nc -z localhost 9999 || exit 1

ENTRYPOINT ["/app/service/docker-entrypoint.sh"]
