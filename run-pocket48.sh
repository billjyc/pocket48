#!/bin/sh
echo "start coolq server"
nohup python3 cool_http_server.py > /dev/null 2&>1

echo "start service"
nohup python3 main.py > /dev/null 2&>1

