#!/usr/bin/env python3
"""
Fix aioredis dependency issue for Python 3.11 compatibility
"""
import subprocess
import sys
from typing import List


def run_command(cmd: List[str], description: str) -> bool:
    """Run a command and return success status"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False


def main():
    print("🔧 Fixing aioredis dependency for Python 3.11 compatibility...")
    print("=" * 60)
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python 3.8+ is required!")
        sys.exit(1)
    
    # Commands to fix dependencies
    commands = [
        (["pip", "uninstall", "aioredis", "-y"], "Uninstalling incompatible aioredis 2.0.1"),
        (["pip", "install", "aioredis>=2.0.6"], "Installing compatible aioredis version"),
        (["pip", "install", "-r", "requirements.txt"], "Installing/updating other dependencies"),
    ]
    
    success_count = 0
    for cmd, desc in commands:
        if run_command(cmd, desc):
            success_count += 1
        else:
            print(f"\n⚠️  Warning: {desc} failed, but continuing...")
    
    print("\n" + "=" * 60)
    if success_count == len(commands):
        print("✅ All dependencies fixed successfully!")
        print("\n🚀 You can now run the server:")
        print("   python start_xdan_vision_server.py --port 8001")
    else:
        print(f"⚠️  {success_count}/{len(commands)} operations completed successfully")
        print("   Please check the error messages above and try manual installation if needed.")
        print("\n💡 Manual fix commands:")
        print("   pip uninstall aioredis -y")
        print("   pip install 'aioredis>=2.0.6'")


if __name__ == "__main__":
    main() 