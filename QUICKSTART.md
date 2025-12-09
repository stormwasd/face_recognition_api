# 快速开始指南

本指南将帮助您在5分钟内启动人脸识别API服务。

## 前置要求

- Python 3.8 或更高版本
- pip 包管理器
- 至少 4GB 可用内存
- 稳定的网络连接（首次运行需要下载模型，约500MB）

## 安装步骤

### 1. 安装依赖

```bash
# 进入项目目录
cd face_recognition_api

# （推荐）创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或者 Windows: venv\Scripts\activate

# 安装依赖包
pip install -r requirements.txt
```

### 2. 启动服务

#### 方式A：使用启动脚本（推荐）

```bash
# 开发模式（支持热重载）
./start.sh dev

# 生产模式
./start.sh
```

#### 方式B：直接运行

```bash
python main.py
```

#### 方式C：使用 uvicorn

```bash
# 单进程
uvicorn main:app --host 0.0.0.0 --port 8000

# 开发模式（热重载）
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 验证服务

打开浏览器访问：

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **服务信息**: http://localhost:8000/

您应该看到类似以下的输出：

```
================================================
启动 人脸识别API v1.0.0
================================================
正在初始化InsightFace模型: buffalo_l...
[下载模型文件...]
InsightFace模型初始化完成！
服务配置:
  - 模型: buffalo_l
  - 检测尺寸: (640, 640)
  - 相似度阈值: 0.65
  - 线程池大小: 8
================================================
✓ 服务启动成功！
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 快速测试

### 使用 cURL

```bash
# 准备两张测试图片：person1.jpg 和 person2.jpg
# 将图片转换为base64后发送请求

IMAGE1=$(base64 -w 0 person1.jpg)
IMAGE2=$(base64 -w 0 person2.jpg)

curl -X POST "http://localhost:8000/compare_faces" \
  -H "Content-Type: application/json" \
  -d "{
    \"image1\": \"$IMAGE1\",
    \"image2\": \"$IMAGE2\"
  }"
```

### 使用 Python

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
print(response.json())
```

### 使用测试脚本

```bash
# 修改 test_api.py 中的图片路径，然后运行
python test_api.py
```

## 预期响应

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

## Docker 快速启动

如果您更喜欢使用 Docker：

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f face-recognition-api

# 停止服务
docker-compose down
```

## 常见问题

### Q: 首次启动很慢？
A: 首次运行需要下载 InsightFace 模型（约500MB），请耐心等待。模型会缓存在 `~/.insightface/models/` 目录。

### Q: 出现内存不足错误？
A: 模型需要约1.5GB内存，请确保系统有足够的可用内存。可以关闭其他应用程序释放内存。

### Q: 检测不到人脸？
A: 请确保：
- 图片清晰可见
- 人脸正面朝向摄像头
- 光线充足
- 人脸未被严重遮挡

### Q: 如何停止服务？
A: 
- 使用脚本：`./stop.sh`
- 或者按 `Ctrl + C`

### Q: 如何修改端口？
A: 
- 编辑 `config.py` 文件，修改 `PORT=8000` 为您需要的端口
- 或设置环境变量：`export PORT=9000`
- 或者在启动时指定：`uvicorn main:app --port 9000`

### Q: 支持 GPU 加速吗？
A: 支持。安装 `onnxruntime-gpu` 并修改 `config.py` 中的 `PROVIDER=CUDAExecutionProvider` 或设置环境变量

## 下一步

- 📖 阅读完整文档：[README.md](README.md)
- 🔧 了解配置选项：[config.py](config.py)
- 🏗️ 查看项目结构：[STRUCTURE.md](STRUCTURE.md)
- 🚀 部署到生产环境：参考 README.md 的部署章节
- 📊 集成监控系统：使用 Prometheus + Grafana

## 技术支持

遇到问题？

1. 查看日志输出
2. 检查 `/health` 端点状态
3. 查阅 [README.md](README.md) 的故障排查章节
4. 提交 Issue

祝您使用愉快！🎉
