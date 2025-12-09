FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量（禁用代理，避免构建时连接本地代理失败）
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    http_proxy="" \
    https_proxy="" \
    HTTP_PROXY="" \
    HTTPS_PROXY="" \
    no_proxy="*" \
    NO_PROXY="*"

# 配置 apt（彻底禁用代理，处理代理和源问题）
# 清除所有可能的代理配置，并明确设置空代理
RUN rm -f /etc/apt/apt.conf.d/*proxy* 2>/dev/null || true && \
    rm -f /etc/apt/apt.conf 2>/dev/null || true && \
    echo "Acquire::http::Proxy \"\";" > /etc/apt/apt.conf.d/99no-proxy && \
    echo "Acquire::https::Proxy \"\";" >> /etc/apt/apt.conf.d/99no-proxy && \
    echo "Acquire::http::Pipeline-Depth 0;" >> /etc/apt/apt.conf.d/99no-proxy && \
    echo "Acquire::http::No-Cache true;" >> /etc/apt/apt.conf.d/99no-proxy

# 安装系统依赖（兼容 Debian 13 trixie）
# 注意：如果仍然遇到代理问题，请使用：
# docker build --network=host -t face-recognition-api:latest .
# 或者使用 Dockerfile.bookworm: docker build -f Dockerfile.bookworm -t face-recognition-api:latest .
RUN apt-get update --allow-releaseinfo-change && \
    apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建模型缓存目录
RUN mkdir -p /root/.insightface/models

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "main.py"]

