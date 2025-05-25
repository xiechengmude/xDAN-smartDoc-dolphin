#!/usr/bin/env python3
"""
完整的依赖检查脚本
检查所有必需的包和模块导入
"""

import sys
import importlib
from typing import List, Tuple


def check_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """检查单个包是否可用"""
    try:
        module_name = import_name or package_name
        importlib.import_module(module_name)
        return True, f"✅ {package_name}"
    except ImportError as e:
        return False, f"❌ {package_name}: {str(e)}"
    except Exception as e:
        return False, f"⚠️  {package_name}: {str(e)}"


def check_all_dependencies() -> bool:
    """检查所有依赖"""
    print("🔍 检查所有依赖包...")
    print("=" * 50)
    
    # 核心包
    core_packages = [
        ("torch", "torch"),
        ("torchvision", "torchvision"),
        ("transformers", "transformers"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("pydantic-settings", "pydantic_settings"),
        ("aioredis", "aioredis"),
        ("redis", "redis"),
        ("structlog", "structlog"),
        ("psutil", "psutil"),
        ("httpx", "httpx"),
        ("python-multipart", "multipart"),
        ("python-dotenv", "dotenv"),
        ("aiofiles", "aiofiles"),
        ("orjson", "orjson"),
        ("ujson", "ujson"),
        ("itsdangerous", "itsdangerous"),
    ]
    
    # 图像处理包
    image_packages = [
        ("pillow", "PIL"),
        ("opencv-python", "cv2"),
        ("albumentations", "albumentations"),
        ("numpy", "numpy"),
    ]
    
    # 配置和工具包
    util_packages = [
        ("omegaconf", "omegaconf"),
        ("accelerate", "accelerate"),
    ]
    
    all_packages = core_packages + image_packages + util_packages
    
    failed_packages = []
    
    print("🔧 核心依赖:")
    for package_name, import_name in core_packages:
        success, message = check_package(package_name, import_name)
        print(f"  {message}")
        if not success:
            failed_packages.append(package_name)
    
    print("\n🖼️ 图像处理依赖:")
    for package_name, import_name in image_packages:
        success, message = check_package(package_name, import_name)
        print(f"  {message}")
        if not success:
            failed_packages.append(package_name)
    
    print("\n⚙️ 工具依赖:")
    for package_name, import_name in util_packages:
        success, message = check_package(package_name, import_name)
        print(f"  {message}")
        if not success:
            failed_packages.append(package_name)
    
    print("\n" + "=" * 50)
    
    if not failed_packages:
        print("🎉 所有依赖检查通过！")
        return True
    else:
        print(f"❌ 以下包缺失或有问题：")
        for pkg in failed_packages:
            print(f"  - {pkg}")
        
        print(f"\n📦 安装缺失的包：")
        print(f"  pip install {' '.join(failed_packages)}")
        print(f"或运行：")
        print(f"  pip install -r requirements.txt")
        
        return False


def check_project_modules():
    """检查项目内部模块"""
    print("\n🔍 检查项目模块...")
    print("=" * 50)
    
    # 添加项目根目录到路径
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    project_modules = [
        ("src.api.routers.health", "健康检查路由"),
        ("src.api.routers.document", "文档处理路由"),
        ("src.api.routers.model", "模型管理路由"),
        ("src.api.routers.tasks", "任务管理路由"),
        ("src.api.routers.system", "系统管理路由"),
        ("src.core.config", "配置模块"),
        ("src.core.logging", "日志模块"),
    ]
    
    failed_modules = []
    
    for module_name, description in project_modules:
        try:
            importlib.import_module(module_name)
            print(f"  ✅ {description} ({module_name})")
        except ImportError as e:
            print(f"  ❌ {description} ({module_name}): {str(e)}")
            failed_modules.append(module_name)
        except Exception as e:
            print(f"  ⚠️  {description} ({module_name}): {str(e)}")
            failed_modules.append(module_name)
    
    return len(failed_modules) == 0


def main():
    """主函数"""
    print("🔧 xDAN-SmartDoc-Dolphin 依赖检查工具")
    print("=" * 60)
    
    # 检查Python版本
    print(f"🐍 Python版本: {sys.version}")
    
    # 检查外部依赖
    deps_ok = check_all_dependencies()
    
    # 检查项目模块
    modules_ok = check_project_modules()
    
    print("\n" + "=" * 60)
    
    if deps_ok and modules_ok:
        print("🎉 所有检查通过！服务器可以启动")
        print("\n🚀 启动命令:")
        print("  python start_xdan_vision_server.py --port 8002")
    else:
        print("❌ 存在问题，请先解决依赖问题")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 