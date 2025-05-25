"""
任务管理路由
处理文档处理任务的API端点
"""

from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

router = APIRouter()

# 内存中存储任务状态（生产环境应使用Redis或数据库）
task_store: Dict[str, dict] = {}


class TaskRequest(BaseModel):
    """任务请求模型"""
    task_type: str
    parameters: dict = {}


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    message: str
    created_at: str


class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str
    status: str
    progress: float = 0.0
    result: Optional[dict] = None
    error: Optional[str] = None


@router.post("/create", response_model=TaskResponse)
async def create_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """
    创建新任务
    支持的任务类型：document_analysis, batch_processing
    """
    task_id = str(uuid4())
    
    # 创建任务记录
    task_record = {
        "task_id": task_id,
        "task_type": request.task_type,
        "status": "pending",
        "progress": 0.0,
        "parameters": request.parameters,
        "result": None,
        "error": None,
        "created_at": "2024-01-01T00:00:00Z"  # TODO: 使用实际时间
    }
    
    task_store[task_id] = task_record
    
    # TODO: 添加到后台任务队列
    # background_tasks.add_task(process_task, task_id)
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "任务已创建，正在处理中",
        "created_at": task_record["created_at"]
    }


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    获取任务状态
    """
    if task_id not in task_store:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = task_store[task_id]
    return TaskStatus(**task)


@router.get("/list", response_model=List[TaskStatus])
async def list_tasks(limit: int = 20, offset: int = 0):
    """
    获取任务列表
    """
    tasks = list(task_store.values())
    total_tasks = len(tasks)
    
    # 分页
    paginated_tasks = tasks[offset:offset + limit]
    
    return [TaskStatus(**task) for task in paginated_tasks]


@router.delete("/{task_id}")
async def cancel_task(task_id: str):
    """
    取消任务
    """
    if task_id not in task_store:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = task_store[task_id]
    if task["status"] in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="任务已完成，无法取消")
    
    task["status"] = "cancelled"
    task_store[task_id] = task
    
    return {"message": "任务已取消"}


# TODO: 实现实际的任务处理逻辑
async def process_task(task_id: str):
    """
    处理任务的后台函数
    """
    if task_id not in task_store:
        return
    
    task = task_store[task_id]
    task["status"] = "processing"
    task["progress"] = 0.5
    
    try:
        # TODO: 实现实际的文档处理逻辑
        # result = await process_document(task["parameters"])
        
        task["status"] = "completed"
        task["progress"] = 1.0
        task["result"] = {"message": "处理完成"}
        
    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)
    
    task_store[task_id] = task 