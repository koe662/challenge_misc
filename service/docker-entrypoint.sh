#!/bin/sh
set -e

echo "=== Starting Guess Number Game ===" >&2

if [ "$GZCTF_FLAG" ]; then
    echo "Using GZCTF_FLAG from environment" >&2
elif [ "$FLAG" ]; then
    export GZCTF_FLAG="$FLAG"
    echo "Using FLAG from environment" >&2
else
    export GZCTF_FLAG="sdpcsec{HasH_1sn0t_e1asy[TEAM_HASH]}"
    echo "Using default flag template" >&2
fi

echo "Starting Python server on port 9999..." >&2


cd /home/ctf


exec python server.py
