#!/usr/bin/env python3
"""
SmartDoc Dolphin - 简化版服务器启动脚本
"""

import os
import sys
import asyncio
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import settings
from src.core.logging import setup_logging

def main():
    """启动服务器"""
    print("🚀 Starting SmartDoc Dolphin API Server...")
    print(f"📍 Model Path: {settings.model_path}")
    print(f"🔧 Device: {settings.model_device}")
    print(f"🌐 Server: http://{settings.api_host}:{settings.api_port}")
    print(f"📚 API Docs: http://{settings.api_host}:{settings.api_port}/docs")
    
    # 检查模型路径
    if not os.path.exists(settings.model_path):
        print(f"⚠️  Warning: Model path {settings.model_path} does not exist")
        print("   Please download the Dolphin model first:")
        print("   git clone https://huggingface.co/ByteDance/Dolphin ./hf_model")
    
    # 启动服务器
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers if not settings.api_reload else 1,
        log_level=settings.log_level.lower()
    )

if __name__ == "__main__":
    main() 