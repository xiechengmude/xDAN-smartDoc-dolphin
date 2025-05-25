"""
API路由模块
包含所有API端点的路由处理器
"""

from fastapi import APIRouter

# 创建主路由器
api_router = APIRouter()

# 导入所有子路由器
from .document import router as document_router
from .health import router as health_router
from .model import router as model_router
from .tasks import router as tasks_router
from .system import router as system_router

# 注册子路由器
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(document_router, prefix="/document", tags=["document"])
api_router.include_router(model_router, prefix="/model", tags=["model"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(system_router, prefix="/system", tags=["system"])

# 导出路由器以供其他模块使用
health = health_router
document = document_router
model = model_router
tasks = tasks_router
system = system_router 