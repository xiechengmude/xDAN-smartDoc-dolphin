# 🔬 xDAN-Vision-SmartDoc 智能文档识别系统

**基于xDAN 高性能多模态模型的智能文档识别与解析系统**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)

## ✨ 核心功能

- 📝 **OCR文本识别**: 高精度多语言文本识别
- 📊 **表格解析**: 结构化表格识别与格式化
- 🖼️ **图表分析**: 智能图表理解与描述
- 🧮 **公式识别**: LaTeX格式数学公式识别
- 🎨 **多格式输出**: JSON/Markdown/HTML/结构化输出
- ⚡ **异步处理**: 高并发批量处理
- 🌐 **Web界面**: 可视化文档处理界面

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- CUDA (可选，用于GPU加速)
- 内存: 8GB+ (推荐16GB+)
- GPU显存: 4GB+ (推荐8GB+)

### 2. 安装依赖

```bash
# 克隆项目
git clone https://github.com/xDAN-AI/xDAN-smartDoc-dolphin.git
cd xDAN-smartDoc-dolphin

# 使用uv创建环境 (推荐)
uv venv xdan-smartdoc
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -e .

# 或使用pip
pip install -r requirements.txt
```

### 3. 下载模型

```bash
# 下载Dolphin模型
git lfs install
git clone https://huggingface.co/ByteDance/Dolphin ./hf_model
```

### 4. 启动服务

```bash
# 基本启动
python start_xdan_vision_server.py

# 指定配置
python start_xdan_vision_server.py --port 8001 --model-path ./hf_model

# 开发模式 (自动重载)
python start_xdan_vision_server.py --dev

# 多进程启动
python start_xdan_vision_server.py --workers 4
```

### 5. 访问服务

- **Web界面**: http://localhost:8000/web
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📖 使用示例

### Web界面使用

1. 访问 http://localhost:8000/web
2. 拖拽或点击上传文档图片
3. 选择输出格式和处理参数
4. 点击"开始智能识别"
5. 查看识别结果并下载

### API调用示例

#### Python客户端

```python
import httpx
import asyncio

async def process_document():
    async with httpx.AsyncClient() as client:
        # 上传文档
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

asyncio.run(process_document())
```

#### cURL调用

```bash
# 处理文档
curl -X POST "http://localhost:8000/api/process/document" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@document.png" \
     -F "output_format=structured" \
     -F "max_batch_size=16"

# 健康检查
curl "http://localhost:8000/health"
```

## 📊 输出格式

### JSON格式 - 程序处理
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

### Markdown格式 - 可读文档
```markdown
# 文档标题

## 章节内容

识别的文本内容...

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |

$$E = mc^2$$
```

### HTML格式 - 网页显示
完整的HTML文档，支持样式和置信度可视化。

### 结构化格式 - 全格式输出
同时包含JSON、Markdown和HTML格式的完整结果。

## ⚙️ 配置选项

### 环境变量

```bash
# 模型配置
export MODEL_PATH="./hf_model"
export DEVICE="cuda"  # 或 "cpu"

# Redis缓存 (可选)
export REDIS_URL="redis://localhost:6379/0"

# 日志级别
export LOG_LEVEL="INFO"
```

### 处理参数

- `max_batch_size`: 批处理大小 (1-64)，影响处理速度
- `output_format`: 输出格式 (json/markdown/html/structured)
- `include_confidence`: 是否包含置信度
- `include_coordinates`: 是否包含坐标信息
- `merge_text_blocks`: 是否合并相邻文本块

## 🎯 性能优化建议

### 批处理大小选择
- **小文档**: batch_size = 32 (快速处理)
- **大文档**: batch_size = 8 (高精度)
- **内存受限**: batch_size = 4 (节省显存)

### GPU配置
```bash
# 指定GPU设备
export CUDA_VISIBLE_DEVICES=0

# 启用GPU加速
export DEVICE=cuda
```

## 📁 项目结构

```
xDAN-smartDoc-dolphin/
├── demo_*.py                    # 原始演示脚本
├── start_xdan_vision_server.py  # 主启动脚本
├── chat.py                      # 聊天界面脚本
├── src/                         # 核心源码
│   ├── api/                     # API服务
│   ├── core/                    # 核心配置
│   ├── engines/                 # 处理引擎
│   ├── utils/                   # 工具函数
│   └── web/                     # Web界面
├── docs/                        # 技术文档
│   ├── API_USAGE_GUIDE.md       # API使用指南
│   ├── DEPLOYMENT_GUIDE.md      # 部署指南
│   ├── VISION_ANALYSIS.md       # 视觉分析文档
│   └── README_ARCHITECTURE.md   # 架构说明
├── tests/                       # 测试文件
├── examples/                    # 示例代码
└── scripts/                     # 工具脚本
```

## 🔧 原始Demo脚本

项目保留了原始的Dolphin demo脚本，可以直接使用：

```bash
# 页面级文档处理
python demo_page_hf.py --input_path document.png --model_path ./hf_model

# 元素级处理
python demo_element_hf.py --input_path element.png --element_type text

# 交互式聊天
python chat.py --model_path ./hf_model
```

## 📚 文档链接

- 📖 [API使用指南](docs/API_USAGE_GUIDE.md)
- 🚀 [部署指南](docs/DEPLOYMENT_GUIDE.md)
- 🏗️ [系统架构](docs/README_ARCHITECTURE.md)
- 🔍 [视觉分析](docs/VISION_ANALYSIS.md)
- ⚡ [快速开始](QUICK_START.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发环境设置

```bash
# 安装开发依赖
uv pip install -e ".[dev]"

# 代码格式化
black src/
isort src/

# 类型检查
mypy src/

# 运行测试
pytest tests/
```

## 📄 许可证

本项目使用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🏷️ 版本历史

- **v2.0.0** - xDAN重构版本，企业级API服务
- **v1.0.0** - 基于Dolphin的基础版本

---

**xDAN-Vision-SmartDoc** - 让智能文档识别更简单高效！ 🚀
