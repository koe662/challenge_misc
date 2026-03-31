# 使用 SageMath 官方镜像，支持多项式环运算
FROM sagemath/sagemath:latest

# 切换到 root 权限来安装依赖包
USER root

# 注意：千万不要在 GitHub Actions 里换国内源！直接用默认的更新
RUN apt-get update && \
    apt-get install -y socat dos2unix && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /home/ctf

# 拷贝代码和启动脚本
COPY ./src/server.sage /home/ctf/server.sage
COPY ./service/docker-entrypoint.sh /docker-entrypoint.sh

# 转换换行符（防止 Windows 提交到 Git 导致换行符报错），并赋予执行权限
RUN dos2unix /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh && \
    chown -R sage:sage /home/ctf

# 降权回 sage 用户，保证靶机安全
USER sage

EXPOSE 9999

ENTRYPOINT ["/bin/sh", "/docker-entrypoint.sh"]


