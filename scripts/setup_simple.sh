#!/bin/bash

# xDAN SmartDoc Dolphin 简化版快速设置脚本

set -e

echo "🚀 设置 SmartDoc Dolphin 简化版..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ 错误: 需要Python 3.8或更高版本，当前版本: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 检查uv是否安装
if ! command -v uv &> /dev/null; then
    echo "📦 安装uv包管理器..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

echo "✅ uv已安装"

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
if [ ! -d ".venv" ]; then
    uv venv xdan-smartdoc-dolphin
fi

# 激活虚拟环境并安装依赖
echo "📦 安装项目依赖..."
source .venv/bin/activate
uv pip install -e .

# 创建必要的目录
echo "📁 创建项目目录..."
mkdir -p storage/uploads
mkdir -p storage/results
mkdir -p logs
mkdir -p hf_model

# 创建环境配置文件
if [ ! -f .env ]; then
    echo "⚙️ 创建环境配置文件..."
    cat > .env << EOF
# SmartDoc Dolphin - 环境配置

# 应用配置
APP_NAME=SmartDoc Dolphin
ENVIRONMENT=development
DEBUG=true

# 模型配置
MODEL_PATH=./hf_model
MODEL_DEVICE=cuda
MODEL_PRECISION=half
MAX_BATCH_SIZE=16
MAX_SEQUENCE_LENGTH=4096

# API服务器配置
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
API_RELOAD=true

# Redis配置（可选，用于结果缓存）
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# 性能配置
MAX_CONCURRENT_TASKS=10
TASK_TIMEOUT=300
MAX_IMAGE_SIZE=52428800

# 日志配置
LOG_LEVEL=INFO

# 安全配置
SECRET_KEY=your-secret-key-change-in-production
EOF
    echo "✅ 环境配置文件已创建: .env"
else
    echo "⚠️ 环境配置文件已存在，跳过创建"
fi

# 创建启动脚本
chmod +x start_server.py
chmod +x test_client.py

echo ""
echo "🎉 设置完成!"
echo ""
echo "📋 下一步操作:"
echo "   1. 激活虚拟环境: source .venv/bin/activate"
echo "   2. 下载模型: git clone https://huggingface.co/ByteDance/Dolphin ./hf_model"
echo "   3. 启动Redis (可选): docker run -d --name smartdoc-redis -p 6379:6379 redis:latest"
echo "   4. 启动服务: python start_server.py"
echo "   5. 测试API: python test_client.py"
echo "   6. 访问文档: http://localhost:8000/docs"
echo ""
echo "📚 更多信息请查看: README_SIMPLE.md" 