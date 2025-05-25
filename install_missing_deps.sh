#!/bin/bash

echo "🔧 检查并安装缺失的依赖..."
echo "======================================"

# 定义需要安装的包列表
REQUIRED_PACKAGES=(
    "structlog>=23.2.0"
    "psutil>=5.9.0"
)

# 检查Python是否可用
if ! command -v python &> /dev/null; then
    echo "❌ Python 未找到，请先安装Python"
    exit 1
fi

echo "🔍 检查当前Python环境..."
python --version

# 安装每个缺失的包
for package in "${REQUIRED_PACKAGES[@]}"; do
    package_name=$(echo $package | cut -d'>' -f1 | cut -d'=' -f1)
    echo ""
    echo "📦 检查 $package_name..."
    
    if python -c "import $package_name" 2>/dev/null; then
        echo "✅ $package_name 已安装"
    else
        echo "📥 安装 $package..."
        pip install "$package"
        
        # 验证安装
        if python -c "import $package_name" 2>/dev/null; then
            echo "✅ $package_name 安装成功"
        else
            echo "❌ $package_name 安装失败"
        fi
    fi
done

echo ""
echo "🔍 最终验证所有依赖..."

# 验证所有关键依赖
CRITICAL_PACKAGES=(
    "torch"
    "transformers" 
    "fastapi"
    "aioredis"
    "structlog"
    "psutil"
    "pydantic_settings"
)

all_good=true
for package in "${CRITICAL_PACKAGES[@]}"; do
    if python -c "import $package" 2>/dev/null; then
        echo "✅ $package"
    else
        echo "❌ $package 缺失"
        all_good=false
    fi
done

echo ""
if [ "$all_good" = true ]; then
    echo "🎉 所有依赖检查通过！"
    echo ""
    echo "现在可以启动服务器："
    echo "   python start_xdan_vision_server.py --port 8002"
else
    echo "⚠️  仍有依赖缺失，请手动安装："
    echo "   pip install -r requirements.txt"
fi 