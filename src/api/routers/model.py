"""
模型管理路由
处理模型相关的API端点
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ModelInfo(BaseModel):
    """模型信息响应模型"""
    name: str
    version: str
    status: str
    device: str


@router.get("/info", response_model=ModelInfo)
async def get_model_info():
    """
    获取模型信息
    返回当前加载的模型状态和信息
    """
    return {
        "name": "SmartDoc Dolphin",
        "version": "1.0.0",
        "status": "loaded",
        "device": "cuda" if True else "cpu"  # TODO: 实现实际设备检测
    } 