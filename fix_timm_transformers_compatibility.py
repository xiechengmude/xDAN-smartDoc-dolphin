#!/usr/bin/env python3
"""
修复 transformers 与 timm 1.0.15 兼容性问题的脚本
解决 "cannot import name 'ImageNetInfo' from 'timm.data'" 错误
"""
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Tuple


def run_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """运行命令并返回成功状态和输出"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} 完成")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败:")
        print(f"   错误: {e.stderr}")
        return False, e.stderr


def check_versions():
    """检查当前版本"""
    print("🔍 检查当前包版本...")
    
    packages = ['torch', 'torchvision', 'transformers', 'timm', 'aioredis']
    for package in packages:
        try:
            result = subprocess.run([sys.executable, '-c', f'import {package}; print(f"{package}=={{getattr({package}, "__version__", "未知")}}")'], 
                                  capture_output=True, text=True, check=True)
            print(f"   {result.stdout.strip()}")
        except:
            print(f"   {package}=未安装")


def fix_timm_compatibility():
    """修复 timm 兼容性问题"""
    print("\n🔧 修复 timm 与 transformers 兼容性...")
    
    # 选项1：降级到兼容版本
    print("\n方案1: 降级到兼容版本")
    commands_v1 = [
        (["pip", "uninstall", "timm", "-y"], "卸载当前 timm"),
        (["pip", "install", "timm==0.9.16"], "安装兼容的 timm 版本"),
        (["pip", "install", "transformers>=4.30.0,<4.40.0"], "安装兼容的 transformers"),
    ]
    
    # 选项2：使用最新版本但打补丁
    print("\n方案2: 使用最新版本并修复兼容性")
    commands_v2 = [
        (["pip", "install", "timm==1.0.15", "--force-reinstall"], "重新安装最新 timm"),
        (["pip", "install", "transformers>=4.40.0", "--upgrade"], "升级 transformers"),
    ]
    
    # 让用户选择方案
    print("\n请选择修复方案:")
    print("1. 使用稳定兼容版本 (timm==0.9.16 + transformers<4.40)")
    print("2. 使用最新版本并应用兼容性补丁 (timm==1.0.15 + transformers>=4.40)")
    
    choice = input("请输入选择 (1 或 2, 默认为 1): ").strip() or "1"
    
    if choice == "1":
        print("\n🔄 执行方案1: 稳定版本组合")
        commands = commands_v1
    else:
        print("\n🔄 执行方案2: 最新版本 + 补丁")
        commands = commands_v2
    
    success_count = 0
    for cmd, desc in commands:
        success, output = run_command(cmd, desc)
        if success:
            success_count += 1
    
    return success_count == len(commands), choice


def create_compatibility_patch():
    """创建兼容性补丁"""
    patch_content = '''"""
兼容性补丁：为 timm 1.0.15 添加 ImageNetInfo 支持
"""
import sys
from types import ModuleType

# 创建虚拟的 ImageNetInfo 类
class ImageNetInfo:
    """兼容性类，用于替代已移除的 timm.data.ImageNetInfo"""
    
    def __init__(self, num_classes=1000):
        self.num_classes = num_classes
        self.label_names = [f"class_{i}" for i in range(num_classes)]
    
    @property
    def synsets(self):
        return self.label_names


def infer_imagenet_subset(*args, **kwargs):
    """兼容性函数，用于替代已移除的 infer_imagenet_subset"""
    return ImageNetInfo()


# 动态注入到 timm.data 模块
try:
    import timm.data as timm_data
    if not hasattr(timm_data, 'ImageNetInfo'):
        timm_data.ImageNetInfo = ImageNetInfo
    if not hasattr(timm_data, 'infer_imagenet_subset'):
        timm_data.infer_imagenet_subset = infer_imagenet_subset
    print("✅ timm 兼容性补丁已应用")
except ImportError:
    print("⚠️ timm 未安装")
'''
    
    # 创建补丁文件
    patch_file = Path("timm_compatibility_patch.py")
    with open(patch_file, 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print(f"✅ 兼容性补丁已创建: {patch_file}")
    
    # 创建使用说明
    usage_content = '''"""
使用 timm 兼容性补丁的方法:

在您的代码开头添加以下导入：

```python
# 在导入 transformers 之前先应用补丁
import timm_compatibility_patch

# 然后正常导入其他库
from transformers import AutoProcessor, VisionEncoderDecoderModel
import timm
```

或者在运行 demo 脚本之前先运行：
python -c "import timm_compatibility_patch"
"""'''
    
    usage_file = Path("TIMM_PATCH_USAGE.md")
    with open(usage_file, 'w', encoding='utf-8') as f:
        f.write(usage_content)
    
    print(f"✅ 使用说明已创建: {usage_file}")


def update_requirements():
    """更新 requirements.txt 为兼容版本"""
    new_requirements = '''albumentations==1.4.0
numpy==1.24.4
omegaconf==2.3.0
opencv-python==4.11.0.86
opencv-python-headless==4.5.5.64
pillow==9.3.0
# 兼容版本组合方案1 (推荐)
timm==0.9.16
torch==2.6.0
torchvision==0.21.0
transformers>=4.30.0,<4.40.0
accelerate==1.7.0
# 或者使用最新版本组合方案2
# timm==1.0.15
# transformers>=4.40.0
# Web framework and async dependencies
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
aiofiles>=23.2.0
# Redis client - Python 3.11 兼容版本
aioredis>=2.0.6
redis>=5.0.0
# Additional web dependencies
python-multipart>=0.0.6
python-dotenv>=1.0.0
# HTTP client
httpx>=0.25.0
# Validation
pydantic>=2.5.0
pydantic-extra-types>=2.10.0
pydantic-settings>=2.9.0
# JSON processing
orjson>=3.10.0
ujson>=5.10.0
# Security
itsdangerous>=2.2.0'''
    
    # 备份原文件
    if Path("requirements.txt").exists():
        subprocess.run(["cp", "requirements.txt", "requirements.txt.backup"], check=False)
        print("✅ 原 requirements.txt 已备份为 requirements.txt.backup")
    
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(new_requirements)
    
    print("✅ requirements.txt 已更新为兼容版本")


def main():
    print("🔧 timm 与 transformers 兼容性修复工具")
    print("=" * 50)
    
    # 检查当前版本
    check_versions()
    
    # 修复兼容性
    success, choice = fix_timm_compatibility()
    
    if success:
        print(f"\n✅ 兼容性修复完成！")
        
        # 如果选择了方案2，创建补丁
        if choice == "2":
            create_compatibility_patch()
            print("\n📋 使用方案2时，请在代码中导入补丁:")
            print("   import timm_compatibility_patch")
        
        # 更新 requirements.txt
        update_requirements()
        
        print(f"\n🚀 现在可以运行服务器:")
        print("   python start_xdan_vision_server.py --port 8001")
        
        # 验证修复
        print(f"\n🔍 验证修复结果...")
        try:
            if choice == "2":
                # 方案2需要先导入补丁
                subprocess.run([sys.executable, "-c", "import timm_compatibility_patch; from transformers.models.timm_wrapper.configuration_timm_wrapper import *; print('✅ 兼容性验证成功')"], check=True)
            else:
                # 方案1直接验证
                subprocess.run([sys.executable, "-c", "from transformers.models.timm_wrapper.configuration_timm_wrapper import *; print('✅ 兼容性验证成功')"], check=True)
        except subprocess.CalledProcessError:
            print("⚠️ 兼容性验证失败，可能需要重启 Python 环境")
    else:
        print(f"\n❌ 修复失败，请手动执行以下命令:")
        print("   pip uninstall timm transformers -y")
        print("   pip install timm==0.9.16 'transformers>=4.30.0,<4.40.0'")


if __name__ == "__main__":
    main() 