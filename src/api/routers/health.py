"""
健康检查路由
提供API服务的健康状态检查
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    version: str = "1.0.0"
    message: str


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    健康检查端点
    返回API服务的运行状态
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "message": "SmartDoc API服务运行正常"
    } 