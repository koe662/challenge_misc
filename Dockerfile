FROM python:3.9-slim
# 使用国内源（修复sed命令）RUN echo "deb http://mirrors.ustc.edu.cn/debian/ bullseye main" > /etc/apt/sources.list && \    echo "deb http://mirrors.ustc.edu.cn/debian-security bullseye-security main" >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y socat
# 使用国内pip源RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \    pycryptodome sympy
RUN useradd -m ctfWORKDIR /home/ctf
COPY ./src/server.py /home/ctf/server.pyCOPY ./service/docker-entrypoint.sh /docker-entrypoint.shRUN chmod +x /docker-entrypoint.sh
USER ctf
ENTRYPOINT ["/bin/sh","/docker-entrypoint.sh"]
