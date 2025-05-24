# xDAN-Vision-SmartDoc 快速开始指南

## 🚀 5分钟快速上手

### 1. 启动服务 (1分钟)

```bash
# 基础启动
python start_xdan_vision_server.py

# 或指定端口
python start_xdan_vision_server.py --port 8001
```

### 2. 选择使用方式 (30秒)

#### 🌐 方式A: 网页版界面 (推荐新手)
```
访问: http://localhost:8000/web
- 📱 拖拽上传文件
- ⚙️ 可视化参数设置
- 📊 实时结果展示
- 📥 一键下载结果
```

#### 💻 方式B: API调用 (程序员)
```bash
# 健康检查
curl http://localhost:8000/health

# 文档处理
curl -X POST "http://localhost:8000/api/process/document" \
  -F "file=@document.png" \
  -F "output_format=json"
```

### 3. 网页版使用流程

1. **📁 上传文件**: 点击或拖拽图像到上传区域
2. **⚙️ 设置参数**: 选择输出格式和处理选项
3. **🚀 开始识别**: 点击"开始智能识别"按钮
4. **📊 查看结果**: 在结果区域查看识别元素、Markdown、HTML和JSON格式
5. **📥 下载结果**: 点击下载按钮保存各种格式的结果

### 4. Python代码示例

```python
import requests

# 处理文档
with open("document.png", "rb") as f:
    files = {"file": f}
    data = {"output_format": "structured"}
    response = requests.post(
        "http://localhost:8000/api/process/document",
        files=files, 
        data=data
    )

result = response.json()
print(f"识别到 {result['total_elements']} 个元素")
```

## 🌐 访问地址

| 功能 | 地址 | 描述 |
|------|------|------|
| 网页版界面 | http://localhost:8000/web | 可视化操作界面 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| ReDoc文档 | http://localhost:8000/redoc | 美观的API文档 |
| 健康检查 | http://localhost:8000/health | 服务状态 |

## 📊 输出格式选择

| 格式 | 用途 | 示例 |
|------|------|------|
| `json` | 程序处理 | `{"elements": [...]}` |
| `markdown` | 文档编辑 | `# 标题\n\n内容...` |
| `html` | 网页显示 | `<h1>标题</h1>` |
| `structured` | 全格式 | 包含以上所有格式 |

## ⚙️ 常用参数

```bash
curl -X POST "http://localhost:8000/api/process/document" \
  -F "file=@document.png" \
  -F "output_format=structured" \
  -F "max_batch_size=16" \
  -F "include_confidence=true"
```

## 🔧 性能调优

- **小文档**: `max_batch_size=32`
- **大文档**: `max_batch_size=8` 
- **高精度**: `max_batch_size=4`
- **快速扫描**: `max_batch_size=64`

## 📚 更多资源

- **完整文档**: [API_USAGE_GUIDE.md](API_USAGE_GUIDE.md)
- **代码示例**: [example_api_calls.py](example_api_calls.py)
- **网页版界面**: http://localhost:8000/web
- **API文档**: http://localhost:8000/docs
- **系统架构**: [VISION_ANALYSIS.md](VISION_ANALYSIS.md)

## ❓ 常见问题

**Q: 服务启动失败？**
A: 检查Python环境和依赖: `pip install torch transformers fastapi[all]`

**Q: 网页版无法访问？**
A: 确保服务正常启动，检查端口是否被占用

**Q: 处理速度慢？**
A: 调整批处理大小或使用GPU: `DEVICE=cuda`

**Q: 识别准确率低？**
A: 确保图像清晰，分辨率≥300DPI

---

🎉 **恭喜！您已经掌握了xDAN-Vision-SmartDoc的基本使用方法！** 