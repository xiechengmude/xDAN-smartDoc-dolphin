# xDAN-Vision-SmartDoc 部署指南

## 📋 部署概览

xDAN-Vision-SmartDoc 是基于xDAN 高性能多模态模型xDAN-Vision-SmartDoc的高性能异步智能文档识别系统，支持多种部署方式。本文档将指导您完成从开发环境到生产环境的完整部署流程。

## 🏗️ 系统架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Interface │    │   FastAPI Server │    │   xDAN Engine   │
│   (静态文件)     │◄──►│   (API 端点)     │◄──►│   (AI 模型)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Redis Cache    │
                       │   (可选缓存)     │
                       └──────────────────┘
```

## 🔧 环境要求

### 最低配置
- **CPU**: 4核以上
- **内存**: 8GB以上 
- **存储**: 50GB以上
- **Python**: 3.8+ 
- **操作系统**: Linux/macOS/Windows

### 推荐配置  
- **CPU**: 8核以上
- **内存**: 32GB以上
- **GPU**: NVIDIA GPU (8GB+ VRAM)
- **存储**: 200GB+ SSD
- **网络**: 稳定网络连接

### 依赖组件
- **必需**: PyTorch, Transformers, FastAPI, OpenCV, Pillow
- **可选**: Redis (缓存), NGINX (反向代理)

## 🚀 部署方式

### 1. 本地开发环境

#### 1.1 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/xDAN-AI/xDAN-smartDoc-dolphin.git
cd xDAN-smartDoc-dolphin

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 下载模型 (示例)
# 将 Dolphin 模型放置到 ./hf_model 目录

# 5. 启动服务
python start_xdan_vision_server.py
```

#### 1.2 环境变量配置

```bash
# .env 文件
MODEL_PATH=./hf_model
DEVICE=cuda                    # 或 cpu
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379/0
HOST=0.0.0.0
PORT=8000
```

#### 1.3 开发模式启动

```bash
# 开发模式 (自动重载)
python start_xdan_vision_server.py --dev

# 指定配置
python start_xdan_vision_server.py \
  --host 0.0.0.0 \
  --port 8000 \
  --model-path ./hf_model \
  --log-level debug
```

### 2. 生产环境部署

#### 2.1 使用 Gunicorn + Uvicorn

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动生产服务器
gunicorn src.api.enhanced_main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300 \
  --keep-alive 2 \
  --max-requests 1000 \
  --preload
```

#### 2.2 系统服务配置

创建 systemd 服务文件：

```bash
sudo nano /etc/systemd/system/xdan-vision.service
```

```ini
[Unit]
Description=xDAN-Vision-SmartDoc API Server
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/xdan-vision-smartdoc
Environment=PATH=/opt/xdan-vision-smartdoc/venv/bin
Environment=MODEL_PATH=/opt/xdan-vision-smartdoc/hf_model
Environment=DEVICE=cuda
Environment=LOG_LEVEL=INFO
ExecStart=/opt/xdan-vision-smartdoc/venv/bin/gunicorn src.api.enhanced_main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable xdan-vision
sudo systemctl start xdan-vision
sudo systemctl status xdan-vision
```

#### 2.3 NGINX 反向代理

```nginx
# /etc/nginx/sites-available/xdan-vision
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # 静态文件缓存
    location /static/ {
        alias /opt/xdan-vision-smartdoc/src/web/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/xdan-vision /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Docker 部署

#### 3.1 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建模型目录
RUN mkdir -p hf_model

# 设置环境变量
ENV MODEL_PATH=/app/hf_model
ENV DEVICE=cpu
ENV HOST=0.0.0.0
ENV PORT=8000

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "start_xdan_vision_server.py", "--host", "0.0.0.0", "--port", "8000"]
```

#### 3.2 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  xdan-vision:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./hf_model:/app/hf_model:ro
      - ./logs:/app/logs
    environment:
      - MODEL_PATH=/app/hf_model
      - DEVICE=cuda
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - xdan-vision
    restart: unless-stopped

volumes:
  redis_data:
```

#### 3.3 构建和运行

```bash
# 构建镜像
docker build -t xdan-vision-smartdoc .

# 运行容器
docker run -d \
  --name xdan-vision \
  --gpus all \
  -p 8000:8000 \
  -v $(pwd)/hf_model:/app/hf_model:ro \
  xdan-vision-smartdoc

# 使用 Docker Compose
docker-compose up -d

# 查看日志
docker-compose logs -f xdan-vision
```

### 4. 云平台部署

#### 4.1 AWS 部署

```bash
# 使用 EC2 + ELB + AutoScaling
# 1. 创建 AMI 镜像
# 2. 配置 Launch Template
# 3. 设置 Auto Scaling Group
# 4. 配置 Application Load Balancer

# 使用 ECS
aws ecs create-cluster --cluster-name xdan-vision-cluster

# 使用 EKS (Kubernetes)
kubectl apply -f k8s/
```

#### 4.2 Azure 部署

```bash
# 使用 Container Instances
az container create \
  --resource-group myResourceGroup \
  --name xdan-vision \
  --image xdan-vision-smartdoc \
  --cpu 4 --memory 16 \
  --ports 8000

# 使用 App Service
az webapp create \
  --resource-group myResourceGroup \
  --plan myAppServicePlan \
  --name xdan-vision-app \
  --deployment-container-image-name xdan-vision-smartdoc
```

#### 4.3 Google Cloud 部署

```bash
# 使用 Cloud Run
gcloud run deploy xdan-vision \
  --image gcr.io/project-id/xdan-vision-smartdoc \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# 使用 GKE
kubectl apply -f gcp-k8s/
```

## 📊 性能优化

### 1. 硬件优化

```bash
# GPU 配置
export CUDA_VISIBLE_DEVICES=0,1  # 指定GPU
export CUDA_LAUNCH_BLOCKING=1     # 调试模式

# CPU 优化
export OMP_NUM_THREADS=8          # OpenMP线程数
export MKL_NUM_THREADS=8          # Intel MKL线程数
```

### 2. 模型优化

```python
# 模型配置优化
MODEL_PRECISION=half              # 半精度推理
MODEL_DEVICE=cuda                 # GPU设备
MAX_BATCH_SIZE=32                 # 批处理大小
MAX_SEQUENCE_LENGTH=4096          # 序列长度
```

### 3. 系统调优

```bash
# 系统参数调优
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'fs.file-max=65536' >> /etc/sysctl.conf
echo 'net.core.rmem_max=134217728' >> /etc/sysctl.conf

# 进程限制
ulimit -n 65536
ulimit -u 32768
```

## 🔒 安全配置

### 1. 防火墙设置

```bash
# UFW 配置
sudo ufw allow 22/tcp          # SSH
sudo ufw allow 80/tcp          # HTTP
sudo ufw allow 443/tcp         # HTTPS
sudo ufw enable
```

### 2. SSL/TLS 配置

```bash
# Let's Encrypt 证书
sudo certbot --nginx -d your-domain.com

# 手动证书配置
sudo mkdir -p /etc/nginx/ssl
sudo cp your-cert.pem /etc/nginx/ssl/
sudo cp your-key.pem /etc/nginx/ssl/
```

### 3. API 安全

```python
# API 密钥认证
API_KEY_HEADER=X-API-Key
API_KEYS=key1,key2,key3

# 速率限制
RATE_LIMIT=100/minute
```

## 📈 监控和日志

### 1. 日志配置

```python
# 日志设置
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/xdan-vision/app.log
```

### 2. 监控指标

```bash
# Prometheus 监控
/metrics                        # 应用指标
/health                         # 健康检查

# 关键指标
- 请求处理时间
- GPU 使用率  
- 内存使用量
- 错误率
- 吞吐量
```

### 3. 告警配置

```yaml
# Alertmanager 规则
groups:
  - name: xdan-vision
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
```

## 🔧 故障排除

### 1. 常见问题

#### 问题：模型加载失败
```bash
# 检查模型文件
ls -la hf_model/
# 检查权限
chmod -R 755 hf_model/
# 检查磁盘空间
df -h
```

#### 问题：GPU 内存不足
```bash
# 查看GPU使用情况
nvidia-smi
# 减少批处理大小
export MAX_BATCH_SIZE=8
# 使用梯度检查点
export GRADIENT_CHECKPOINTING=true
```

#### 问题：服务启动失败
```bash
# 检查端口占用
sudo netstat -tlnp | grep 8000
# 检查服务状态
sudo systemctl status xdan-vision
# 查看详细日志
journalctl -u xdan-vision -f
```

### 2. 性能问题

#### 处理速度慢
```bash
# 检查资源使用
top -p $(pgrep -f xdan-vision)
# 调整worker数量
gunicorn --workers 8 ...
# 启用GPU加速
export DEVICE=cuda
```

#### 内存泄漏
```bash
# 监控内存使用
watch -n 1 'free -h'
# 设置内存限制
docker run --memory="16g" ...
# 定期重启服务
sudo systemctl restart xdan-vision
```

## 📞 技术支持

### 获取帮助

- **GitHub Issues**: [项目地址]
- **文档**: [在线文档地址]
- **社区**: [社区论坛地址]

### 日志收集

```bash
# 收集系统信息
sudo dmesg > system.log
sudo journalctl -u xdan-vision > service.log
docker logs xdan-vision > container.log

# 性能诊断
top -b -n 1 > performance.log
nvidia-smi > gpu.log
free -h > memory.log
```

---

**xDAN-Vision-SmartDoc 部署指南** - 让智能文档识别轻松上线！ 🚀 