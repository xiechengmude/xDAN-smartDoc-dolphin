# 🔬 xDAN-Vision-SmartDoc API Server
> 基于xDAN 高性能多模态模型的高性能异步智能文档识别系统

## 🚀 快速开始

### 1. 环境准备

```bash
# 使用uv创建环境
uv venv xdan-smartdoc-dolphin
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -e .
```

### 2. 下载模型

```bash
# 下载Dolphin模型
git lfs install
git clone https://huggingface.co/ByteDance/Dolphin ./hf_model
```

### 3. 配置环境

```bash
# 复制环境配置
cp .env.example .env

# 编辑配置（可选）
nano .env
```

### 4. 启动Redis（可选，用于结果缓存）

```bash
# 使用Docker启动Redis
docker run -d --name smartdoc-redis -p 6379:6379 redis:latest

# 或者使用系统安装的Redis
redis-server
```

### 5. 启动服务

```bash
# 启动API服务器
python start_server.py

# 或者直接使用uvicorn
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. 测试API

```bash
# 测试客户端
python test_client.py

# 或者访问API文档
# http://localhost:8000/docs
```

## 📋 API接口

### 健康检查
```bash
GET /health
```

### 页面级文档处理
```bash
POST /api/v1/process/page
Content-Type: multipart/form-data

file: <图像文件>
max_batch_size: 16  # 可选，批处理大小
```

### 元素级处理
```bash
POST /api/v1/process/element
Content-Type: multipart/form-data

file: <图像文件>
element_type: text  # text, table, formula
```

### 获取结果（需要Redis）
```bash
GET /api/v1/result/{task_id}
```

## 🔧 核心特性

### ✅ 已实现功能
- **异步处理**: 基于FastAPI和asyncio的高性能异步处理
- **批量处理**: 支持元素级批量处理，提升GPU利用率
- **模型优化**: 支持半精度推理，减少显存占用
- **结果缓存**: 使用Redis缓存处理结果
- **错误处理**: 完善的异常处理和日志记录

### 📦 系统架构

```
SmartDoc Dolphin API
├── 异步FastAPI服务器
├── AsyncDolphinEngine (基于demo代码改造)
├── Redis缓存 (可选)
└── 结构化日志
```

### 🎯 性能优化

1. **异步I/O**: 使用asyncio避免阻塞
2. **线程池**: 模型推理在线程池中执行
3. **批处理**: 元素级批量处理
4. **内存管理**: 自动GPU内存清理
5. **连接池**: Redis连接复用

## 📊 API使用示例

### Python客户端

```python
import httpx
from pathlib import Path

async def process_document(image_path: str):
    async with httpx.AsyncClient() as client:
        with open(image_path, "rb") as f:
            files = {"file": (Path(image_path).name, f, "image/png")}
            data = {"max_batch_size": 16}
            
            response = await client.post(
                "http://localhost:8000/api/v1/process/page",
                files=files,
                data=data
            )
            
        return response.json()

# 使用示例
result = await process_document("./test.png")
print(f"找到 {result['result']['total_elements']} 个元素")
```

### cURL示例

```bash
# 页面处理
curl -X POST "http://localhost:8000/api/v1/process/page" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test.png" \
     -F "max_batch_size=16"

# 元素处理
curl -X POST "http://localhost:8000/api/v1/process/element" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@element.png" \
     -F "element_type=table"
```

## 🔨 开发工具

```bash
# 代码格式化
uv run black src/
uv run isort src/

# 类型检查
uv run mypy src/

# 代码检查
uv run ruff check src/
```

## ⚙️ 配置选项

主要配置项（`.env`文件）：

```bash
# 模型配置
MODEL_PATH=./hf_model
MODEL_DEVICE=cuda
MODEL_PRECISION=half
MAX_BATCH_SIZE=16

# API配置
API_HOST=0.0.0.0
API_PORT=8000

# Redis配置（可选）
REDIS_URL=redis://localhost:6379

# 日志配置
LOG_LEVEL=INFO
```

## 🚀 部署选项

### Docker部署

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv pip install -e .
CMD ["python", "start_server.py"]
```

### 生产环境

```bash
# 使用gunicorn + uvicorn worker
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📈 性能基准

- **并发处理**: 10-50个并发请求
- **处理速度**: 单页文档 2-8秒
- **内存使用**: 2-6GB GPU显存
- **吞吐量**: 500-1000页/小时

## 🤝 与原demo的对比

| 特性 | 原demo | 简化版API |
|------|--------|----------|
| 处理方式 | 同步批处理 | 异步单请求/批处理 |
| 接口类型 | 命令行 | REST API |
| 并发支持 | 无 | 多请求并发 |
| 结果存储 | 文件 | 内存+Redis缓存 |
| 错误处理 | 基础 | 完善的异常处理 |
| 监控 | 无 | 结构化日志 |

## 🛠️ 故障排除

### 常见问题

1. **模型加载失败**
   ```bash
   # 检查模型路径
   ls -la ./hf_model/
   ```

2. **CUDA内存不足**
   ```bash
   # 减少批处理大小
   export MAX_BATCH_SIZE=8
   ```

3. **Redis连接失败**
   ```bash
   # 检查Redis状态
   redis-cli ping
   ```

## 📝 更新日志

### v1.0.0
- ✅ 基于demo代码的异步API实现
- ✅ 支持页面级和元素级处理
- ✅ Redis缓存集成
- ✅ 完善的错误处理和日志

---

**项目地址**: [GitHub Repository](https://github.com/yourusername/xDAN-smartDoc-dolphin)

**API文档**: http://localhost:8000/docs 