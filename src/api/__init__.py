"""
API modules for SmartDoc Dolphin system.
"""

# 主应用导入
from .main import app
from .enhanced_main import app as enhanced_app

# 安全的路由导入
try:
    from .routers import tasks, health, system, document, model
    _routers_available = True
except ImportError:
    # 如果路由模块不可用，创建占位符
    tasks = health = system = document = model = None
    _routers_available = False

__all__ = ["app", "enhanced_app", "tasks", "health", "system", "document", "model"] 