#!/bin/bash

# 人脸识别API停止脚本

echo "================================================"
echo "      停止人脸识别API服务"
echo "================================================"

# 查找运行中的进程
PID=$(ps aux | grep "main:app\|python main.py" | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
    echo "⚠️  未找到运行中的服务"
    exit 0
fi

echo "找到进程: $PID"
echo "正在停止服务..."

# 发送终止信号
kill $PID

# 等待进程结束
sleep 2

# 检查是否还在运行
if ps -p $PID > /dev/null; then
    echo "⚠️  进程未响应，强制终止..."
    kill -9 $PID
fi

echo "✅ 服务已停止"

