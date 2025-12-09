#!/bin/bash
# Docker 容器启动脚本
# 处理 onnxruntime 可执行栈问题

# 设置允许栈执行（解决 onnxruntime 在容器环境中的可执行栈问题）
export ALLOW_STACK_EXEC=1

# 执行主程序
exec python main.py "$@"

