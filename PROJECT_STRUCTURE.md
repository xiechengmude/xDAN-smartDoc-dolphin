# 📁 xDAN-Vision-SmartDoc 项目结构

## 🗂️ 整理后的目录结构

```
xDAN-smartDoc-dolphin/
├── 📄 README.md                     # 项目主文档 (统一入口)
├── ⚡ QUICK_START.md                # 快速开始指南
├── 🚀 start_xdan_vision_server.py   # 主启动脚本
├── 💬 chat.py                       # 交互式聊天界面
├── 📦 pyproject.toml                # 项目配置和依赖
├── 📋 requirements.txt              # 依赖清单
├── ⚖️ LICENSE                       # 许可证
├── 🔧 .gitignore                    # Git忽略文件
├── 🪝 .pre-commit-config.yaml       # 代码检查配置
│
├── 🎯 demo_*.py                     # 原始Dolphin演示脚本 (保持不变)
│   ├── demo_page_hf.py              # 页面级处理 (HF版本)
│   ├── demo_element_hf.py           # 元素级处理 (HF版本)
│   ├── demo_page.py                 # 页面级处理 (原版)
│   └── demo_element.py              # 元素级处理 (原版)
│
├── 📂 src/                          # 核心源代码
│   ├── api/                         # API服务模块
│   │   └── enhanced_main.py         # 主API应用
│   ├── core/                        # 核心配置
│   ├── engines/                     # 处理引擎
│   ├── utils/                       # 工具函数
│   └── web/                         # Web界面
│
├── 📚 docs/                         # 技术文档目录
│   ├── API_USAGE_GUIDE.md           # API使用指南
│   ├── DEPLOYMENT_GUIDE.md          # 部署指南
│   ├── VISION_ANALYSIS.md           # 视觉分析文档
│   ├── README_ARCHITECTURE.md       # 系统架构说明
│   └── CONVERSION_SUMMARY.md        # 转换总结
│
├── 🧪 tests/                        # 测试文件目录
│   ├── test_enhanced_client.py      # 完整API测试客户端
│   └── test_client.py               # 基础测试客户端
│
├── 📘 examples/                     # 示例代码目录
│   └── example_api_calls.py         # API调用示例
│
├── 🛠️ scripts/                      # 工具脚本
├── ⚙️ config/                       # 配置文件
├── 🖼️ assets/                       # 资源文件
├── 📂 demo/                         # 演示数据
└── 🔧 utils/                        # 工具模块
```

## 📋 整理说明

### ✅ 已完成的整理

1. **📁 目录分类**
   - `docs/` - 所有技术文档集中管理
   - `tests/` - 测试文件统一存放
   - `examples/` - 示例代码独立目录

2. **📄 文档合并**
   - 合并 `README_xDAN_Vision.md` 和 `README_SIMPLE.md` 到主 `README.md`
   - 保留核心技术文档在 `docs/` 目录

3. **🗑️ 清理重复**
   - 删除重复的 `start_server.py` 启动脚本
   - 删除重复的README文件

4. **🎯 保留原始**
   - 完整保留所有 `demo_*.py` 原始Dolphin脚本
   - 保持其功能和接口不变

### 📖 文档层次

#### 🏠 主入口文档
- `README.md` - 项目概览、快速开始、使用示例
- `QUICK_START.md` - 5分钟快速开始指南

#### 📚 技术文档 (docs/)
- `API_USAGE_GUIDE.md` - 完整API使用说明
- `DEPLOYMENT_GUIDE.md` - 部署和运维指南
- `VISION_ANALYSIS.md` - 视觉识别能力分析
- `README_ARCHITECTURE.md` - 系统架构设计
- `CONVERSION_SUMMARY.md` - 项目转换总结

#### 🧪 测试和示例
- `tests/` - 各种测试客户端
- `examples/` - API调用示例代码

## 🚀 使用指南

### 📚 文档阅读顺序

1. **新用户**: `README.md` → `QUICK_START.md`
2. **开发者**: `docs/API_USAGE_GUIDE.md` → `docs/README_ARCHITECTURE.md`
3. **运维人员**: `docs/DEPLOYMENT_GUIDE.md`
4. **研究人员**: `docs/VISION_ANALYSIS.md`

### 🎯 脚本使用

```bash
# 新版企业级API服务
python start_xdan_vision_server.py

# 原始Dolphin演示脚本
python demo_page_hf.py --input_path document.png
python demo_element_hf.py --input_path element.png --element_type text

# 交互式聊天
python chat.py --model_path ./hf_model

# 测试客户端
python tests/test_enhanced_client.py
python examples/example_api_calls.py
```

## 🎯 设计原则

1. **🔄 向后兼容** - 保留所有原始demo脚本
2. **📁 清晰分类** - 文档、测试、示例分离
3. **📚 统一入口** - 主README作为项目门户
4. **🧹 避免重复** - 删除冗余文件
5. **📖 易于导航** - 清晰的文档层次结构

---

**整理完成！** 现在项目结构更加清晰、易于维护和使用。 ✨ 