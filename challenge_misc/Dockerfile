FROM python:3.9-slim

RUN apt-get update && apt-get install -y socat
RUN pip install pycryptodome sympy

RUN useradd -m ctf
WORKDIR /home/ctf

COPY ./src/server.py /home/ctf/server.py
COPY ./service/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

USER ctf

ENTRYPOINT ["/bin/sh","/docker-entrypoint.sh"]
#12
