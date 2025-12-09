# Dockerfile 使用指南

## 两个 Dockerfile 的区别

### 1. 主 Dockerfile（默认）
- **基础镜像**: `python:3.10-slim` (Debian 13 - trixie)
- **特点**: 使用最新的 Debian 版本
- **适用场景**: 一般情况，想要最新系统版本
- **构建命令**: 
  ```bash
  docker build --network=host -t face-recognition-api:latest .
  ```

### 2. Dockerfile.bookworm（推荐）
- **基础镜像**: `python:3.10-slim-bookworm` (Debian 12 - bookworm)
- **特点**: 使用稳定的 Debian LTS 版本，包更稳定
- **适用场景**: **生产环境推荐**，稳定性更好
- **构建命令**: 
  ```bash
  docker build --network=host -f Dockerfile.bookworm -t face-recognition-api:latest .
  ```

## 推荐使用方案

### 🎯 推荐：使用 Dockerfile.bookworm（生产环境）

**原因：**
- Debian 12 (bookworm) 是稳定版本，包更成熟
- 系统依赖更稳定，兼容性更好
- 适合生产环境部署

**构建命令：**
```bash
docker build --network=host -f Dockerfile.bookworm -t face-recognition-api:version_1209_2059 .
```

### 备选：使用主 Dockerfile（开发环境）

**原因：**
- 使用最新的 Debian 13
- 适合开发测试

**构建命令：**
```bash
docker build --network=host -t face-recognition-api:version_1209_2059 .
```

## 重要提示

1. **必须使用 `--network=host`**：如果遇到代理连接问题（`Unable to connect to 127.0.0.1:7890`），必须添加此参数
2. **两个 Dockerfile 功能相同**：都使用环境变量和启动脚本处理 onnxruntime 问题
3. **推荐使用 bookworm**：更稳定，适合生产环境

## 快速开始

**生产环境（推荐）：**
```bash
docker build --network=host -f Dockerfile.bookworm -t face-recognition-api:latest .
```

**开发环境：**
```bash
docker build --network=host -t face-recognition-api:latest .
```

## 运行容器

构建完成后，运行容器：

```bash
docker run -d \
  --name face_recognition_api \
  -p 8087:8000 \
  -v $(pwd)/models:/root/.insightface/models \
  --restart unless-stopped \
  face-recognition-api:latest
```

