#!/usr/bin/env python3
"""
xDAN-Vision-SmartDoc API Server 启动脚本
基于xDAN 高性能多模态模型xDAN-Vision-SmartDoc的高性能异步智能文档识别系统
"""

import os
import sys
import asyncio
import argparse
import uvicorn
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def setup_environment():
    """设置环境变量"""
    # 设置默认模型路径
    if not os.getenv("MODEL_PATH"):
        os.environ["MODEL_PATH"] = "./hf_model"
    
    # 设置默认设备
    if not os.getenv("DEVICE"):
        os.environ["DEVICE"] = "cuda"
    
    # 设置默认日志级别
    if not os.getenv("LOG_LEVEL"):
        os.environ["LOG_LEVEL"] = "INFO"
    
    # 设置Redis URL
    if not os.getenv("REDIS_URL"):
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"

def check_dependencies():
    """检查依赖是否满足"""
    try:
        import torch
        import transformers
        import fastapi
        import aioredis
        import cv2
        import PIL
        print("✅ All dependencies are available")
        
        # 检查CUDA可用性
        if torch.cuda.is_available():
            print(f"✅ CUDA is available: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠️  CUDA not available, will use CPU")
            
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install torch transformers fastapi[all] aioredis opencv-python pillow")
        sys.exit(1)

def check_model_availability(model_path: str):
    """检查模型是否可用"""
    if not Path(model_path).exists():
        print(f"⚠️  Model not found at {model_path}")
        print("Please download the Dolphin model or set correct MODEL_PATH")
        print("You can set MODEL_PATH environment variable or use --model-path argument")
        return False
    
    print(f"✅ Model found at {model_path}")
    return True

def print_banner(host: str = "localhost", port: int = 8000):
    """打印启动横幅"""
    # 动态生成访问地址
    display_host = "localhost" if host == "0.0.0.0" else host
    web_url = f"http://{display_host}:{port}/web"
    docs_url = f"http://{display_host}:{port}/docs"
    
    print("    ╔══════════════════════════════════════════════════════════════╗")
    print("    ║                  xDAN-Vision-SmartDoc API Server             ║")
    print("    ║                                                              ║")
    print("    ║    🔬 基于xDAN 高性能多模态模型的异步智能文档识别系统         ║")
    print("    ║                                                              ║")
    print("    ║    ✨ 核心功能:                                               ║")
    print("    ║    📝 OCR文本识别  📊 表格解析  🖼️ 图表分析  🧮 公式识别      ║")
    print("    ║                                                              ║")
    print("    ║    🚀 技术特色:                                               ║")
    print("    ║    ⚡ 异步处理  🎨 多格式输出  📊 性能监控  🔧 企业级架构       ║")
    print("    ║                                                              ║")
    print("    ║    🌐 访问方式:                                               ║")
    print(f"    ║    📱 网页版界面: {web_url:<44} ║")
    print(f"    ║    📚 API文档: {docs_url:<47} ║")
    print("    ╚══════════════════════════════════════════════════════════════╝")

async def health_check(host: str, port: int):
    """启动后健康检查"""
    import httpx
    import time
    
    max_retries = 10
    retry_delay = 2
    
    print(f"\n🔍 Checking service health at http://{host}:{port}/health")
    
    async with httpx.AsyncClient() as client:
        for attempt in range(max_retries):
            try:
                response = await client.get(f"http://{host}:{port}/health", timeout=5.0)
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"✅ Service is healthy!")
                    print(f"   Status: {health_data.get('status')}")
                    print(f"   Service: {health_data.get('service_name')}")
                    print(f"   Version: {health_data.get('version')}")
                    
                    components = health_data.get('components', {})
                    print(f"   Components:")
                    for name, status in components.items():
                        print(f"     - {name}: {status}")
                    
                    return True
                else:
                    print(f"⚠️  Health check failed with status {response.status_code}")
            except Exception as e:
                print(f"⚠️  Health check attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
    
    print(f"❌ Service health check failed after {max_retries} attempts")
    return False

def main():
    parser = argparse.ArgumentParser(
        description="xDAN-Vision-SmartDoc API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_xdan_vision_server.py                          # 默认设置启动
  python start_xdan_vision_server.py --port 8001              # 指定端口
  python start_xdan_vision_server.py --model-path ./models    # 指定模型路径
  python start_xdan_vision_server.py --workers 4              # 多进程启动
  python start_xdan_vision_server.py --dev                    # 开发模式
        """
    )
    
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind (default: 8000)"
    )
    parser.add_argument(
        "--model-path", 
        default=None, 
        help="Path to Dolphin model (default: ./hf_model)"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="Number of worker processes (default: 1)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--dev", 
        action="store_true", 
        help="Development mode (enables reload and detailed logging)"
    )
    parser.add_argument(
        "--log-level", 
        choices=["debug", "info", "warning", "error"], 
        default="info", 
        help="Log level (default: info)"
    )
    parser.add_argument(
        "--no-health-check", 
        action="store_true", 
        help="Skip health check after startup"
    )
    
    args = parser.parse_args()
    
    # 打印横幅
    print_banner(args.host, args.port)
    
    # 设置环境
    setup_environment()
    
    # 如果指定了模型路径，更新环境变量
    if args.model_path:
        os.environ["MODEL_PATH"] = args.model_path
    
    # 如果是开发模式，启用重载
    if args.dev:
        args.reload = True
        args.log_level = "debug"
    
    # 检查依赖
    print("\n🔍 Checking system dependencies...")
    check_dependencies()
    
    # 检查模型
    model_path = os.getenv("MODEL_PATH", "./hf_model")
    print(f"\n🔍 Checking model at {model_path}...")
    if not check_model_availability(model_path):
        if not args.dev:  # 开发模式下允许跳过模型检查
            sys.exit(1)
        else:
            print("⚠️  Development mode: continuing without model validation")
    
    # 启动配置
    print(f"\n🚀 Starting xDAN-Vision-SmartDoc API Server...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Workers: {args.workers}")
    print(f"   Model: {model_path}")
    print(f"   Log Level: {args.log_level.upper()}")
    print(f"   Reload: {args.reload}")
    
    # API文档链接
    docs_url = f"http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/docs"
    web_url = f"http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/web"
    print(f"\n🌐 访问方式:")
    print(f"   📱 网页版界面: {web_url}")
    print(f"   📚 API文档: {docs_url}")
    print(f"   🔧 ReDoc文档: {docs_url.replace('/docs', '/redoc')}")
    
    print(f"\n" + "="*60)
    
    try:
        # 启动服务器
        uvicorn.run(
            "src.api.enhanced_main:app",
            host=args.host,
            port=args.port,
            workers=args.workers,
            reload=args.reload,
            log_level=args.log_level,
            access_log=True,
            server_header=False,
            date_header=False
        )
    except KeyboardInterrupt:
        print(f"\n\n👋 xDAN-Vision-SmartDoc API Server stopped by user")
    except Exception as e:
        print(f"\n\n❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 