"""
简化版Redis队列服务 - 用于异步任务处理
"""

import asyncio
import json
import uuid
from typing import Any, Dict, Optional
from datetime import datetime

import aioredis

from ..core.config import settings
from ..core.logging import worker_logger


class SimpleQueue:
    """简化版Redis队列"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self.redis = None
        self.task_queue = "smartdoc:tasks"
        self.result_key_prefix = "smartdoc:result:"
        self.status_key_prefix = "smartdoc:status:"
        
    async def connect(self):
        """连接Redis"""
        try:
            self.redis = aioredis.from_url(self.redis_url)
            await self.redis.ping()
            worker_logger.info("Redis queue connected successfully")
        except Exception as e:
            worker_logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.redis:
            await self.redis.close()
    
    async def add_task(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """添加任务到队列"""
        if not self.redis:
            await self.connect()
        
        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "task_type": task_type,
            "data": task_data,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        
        # 添加任务到队列
        await self.redis.lpush(self.task_queue, json.dumps(task))
        
        # 设置任务状态
        await self.redis.setex(
            f"{self.status_key_prefix}{task_id}",
            3600,  # 1小时过期
            json.dumps({"status": "pending", "created_at": task["created_at"]})
        )
        
        worker_logger.info("Task added to queue", task_id=task_id, task_type=task_type)
        return task_id
    
    async def get_task(self, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """从队列获取任务"""
        if not self.redis:
            await self.connect()
        
        try:
            # 阻塞式获取任务
            result = await self.redis.brpop(self.task_queue, timeout=timeout)
            if result:
                task_data = json.loads(result[1])
                return task_data
            return None
        except Exception as e:
            worker_logger.error("Failed to get task from queue", error=str(e))
            return None
    
    async def update_task_status(self, task_id: str, status: str, progress: float = 0.0, result: Dict = None):
        """更新任务状态"""
        if not self.redis:
            await self.connect()
        
        status_data = {
            "status": status,
            "progress": progress,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if result:
            status_data["result"] = result
        
        await self.redis.setex(
            f"{self.status_key_prefix}{task_id}",
            3600,  # 1小时过期
            json.dumps(status_data)
        )
        
        # 如果任务完成，保存结果
        if status == "completed" and result:
            await self.redis.setex(
                f"{self.result_key_prefix}{task_id}",
                3600,  # 1小时过期
                json.dumps(result)
            )
        
        worker_logger.info("Task status updated", task_id=task_id, status=status)
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if not self.redis:
            await self.connect()
        
        status_data = await self.redis.get(f"{self.status_key_prefix}{task_id}")
        if status_data:
            return json.loads(status_data)
        return None
    
    async def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务结果"""
        if not self.redis:
            await self.connect()
        
        result_data = await self.redis.get(f"{self.result_key_prefix}{task_id}")
        if result_data:
            return json.loads(result_data)
        return None


class QueueWorker:
    """队列Worker"""
    
    def __init__(self, queue: SimpleQueue):
        self.queue = queue
        self.running = False
        self.processor = None
    
    def set_processor(self, processor):
        """设置任务处理器"""
        self.processor = processor
    
    async def start(self):
        """启动Worker"""
        self.running = True
        worker_logger.info("Queue worker started")
        
        while self.running:
            try:
                task = await self.queue.get_task()
                if task:
                    await self._process_task(task)
                else:
                    # 没有任务时短暂休息
                    await asyncio.sleep(1)
            except Exception as e:
                worker_logger.error("Worker error", error=str(e))
                await asyncio.sleep(5)  # 错误时等待更长时间
    
    async def stop(self):
        """停止Worker"""
        self.running = False
        worker_logger.info("Queue worker stopped")
    
    async def _process_task(self, task: Dict[str, Any]):
        """处理单个任务"""
        task_id = task["task_id"]
        task_type = task["task_type"]
        
        try:
            # 更新状态为处理中
            await self.queue.update_task_status(task_id, "processing", 0.0)
            
            worker_logger.info("Processing task", task_id=task_id, task_type=task_type)
            
            # 调用处理器
            if self.processor:
                result = await self.processor(task)
                await self.queue.update_task_status(task_id, "completed", 100.0, result)
                worker_logger.info("Task completed", task_id=task_id)
            else:
                await self.queue.update_task_status(task_id, "failed", 0.0, {"error": "No processor set"})
                
        except Exception as e:
            error_msg = str(e)
            await self.queue.update_task_status(task_id, "failed", 0.0, {"error": error_msg})
            worker_logger.error("Task failed", task_id=task_id, error=error_msg) 