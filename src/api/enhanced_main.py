"""
基于xDAN 高性能多模态模型xDAN-Vision-SmartDoc的高性能异步智能文档识别系统
"""

import asyncio
import io
import json
import time
import uuid
from contextlib import asynccontextmanager
from enum import Enum
from typing import Dict, List, Optional, Union

import aioredis
import cv2
import torch
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel, Field, validator
from transformers import AutoProcessor, VisionEncoderDecoderModel

from ..core.config import settings
from ..core.logging import api_logger, setup_logging
from ..utils.image_utils import ImageDimensions, prepare_image, process_coordinates
from ..utils.parsing_utils import generate_json_output, generate_markdown, parse_layout_string


# ========================= 数据模型 =========================

class OutputFormat(str, Enum):
    """输出格式枚举"""
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    STRUCTURED = "structured"  # 包含所有格式的结构化输出


class ProcessingMode(str, Enum):
    """处理模式枚举"""
    SYNC = "sync"      # 同步处理，立即返回结果
    ASYNC = "async"    # 异步处理，返回任务ID
    STREAM = "stream"  # 流式处理，实时返回进度


class ElementType(str, Enum):
    """元素类型枚举"""
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    FORMULA = "formula"
    CHART = "chart"
    DIAGRAM = "diagram"


class ProcessingRequest(BaseModel):
    """处理请求模型"""
    max_batch_size: int = Field(default=16, ge=1, le=64, description="批处理大小")
    output_format: OutputFormat = Field(default=OutputFormat.STRUCTURED, description="输出格式")
    processing_mode: ProcessingMode = Field(default=ProcessingMode.SYNC, description="处理模式")
    include_confidence: bool = Field(default=True, description="是否包含置信度")
    include_coordinates: bool = Field(default=True, description="是否包含坐标信息")
    include_images: bool = Field(default=False, description="是否包含提取的图像")
    merge_text_blocks: bool = Field(default=True, description="是否合并相邻文本块")
    
    @validator('max_batch_size')
    def validate_batch_size(cls, v):
        if v < 1 or v > 64:
            raise ValueError('Batch size must be between 1 and 64')
        return v


class ElementResponse(BaseModel):
    """元素响应模型"""
    element_id: str = Field(description="元素ID")
    type: ElementType = Field(description="元素类型")
    bbox: List[float] = Field(description="边界框坐标 [x1, y1, x2, y2]")
    text: str = Field(default="", description="提取的文本内容")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="置信度")
    reading_order: int = Field(description="阅读顺序")
    metadata: Dict = Field(default_factory=dict, description="元数据")
    image_data: Optional[str] = Field(default=None, description="Base64编码的图像数据")


class ProcessingResult(BaseModel):
    """处理结果模型"""
    task_id: str = Field(description="任务ID")
    filename: str = Field(description="文件名")
    status: str = Field(description="处理状态")
    processing_time: float = Field(description="处理时间(秒)")
    total_elements: int = Field(description="元素总数")
    elements: List[ElementResponse] = Field(description="识别的元素列表")
    markdown_content: Optional[str] = Field(default=None, description="Markdown格式内容")
    html_content: Optional[str] = Field(default=None, description="HTML格式内容")
    json_data: Optional[Dict] = Field(default=None, description="结构化JSON数据")
    created_at: float = Field(description="创建时间戳")
    completed_at: Optional[float] = Field(default=None, description="完成时间戳")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: float = Field(ge=0.0, le=100.0)
    message: Optional[str] = None
    estimated_remaining_time: Optional[float] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: float
    version: str
    service_name: str
    components: Dict[str, str]
    performance_metrics: Optional[Dict] = None


# ========================= xDAN Vision引擎 =========================

class xDANVisionEngine:
    """xDAN Vision智能文档识别引擎"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model_loaded = False
        self._load_lock = asyncio.Lock()
        self._processing_semaphore = asyncio.Semaphore(settings.max_concurrent_tasks)
        
        # 性能监控
        self._total_requests = 0
        self._total_processing_time = 0.0
        self._last_request_time = 0.0
        
    async def load_model(self):
        """异步模型加载"""
        if self._model_loaded:
            return
            
        async with self._load_lock:
            if self._model_loaded:
                return
                
            api_logger.info("Loading xDAN Vision model", path=settings.model_path)
            start_time = time.time()
            
            # 在线程池中加载模型
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model_sync)
            
            load_time = time.time() - start_time
            self._model_loaded = True
            
            api_logger.info("xDAN Vision model loaded successfully", 
                          load_time=f"{load_time:.2f}s",
                          device=self.device)
    
    def _load_model_sync(self):
        """同步模型加载"""
        try:
            # 加载Dolphin模型组件
            self.processor = AutoProcessor.from_pretrained(settings.model_path)
            self.model = VisionEncoderDecoderModel.from_pretrained(settings.model_path)
            
            # 模型优化
            self.model.eval()
            self.model.to(self.device)
            
            # 精度优化
            if settings.model_precision == "half" and self.device != "cpu":
                self.model = self.model.half()
            
            # 编译优化 (PyTorch 2.0+)
            if hasattr(torch, 'compile') and settings.model_device == "cuda":
                try:
                    self.model = torch.compile(self.model, mode="reduce-overhead")
                    api_logger.info("Model compiled with torch.compile")
                except Exception as e:
                    api_logger.warning("Failed to compile model", error=str(e))
            
            self.tokenizer = self.processor.tokenizer
            
            # GPU内存优化
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
        except Exception as e:
            api_logger.error("Failed to load xDAN Vision model", error=str(e))
            raise
    
    async def process_document(
        self, 
        image: Image.Image, 
        request: ProcessingRequest,
        background_tasks: BackgroundTasks = None
    ) -> ProcessingResult:
        """文档处理主入口"""
        
        async with self._processing_semaphore:
            start_time = time.time()
            task_id = str(uuid.uuid4())
            
            try:
                # 更新性能指标
                self._total_requests += 1
                self._last_request_time = start_time
                
                # 执行处理
                if request.processing_mode == ProcessingMode.SYNC:
                    result = await self._process_sync(image, request, task_id, start_time)
                elif request.processing_mode == ProcessingMode.ASYNC:
                    result = await self._process_async(image, request, task_id, start_time, background_tasks)
                else:  # STREAM
                    result = await self._process_stream(image, request, task_id, start_time)
                
                # 更新性能统计
                processing_time = time.time() - start_time
                self._total_processing_time += processing_time
                
                return result
                
            except Exception as e:
                api_logger.error("xDAN Vision document processing failed", 
                               task_id=task_id, error=str(e))
                raise
    
    async def _process_sync(
        self, 
        image: Image.Image, 
        request: ProcessingRequest,
        task_id: str,
        start_time: float
    ) -> ProcessingResult:
        """同步处理模式"""
        
        # 阶段1: 布局解析
        layout_output = await self.chat("Parse the reading order of this document.", image)
        
        # 阶段2: 元素处理
        loop = asyncio.get_event_loop()
        padded_image, dims = await loop.run_in_executor(None, prepare_image, image)
        
        elements = await self._process_elements(
            layout_output, padded_image, dims, request
        )
        
        # 格式化输出
        return await self._format_result(
            elements, task_id, request, start_time, "unknown.png"
        )
    
    async def _process_elements(
        self, 
        layout_results: str, 
        padded_image, 
        dims: ImageDimensions, 
        request: ProcessingRequest
    ) -> List[Dict]:
        """处理文档元素"""
        
        loop = asyncio.get_event_loop()
        layout_data = await loop.run_in_executor(None, parse_layout_string, layout_results)
        
        # 分类收集元素
        element_groups = {
            "text": [],
            "table": [], 
            "figure": [],
            "formula": []
        }
        
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
                    element_info = {
                        "bbox": [orig_x1, orig_y1, orig_x2, orig_y2],
                        "reading_order": reading_order,
                        "element_id": str(uuid.uuid4())
                    }
                    
                    if label == "fig":
                        element_info.update({
                            "type": "figure",
                            "text": "",
                            "confidence": 1.0
                        })
                        
                        # 如果需要包含图像数据
                        if request.include_images:
                            pil_crop = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
                            element_info["image_data"] = await self._encode_image_base64(pil_crop)
                        
                        element_groups["figure"].append(element_info)
                    else:
                        pil_crop = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
                        element_info["crop"] = pil_crop
                        
                        if label == "tab":
                            element_info["type"] = "table"
                            element_groups["table"].append(element_info)
                        else:
                            element_info["type"] = "text"
                            element_groups["text"].append(element_info)
                
                reading_order += 1
                
            except Exception as e:
                api_logger.warning("Failed to process element", 
                                 label=label, error=str(e))
                continue
        
        # 批量处理各类元素
        all_elements = element_groups["figure"].copy()
        
        # 处理文本元素
        if element_groups["text"]:
            text_results = await self._process_element_batch(
                element_groups["text"], "Read text in the image.", request
            )
            all_elements.extend(text_results)
        
        # 处理表格元素
        if element_groups["table"]:
            table_results = await self._process_element_batch(
                element_groups["table"], "Parse the table in the image.", request
            )
            all_elements.extend(table_results)
        
        # 排序并后处理
        all_elements.sort(key=lambda x: x["reading_order"])
        
        # 合并相邻文本块
        if request.merge_text_blocks:
            all_elements = await self._merge_adjacent_text_blocks(all_elements)
        
        return all_elements
    
    async def _process_element_batch(
        self, 
        elements: List[Dict], 
        prompt: str, 
        request: ProcessingRequest
    ) -> List[Dict]:
        """批量处理元素"""
        results = []
        
        for i in range(0, len(elements), request.max_batch_size):
            batch = elements[i:i + request.max_batch_size]
            crops = [elem["crop"] for elem in batch]
            prompts = [prompt] * len(crops)
            
            try:
                # 批量推理
                texts = await self.chat_batch(prompts, crops)
                
                # 构建结果
                for elem, text in zip(batch, texts):
                    result = {
                        "element_id": elem["element_id"],
                        "type": elem["type"],
                        "bbox": elem["bbox"],
                        "text": text.strip(),
                        "reading_order": elem["reading_order"],
                        "metadata": {}
                    }
                    
                    # 添加置信度（简化版，实际应该从模型获取）
                    if request.include_confidence:
                        result["confidence"] = min(1.0, len(text) / 100.0)  # 简化计算
                    
                    # 添加图像数据
                    if request.include_images and "crop" in elem:
                        result["image_data"] = await self._encode_image_base64(elem["crop"])
                    
                    results.append(result)
                    
            except Exception as e:
                api_logger.error("Batch processing failed", error=str(e))
                # 添加空结果
                for elem in batch:
                    results.append({
                        "element_id": elem["element_id"],
                        "type": elem["type"],
                        "bbox": elem["bbox"],
                        "text": "",
                        "reading_order": elem["reading_order"],
                        "confidence": 0.0,
                        "metadata": {"error": "Processing failed"}
                    })
        
        return results
    
    async def _format_result(
        self,
        elements: List[Dict],
        task_id: str,
        request: ProcessingRequest,
        start_time: float,
        filename: str
    ) -> ProcessingResult:
        """格式化结果 - 支持多种输出格式"""
        
        processing_time = time.time() - start_time
        completed_at = time.time()
        
        # 转换为响应模型
        element_responses = []
        for elem in elements:
            element_responses.append(ElementResponse(
                element_id=elem["element_id"],
                type=ElementType(elem["type"]),
                bbox=elem["bbox"],
                text=elem["text"],
                confidence=elem.get("confidence") if request.include_confidence else None,
                reading_order=elem["reading_order"],
                metadata=elem.get("metadata", {}),
                image_data=elem.get("image_data") if request.include_images else None
            ))
        
        # 基础结果
        result = ProcessingResult(
            task_id=task_id,
            filename=filename,
            status="completed",
            processing_time=processing_time,
            total_elements=len(elements),
            elements=element_responses,
            created_at=start_time,
            completed_at=completed_at
        )
        
        # 根据输出格式添加内容
        if request.output_format in [OutputFormat.MARKDOWN, OutputFormat.STRUCTURED]:
            result.markdown_content = generate_markdown(elements)
        
        if request.output_format in [OutputFormat.HTML, OutputFormat.STRUCTURED]:
            result.html_content = await self._generate_html(elements)
        
        if request.output_format in [OutputFormat.JSON, OutputFormat.STRUCTURED]:
            result.json_data = generate_json_output(elements, processing_time)
        
        return result
    
    async def _generate_html(self, elements: List[Dict]) -> str:
        """生成HTML格式输出"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='zh-CN'>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "    <title>xDAN Vision Document Analysis Result</title>",
            "    <style>",
            "        .document-container { max-width: 800px; margin: 0 auto; padding: 20px; }",
            "        .header { text-align: center; margin-bottom: 30px; }",
            "        .element { margin: 15px 0; padding: 10px; border-left: 3px solid #007acc; }",
            "        .text-element { font-family: Arial, sans-serif; background-color: #f8f9fa; }",
            "        .table-element { background-color: #fff3cd; }",
            "        .figure-element { text-align: center; background-color: #d1ecf1; }",
            "        .formula-element { text-align: center; background-color: #d4edda; }",
            "        .confidence-indicator { ",
            "            display: inline-block; width: 10px; height: 10px; ",
            "            border-radius: 50%; margin-right: 8px; ",
            "        }",
            "        .high-confidence { background-color: #28a745; }",
            "        .medium-confidence { background-color: #ffc107; }",
            "        .low-confidence { background-color: #dc3545; }",
            "        table { border-collapse: collapse; width: 100%; }",
            "        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "        th { background-color: #f2f2f2; }",
            "    </style>",
            "</head>",
            "<body>",
            "    <div class='document-container'>",
            "        <div class='header'>",
            "            <h1>📄 xDAN Vision 文档分析结果</h1>",
            "            <p>智能文档识别与结构化解析</p>",
            "        </div>"
        ]
        
        for element in sorted(elements, key=lambda x: x["reading_order"]):
            elem_type = element["type"]
            text = element["text"]
            bbox = element["bbox"]
            confidence = element.get("confidence", 0.0)
            
            # 置信度指示器
            if confidence >= 0.8:
                confidence_class = "high-confidence"
            elif confidence >= 0.5:
                confidence_class = "medium-confidence" 
            else:
                confidence_class = "low-confidence"
            
            # 添加元素容器
            html_parts.append(f'        <div class="element {elem_type}-element" data-bbox="{bbox}">')
            html_parts.append(f'            <span class="confidence-indicator {confidence_class}" title="Confidence: {confidence:.2f}"></span>')
            
            if elem_type == "text":
                html_parts.append(f"            <p>{text}</p>")
            elif elem_type == "table":
                # 尝试解析表格结构
                if "|" in text:
                    html_parts.append("            " + self._markdown_table_to_html(text))
                else:
                    html_parts.append(f"            <pre class='table-content'>{text}</pre>")
            elif elem_type == "figure":
                html_parts.append("            <div class='figure-placeholder'>")
                html_parts.append("                📊 <strong>图表/图像</strong>")
                if text:
                    html_parts.append(f"                <p>{text}</p>")
                html_parts.append("            </div>")
            elif elem_type == "formula":
                html_parts.append(f"            <div class='formula'>📐 <code>{text}</code></div>")
            
            html_parts.append("        </div>")
        
        html_parts.extend([
            "    </div>",
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_parts)
    
    def _markdown_table_to_html(self, markdown_table: str) -> str:
        """将Markdown表格转换为HTML"""
        lines = [line.strip() for line in markdown_table.split('\n') if line.strip()]
        if not lines:
            return "<table></table>"
        
        html = ["<table>"]
        
        for i, line in enumerate(lines):
            if line.startswith('|') and line.endswith('|'):
                cells = [cell.strip() for cell in line[1:-1].split('|')]
                
                if i == 1 and all(set(cell.strip()) <= {'-', ':', ' '} for cell in cells):
                    continue  # Skip separator line
                
                tag = "th" if i == 0 else "td"
                html.append("    <tr>")
                for cell in cells:
                    html.append(f"        <{tag}>{cell}</{tag}>")
                html.append("    </tr>")
        
        html.append("</table>")
        return "\n".join(html)
    
    async def _encode_image_base64(self, image: Image.Image) -> str:
        """将图像编码为Base64字符串"""
        import base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    async def _merge_adjacent_text_blocks(self, elements: List[Dict]) -> List[Dict]:
        """合并相邻的文本块"""
        if not elements:
            return elements
        
        merged = []
        current_group = []
        
        for element in sorted(elements, key=lambda x: x["reading_order"]):
            if element["type"] == "text":
                if not current_group:
                    current_group.append(element)
                else:
                    # 检查是否相邻（简化逻辑）
                    last_elem = current_group[-1]
                    if self._are_adjacent(last_elem["bbox"], element["bbox"]):
                        current_group.append(element)
                    else:
                        # 合并当前组并开始新组
                        if len(current_group) > 1:
                            merged.append(self._merge_text_group(current_group))
                        else:
                            merged.extend(current_group)
                        current_group = [element]
            else:
                # 处理非文本元素
                if current_group:
                    if len(current_group) > 1:
                        merged.append(self._merge_text_group(current_group))
                    else:
                        merged.extend(current_group)
                    current_group = []
                merged.append(element)
        
        # 处理最后一组
        if current_group:
            if len(current_group) > 1:
                merged.append(self._merge_text_group(current_group))
            else:
                merged.extend(current_group)
        
        return merged
    
    def _are_adjacent(self, bbox1: List[float], bbox2: List[float], threshold: float = 20.0) -> bool:
        """检查两个边界框是否相邻"""
        # 简化的相邻检测逻辑
        vertical_distance = abs(bbox2[1] - bbox1[3])  # 上下距离
        return vertical_distance <= threshold
    
    def _merge_text_group(self, group: List[Dict]) -> Dict:
        """合并文本组"""
        if not group:
            return {}
        
        # 合并文本
        texts = [elem["text"] for elem in group if elem["text"].strip()]
        merged_text = " ".join(texts)
        
        # 计算合并边界框
        min_x = min(elem["bbox"][0] for elem in group)
        min_y = min(elem["bbox"][1] for elem in group)
        max_x = max(elem["bbox"][2] for elem in group)
        max_y = max(elem["bbox"][3] for elem in group)
        
        # 使用第一个元素作为基础
        merged = group[0].copy()
        merged.update({
            "text": merged_text,
            "bbox": [min_x, min_y, max_x, max_y],
            "metadata": {"merged_from": len(group)}
        })
        
        return merged
    
    async def chat(self, prompt: str, image: Image.Image) -> str:
        """单图像处理"""
        if not self._model_loaded:
            await self.load_model()
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._chat_sync, prompt, image)
    
    async def chat_batch(self, prompts: List[str], images: List[Image.Image]) -> List[str]:
        """批量图像处理"""
        if not self._model_loaded:
            await self.load_model()
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._chat_batch_sync, prompts, images)
    
    def _chat_sync(self, prompt: str, image: Image.Image) -> str:
        """同步单图像处理"""
        try:
            # 准备输入
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
            
            # 解码
            sequence = self.tokenizer.batch_decode(outputs.sequences, skip_special_tokens=False)[0]
            result = sequence.replace(formatted_prompt, "").replace("<pad>", "").replace("</s>", "").strip()
            
            return result
            
        except Exception as e:
            api_logger.error("Single chat processing failed", error=str(e))
            return ""
        finally:
            # 清理GPU内存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    def _chat_batch_sync(self, prompts: List[str], images: List[Image.Image]) -> List[str]:
        """同步批量处理"""
        try:
            # 准备批量输入
            batch_inputs = self.processor(images, return_tensors="pt", padding=True)
            batch_pixel_values = batch_inputs.pixel_values
            
            if settings.model_precision == "half" and self.device != "cpu":
                batch_pixel_values = batch_pixel_values.half()
            batch_pixel_values = batch_pixel_values.to(self.device)
            
            # 准备批量提示
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
            
            # 批量解码
            sequences = self.tokenizer.batch_decode(outputs.sequences, skip_special_tokens=False)
            results = []
            for i, sequence in enumerate(sequences):
                cleaned = sequence.replace(formatted_prompts[i], "").replace("<pad>", "").replace("</s>", "").strip()
                results.append(cleaned)
                
            return results
            
        except Exception as e:
            api_logger.error("Batch chat processing failed", error=str(e))
            return [""] * len(prompts)
        finally:
            # 清理GPU内存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    def get_performance_metrics(self) -> Dict:
        """获取性能指标"""
        if self._total_requests == 0:
            return {"total_requests": 0}
        
        avg_processing_time = self._total_processing_time / self._total_requests
        
        return {
            "total_requests": self._total_requests,
            "average_processing_time": round(avg_processing_time, 3),
            "total_processing_time": round(self._total_processing_time, 3),
            "last_request_time": self._last_request_time,
            "model_loaded": self._model_loaded,
            "device": self.device
        }


# ========================= 全局变量和依赖 =========================

vision_engine = None
redis_client = None
security = HTTPBearer(auto_error=False)


async def get_engine() -> xDANVisionEngine:
    """获取引擎实例"""
    global vision_engine
    if not vision_engine:
        raise HTTPException(status_code=503, detail="xDAN Vision service not ready")
    return vision_engine


async def get_redis() -> Optional[aioredis.Redis]:
    """获取Redis客户端"""
    return redis_client


# ========================= 应用生命周期 =========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global vision_engine, redis_client
    
    # 启动时初始化
    setup_logging()
    api_logger.info("Starting xDAN-Vision-SmartDoc API Server")
    
    # 初始化xDAN Vision引擎
    vision_engine = xDANVisionEngine()
    
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
    api_logger.info("xDAN-Vision-SmartDoc API Server stopped")


# ========================= FastAPI应用 =========================

app = FastAPI(
    title="xDAN-Vision-SmartDoc API Server",
    version="2.0.0",
    description="🔬 基于xDAN 高性能多模态模型xDAN-Vision-SmartDoc的高性能异步智能文档识别系统\n\n"
    "## 🚀 核心功能\n"
    "- 📝 **OCR文本识别**: 高精度文本提取和识别\n"
    "- 📊 **表格解析**: 智能表格结构识别和内容提取\n"
    "- 🖼️ **图表分析**: 图表、图像内容理解和描述\n"
    "- 🧮 **公式识别**: 数学公式和科学符号识别\n"
    "- 📋 **版面分析**: 文档结构和阅读顺序分析\n"
    "- 🎯 **多格式输出**: JSON/Markdown/HTML/结构化数据\n\n"
    "## ⚡ 性能特色\n"
    "- 🔥 **异步处理**: 高并发请求处理能力\n"
    "- 🚀 **批量识别**: 智能批处理优化\n"
    "- 💾 **智能缓存**: Redis缓存加速\n"
    "- 📊 **实时监控**: 性能指标和健康检查\n"
    "- 🔧 **企业级**: 生产环境优化配置\n\n"
    "## 📖 使用说明\n"
    "1. 📱 **网页版**: 访问 `/web` 进行可视化操作\n"
    "2. 🔧 **API调用**: 使用 `/api/v2/document/analyze` 端点\n"
    "3. 📚 **文档**: 查看完整API文档和示例\n"
    "4. 🎯 **格式选择**: 根据需求选择最适合的输出格式",
    contact={
        "name": "xDAN-Vision-SmartDoc 技术支持",
        "url": "https://github.com/xDAN-AI/xDAN-smartDoc-dolphin",
        "email": "support@xdan.ai",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "document",
            "description": "文档识别相关操作",
        },
        {
            "name": "system",
            "description": "系统监控和健康检查",
        },
        {
            "name": "web",
            "description": "Web界面和静态资源",
        },
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 静态文件服务
app.mount("/static", StaticFiles(directory="src/web"), name="static")


# ========================= API路由 =========================

@app.get("/", tags=["system"])
async def root():
    """根路径信息"""
    return {
        "service": "xDAN-Vision-SmartDoc API Server",
        "version": "2.0.0",
        "description": "基于xDAN 高性能多模态模型xDAN-Vision-SmartDoc的智能文档识别系统",
        "endpoints": {
            "web_interface": "/web",
            "api_docs": "/docs",
            "redoc_docs": "/redoc",
            "health_check": "/health",
            "document_analysis": "/api/v2/document/analyze"
        },
        "features": [
            "OCR文本识别",
            "表格解析", 
            "图表分析",
            "公式识别",
            "多格式输出",
            "异步处理"
        ]
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(engine: xDANVisionEngine = Depends(get_engine)):
    """健康检查"""
    performance_metrics = engine.get_performance_metrics()
    
    health_response = HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version="2.0.0",
        service_name="xDAN-Vision-SmartDoc",
        components={
            "vision_engine": "loaded" if engine._model_loaded else "not_loaded",
            "redis_cache": "connected" if redis_client else "disconnected",
            "compute_device": engine.device,
            "model_precision": settings.model_precision
        },
        performance_metrics=performance_metrics
    )
    
    return health_response


@app.post("/api/process/document", response_model=ProcessingResult)
async def process_document(
    file: UploadFile = File(..., description="📄 文档图像文件 (支持PNG, JPG, JPEG)"),
    request: ProcessingRequest = Depends(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    engine: xDANVisionEngine = Depends(get_engine)
):
    """
    🔬 **智能文档处理API**
    
    **功能描述:**
    - 📝 OCR文本识别与提取
    - 📊 表格结构解析与格式化  
    - 🖼️ 图表/图像分析与描述
    - 🧮 数学公式识别(LaTeX格式)
    - 📋 智能布局分析与阅读顺序
    
    **参数说明:**
    - **file**: 上传的文档图像文件
    - **max_batch_size**: 批处理大小 (1-64)，影响处理速度
    - **output_format**: 输出格式选择
        - `json`: 结构化数据，适合程序处理
        - `markdown`: 可读性文档，适合编辑
        - `html`: 网页显示，适合预览
        - `structured`: 包含所有格式的完整输出
    - **processing_mode**: 处理模式 (sync/async/stream)
    - **include_confidence**: 是否包含识别置信度
    - **include_coordinates**: 是否包含元素坐标信息
    - **include_images**: 是否包含提取的图像数据(Base64)
    - **merge_text_blocks**: 是否合并相邻文本块
    
    **返回结果:**
    包含识别的文档元素、格式化内容和处理统计信息
    """
    
    # 文件验证
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400, 
            detail="❌ 文件格式错误: 请上传图像文件 (支持PNG, JPG, JPEG)"
        )
    
    try:
        # 读取图像
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # 处理文档
        result = await engine.process_document(
            image=image,
            request=request,
            background_tasks=background_tasks
        )
        
        # 更新文件名
        result.filename = file.filename or "unknown.png"
        
        # 缓存结果
        if redis_client and request.processing_mode == ProcessingMode.SYNC:
            try:
                await redis_client.setex(
                    f"xdan:result:{result.task_id}",
                    3600,  # 1小时过期
                    result.json()
                )
            except Exception as e:
                api_logger.warning("Failed to cache result", error=str(e))
        
        api_logger.info("Document processed successfully",
                       task_id=result.task_id,
                       filename=file.filename,
                       total_elements=result.total_elements,
                       processing_time=result.processing_time,
                       output_format=request.output_format.value)
        
        return result
        
    except Exception as e:
        api_logger.error("xDAN Vision document processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"❌ 处理失败: {str(e)}")


@app.get("/api/result/{task_id}", response_model=ProcessingResult)
async def get_result(
    task_id: str,
    redis_client: Optional[aioredis.Redis] = Depends(get_redis)
):
    """📄 获取处理结果"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="❌ 结果存储服务不可用")
    
    try:
        result_data = await redis_client.get(f"xdan:result:{task_id}")
        if not result_data:
            raise HTTPException(status_code=404, detail="❌ 未找到指定任务结果")
        
        # 解析JSON结果
        result_dict = json.loads(result_data)
        return ProcessingResult(**result_dict)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="❌ 结果数据格式错误")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ 获取结果失败: {str(e)}")


@app.get("/api/metrics", response_model=Dict)
async def get_performance_metrics(engine: xDANVisionEngine = Depends(get_engine)):
    """📊 获取系统性能指标"""
    return engine.get_performance_metrics()


@app.get("/api/formats", response_model=Dict[str, Any])
async def get_supported_formats():
    """📋 获取支持的格式信息"""
    return {
        "input_formats": {
            "images": ["PNG", "JPG", "JPEG"],
            "max_file_size": "50MB",
            "recommended_dpi": "300 DPI"
        },
        "output_formats": {
            "json": {
                "description": "结构化数据格式",
                "use_case": "程序处理、API对接",
                "features": ["元素信息", "坐标数据", "置信度"]
            },
            "markdown": {
                "description": "可读性文档格式", 
                "use_case": "文档编辑、版本控制",
                "features": ["保持格式", "支持公式", "易于编辑"]
            },
            "html": {
                "description": "网页显示格式",
                "use_case": "在线预览、Web集成",
                "features": ["可视化展示", "样式美化", "交互支持"]
            },
            "structured": {
                "description": "完整结构化输出",
                "use_case": "全格式需求、一次性处理", 
                "features": ["包含所有格式", "完整信息", "灵活使用"]
            }
        },
        "supported_elements": {
            "text": "文本内容识别",
            "table": "表格结构解析",
            "figure": "图表/图像分析",
            "formula": "数学公式识别",
            "chart": "图表数据提取",
            "diagram": "流程图理解"
        }
    }

# 网页版用户界面路由
@app.get("/web")
async def web_interface():
    """网页版用户界面"""
    return FileResponse("src/web/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 