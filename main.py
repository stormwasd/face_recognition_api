"""
人脸识别API服务 - 主程序
基于InsightFace实现的高性能、高可用人脸对比服务
"""
import asyncio
import time
import base64
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Generic, TypeVar, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
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

# 全局异常处理器 - 统一错误响应格式
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "data": {},
            "msg": exc.detail
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    errors = exc.errors()
    error_msg = "; ".join([f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in errors])
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "code": 400,
            "data": {},
            "msg": f"请求参数验证失败: {error_msg}"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "data": {},
            "msg": f"服务器内部错误: {str(exc)}"
        }
    )

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
face_count_counter = SimpleMetric('face_count_results_total')

# 统一响应模型
T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """统一API响应结构"""
    code: int = Field(..., description="响应码，200时返回0，其他情况使用HTTP状态码")
    data: T = Field(..., description="响应数据")
    msg: str = Field(..., description="响应消息")


class CompareFacesRequest(BaseModel):
    """人脸对比请求模型"""
    image1: str = Field(..., description="第一张图片的base64编码字符串")
    image2: str = Field(..., description="第二张图片的base64编码字符串")


class ComparisonResult(BaseModel):
    """人脸对比结果模型"""
    is_same_person: bool = Field(..., description="是否为同一个人")
    similarity: float = Field(..., description="相似度分数（0-1之间）")
    confidence: str = Field(..., description="置信度等级：高/中/低/无")
    face1_detected: bool = Field(..., description="图片1是否检测到人脸")
    face2_detected: bool = Field(..., description="图片2是否检测到人脸")
    message: str = Field(..., description="结果说明")
    processing_time: Optional[float] = Field(None, description="处理时间（毫秒）")


class CountFacesRequest(BaseModel):
    """人脸计数请求模型"""
    image: str = Field(..., description="图片的base64编码字符串（支持带或不带data URI前缀）")


class FaceInfo(BaseModel):
    """单个人脸信息模型"""
    bbox: List[float] = Field(..., description="人脸边界框 [x1, y1, x2, y2]")
    det_score: float = Field(..., description="检测置信度分数（0-1之间）")


class FaceCountResult(BaseModel):
    """人脸计数结果模型"""
    face_count: int = Field(..., description="检测到的人脸数量")
    faces_detected: bool = Field(..., description="是否检测到人脸")
    message: str = Field(..., description="结果说明")
    face_details: List[FaceInfo] = Field(default_factory=list, description="人脸详细信息列表（包含边界框和置信度）")
    processing_time: Optional[float] = Field(None, description="处理时间（毫秒）")




@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加请求处理时间的中间件"""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # 转换为毫秒
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response


def validate_base64_image(base64_str: str) -> bytes:
    """
    验证并解码base64图片
    
    Args:
        base64_str: base64编码的图片字符串
        
    Returns:
        图片字节数据
        
    Raises:
        HTTPException: base64验证失败
    """
    if not base64_str:
        raise HTTPException(status_code=400, detail="base64图片数据不能为空")
    
    # 移除可能的前缀（如 data:image/jpeg;base64,）
    if ',' in base64_str:
        base64_str = base64_str.split(',')[-1]
    
    try:
        # 解码base64
        image_bytes = base64.b64decode(base64_str)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"base64解码失败: {str(e)}"
        )
    
    # 验证文件大小
    if len(image_bytes) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"图片过大，最大支持 {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="图片数据为空")
    
    # 验证是否为有效的图片格式（通过文件头判断）
    valid_signatures = [
        b'\xff\xd8\xff',  # JPEG
        b'\x89\x50\x4e\x47',  # PNG
        b'RIFF',  # WEBP (需要进一步检查)
    ]
    
    is_valid = False
    for sig in valid_signatures:
        if image_bytes.startswith(sig):
            is_valid = True
            break
    
    # WEBP 特殊检查
    if not is_valid and image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        is_valid = True
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片格式，支持的格式: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    return image_bytes


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


async def process_face_count_async(
    image_bytes: bytes
) -> FaceCountResult:
    """
    异步处理人脸计数
    
    Args:
        image_bytes: 图片字节数据
        
    Returns:
        人脸计数结果
    """
    start_time = time.time()
    
    # 在线程池中执行CPU密集型任务
    loop = asyncio.get_event_loop()
    face_count, success, message, face_details = await loop.run_in_executor(
        executor,
        face_service.count_faces,
        image_bytes
    )
    
    # 计算处理时间
    processing_time = (time.time() - start_time) * 1000  # 毫秒
    
    # 构建人脸信息列表
    face_info_list = [
        FaceInfo(bbox=detail["bbox"], det_score=round(detail["det_score"], 4))
        for detail in face_details
    ]
    
    return FaceCountResult(
        face_count=face_count,
        faces_detected=face_count > 0,
        message=message,
        face_details=face_info_list,
        processing_time=round(processing_time, 2)
    )


@app.post("/compare_faces", response_model=ApiResponse[ComparisonResult], tags=["人脸识别"])
async def compare_faces(request: CompareFacesRequest):
    """
    比较两张人脸图片是否为同一个人
    
    **请求参数**:
    - `image1`: 第一张图片的base64编码字符串（支持带或不带data URI前缀）
    - `image2`: 第二张图片的base64编码字符串（支持带或不带data URI前缀）
    
    **支持的图片格式**: JPG, JPEG, PNG, WEBP
    
    **文件大小限制**: 最大10MB
    
    **返回信息**:
    - `code`: 响应码，成功时为0
    - `data`: 包含对比结果数据
      - `is_same_person`: 是否为同一个人
      - `similarity`: 相似度分数（0-1之间，越接近1越相似）
      - `confidence`: 置信度等级（高/中/低）
      - `face1_detected`: 第一张图片是否检测到人脸
      - `face2_detected`: 第二张图片是否检测到人脸
      - `message`: 详细说明
      - `processing_time`: 处理时间（毫秒）
    - `msg`: 响应消息
    
    **示例**:
    ```bash
    curl -X POST "http://localhost:8000/compare_faces" \\
      -H "Content-Type: application/json" \\
      -d '{
        "image1": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
        "image2": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
      }'
    ```
    """
    try:
        # 记录请求
        request_count.labels(endpoint='compare_faces', status='started').inc()
        
        with request_duration.labels(endpoint='compare_faces').time():
            # 验证并解码base64图片
            image1_bytes = validate_base64_image(request.image1)
            image2_bytes = validate_base64_image(request.image2)
            
            # 处理人脸对比
            result = await process_face_comparison_async(image1_bytes, image2_bytes)
            
            # 记录成功
            request_count.labels(endpoint='compare_faces', status='success').inc()
            
            return ApiResponse(
                code=0,
                data=result,
                msg="人脸对比成功"
            )
    
    except HTTPException:
        request_count.labels(endpoint='compare_faces', status='error').inc()
        raise
    except Exception as e:
        request_count.labels(endpoint='compare_faces', status='error').inc()
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@app.post("/count_faces", response_model=ApiResponse[FaceCountResult], tags=["人脸识别"])
async def count_faces(request: CountFacesRequest):
    """
    检测图片中的人脸数量
    
    **请求参数**:
    - `image`: 图片的base64编码字符串（支持带或不带data URI前缀）
    
    **支持的图片格式**: JPG, JPEG, PNG, WEBP
    
    **文件大小限制**: 最大10MB
    
    **返回信息**:
    - `code`: 响应码，成功时为0
    - `data`: 包含人脸计数结果数据
      - `face_count`: 检测到的人脸数量
      - `faces_detected`: 是否检测到人脸
      - `message`: 详细说明
      - `face_details`: 人脸详细信息列表，每个包含：
        - `bbox`: 人脸边界框坐标 [x1, y1, x2, y2]
        - `det_score`: 检测置信度分数（0-1之间，越高越可靠）
      - `processing_time`: 处理时间（毫秒）
    - `msg`: 响应消息
    
    **示例**:
    ```bash
    curl -X POST "http://localhost:8000/count_faces" \\
      -H "Content-Type: application/json" \\
      -d '{
        "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
      }'
    ```
    
    **注意**: 本接口使用高精度InsightFace模型，能够准确检测图片中的多张人脸。
    """
    try:
        # 记录请求
        request_count.labels(endpoint='count_faces', status='started').inc()
        
        with request_duration.labels(endpoint='count_faces').time():
            # 验证并解码base64图片
            image_bytes = validate_base64_image(request.image)
            
            # 处理人脸计数
            result = await process_face_count_async(image_bytes)
            
            # 记录成功和计数结果
            request_count.labels(endpoint='count_faces', status='success').inc()
            face_count_counter.inc()
            
            return ApiResponse(
                code=0,
                data=result,
                msg="人脸计数成功"
            )
    
    except HTTPException:
        request_count.labels(endpoint='count_faces', status='error').inc()
        raise
    except Exception as e:
        request_count.labels(endpoint='count_faces', status='error').inc()
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@app.get("/", response_model=ApiResponse[dict], tags=["系统"])
async def root():
    """API根路径 - 服务信息"""
    return ApiResponse(
        code=0,
        data={
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "endpoints": {
                "比较人脸": "/compare_faces",
                "人脸计数": "/count_faces",
                "服务信息": "/info",
                "API文档": "/docs",
                "健康检查": "/health",
                "监控指标": "/metrics"
            },
            "documentation": "/docs"
        },
        msg="服务运行正常"
    )


@app.get("/health", response_model=ApiResponse[dict], tags=["系统"])
async def health_check():
    """健康检查接口"""
    return ApiResponse(
        code=0,
        data={
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "model_loaded": face_service._initialized,
            "model_name": settings.MODEL_NAME
        },
        msg="服务健康检查通过"
    )


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
face_recognition_requests_total{{endpoint="count_faces",status="success"}} {request_count.value}

# HELP face_recognition_request_duration_seconds Request duration in seconds  
# TYPE face_recognition_request_duration_seconds histogram
face_recognition_request_duration_seconds_count {{endpoint="compare_faces"}} {request_duration.value}
face_recognition_request_duration_seconds_count {{endpoint="count_faces"}} {request_duration.value}

# HELP face_comparison_results_total Total number of face comparison results
# TYPE face_comparison_results_total counter
face_comparison_results_total{{result="same_person"}} {comparison_result_counter.value}

# HELP face_count_results_total Total number of face count requests
# TYPE face_count_results_total counter
face_count_results_total {face_count_counter.value}
"""
    
    return Response(content=default_metrics + custom_metrics, media_type="text/plain")


@app.get("/info", response_model=ApiResponse[dict], tags=["系统"])
async def get_info():
    """获取服务配置信息"""
    return ApiResponse(
        code=0,
        data={
            "model": settings.MODEL_NAME,
            "detection_size": settings.DET_SIZE,
            "similarity_threshold": settings.SIMILARITY_THRESHOLD,
            "max_file_size_mb": settings.MAX_FILE_SIZE // (1024 * 1024),
            "supported_formats": settings.ALLOWED_EXTENSIONS,
            "thread_pool_workers": settings.THREAD_POOL_WORKERS
        },
        msg="获取服务配置信息成功"
    )


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

