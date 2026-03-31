# 必须使用 SageMath 官方镜像
FROM sagemath/sagemath:latest

USER root

# 替换为国内源 (Sage 镜像底层通常是 Ubuntu)
RUN sed -i 's/archive.ubuntu.com/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.ustc.edu.cn/g' /etc/apt/sources.list

# 安装 socat 和 dos2unix (防止 Windows 下写的 sh 脚本在 Linux 下报错)
RUN apt-get update && apt-get install -y socat dos2unix && rm -rf /var/lib/apt/lists/*

WORKDIR /home/ctf

# 拷贝你的题目代码和启动脚本
COPY ./src/server.sage /home/ctf/server.sage
COPY ./service/docker-entrypoint.sh /docker-entrypoint.sh

# 修复换行符并赋予执行权限，移交权限给 sage 默认用户
RUN dos2unix /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh && \
    chown -R sage:sage /home/ctf

# 切换回低权限用户，保证容器安全
USER sage

EXPOSE 9999

ENTRYPOINT ["/bin/sh", "/docker-entrypoint.sh"]
