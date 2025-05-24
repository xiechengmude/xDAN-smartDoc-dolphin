"""
SmartDoc Dolphin - 简化版异步API服务
基于demo_page_hf.py和demo_element_hf.py改造
"""

import asyncio
import io
import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import aioredis
import cv2
import torch
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
from transformers import AutoProcessor, VisionEncoderDecoderModel

from ..core.config import settings
from ..core.logging import api_logger, setup_logging
from ..utils.image_utils import ImageDimensions, prepare_image, process_coordinates
from ..utils.parsing_utils import generate_json_output, generate_markdown, parse_layout_string
from ..utils.file_utils import calculate_file_hash_async, validate_image_file


class AsyncDolphinEngine:
    """简化版异步Dolphin引擎，基于demo代码改造"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model_loaded = False
        self._lock = asyncio.Lock()
        
    async def load_model(self):
        """异步加载模型"""
        if self._model_loaded:
            return
            
        async with self._lock:
            if self._model_loaded:
                return
                
            api_logger.info("Loading Dolphin model", path=settings.model_path)
            
            # 在线程池中加载模型，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model_sync)
            
            self._model_loaded = True
            api_logger.info("Model loaded successfully")
    
    def _load_model_sync(self):
        """同步模型加载"""
        self.processor = AutoProcessor.from_pretrained(settings.model_path)
        self.model = VisionEncoderDecoderModel.from_pretrained(settings.model_path)
        self.model.eval()
        self.model.to(self.device)
        
        if settings.model_precision == "half" and self.device != "cpu":
            self.model = self.model.half()
            
        self.tokenizer = self.processor.tokenizer
    
    async def chat(self, prompt: str, image: Image.Image) -> str:
        """单图像处理 - 基于demo代码"""
        if not self._model_loaded:
            await self.load_model()
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._chat_sync, prompt, image)
    
    async def chat_batch(self, prompts: List[str], images: List[Image.Image]) -> List[str]:
        """批量图像处理 - 基于demo代码优化"""
        if not self._model_loaded:
            await self.load_model()
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._chat_batch_sync, prompts, images)
    
    def _chat_sync(self, prompt: str, image: Image.Image) -> str:
        """同步单图像处理"""
        # 准备图像
        pixel_values = self.processor(image, return_tensors="pt").pixel_values
        if settings.model_precision == "half" and self.device != "cpu":
            pixel_values = pixel_values.half()
        pixel_values = pixel_values.to(self.device)
        
        # 准备提示
        formatted_prompt = f"<s>{prompt} <Answer/>"
        prompt_ids = self.tokenizer(
            formatted_prompt, 
            add_special_tokens=False, 
            return_tensors="pt"
        ).input_ids.to(self.device)
        
        # 生成
        with torch.inference_mode():
            outputs = self.model.generate(
                pixel_values=pixel_values,
                decoder_input_ids=prompt_ids,
                min_length=1,
                max_length=settings.max_sequence_length,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                use_cache=True,
                bad_words_ids=[[self.tokenizer.unk_token_id]],
                do_sample=False,
                num_beams=1,
                repetition_penalty=1.1
            )
        
        # 解码结果
        sequence = self.tokenizer.batch_decode(outputs.sequences, skip_special_tokens=False)[0]
        result = sequence.replace(formatted_prompt, "").replace("<pad>", "").replace("</s>", "").strip()
        
        return result
    
    def _chat_batch_sync(self, prompts: List[str], images: List[Image.Image]) -> List[str]:
        """同步批量图像处理 - 基于demo_page_hf.py的批处理逻辑"""
        # 准备图像
        batch_inputs = self.processor(images, return_tensors="pt", padding=True)
        batch_pixel_values = batch_inputs.pixel_values
        
        if settings.model_precision == "half" and self.device != "cpu":
            batch_pixel_values = batch_pixel_values.half()
        batch_pixel_values = batch_pixel_values.to(self.device)
        
        # 准备提示
        formatted_prompts = [f"<s>{p} <Answer/>" for p in prompts]
        batch_prompt_inputs = self.tokenizer(
            formatted_prompts,
            add_special_tokens=False,
            return_tensors="pt",
            padding=True
        )
        
        batch_prompt_ids = batch_prompt_inputs.input_ids.to(self.device)
        batch_attention_mask = batch_prompt_inputs.attention_mask.to(self.device)
        
        # 批量生成
        with torch.inference_mode():
            outputs = self.model.generate(
                pixel_values=batch_pixel_values,
                decoder_input_ids=batch_prompt_ids,
                decoder_attention_mask=batch_attention_mask,
                min_length=1,
                max_length=settings.max_sequence_length,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                use_cache=True,
                bad_words_ids=[[self.tokenizer.unk_token_id]],
                do_sample=False,
                num_beams=1,
                repetition_penalty=1.1
            )
        
        # 解码结果
        sequences = self.tokenizer.batch_decode(outputs.sequences, skip_special_tokens=False)
        results = []
        for i, sequence in enumerate(sequences):
            cleaned = sequence.replace(formatted_prompts[i], "").replace("<pad>", "").replace("</s>", "").strip()
            results.append(cleaned)
            
        return results
    
    async def process_page(self, image: Image.Image, max_batch_size: int = 16) -> Dict:
        """页面级文档处理 - 基于demo_page_hf.py"""
        start_time = time.time()
        
        # 阶段1: 页面级布局解析
        layout_output = await self.chat("Parse the reading order of this document.", image)
        
        # 阶段2: 元素级处理
        loop = asyncio.get_event_loop()
        padded_image, dims = await loop.run_in_executor(None, prepare_image, image)
        
        elements = await self._process_elements(layout_output, padded_image, dims, max_batch_size)
        
        processing_time = time.time() - start_time
        
        # 生成结果
        result = {
            "elements": elements,
            "markdown": generate_markdown(elements),
            "json_data": generate_json_output(elements, processing_time),
            "processing_time": processing_time,
            "total_elements": len(elements)
        }
        
        return result
    
    async def _process_elements(self, layout_results: str, padded_image, dims: ImageDimensions, max_batch_size: int):
        """处理文档元素 - 基于demo_page_hf.py的process_elements"""
        loop = asyncio.get_event_loop()
        layout_data = await loop.run_in_executor(None, parse_layout_string, layout_results)
        
        # 收集待处理元素
        text_elements = []
        table_elements = []
        figure_elements = []
        reading_order = 0
        
        for bbox, label in layout_data:
            try:
                # 处理坐标
                coords_result = await loop.run_in_executor(
                    None, process_coordinates, bbox, padded_image, dims, None
                )
                x1, y1, x2, y2, orig_x1, orig_y1, orig_x2, orig_y2, _ = coords_result
                
                # 裁剪元素
                cropped = padded_image[y1:y2, x1:x2]
                if cropped.size > 0:
                    if label == "fig":
                        figure_elements.append({
                            "type": "figure",
                            "bbox": [orig_x1, orig_y1, orig_x2, orig_y2],
                            "text": "",
                            "reading_order": reading_order
                        })
                    else:
                        pil_crop = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
                        element_info = {
                            "crop": pil_crop,
                            "bbox": [orig_x1, orig_y1, orig_x2, orig_y2],
                            "reading_order": reading_order,
                            "type": "table" if label == "tab" else "text"
                        }
                        
                        if label == "tab":
                            table_elements.append(element_info)
                        else:
                            text_elements.append(element_info)
                
                reading_order += 1
                
            except Exception as e:
                api_logger.warning("Failed to process element", label=label, error=str(e))
                continue
        
        # 批量处理元素
        all_elements = figure_elements.copy()
        
        if text_elements:
            text_results = await self._process_element_batch(
                text_elements, "Read text in the image.", max_batch_size
            )
            all_elements.extend(text_results)
        
        if table_elements:
            table_results = await self._process_element_batch(
                table_elements, "Parse the table in the image.", max_batch_size
            )
            all_elements.extend(table_results)
        
        # 按阅读顺序排序
        all_elements.sort(key=lambda x: x["reading_order"])
        
        return all_elements
    
    async def _process_element_batch(self, elements: List[Dict], prompt: str, max_batch_size: int):
        """批量处理元素 - 基于demo的batch处理"""
        results = []
        
        for i in range(0, len(elements), max_batch_size):
            batch = elements[i:i + max_batch_size]
            crops = [elem["crop"] for elem in batch]
            prompts = [prompt] * len(crops)
            
            try:
                texts = await self.chat_batch(prompts, crops)
                
                for elem, text in zip(batch, texts):
                    results.append({
                        "type": elem["type"],
                        "bbox": elem["bbox"],
                        "text": text.strip(),
                        "reading_order": elem["reading_order"]
                    })
                    
            except Exception as e:
                api_logger.error("Batch processing failed", error=str(e))
                # 添加空结果
                for elem in batch:
                    results.append({
                        "type": elem["type"],
                        "bbox": elem["bbox"],
                        "text": "",
                        "reading_order": elem["reading_order"]
                    })
        
        return results


# 全局变量
dolphin_engine = None
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global dolphin_engine, redis_client
    
    # 启动时初始化
    setup_logging()
    api_logger.info("Starting SmartDoc Dolphin API")
    
    # 初始化引擎
    dolphin_engine = AsyncDolphinEngine()
    
    # 初始化Redis
    try:
        redis_client = aioredis.from_url(settings.redis_url)
        await redis_client.ping()
        api_logger.info("Redis connected successfully")
    except Exception as e:
        api_logger.warning("Redis connection failed", error=str(e))
        redis_client = None
    
    yield
    
    # 关闭时清理
    if redis_client:
        await redis_client.close()
    api_logger.info("SmartDoc Dolphin API stopped")


# 创建FastAPI应用
app = FastAPI(
    title="SmartDoc Dolphin API",
    description="高性能异步智能文档识别系统",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "SmartDoc Dolphin API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "model": "loaded" if dolphin_engine and dolphin_engine._model_loaded else "not_loaded",
            "redis": "connected" if redis_client else "disconnected"
        }
    }
    return health_status


@app.post("/api/v1/process/page")
async def process_page(
    file: UploadFile = File(...),
    max_batch_size: int = Form(16)
):
    """
    页面级文档处理API
    基于demo_page_hf.py的process_page函数
    """
    if not dolphin_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    # 验证文件
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # 读取图像
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 处理文档
        start_time = time.time()
        result = await dolphin_engine.process_page(image, max_batch_size)
        
        # 添加任务信息
        response = {
            "task_id": task_id,
            "filename": file.filename,
            "status": "completed",
            "result": result,
            "created_at": start_time,
            "completed_at": time.time()
        }
        
        # 缓存结果到Redis（如果可用）
        if redis_client:
            try:
                await redis_client.setex(
                    f"result:{task_id}", 
                    3600,  # 1小时过期
                    json.dumps(response, default=str)
                )
            except Exception as e:
                api_logger.warning("Failed to cache result", error=str(e))
        
        api_logger.info("Page processed successfully", 
                       task_id=task_id, 
                       elements=result["total_elements"],
                       processing_time=result["processing_time"])
        
        return response
        
    except Exception as e:
        api_logger.error("Page processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/api/v1/process/element")
async def process_element(
    file: UploadFile = File(...),
    element_type: str = Form("text")
):
    """
    元素级处理API
    基于demo_element_hf.py的process_element函数
    """
    if not dolphin_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    if element_type not in ["text", "table", "formula"]:
        raise HTTPException(status_code=400, detail="Invalid element_type")
    
    try:
        # 读取图像
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # 选择提示
        if element_type == "table":
            prompt = "Parse the table in the image."
        elif element_type == "formula":
            prompt = "Read text in the image."
        else:
            prompt = "Read text in the image."
        
        # 处理元素
        result_text = await dolphin_engine.chat(prompt, image)
        
        response = {
            "task_id": str(uuid.uuid4()),
            "filename": file.filename,
            "element_type": element_type,
            "text": result_text.strip(),
            "status": "completed"
        }
        
        return response
        
    except Exception as e:
        api_logger.error("Element processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/api/v1/result/{task_id}")
async def get_result(task_id: str):
    """获取处理结果"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Result storage not available")
    
    try:
        result = await redis_client.get(f"result:{task_id}")
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        return json.loads(result)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid result data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 