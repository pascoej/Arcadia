#!/bin/sh

#template from http://stackoverflow.com/questions/696839/how-do-i-write-a-bash-script-to-restart-a-process-if-it-dies
until python3 server.py; do
    echo "Server 'myserver' crashed with exit code $?.  Respawning.." >&2
    sleep 1
done
