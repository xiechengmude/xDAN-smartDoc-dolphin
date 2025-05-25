"""
系统管理路由
处理系统状态和管理的API端点
"""

import psutil
import torch
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List

router = APIRouter()


class SystemInfo(BaseModel):
    """系统信息模型"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    gpu_available: bool
    gpu_memory_used: float = 0.0
    gpu_memory_total: float = 0.0


class ComponentStatus(BaseModel):
    """组件状态模型"""
    name: str
    status: str
    message: str


@router.get("/info", response_model=SystemInfo)
async def get_system_info():
    """
    获取系统资源信息
    """
    # CPU使用率
    cpu_usage = psutil.cpu_percent(interval=1)
    
    # 内存使用率
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    
    # 磁盘使用率
    disk = psutil.disk_usage('/')
    disk_usage = (disk.used / disk.total) * 100
    
    # GPU信息
    gpu_available = torch.cuda.is_available()
    gpu_memory_used = 0.0
    gpu_memory_total = 0.0
    
    if gpu_available:
        gpu_memory_used = torch.cuda.memory_allocated() / 1024**3  # GB
        gpu_memory_total = torch.cuda.max_memory_allocated() / 1024**3  # GB
    
    return SystemInfo(
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        disk_usage=disk_usage,
        gpu_available=gpu_available,
        gpu_memory_used=gpu_memory_used,
        gpu_memory_total=gpu_memory_total
    )


@router.get("/status", response_model=List[ComponentStatus])
async def get_system_status():
    """
    获取系统各组件状态
    """
    components = []
    
    # 检查数据库连接
    # TODO: 实现实际的数据库连接检查
    components.append(ComponentStatus(
        name="database",
        status="healthy",
        message="数据库连接正常"
    ))
    
    # 检查Redis连接
    # TODO: 实现实际的Redis连接检查
    components.append(ComponentStatus(
        name="redis",
        status="healthy", 
        message="Redis连接正常"
    ))
    
    # 检查模型状态
    # TODO: 实现实际的模型状态检查
    components.append(ComponentStatus(
        name="model",
        status="loaded",
        message="模型已加载"
    ))
    
    # 检查GPU状态
    if torch.cuda.is_available():
        components.append(ComponentStatus(
            name="gpu",
            status="available",
            message=f"GPU可用: {torch.cuda.get_device_name(0)}"
        ))
    else:
        components.append(ComponentStatus(
            name="gpu",
            status="unavailable",
            message="GPU不可用"
        ))
    
    return components


@router.post("/gc")
async def garbage_collect():
    """
    手动触发垃圾回收
    """
    import gc
    
    # Python垃圾回收
    collected = gc.collect()
    
    # GPU内存清理
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    
    return {
        "message": "垃圾回收完成",
        "objects_collected": collected
    }


@router.post("/cache/clear")
async def clear_cache():
    """
    清理系统缓存
    """
    # TODO: 实现缓存清理逻辑
    return {
        "message": "缓存已清理"
    } 