#!/bin/bash

# xDAN SmartDoc Dolphin 快速设置脚本
# 使用方法: ./scripts/setup.sh

set -e

echo "🚀 开始设置 xDAN SmartDoc Dolphin 项目..."

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
uv venv xdan-smartdoc-dolphin
source .venv/bin/activate

# 安装依赖
echo "📦 安装项目依赖..."
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

# 数据库配置
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=smartdoc

# Redis配置
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_WORKER_CONCURRENCY=4

# 存储配置
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./storage

# 安全配置
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# 性能配置
MAX_CONCURRENT_TASKS=10
TASK_TIMEOUT=300
MAX_IMAGE_SIZE=52428800

# 日志配置
LOG_LEVEL=INFO

# 监控配置
MONITORING_ENABLED=false
PROMETHEUS_PORT=9090
EOF
    echo "✅ 环境配置文件已创建: .env"
else
    echo "⚠️ 环境配置文件已存在，跳过创建"
fi

# 检查Docker是否安装
if command -v docker &> /dev/null; then
    echo "🐳 检测到Docker，准备启动基础设施..."
    
    # 创建docker-compose.yml
    if [ ! -f docker-compose.yml ]; then
        cat > docker-compose.yml << EOF
version: '3.8'

services:
  mongodb:
    image: mongo:latest
    container_name: smartdoc-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=smartdoc
    restart: unless-stopped

  redis:
    image: redis:latest
    container_name: smartdoc-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

  # 可选: Redis管理界面
  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: smartdoc-redis-commander
    ports:
      - "8081:8081"
    environment:
      - REDIS_HOSTS=local:redis:6379
    depends_on:
      - redis
    restart: unless-stopped

volumes:
  mongodb_data:
  redis_data:
EOF
        echo "✅ Docker Compose配置已创建"
    fi
    
    # 启动基础设施
    echo "🚀 启动MongoDB和Redis..."
    docker-compose up -d mongodb redis
    
    # 等待服务启动
    echo "⏳ 等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        echo "✅ 基础设施启动成功"
    else
        echo "⚠️ 基础设施启动可能有问题，请检查Docker日志"
    fi
else
    echo "⚠️ 未检测到Docker，请手动安装MongoDB和Redis"
    echo "   MongoDB: https://docs.mongodb.com/manual/installation/"
    echo "   Redis: https://redis.io/download"
fi

# 下载模型提示
echo ""
echo "📥 下载Dolphin模型 (可选，但推荐):"
echo "   方法1: git lfs install && git clone https://huggingface.co/ByteDance/Dolphin ./hf_model"
echo "   方法2: huggingface-cli download ByteDance/Dolphin --local-dir ./hf_model"
echo ""

# 创建启动脚本
cat > scripts/start.sh << 'EOF'
#!/bin/bash

# 启动脚本
echo "🚀 启动 SmartDoc Dolphin 服务..."

# 激活虚拟环境
source .venv/bin/activate

# 启动API服务器
echo "📡 启动API服务器..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# 启动Celery Worker (如果需要)
# echo "👷 启动Celery Worker..."
# celery -A src.worker.main worker --loglevel=info &
# WORKER_PID=$!

echo "✅ 服务启动完成!"
echo "   API服务器: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "按Ctrl+C停止服务"

# 等待中断信号
trap 'echo "🛑 停止服务..."; kill $API_PID 2>/dev/null; exit 0' INT
wait
EOF

chmod +x scripts/start.sh

# 创建开发工具脚本
cat > scripts/dev.sh << 'EOF'
#!/bin/bash

# 开发工具脚本
source .venv/bin/activate

case "$1" in
    "format")
        echo "🎨 格式化代码..."
        black src/
        isort src/
        ;;
    "lint")
        echo "🔍 代码检查..."
        ruff check src/
        mypy src/
        ;;
    "test")
        echo "🧪 运行测试..."
        pytest tests/ -v
        ;;
    "coverage")
        echo "📊 测试覆盖率..."
        pytest --cov=src tests/
        ;;
    *)
        echo "用法: $0 {format|lint|test|coverage}"
        exit 1
        ;;
esac
EOF

chmod +x scripts/dev.sh

echo ""
echo "🎉 设置完成!"
echo ""
echo "📋 下一步操作:"
echo "   1. 激活虚拟环境: source .venv/bin/activate"
echo "   2. 下载模型 (可选): git clone https://huggingface.co/ByteDance/Dolphin ./hf_model"
echo "   3. 启动服务: ./scripts/start.sh"
echo "   4. 访问API文档: http://localhost:8000/docs"
echo ""
echo "🛠️ 开发工具:"
echo "   格式化代码: ./scripts/dev.sh format"
echo "   代码检查: ./scripts/dev.sh lint"
echo "   运行测试: ./scripts/dev.sh test"
echo ""
echo "📚 更多信息请查看: README_ARCHITECTURE.md" 