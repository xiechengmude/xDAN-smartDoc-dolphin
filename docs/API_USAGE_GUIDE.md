# xDAN-Vision-SmartDoc API 使用说明文档

## 📖 API 概览

xDAN-Vision-SmartDoc API Server 提供强大的文档智能识别服务，支持文本、表格、图表和公式的识别与解析。

### 🔗 基础信息

- **服务地址**: `http://localhost:8000` (默认)
- **API版本**: v2.0.0  
- **协议**: HTTP/HTTPS
- **认证**: 无需认证 (可根据需要添加)
- **文档**: `http://localhost:8000/docs` (Swagger UI)

### 📋 API 端点列表

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/health` | GET | 健康检查 |
| `/api/process/document` | POST | 文档处理 |
| `/api/result/{task_id}` | GET | 获取结果 |
| `/api/metrics` | GET | 性能指标 |
| `/api/formats` | GET | 支持的格式 |

## 🚀 快速开始

### 1. 基础健康检查

```bash
curl -X GET "http://localhost:8000/health"
```

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": 1703765432.123,
  "version": "2.0.0",
  "service_name": "xDAN-Vision-SmartDoc",
  "components": {
    "vision_engine": "loaded",
    "redis_cache": "connected",
    "compute_device": "cuda",
    "model_precision": "half"
  },
  "performance_metrics": {
    "total_requests": 42,
    "average_processing_time": 2.341,
    "model_loaded": true,
    "device": "cuda"
  }
}
```

### 2. 服务信息查询

```bash
curl -X GET "http://localhost:8000/"
```

**响应示例:**
```json
{
  "service": "xDAN-Vision-SmartDoc API Server",
  "version": "2.0.0",
  "status": "🚀 running",
  "description": "基于xDAN 高性能多模态模型的智能文档识别系统",
  "docs": "/docs",
  "github": "https://github.com/xDAN-AI/xDAN-smartDoc-dolphin"
}
```

## 📄 文档处理 API

### 主要接口: `/api/process/document`

这是核心的文档处理接口，支持多种输出格式和处理选项。

#### 请求参数

**文件参数:**
- `file` (必填): 上传的图像文件，支持 PNG, JPG, JPEG 格式

**表单参数:**
- `max_batch_size` (可选): 批处理大小，1-64，默认16
- `output_format` (可选): 输出格式，可选值: `json`, `markdown`, `html`, `structured`，默认 `structured`
- `processing_mode` (可选): 处理模式，可选值: `sync`, `async`, `stream`，默认 `sync`
- `include_confidence` (可选): 是否包含置信度，默认 `true`
- `include_coordinates` (可选): 是否包含坐标信息，默认 `true`
- `include_images` (可选): 是否包含提取的图像数据，默认 `false`
- `merge_text_blocks` (可选): 是否合并相邻文本块，默认 `true`

#### cURL 示例

##### 基础调用
```bash
curl -X POST "http://localhost:8000/api/process/document" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.png" \
  -F "output_format=json"
```

##### 完整参数调用
```bash
curl -X POST "http://localhost:8000/api/process/document" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.png" \
  -F "output_format=structured" \
  -F "max_batch_size=16" \
  -F "include_confidence=true" \
  -F "include_coordinates=true" \
  -F "include_images=false" \
  -F "merge_text_blocks=true"
```

##### 高精度处理 (包含图像数据)
```bash
curl -X POST "http://localhost:8000/api/process/document" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.png" \
  -F "output_format=structured" \
  -F "max_batch_size=8" \
  -F "include_confidence=true" \
  -F "include_images=true" \
  -F "merge_text_blocks=false"
```

## 🐍 Python 客户端示例

### 基础 Python 客户端

```python
import asyncio
import httpx
from pathlib import Path
from typing import Dict, Any

class xDANVisionClient:
    """xDAN Vision API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        response = await self.client.get(f"{self.base_url}/health")
        return response.json()
    
    async def process_document(
        self,
        image_path: str,
        output_format: str = "structured",
        max_batch_size: int = 16,
        include_confidence: bool = True,
        include_coordinates: bool = True,
        include_images: bool = False,
        merge_text_blocks: bool = True
    ) -> Dict[str, Any]:
        """处理文档"""
        with open(image_path, "rb") as f:
            files = {"file": (Path(image_path).name, f, "image/png")}
            data = {
                "output_format": output_format,
                "max_batch_size": max_batch_size,
                "include_confidence": include_confidence,
                "include_coordinates": include_coordinates,
                "include_images": include_images,
                "merge_text_blocks": merge_text_blocks
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/process/document",
                files=files,
                data=data
            )
            
        return response.json()
    
    async def get_result(self, task_id: str) -> Dict[str, Any]:
        """获取结果 (用于异步模式)"""
        response = await self.client.get(f"{self.base_url}/api/result/{task_id}")
        return response.json()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        response = await self.client.get(f"{self.base_url}/api/metrics")
        return response.json()
    
    async def get_formats(self) -> Dict[str, Any]:
        """获取支持的格式信息"""
        response = await self.client.get(f"{self.base_url}/api/formats")
        return response.json()
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

# 使用示例
async def main():
    client = xDANVisionClient()
    
    try:
        # 1. 健康检查
        health = await client.health_check()
        print(f"服务状态: {health['status']}")
        
        # 2. 处理文档
        result = await client.process_document(
            image_path="document.png",
            output_format="structured",
            max_batch_size=16
        )
        
        print(f"识别到 {result['total_elements']} 个元素")
        print(f"处理时间: {result['processing_time']:.2f}s")
        
        # 3. 显示识别结果
        for element in result['elements']:
            print(f"类型: {element['type']}")
            print(f"文本: {element['text'][:100]}...")
            print(f"置信度: {element.get('confidence', 'N/A')}")
            print("-" * 40)
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 同步版本客户端

```python
import requests
from pathlib import Path
from typing import Dict, Any

class xDANVisionSyncClient:
    """xDAN Vision API 同步客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 300
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def process_document(
        self,
        image_path: str,
        output_format: str = "structured",
        **kwargs
    ) -> Dict[str, Any]:
        """处理文档"""
        with open(image_path, "rb") as f:
            files = {"file": (Path(image_path).name, f, "image/png")}
            data = {
                "output_format": output_format,
                **kwargs
            }
            
            response = self.session.post(
                f"{self.base_url}/api/process/document",
                files=files,
                data=data
            )
            
        response.raise_for_status()
        return response.json()

# 使用示例
def main():
    client = xDANVisionSyncClient()
    
    try:
        # 健康检查
        health = client.health_check()
        print(f"服务状态: {health['status']}")
        
        # 处理文档
        result = client.process_document(
            image_path="document.png",
            output_format="markdown",
            max_batch_size=16,
            include_confidence=True
        )
        
        print(f"处理完成!")
        print(f"任务ID: {result['task_id']}")
        print(f"识别元素: {result['total_elements']}")
        
        # 保存 Markdown 结果
        if result.get('markdown_content'):
            with open('result.md', 'w', encoding='utf-8') as f:
                f.write(result['markdown_content'])
            print("Markdown 结果已保存到 result.md")
            
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")

if __name__ == "__main__":
    main()
```

## 📊 输出格式详解

### 1. JSON 格式 (`output_format=json`)

**特点**: 结构化数据，适合程序处理

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.png",
  "status": "completed",
  "processing_time": 3.456,
  "total_elements": 15,
  "elements": [
    {
      "element_id": "elem_001",
      "type": "text",
      "bbox": [100.5, 200.3, 500.8, 250.9],
      "text": "第一章 引言",
      "confidence": 0.98,
      "reading_order": 1,
      "metadata": {}
    },
    {
      "element_id": "elem_002", 
      "type": "table",
      "bbox": [120.0, 300.0, 480.0, 450.0],
      "text": "| 指标 | 数值 | 说明 |\n|------|------|------|\n| 准确率 | 95.2% | 模型准确率 |",
      "confidence": 0.92,
      "reading_order": 2,
      "metadata": {}
    }
  ],
  "created_at": 1703765432.123,
  "completed_at": 1703765435.579
}
```

### 2. Markdown 格式 (`output_format=markdown`)

**特点**: 人类可读，易于编辑

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "markdown_content": "# 文档标题\n\n## 第一章 引言\n\n这里是引言内容...\n\n### 1.1 数据分析\n\n| 指标 | 数值 | 说明 |\n|------|------|------|\n| 准确率 | 95.2% | 模型准确率 |\n| 召回率 | 88.7% | 模型召回率 |\n\n### 1.2 公式推导\n\n$$accuracy = \\frac{TP + TN}{TP + TN + FP + FN}$$\n\n其中：\n- TP: 真正例\n- TN: 真负例",
  "total_elements": 15,
  "processing_time": 3.456,
  "status": "completed"
}
```

### 3. HTML 格式 (`output_format=html`)

**特点**: 网页显示，支持样式和交互

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "html_content": "<!DOCTYPE html>\n<html lang='zh-CN'>\n<head>\n    <meta charset='UTF-8'>\n    <title>xDAN Vision Document Analysis Result</title>\n    <style>\n        .document-container { max-width: 800px; margin: 0 auto; }\n        .confidence-indicator { width: 10px; height: 10px; }\n        .high-confidence { background-color: #28a745; }\n    </style>\n</head>\n<body>\n    <div class='document-container'>\n        <h1>📄 xDAN Vision 文档分析结果</h1>\n        <div class='element text-element'>\n            <span class='confidence-indicator high-confidence'></span>\n            <h2>第一章 引言</h2>\n        </div>\n    </div>\n</body>\n</html>",
  "total_elements": 15,
  "processing_time": 3.456,
  "status": "completed"
}
```

### 4. 结构化格式 (`output_format=structured`)

**特点**: 包含所有格式的完整输出

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.png",
  "status": "completed",
  "processing_time": 3.456,
  "total_elements": 15,
  "elements": [...],
  "markdown_content": "# 文档标题\n\n...",
  "html_content": "<!DOCTYPE html>...",
  "json_data": {
    "document_info": {...},
    "elements": [...],
    "statistics": {...}
  },
  "created_at": 1703765432.123,
  "completed_at": 1703765435.579
}
```

## 🔧 高级用法

### 1. 批量处理示例

```python
import asyncio
from pathlib import Path

async def batch_process_documents():
    """批量处理多个文档"""
    client = xDANVisionClient()
    
    # 获取所有图像文件
    image_files = list(Path("documents").glob("*.png"))
    
    # 并发处理 (限制并发数)
    semaphore = asyncio.Semaphore(3)  # 最多3个并发
    
    async def process_single(image_path):
        async with semaphore:
            try:
                result = await client.process_document(
                    str(image_path),
                    output_format="json",
                    max_batch_size=8
                )
                return {"file": image_path.name, "result": result}
            except Exception as e:
                return {"file": image_path.name, "error": str(e)}
    
    # 执行批量处理
    tasks = [process_single(img) for img in image_files]
    results = await asyncio.gather(*tasks)
    
    # 统计结果
    success_count = sum(1 for r in results if "result" in r)
    error_count = len(results) - success_count
    
    print(f"处理完成: 成功 {success_count}, 失败 {error_count}")
    
    await client.close()
    return results

# 运行批量处理
asyncio.run(batch_process_documents())
```

### 2. 流式处理示例

```python
async def stream_process_large_document():
    """流式处理大文档"""
    client = xDANVisionClient()
    
    # 启动异步处理
    result = await client.process_document(
        "large_document.png",
        output_format="json",
        processing_mode="async",  # 异步模式
        max_batch_size=4  # 较小的批次
    )
    
    task_id = result["task_id"]
    print(f"任务已启动: {task_id}")
    
    # 轮询结果
    while True:
        try:
            result = await client.get_result(task_id)
            if result["status"] == "completed":
                print("处理完成!")
                print(f"识别到 {result['total_elements']} 个元素")
                break
            elif result["status"] == "failed":
                print(f"处理失败: {result.get('error', '未知错误')}")
                break
            else:
                print(f"处理中... 状态: {result['status']}")
                await asyncio.sleep(2)  # 等待2秒后再查询
                
        except Exception as e:
            print(f"查询结果失败: {e}")
            await asyncio.sleep(5)
    
    await client.close()

asyncio.run(stream_process_large_document())
```

### 3. 性能监控示例

```python
async def monitor_performance():
    """监控API性能"""
    client = xDANVisionClient()
    
    # 获取当前指标
    metrics = await client.get_metrics()
    
    print("=== xDAN Vision 性能指标 ===")
    print(f"总请求数: {metrics.get('total_requests', 0)}")
    print(f"平均处理时间: {metrics.get('average_processing_time', 0):.3f}s")
    print(f"设备: {metrics.get('device', 'unknown')}")
    print(f"模型状态: {'已加载' if metrics.get('model_loaded') else '未加载'}")
    
    # 处理几个文档并比较性能
    test_files = ["doc1.png", "doc2.png", "doc3.png"]
    
    for file in test_files:
        if Path(file).exists():
            start_time = time.time()
            result = await client.process_document(file, output_format="json")
            end_time = time.time()
            
            print(f"\n文件: {file}")
            print(f"  客户端耗时: {end_time - start_time:.3f}s")
            print(f"  服务器耗时: {result.get('processing_time', 0):.3f}s")
            print(f"  识别元素: {result.get('total_elements', 0)}")
    
    await client.close()

asyncio.run(monitor_performance())
```

## ❌ 错误处理

### 常见错误码

| HTTP状态码 | 错误类型 | 描述 |
|-----------|----------|------|
| 400 | 请求错误 | 文件格式不支持或参数错误 |
| 404 | 未找到 | 任务ID不存在 |
| 500 | 服务器错误 | 模型处理失败或系统错误 |
| 503 | 服务不可用 | 模型未加载或系统资源不足 |

### 错误响应示例

```json
{
  "detail": "❌ 文件格式错误: 请上传图像文件 (支持PNG, JPG, JPEG)"
}
```

### Python 错误处理

```python
import httpx

async def robust_process_document(client, image_path):
    """健壮的文档处理，包含错误处理"""
    try:
        result = await client.process_document(image_path)
        return {"success": True, "data": result}
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            return {"success": False, "error": "请求参数错误", "details": e.response.text}
        elif e.response.status_code == 500:
            return {"success": False, "error": "服务器处理错误", "details": e.response.text}
        else:
            return {"success": False, "error": f"HTTP错误: {e.response.status_code}"}
            
    except httpx.ConnectError:
        return {"success": False, "error": "无法连接到服务器"}
        
    except httpx.TimeoutException:
        return {"success": False, "error": "请求超时"}
        
    except Exception as e:
        return {"success": False, "error": f"未知错误: {str(e)}"}
```

## 🎯 最佳实践

### 1. 性能优化建议

```python
# 推荐的参数配置
performance_configs = {
    "小文档": {
        "max_batch_size": 32,
        "include_images": False,
        "merge_text_blocks": True
    },
    "大文档": {
        "max_batch_size": 8,
        "include_images": False,
        "merge_text_blocks": True
    },
    "高精度": {
        "max_batch_size": 4,
        "include_confidence": True,
        "include_images": True,
        "merge_text_blocks": False
    },
    "快速扫描": {
        "max_batch_size": 64,
        "include_confidence": False,
        "include_coordinates": False,
        "merge_text_blocks": True
    }
}
```

### 2. 图像预处理建议

```python
from PIL import Image
import numpy as np

def optimize_image_for_ocr(image_path: str, output_path: str):
    """优化图像以提高OCR效果"""
    image = Image.open(image_path)
    
    # 转换为RGB
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 调整分辨率 (推荐300 DPI)
    width, height = image.size
    if width < 1200:  # 如果宽度小于1200px，放大
        scale = 1200 / width
        new_size = (int(width * scale), int(height * scale))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # 保存优化后的图像
    image.save(output_path, 'PNG', quality=95)
    return output_path

# 使用示例
optimized_path = optimize_image_for_ocr("original.jpg", "optimized.png")
result = await client.process_document(optimized_path)
```

### 3. 结果后处理示例

```python
def post_process_results(result):
    """结果后处理"""
    elements = result.get('elements', [])
    
    # 按置信度过滤
    high_confidence_elements = [
        elem for elem in elements 
        if elem.get('confidence', 0) > 0.8
    ]
    
    # 按类型分组
    grouped = {}
    for elem in high_confidence_elements:
        elem_type = elem['type']
        if elem_type not in grouped:
            grouped[elem_type] = []
        grouped[elem_type].append(elem)
    
    # 提取纯文本
    all_text = []
    for elem in sorted(elements, key=lambda x: x['reading_order']):
        if elem.get('text'):
            all_text.append(elem['text'])
    
    return {
        'grouped_elements': grouped,
        'full_text': '\n'.join(all_text),
        'statistics': {
            'total_elements': len(elements),
            'high_confidence_elements': len(high_confidence_elements),
            'element_types': list(grouped.keys())
        }
    }

# 使用示例
result = await client.process_document("document.png")
processed = post_process_results(result)
print(f"高置信度元素: {processed['statistics']['high_confidence_elements']}")
```

## 📞 技术支持

### 常见问题

**Q: 处理速度慢怎么办？**
A: 
- 调整 `max_batch_size` 参数
- 使用GPU加速 (`DEVICE=cuda`)
- 预处理图像大小
- 关闭不必要的选项 (`include_images=false`)

**Q: 识别准确率不高？**
A:
- 确保图像清晰，分辨率足够
- 使用 `include_confidence=true` 查看置信度
- 调小 `max_batch_size` 提高精度
- 尝试不同的图像预处理

**Q: 内存不足错误？**
A:
- 减小 `max_batch_size`
- 使用较小的图像尺寸
- 设置 `include_images=false`

### 获取帮助

- **API文档**: `http://localhost:8000/docs`
- **健康状态**: `http://localhost:8000/health`
- **性能监控**: `http://localhost:8000/api/metrics`

---

**xDAN-Vision-SmartDoc API** - 让文档智能识别更简单高效！ 🚀 