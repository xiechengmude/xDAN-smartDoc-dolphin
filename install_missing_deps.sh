#!/bin/bash

echo "🔧 安装缺失的依赖..."
echo "========================"

# 安装 structlog
echo "📦 安装 structlog (结构化日志)..."
pip install "structlog>=23.2.0"

# 验证安装
echo "🔍 验证安装..."
python -c "import structlog; print(f'✅ structlog v{structlog.__version__} 安装成功')"

echo ""
echo "✅ 依赖安装完成！现在可以重新启动服务器："
echo "   python start_xdan_vision_server.py --port 8002" 