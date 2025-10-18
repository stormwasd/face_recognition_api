#!/bin/bash

# 人脸识别API启动脚本

echo "================================================"
echo "      人脸识别API服务启动脚本"
echo "================================================"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  警告: 未检测到虚拟环境"
    echo "建议创建虚拟环境: python3 -m venv venv && source venv/bin/activate"
    read -p "是否继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查依赖是否安装
echo "📦 检查依赖..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  依赖未安装，正在安装..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi

# 创建必要的目录
mkdir -p logs

# 设置环境变量
export PYTHONUNBUFFERED=1

# 启动服务
echo "🚀 启动服务..."
echo "================================================"

# 使用uvicorn启动，支持热重载（开发模式）
if [ "$1" = "dev" ]; then
    echo "🔧 开发模式 (支持热重载)"
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    # 生产模式
    echo "🏭 生产模式"
    python main.py
fi

