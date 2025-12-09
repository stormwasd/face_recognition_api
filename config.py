"""
配置文件
"""
import os
from typing import Union
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import field_validator
except ImportError:
    from pydantic import BaseSettings, validator as field_validator


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基本信息
    APP_NAME: str = "人脸识别API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "基于InsightFace的高性能人脸对比服务"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4  # 工作进程数，根据CPU核心数调整
    
    # InsightFace模型配置
    MODEL_NAME: str = "buffalo_l"  # 使用buffalo_l高精度模型
    DET_SIZE: list = [640, 640]  # 人脸检测尺寸
    
    # GPU配置（如果有GPU，改为CUDAExecutionProvider）
    PROVIDER: str = "CPUExecutionProvider"
    CTX_ID: int = 0
    
    # 人脸识别阈值
    SIMILARITY_THRESHOLD: float = 0.65  # 判断是否为同一人的相似度阈值
    HIGH_CONFIDENCE_THRESHOLD: float = 0.75  # 高置信度阈值
    MEDIUM_CONFIDENCE_THRESHOLD: float = 0.60  # 中等置信度阈值
    
    # 文件限制
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".jpg", ".jpeg", ".png", ".webp"]
    ALLOWED_CONTENT_TYPES: list = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    
    # 并发配置
    THREAD_POOL_WORKERS: int = 8  # 线程池大小
    
    # 缓存配置（可选，用于提高性能）
    ENABLE_CACHE: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CACHE_TTL: int = 3600  # 缓存过期时间（秒）
    
    @field_validator('DET_SIZE', mode='before')
    @classmethod
    def parse_det_size(cls, v):
        if isinstance(v, str):
            # 处理 "(640, 640)" 格式
            v = v.strip('()')
            return [int(x.strip()) for x in v.split(',')]
        return v
    
    model_config = SettingsConfigDict(
        env_file=None,  # 不依赖 .env 文件，所有配置在代码中定义
        case_sensitive=True,
        env_parse_none_str='None',
        # 仍然支持环境变量覆盖（通过系统环境变量），但不强制需要 .env 文件
        env_file_encoding='utf-8'
    )


# 创建全局配置实例
settings = Settings()

