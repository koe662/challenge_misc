FROM python:3.9-slim

WORKDIR /app

COPY server.py .
RUN chmod +x server.py

# 创建非root用户
RUN useradd -m -u 1000 ctf && \
    chown -R ctf:ctf /app

USER ctf

EXPOSE 9999

CMD ["python", "server.py"]
