"""
人脸识别服务核心模块
封装InsightFace的所有操作
"""
import hashlib
from typing import Optional, Tuple
import numpy as np
import cv2
import insightface
from insightface.app import FaceAnalysis
from config import settings


class FaceRecognitionService:
    """人脸识别服务类"""
    
    def __init__(self):
        """初始化人脸识别服务"""
        self.face_analyzer: Optional[FaceAnalysis] = None
        self._initialized = False
    
    def initialize(self):
        """初始化InsightFace模型"""
        if self._initialized:
            return
        
        print(f"正在初始化InsightFace模型: {settings.MODEL_NAME}...")
        
        # 创建人脸分析器
        self.face_analyzer = FaceAnalysis(
            name=settings.MODEL_NAME,
            providers=[settings.PROVIDER]
        )
        
        # 准备模型
        self.face_analyzer.prepare(
            ctx_id=settings.CTX_ID,
            det_size=settings.DET_SIZE
        )
        
        self._initialized = True
        print("InsightFace模型初始化完成！")
    
    @staticmethod
    def read_image_from_bytes(image_bytes: bytes) -> Optional[np.ndarray]:
        """
        从字节数据读取图片
        
        Args:
            image_bytes: 图片字节数据
            
        Returns:
            OpenCV格式的图片数组，失败返回None
        """
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return None
            
            return img
        except Exception as e:
            print(f"读取图片失败: {str(e)}")
            return None
    
    def extract_face_embedding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        从图片中提取人脸特征向量
        
        Args:
            image: OpenCV格式的图片
            
        Returns:
            人脸特征向量（512维），未检测到人脸返回None
        """
        if not self._initialized:
            raise RuntimeError("人脸识别服务未初始化")
        
        try:
            # 检测人脸
            faces = self.face_analyzer.get(image)
            
            if len(faces) == 0:
                return None
            
            # 如果检测到多张人脸，选择面积最大的（主要人物）
            if len(faces) > 1:
                faces = sorted(
                    faces,
                    key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]),
                    reverse=True
                )
            
            # 返回人脸特征向量
            return faces[0].embedding
            
        except Exception as e:
            print(f"提取人脸特征失败: {str(e)}")
            return None
    
    @staticmethod
    def calculate_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        计算两个特征向量的余弦相似度
        
        Args:
            embedding1: 第一个特征向量
            embedding2: 第二个特征向量
            
        Returns:
            相似度分数 (0-1)
        """
        # L2归一化
        embedding1_normalized = embedding1 / np.linalg.norm(embedding1)
        embedding2_normalized = embedding2 / np.linalg.norm(embedding2)
        
        # 计算余弦相似度
        similarity = np.dot(embedding1_normalized, embedding2_normalized)
        
        # 映射到0-1区间
        similarity = float((similarity + 1) / 2)
        
        return similarity
    
    @staticmethod
    def get_confidence_level(similarity: float) -> str:
        """
        根据相似度返回置信度等级
        
        Args:
            similarity: 相似度分数
            
        Returns:
            置信度等级
        """
        if similarity >= settings.HIGH_CONFIDENCE_THRESHOLD:
            return "高"
        elif similarity >= settings.MEDIUM_CONFIDENCE_THRESHOLD:
            return "中"
        else:
            return "低"
    
    def compare_faces(
        self,
        image1_bytes: bytes,
        image2_bytes: bytes
    ) -> Tuple[bool, float, str, bool, bool, str]:
        """
        比较两张人脸图片
        
        Args:
            image1_bytes: 第一张图片的字节数据
            image2_bytes: 第二张图片的字节数据
            
        Returns:
            (是否同一人, 相似度, 置信度, 人脸1检测, 人脸2检测, 消息)
        """
        # 读取图片
        image1 = self.read_image_from_bytes(image1_bytes)
        image2 = self.read_image_from_bytes(image2_bytes)
        
        if image1 is None or image2 is None:
            return False, 0.0, "无", False, False, "无法读取图片文件"
        
        # 提取人脸特征
        embedding1 = self.extract_face_embedding(image1)
        embedding2 = self.extract_face_embedding(image2)
        
        face1_detected = embedding1 is not None
        face2_detected = embedding2 is not None
        
        # 检查是否都检测到人脸
        if not face1_detected or not face2_detected:
            if not face1_detected and not face2_detected:
                message = "两张图片都未检测到人脸"
            elif not face1_detected:
                message = "图片1未检测到人脸"
            else:
                message = "图片2未检测到人脸"
            
            return False, 0.0, "无", face1_detected, face2_detected, message
        
        # 计算相似度
        similarity = self.calculate_similarity(embedding1, embedding2)
        
        # 判断是否为同一人
        is_same_person = similarity >= settings.SIMILARITY_THRESHOLD
        confidence = self.get_confidence_level(similarity)
        
        if is_same_person:
            message = f"两张图片是同一个人（相似度: {similarity:.2%}）"
        else:
            message = f"两张图片不是同一个人（相似度: {similarity:.2%}）"
        
        return is_same_person, similarity, confidence, face1_detected, face2_detected, message
    
    @staticmethod
    def calculate_image_hash(image_bytes: bytes) -> str:
        """
        计算图片的哈希值（用于缓存）
        
        Args:
            image_bytes: 图片字节数据
            
        Returns:
            MD5哈希值
        """
        return hashlib.md5(image_bytes).hexdigest()


# 创建全局服务实例
face_service = FaceRecognitionService()

