# 🔬 xDAN-Vision-SmartDoc API Server
🔬 **基于xDAN 高性能多模态模型的高性能异步智能文档识别系统**

## ✨ 核心功能

- 📝 **OCR文本识别**: 高精度多语言文本识别
- 📊 **表格解析**: 结构化表格识别与格式化
- 🖼️ **图表分析**: 智能图表理解与描述
- 🧮 **公式识别**: LaTeX格式数学公式识别
- 🎨 **多格式输出**: JSON/Markdown/HTML/结构化输出
- ⚡ **异步处理**: 高并发批量处理

## 🚀 技术特色

- **Vision-Encoder-Decoder架构**: SwinTransformer + mBART
- **GPU加速推理优化**: 支持半精度推理和模型编译
- **智能文档布局分析**: 自动识别阅读顺序
- **自适应批处理**: 动态调整批处理大小
- **企业级API**: FastAPI + 异步处理 + 性能监控

## 🛠️ 快速开始

### 1. 环境要求

```bash
# Python 3.8+
# CUDA (可选，用于GPU加速)

# 安装依赖
pip install torch transformers fastapi[all] aioredis opencv-python pillow uvicorn
```

### 2. 启动服务

```bash
# 基本启动
python start_xdan_vision_server.py

# 指定端口
python start_xdan_vision_server.py --port 8001

# 开发模式 (自动重载)
python start_xdan_vision_server.py --dev

# 多进程启动
python start_xdan_vision_server.py --workers 4
```

### 3. API文档

启动后访问：`http://localhost:8000/docs`

## 📖 API使用示例

### Python客户端

```python
import httpx
from pathlib import Path

async def test_document_processing():
    async with httpx.AsyncClient() as client:
        # 上传文档图像
        with open("document.png", "rb") as f:
            files = {"file": ("document.png", f, "image/png")}
            data = {
                "output_format": "structured",
                "max_batch_size": 16,
                "include_confidence": True
            }
            
            response = await client.post(
                "http://localhost:8000/api/process/document",
                files=files,
                data=data
            )
            
        result = response.json()
        print(f"识别到 {result['total_elements']} 个元素")
        print(f"处理时间: {result['processing_time']:.2f}s")
```

### cURL示例

```bash
# 处理文档
curl -X POST "http://localhost:8000/api/process/document" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@document.png" \
     -F "output_format=structured" \
     -F "max_batch_size=16"

# 健康检查
curl "http://localhost:8000/health"

# 获取性能指标
curl "http://localhost:8000/api/metrics"
```

## 📊 输出格式

### JSON格式 - 结构化数据
```json
{
  "task_id": "uuid",
  "total_elements": 15,
  "processing_time": 3.45,
  "elements": [
    {
      "element_id": "elem_001",
      "type": "text",
      "bbox": [100, 200, 500, 250],
      "text": "识别的文本内容",
      "confidence": 0.98,
      "reading_order": 1
    }
  ]
}
```

### Markdown格式 - 可读性文档
```markdown
# 文档标题

## 1. 章节标题

这里是识别的文本内容...

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |

$$E = mc^2$$
```

### HTML格式 - 网页显示
包含样式和交互的完整HTML文档，支持置信度可视化。

### 结构化格式 - 全格式输出
同时包含JSON、Markdown和HTML格式的完整结果。

## ⚙️ 配置选项

### 环境变量

```bash
# 模型路径
export MODEL_PATH="./hf_model"

# 计算设备
export DEVICE="cuda"  # 或 "cpu"

# Redis连接
export REDIS_URL="redis://localhost:6379/0"

# 日志级别
export LOG_LEVEL="INFO"
```

### 处理参数

- `max_batch_size`: 批处理大小 (1-64)
- `output_format`: 输出格式 (json/markdown/html/structured)
- `include_confidence`: 是否包含置信度
- `include_coordinates`: 是否包含坐标信息
- `include_images`: 是否包含提取的图像数据
- `merge_text_blocks`: 是否合并相邻文本块

## 🎯 性能优化

### GPU配置
```python
# 自动检测最佳设备
device = "cuda" if torch.cuda.is_available() else "cpu"

# 半精度推理 (节省显存)
model = model.half()

# 模型编译优化 (PyTorch 2.0+)
model = torch.compile(model)
```

### 批处理优化
- 小文档: batch_size = 16-32
- 大文档: batch_size = 4-8
- 内存受限: batch_size = 1-2

### 并发配置
```bash
# 单进程异步 (推荐)
python start_xdan_vision_server.py --workers 1

# 多进程 (CPU密集型)
python start_xdan_vision_server.py --workers 4
```

## 📈 监控和日志

### 健康检查
```bash
GET /health
```

### 性能指标
```bash
GET /api/metrics
```

### 支持的格式信息
```bash
GET /api/formats
```

## 🔧 开发和测试

### 运行测试客户端
```bash
python test_enhanced_client.py
```

### 开发模式启动
```bash
python start_xdan_vision_server.py --dev
```

### API测试
```bash
# 测试所有功能
python test_enhanced_client.py

# 只测试基础功能
curl "http://localhost:8000/health"
```

## 📋 项目结构

```
xDAN-smartDoc-dolphin/
├── src/
│   ├── api/
│   │   └── enhanced_main.py          # 主API应用
│   ├── core/                         # 核心配置
│   ├── utils/                        # 工具函数
│   └── models/                       # 数据模型
├── start_xdan_vision_server.py       # 启动脚本
├── test_enhanced_client.py           # 测试客户端
├── demo_page_hf.py                   # 页面级处理示例
├── demo_element_hf.py                # 元素级处理示例
└── README_xDAN_Vision.md             # 本文档
```

## 🤝 支持和贡献

### 问题反馈
- GitHub Issues: [项目地址]
- 技术支持: xDAN团队

### 贡献指南
1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 发起 Pull Request

---

**xDAN-Vision-SmartDoc** - 让文档智能识别更简单高效！ 🚀 