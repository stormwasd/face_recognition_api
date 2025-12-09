# Docker 构建问题修复指南

## 问题描述

如果遇到以下错误：
```
Unable to connect to 127.0.0.1:7890
Unable to locate package libgl1
```

这是因为 Docker 构建时尝试使用本地代理（127.0.0.1:7890），但代理不可用。

## 解决方案

### 方案1：使用 --network=host（推荐）

```bash
docker build --network=host -t face-recognition-api:version_1209_2025 .
```

这会使用主机网络，绕过代理设置。

### 方案2：使用 Debian 12 版本（最稳定）

```bash
docker build -f Dockerfile.bookworm -t face-recognition-api:version_1209_2025 .
```

`Dockerfile.bookworm` 使用 Debian 12 (bookworm)，包更稳定，代理问题更少。

### 方案3：清除系统代理环境变量

在构建前清除代理环境变量：

**Linux/Mac:**
```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
docker build -t face-recognition-api:version_1209_2025 .
```

**Windows PowerShell:**
```powershell
$env:http_proxy=""
$env:https_proxy=""
$env:HTTP_PROXY=""
$env:HTTPS_PROXY=""
docker build -t face-recognition-api:version_1209_2025 .
```

**Windows CMD:**
```cmd
set http_proxy=
set https_proxy=
set HTTP_PROXY=
set HTTPS_PROXY=
docker build -t face-recognition-api:version_1209_2025 .
```

### 方案4：配置 Docker 守护进程代理（如果需要使用代理）

如果需要使用代理，需要正确配置 Docker 守护进程：

1. 编辑或创建 `/etc/docker/daemon.json` (Linux) 或 Docker Desktop 设置
2. 添加代理配置：
```json
{
  "proxies": {
    "http-proxy": "http://your-proxy:port",
    "https-proxy": "http://your-proxy:port",
    "no-proxy": "localhost,127.0.0.1"
  }
}
```

## 推荐方案

**最简单可靠的方法：**

```bash
# 使用 Debian 12 版本，最稳定
docker build -f Dockerfile.bookworm -t face-recognition-api:version_1209_2025 .
```

或者

```bash
# 使用主机网络，绕过代理
docker build --network=host -t face-recognition-api:version_1209_2025 .
```

## 验证构建

构建成功后，运行容器：

```bash
docker run -d \
  --name face_recognition_api \
  -p 8000:8000 \
  -v $(pwd)/models:/root/.insightface/models \
  --restart unless-stopped \
  face-recognition-api:version_1209_2025
```

检查服务：

```bash
curl http://localhost:8000/health
```

