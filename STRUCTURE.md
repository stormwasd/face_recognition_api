# 项目结构说明

## 文件树

```
face_recognition_api/
├── main.py                    # FastAPI主程序，API接口定义
├── config.py                  # 配置文件，所有配置项管理
├── face_service.py            # 人脸识别核心服务，封装InsightFace
├── requirements.txt           # Python依赖包列表
├── .env.example               # 环境变量示例文件
├── .gitignore                 # Git忽略文件配置
├── README.md                  # 项目完整文档
├── STRUCTURE.md               # 项目结构说明（本文件）
├── Dockerfile                 # Docker镜像构建文件
├── docker-compose.yml         # Docker Compose编排文件
├── nginx.conf                 # Nginx负载均衡配置
├── start.sh                   # 启动脚本（Linux/Mac）
├── stop.sh                    # 停止脚本（Linux/Mac）
└── test_api.py                # API测试脚本
```

## 核心文件说明

### main.py
- **作用**: FastAPI应用主程序
- **包含**: 
  - API路由定义
  - 中间件配置（CORS、GZIP、日志）
  - 请求处理逻辑
  - 监控指标（Prometheus）
  - 健康检查端点

### config.py
- **作用**: 集中管理所有配置项
- **包含**:
  - 服务器配置（地址、端口）
  - 模型配置（模型名称、检测尺寸）
  - 阈值配置（相似度判断）
  - 性能配置（线程池大小）
  - 文件限制配置

### face_service.py
- **作用**: 人脸识别核心业务逻辑
- **包含**:
  - FaceRecognitionService类
  - 模型初始化
  - 图片读取和预处理
  - 人脸检测和特征提取
  - 相似度计算
  - 结果判断逻辑

### requirements.txt
- **作用**: Python项目依赖
- **核心依赖**:
  - `fastapi`: Web框架
  - `insightface`: 人脸识别库
  - `onnxruntime`: 深度学习推理引擎
  - `opencv-python`: 图像处理
  - `prometheus-client`: 监控指标

### .env.example
- **作用**: 环境变量配置模板
- **使用**: 复制为`.env`并根据需要修改

### Dockerfile
- **作用**: 构建Docker镜像
- **特点**:
  - 基于Python 3.10-slim
  - 安装系统依赖
  - 优化镜像大小

### docker-compose.yml
- **作用**: Docker服务编排
- **包含**:
  - API服务配置
  - 资源限制
  - 健康检查
  - 可选的Redis和Nginx配置

### nginx.conf
- **作用**: Nginx反向代理和负载均衡配置
- **特点**:
  - 支持多实例负载均衡
  - 配置超时和文件大小限制

### start.sh / stop.sh
- **作用**: 便捷的启动和停止脚本
- **功能**:
  - 环境检查
  - 依赖安装
  - 服务启动/停止

### test_api.py
- **作用**: API测试工具
- **功能**:
  - 健康检查测试
  - 人脸对比功能测试
  - 性能压力测试
  - 结果统计分析

## 数据流程

1. **请求接收**: FastAPI (main.py) 接收HTTP请求
2. **参数验证**: 验证文件类型、大小等
3. **异步处理**: 在线程池中执行CPU密集型任务
4. **服务调用**: 调用 face_service.py 进行人脸识别
5. **结果返回**: 返回JSON格式的对比结果

## 高性能设计

1. **异步处理**: FastAPI原生异步支持
2. **线程池**: ThreadPoolExecutor处理CPU密集任务
3. **模型复用**: 模型加载一次，常驻内存
4. **响应压缩**: GZIP中间件减少网络传输
5. **监控优化**: Prometheus指标监控性能瓶颈

## 高可用设计

1. **健康检查**: `/health` 端点供负载均衡器检查
2. **优雅重启**: 信号处理和资源清理
3. **错误处理**: 完善的异常捕获和错误返回
4. **日志记录**: 详细的运行日志
5. **Docker部署**: 容器化便于扩展和恢复

## 扩展建议

### 添加缓存
创建 `cache.py` 实现Redis缓存：
- 缓存重复的人脸对比结果
- 减少重复计算
- 提高响应速度

### 添加数据库
创建 `database.py` 实现持久化存储：
- 记录对比历史
- 统计分析
- 用户管理

### 添加认证
创建 `auth.py` 实现API认证：
- JWT Token
- API Key
- OAuth2

### 批量处理
创建 `batch.py` 实现批量对比：
- 一对多人脸搜索
- 批量人脸识别
- 异步任务队列
