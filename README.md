# 人脸识别API服务

基于 [InsightFace](https://github.com/deepinsight/insightface) 实现的高性能、高可用人脸识别对比服务。

## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [API文档](#api文档)
- [配置说明](#配置说明)
- [性能优化](#性能优化)
- [部署方案](#部署方案)
- [测试](#测试)

## ✨ 功能特性

- ✅ **人脸对比**: 比较两张图片是否为同一个人
- ✅ **高精度**: 基于InsightFace的ArcFace算法，识别准确率高
- ✅ **高性能**: 异步处理 + 线程池优化，支持高并发
- ✅ **自动检测**: 自动检测图片中的人脸，支持多人脸场景
- ✅ **相似度评分**: 返回0-1之间的相似度分数和置信度等级
- ✅ **RESTful API**: 标准的HTTP接口，易于集成
- ✅ **完整文档**: 自动生成的API文档（Swagger UI）
- ✅ **健康检查**: 提供健康检查和监控指标接口
- ✅ **Docker支持**: 提供完整的Docker部署方案
- ✅ **生产就绪**: 包含错误处理、日志、监控等生产环境必备功能

## 🛠 技术栈

- **Web框架**: FastAPI（高性能异步框架）
- **人脸识别**: InsightFace（CVPR 2019 ArcFace算法）
- **深度学习**: ONNX Runtime（高效推理）
- **图像处理**: OpenCV + NumPy
- **容器化**: Docker + Docker Compose
- **负载均衡**: Nginx（可选）
- **监控**: Prometheus metrics

## 🚀 快速开始

### 方式一：本地运行

#### 1. 安装依赖

```bash
# 克隆项目
cd face_recognition_api

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置（可选）

所有配置都在 `config.py` 文件中，可以直接修改。如果需要通过环境变量覆盖配置，可以在系统环境变量中设置（不需要创建 .env 文件）。

#### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。

### 方式二：Docker运行

#### 使用 Docker Compose（推荐）

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 直接使用 Docker 命令

```bash
# 构建镜像
docker build -t face-recognition-api:latest .

# 运行容器
docker run -d \
  --name face_recognition_api \
  -p 8000:8000 \
  -v $(pwd)/models:/root/.insightface/models \
  --restart unless-stopped \
  face-recognition-api:latest

# 查看日志
docker logs -f face_recognition_api

# 停止容器
docker stop face_recognition_api

# 删除容器
docker rm face_recognition_api
```

**注意**: 首次运行会自动下载模型文件（约500MB），请确保网络连接正常。

## 📚 API文档

### 访问交互式文档

启动服务后，访问以下地址查看完整的API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 核心接口

#### 1. 人脸对比

**接口**: `POST /compare_faces`

**描述**: 比较两张人脸图片是否为同一个人

**请求参数**:
- `image1`: 第一张图片的base64编码字符串（JSON格式）
- `image2`: 第二张图片的base64编码字符串（JSON格式）

**支持格式**: JPG, JPEG, PNG, WEBP

**文件大小限制**: 最大 10MB（base64编码前）

**响应示例**:

```json
{
  "is_same_person": true,
  "similarity": 0.8523,
  "confidence": "高",
  "face1_detected": true,
  "face2_detected": true,
  "message": "两张图片是同一个人（相似度: 85.23%）",
  "processing_time": 245.67
}
```

**字段说明**:
- `is_same_person`: 是否为同一个人（boolean）
- `similarity`: 相似度分数，0-1之间（float）
- `confidence`: 置信度等级：高/中/低（string）
- `face1_detected`: 图片1是否检测到人脸（boolean）
- `face2_detected`: 图片2是否检测到人脸（boolean）
- `message`: 详细说明（string）
- `processing_time`: 处理时间，单位毫秒（float）

#### 2. 健康检查

**接口**: `GET /health`

**响应示例**:

```json
{
  "status": "healthy",
  "service": "人脸识别API",
  "version": "1.0.0",
  "model_loaded": true,
  "model_name": "buffalo_l"
}
```

#### 3. 服务信息

**接口**: `GET /info`

**响应示例**:

```json
{
  "model": "buffalo_l",
  "detection_size": [640, 640],
  "similarity_threshold": 0.65,
  "max_file_size_mb": 10,
  "supported_formats": [".jpg", ".jpeg", ".png", ".webp"],
  "thread_pool_workers": 8
}
```

#### 4. 监控指标

**接口**: `GET /metrics`

**描述**: Prometheus格式的监控指标

### 使用示例

#### cURL

```bash
# 将图片转换为base64（示例）
IMAGE1_BASE64=$(base64 -w 0 person1.jpg)
IMAGE2_BASE64=$(base64 -w 0 person2.jpg)

curl -X POST "http://localhost:8000/compare_faces" \
  -H "Content-Type: application/json" \
  -d "{
    \"image1\": \"$IMAGE1_BASE64\",
    \"image2\": \"$IMAGE2_BASE64\"
  }"
```

#### Python

```python
import requests
import base64

# 读取图片并转换为base64
with open('person1.jpg', 'rb') as f:
    image1_base64 = base64.b64encode(f.read()).decode('utf-8')

with open('person2.jpg', 'rb') as f:
    image2_base64 = base64.b64encode(f.read()).decode('utf-8')

# 发送请求
response = requests.post(
    'http://localhost:8000/compare_faces',
    json={
        'image1': image1_base64,
        'image2': image2_base64
    }
)

result = response.json()
print(f"是否同一人: {result['is_same_person']}")
print(f"相似度: {result['similarity']:.2%}")
```

#### JavaScript (Node.js)

```javascript
const fs = require('fs');
const axios = require('axios');

// 读取图片并转换为base64
const image1 = fs.readFileSync('person1.jpg').toString('base64');
const image2 = fs.readFileSync('person2.jpg').toString('base64');

// 发送请求
axios.post('http://localhost:8000/compare_faces', {
  image1: image1,
  image2: image2
})
.then(response => {
  console.log('结果:', response.data);
})
.catch(error => {
  console.error('错误:', error.response.data);
});
```

## ⚙️ 配置说明

### 配置说明

主要配置项（在 `config.py` 文件中设置，也可通过环境变量覆盖）：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `HOST` | 服务监听地址 | `0.0.0.0` |
| `PORT` | 服务监听端口 | `8000` |
| `MODEL_NAME` | InsightFace模型名称 | `buffalo_l` |
| `SIMILARITY_THRESHOLD` | 判断同一人的相似度阈值 | `0.65` |
| `THREAD_POOL_WORKERS` | 线程池大小 | `8` |
| `MAX_FILE_SIZE` | 最大文件大小（字节） | `10485760` (10MB) |
| `PROVIDER` | 推理引擎 | `CPUExecutionProvider` |

### 相似度阈值说明

- **阈值 0.65**: 默认值，平衡准确率和召回率
- **阈值 0.70**: 更严格，减少误识别
- **阈值 0.60**: 更宽松，提高召回率

建议根据实际业务场景调整阈值。

### GPU加速

如果有NVIDIA GPU，可以启用GPU加速：

1. 安装 `onnxruntime-gpu`：
```bash
pip uninstall onnxruntime
pip install onnxruntime-gpu
```

2. 修改 `config.py` 配置或设置环境变量：
```python
# 在 config.py 中修改
PROVIDER: str = "CUDAExecutionProvider"

# 或通过环境变量
export PROVIDER=CUDAExecutionProvider
```

## 🚄 性能优化

### 已实现的优化

1. **异步处理**: 使用 FastAPI 的异步特性，提高并发能力
2. **线程池**: CPU密集型任务在线程池中执行，避免阻塞
3. **模型缓存**: 模型只加载一次，常驻内存
4. **响应压缩**: GZIP压缩减少网络传输
5. **批量处理**: 支持高并发请求

### 性能指标

在标准配置下（Intel i7, 16GB RAM）：

- **单次请求延迟**: 200-400ms
- **吞吐量**: 约 20-30 QPS（单进程）
- **内存占用**: ~1.5GB

### 进一步优化建议

1. **多进程部署**: 使用 Gunicorn + Uvicorn workers
2. **负载均衡**: 使用 Nginx 进行负载均衡
3. **缓存策略**: 对相同图片对比结果进行缓存
4. **GPU加速**: 使用GPU可提升3-5倍性能
5. **模型优化**: 使用更小的模型如 `buffalo_s` 可提升速度

## 🏗 部署方案

### 单机部署

适合小规模应用：

```bash
# 使用 Docker Compose
docker-compose up -d
```

### 多实例部署（高可用）

1. **启动多个服务实例**:

```bash
# 修改 docker-compose.yml，添加多个实例
docker-compose up -d --scale face-recognition-api=3
```

2. **配置 Nginx 负载均衡**:

取消注释 `docker-compose.yml` 中的 nginx 配置

3. **启动完整服务栈**:

```bash
docker-compose up -d
```

### 生产环境部署建议

1. **使用反向代理**: Nginx / Caddy
2. **HTTPS加密**: 配置SSL证书
3. **限流保护**: 使用 rate limiting
4. **监控告警**: 集成 Prometheus + Grafana
5. **日志收集**: ELK / Loki
6. **健康检查**: 配置自动重启
7. **资源限制**: 设置合理的CPU/内存限制

### Kubernetes部署

可以将服务部署到K8s集群，实现自动扩缩容：

```yaml
# 示例 deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: face-recognition-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: face-recognition-api
  template:
    metadata:
      labels:
        app: face-recognition-api
    spec:
      containers:
      - name: api
        image: face-recognition-api:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: "2"
            memory: "2Gi"
          requests:
            cpu: "1"
            memory: "1Gi"
```

## 🧪 测试

### 运行测试脚本

```bash
python test_api.py
```

### 手动测试

1. **健康检查**:
```bash
curl http://localhost:8000/health
```

2. **人脸对比**:
```bash
# 将图片转换为base64后发送请求
IMAGE1=$(base64 -w 0 test_image1.jpg)
IMAGE2=$(base64 -w 0 test_image2.jpg)
curl -X POST "http://localhost:8000/compare_faces" \
  -H "Content-Type: application/json" \
  -d "{\"image1\": \"$IMAGE1\", \"image2\": \"$IMAGE2\"}"
```

### 性能测试

使用 Apache Bench 进行压力测试：

```bash
# 安装 ab
apt-get install apache2-utils  # Ubuntu/Debian
yum install httpd-tools         # CentOS/RHEL

# 准备JSON数据文件（包含base64编码的图片）
# 然后运行测试
ab -n 100 -c 10 -p post_data.json -T application/json http://localhost:8000/compare_faces
```

## 📊 监控

### Prometheus 指标

访问 `http://localhost:8000/metrics` 查看监控指标：

- `face_recognition_requests_total`: 总请求数
- `face_recognition_request_duration_seconds`: 请求耗时
- `face_comparison_results_total`: 对比结果统计

### 集成 Grafana

可以将 Prometheus 指标导入 Grafana 进行可视化监控。

## 🔧 故障排查

### 常见问题

1. **模型下载失败**
   - 首次运行时会自动下载模型，需要网络连接
   - 可以手动下载模型到 `~/.insightface/models/` 目录

2. **内存不足**
   - 模型约占用 1-2GB 内存
   - 建议至少 4GB 可用内存

3. **检测不到人脸**
   - 确保图片清晰，人脸可见
   - 图片质量过低可能影响检测
   - 侧脸、遮挡严重可能检测失败

4. **性能较慢**
   - 考虑启用 GPU 加速
   - 增加线程池大小
   - 使用更小的模型

## 📝 许可证

本项目基于 MIT 许可证开源。

InsightFace 项目请参考其官方许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题，请提交 Issue 或联系维护者。

## 🙏 致谢

- [InsightFace](https://github.com/deepinsight/insightface) - 提供优秀的人脸识别算法
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架

---

**注意**: 本服务仅供学习和研究使用，请遵守相关法律法规，尊重隐私权。

