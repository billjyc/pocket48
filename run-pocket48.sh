#!/bin/sh
echo stop application
PID=$(ps -ef | grep 'pocket48_handler' | grep -v grep | awk '{print $2}')
if [-z PID]
then
    echo Application is already stopped
else
    echo kill $PID
    kill $PID
fi

echo start application
cd /home/pocket48
git pull

nohup python pocket48_handler.py > pocket48.log 2>&1 &
