"""
人脸识别API服务 - 主程序
基于InsightFace实现的高性能、高可用人脸对比服务
"""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

from config import settings
from face_service import face_service


# 线程池执行器（用于CPU密集型任务）
executor = ThreadPoolExecutor(max_workers=settings.THREAD_POOL_WORKERS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("=" * 60)
    print(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 60)
    
    # 初始化人脸识别服务
    face_service.initialize()
    
    print(f"服务配置:")
    print(f"  - 模型: {settings.MODEL_NAME}")
    print(f"  - 检测尺寸: {settings.DET_SIZE}")
    print(f"  - 相似度阈值: {settings.SIMILARITY_THRESHOLD}")
    print(f"  - 线程池大小: {settings.THREAD_POOL_WORKERS}")
    print("=" * 60)
    print("✓ 服务启动成功！")
    
    yield
    
    # 关闭时执行
    print("正在关闭服务...")
    executor.shutdown(wait=True)
    print("✓ 资源清理完成")

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加CORS中间件（跨域支持）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加GZIP压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 简化的指标处理 - 使用占位符避免Prometheus冲突
class SimpleMetric:
    def __init__(self, name):
        self.name = name
        self.value = 0
        
    def labels(self, **kwargs):
        return self
        
    def inc(self):
        self.value += 1
        
    def time(self):
        return self
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass

# 创建简单的指标对象
request_count = SimpleMetric('face_recognition_requests_total')
request_duration = SimpleMetric('face_recognition_request_duration_seconds')
comparison_result_counter = SimpleMetric('face_comparison_results_total')


class ComparisonResult(BaseModel):
    """人脸对比结果模型"""
    is_same_person: bool = Field(..., description="是否为同一个人")
    similarity: float = Field(..., description="相似度分数（0-1之间）")
    confidence: str = Field(..., description="置信度等级：高/中/低/无")
    face1_detected: bool = Field(..., description="图片1是否检测到人脸")
    face2_detected: bool = Field(..., description="图片2是否检测到人脸")
    message: str = Field(..., description="结果说明")
    processing_time: Optional[float] = Field(None, description="处理时间（毫秒）")




@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加请求处理时间的中间件"""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # 转换为毫秒
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response


async def validate_image_file(file: UploadFile) -> bytes:
    """
    验证并读取图片文件
    
    Args:
        file: 上传的文件
        
    Returns:
        文件字节数据
        
    Raises:
        HTTPException: 文件验证失败
    """
    # 验证文件类型
    if file.content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。支持的格式: {', '.join(settings.ALLOWED_CONTENT_TYPES)}"
        )
    
    # 读取文件内容
    file_bytes = await file.read()
    
    # 验证文件大小
    if len(file_bytes) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大。最大支持 {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")
    
    return file_bytes


async def process_face_comparison_async(
    image1_bytes: bytes,
    image2_bytes: bytes
) -> ComparisonResult:
    """
    异步处理人脸对比
    
    Args:
        image1_bytes: 第一张图片字节数据
        image2_bytes: 第二张图片字节数据
        
    Returns:
        对比结果
    """
    start_time = time.time()
    
    # 在线程池中执行CPU密集型任务
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        face_service.compare_faces,
        image1_bytes,
        image2_bytes
    )
    
    is_same, similarity, confidence, face1_det, face2_det, message = result
    
    # 计算处理时间
    processing_time = (time.time() - start_time) * 1000  # 毫秒
    
    # 记录监控指标
    if is_same:
        comparison_result_counter.labels(result='same_person').inc()
    else:
        comparison_result_counter.labels(result='different_person').inc()
    
    return ComparisonResult(
        is_same_person=is_same,
        similarity=round(similarity, 4),
        confidence=confidence,
        face1_detected=face1_det,
        face2_detected=face2_det,
        message=message,
        processing_time=round(processing_time, 2)
    )


@app.post("/api/v1/compare_faces", response_model=ComparisonResult, tags=["人脸识别"])
async def compare_faces(
    image1: UploadFile = File(..., description="第一张人脸图片"),
    image2: UploadFile = File(..., description="第二张人脸图片")
):
    """
    比较两张人脸图片是否为同一个人
    
    **支持的图片格式**: JPG, JPEG, PNG, WEBP
    
    **文件大小限制**: 最大10MB
    
    **返回信息**:
    - `is_same_person`: 是否为同一个人
    - `similarity`: 相似度分数（0-1之间，越接近1越相似）
    - `confidence`: 置信度等级（高/中/低）
    - `face1_detected`: 第一张图片是否检测到人脸
    - `face2_detected`: 第二张图片是否检测到人脸
    - `message`: 详细说明
    - `processing_time`: 处理时间（毫秒）
    
    **示例**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/compare_faces" \\
      -F "image1=@person1.jpg" \\
      -F "image2=@person2.jpg"
    ```
    """
    try:
        # 记录请求
        request_count.labels(endpoint='compare_faces', status='started').inc()
        
        with request_duration.labels(endpoint='compare_faces').time():
            # 验证并读取图片文件
            image1_bytes = await validate_image_file(image1)
            image2_bytes = await validate_image_file(image2)
            
            # 处理人脸对比
            result = await process_face_comparison_async(image1_bytes, image2_bytes)
            
            # 记录成功
            request_count.labels(endpoint='compare_faces', status='success').inc()
            
            return result
    
    except HTTPException:
        request_count.labels(endpoint='compare_faces', status='error').inc()
        raise
    except Exception as e:
        request_count.labels(endpoint='compare_faces', status='error').inc()
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@app.get("/", tags=["系统"])
async def root():
    """API根路径 - 服务信息"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "比较人脸": "/api/v1/compare_faces",
            "API文档": "/docs",
            "健康检查": "/health",
            "监控指标": "/metrics"
        },
        "documentation": "/docs"
    }


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "model_loaded": face_service._initialized,
        "model_name": settings.MODEL_NAME
    }


@app.get("/metrics", tags=["系统"])
async def metrics():
    """Prometheus监控指标"""
    # 获取默认的Prometheus指标
    default_metrics = generate_latest().decode('utf-8')
    
    # 添加我们的自定义指标
    custom_metrics = f"""
# HELP face_recognition_requests_total Total number of face recognition requests
# TYPE face_recognition_requests_total counter
face_recognition_requests_total{{endpoint="compare_faces",status="success"}} {request_count.value}

# HELP face_recognition_request_duration_seconds Request duration in seconds  
# TYPE face_recognition_request_duration_seconds histogram
face_recognition_request_duration_seconds_count {{endpoint="compare_faces"}} {request_duration.value}

# HELP face_comparison_results_total Total number of face comparison results
# TYPE face_comparison_results_total counter
face_comparison_results_total{{result="same_person"}} {comparison_result_counter.value}
"""
    
    return Response(content=default_metrics + custom_metrics, media_type="text/plain")


@app.get("/api/v1/info", tags=["系统"])
async def get_info():
    """获取服务配置信息"""
    return {
        "model": settings.MODEL_NAME,
        "detection_size": settings.DET_SIZE,
        "similarity_threshold": settings.SIMILARITY_THRESHOLD,
        "max_file_size_mb": settings.MAX_FILE_SIZE // (1024 * 1024),
        "supported_formats": settings.ALLOWED_EXTENSIONS,
        "thread_pool_workers": settings.THREAD_POOL_WORKERS
    }


if __name__ == "__main__":
    import uvicorn
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=1,  # 使用单进程，因为模型占用内存
        log_level="info",
        access_log=True
    )

