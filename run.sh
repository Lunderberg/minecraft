#!/bin/bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while true; do
    $DIR/minecraft_server.py -a $DIR/minecraft_server -j minecraft_server.15w43b.jar
    echo "Restarting server in 15 seconds, Ctrl-C to abort"
    sleep 15
done
