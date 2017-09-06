#!/bin/sh
echo stop application
qq stop

# git pull

echo start qqbot
# 将用户名换成在conf中填写的用户名
qqbot -u 'fxftest'
