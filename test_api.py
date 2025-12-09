"""
API测试脚本
用于测试人脸识别API的功能
"""
import requests
import time
import base64
from pathlib import Path


class FaceRecognitionAPITester:
    """人脸识别API测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/compare_faces"
    
    def test_health(self):
        """测试健康检查接口"""
        print("\n" + "="*60)
        print("测试健康检查接口...")
        print("="*60)
        
        try:
            response = requests.get(f"{self.base_url}/health")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False
    
    def test_root(self):
        """测试根路径"""
        print("\n" + "="*60)
        print("测试根路径...")
        print("="*60)
        
        try:
            response = requests.get(self.base_url)
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False
    
    def test_info(self):
        """测试服务信息接口"""
        print("\n" + "="*60)
        print("测试服务信息接口...")
        print("="*60)
        
        try:
            response = requests.get(f"{self.base_url}/info")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False
    
    def test_compare_faces(self, image1_path: str, image2_path: str):
        """
        测试人脸对比接口
        
        Args:
            image1_path: 第一张图片路径
            image2_path: 第二张图片路径
        """
        print("\n" + "="*60)
        print(f"测试人脸对比: {image1_path} vs {image2_path}")
        print("="*60)
        
        # 检查文件是否存在
        if not Path(image1_path).exists():
            print(f"❌ 文件不存在: {image1_path}")
            return False
        
        if not Path(image2_path).exists():
            print(f"❌ 文件不存在: {image2_path}")
            return False
        
        try:
            # 读取图片并转换为base64
            with open(image1_path, 'rb') as f1:
                image1_base64 = base64.b64encode(f1.read()).decode('utf-8')
            
            with open(image2_path, 'rb') as f2:
                image2_base64 = base64.b64encode(f2.read()).decode('utf-8')
            
            # 准备请求数据
            payload = {
                "image1": image1_base64,
                "image2": image2_base64
            }
            
            # 发送请求
            start_time = time.time()
            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            elapsed_time = (time.time() - start_time) * 1000
            
            print(f"状态码: {response.status_code}")
            print(f"请求耗时: {elapsed_time:.2f}ms")
            
            if response.status_code == 200:
                result = response.json()
                print("\n结果:")
                print(f"  是否同一人: {'✓ 是' if result['is_same_person'] else '✗ 否'}")
                print(f"  相似度: {result['similarity']:.4f} ({result['similarity']*100:.2f}%)")
                print(f"  置信度: {result['confidence']}")
                print(f"  图片1检测到人脸: {'✓' if result['face1_detected'] else '✗'}")
                print(f"  图片2检测到人脸: {'✓' if result['face2_detected'] else '✗'}")
                print(f"  消息: {result['message']}")
                print(f"  服务器处理时间: {result.get('processing_time', 'N/A')}ms")
                return True
            else:
                print(f"❌ 请求失败: {response.text}")
                return False
                    
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False
    
    def test_performance(self, image1_path: str, image2_path: str, num_requests: int = 10):
        """
        性能测试
        
        Args:
            image1_path: 第一张图片路径
            image2_path: 第二张图片路径
            num_requests: 请求次数
        """
        print("\n" + "="*60)
        print(f"性能测试 - 连续发送 {num_requests} 个请求")
        print("="*60)
        
        # 预先读取并编码图片
        try:
            with open(image1_path, 'rb') as f1:
                image1_base64 = base64.b64encode(f1.read()).decode('utf-8')
            with open(image2_path, 'rb') as f2:
                image2_base64 = base64.b64encode(f2.read()).decode('utf-8')
        except Exception as e:
            print(f"❌ 读取图片失败: {e}")
            return
        
        payload = {
            "image1": image1_base64,
            "image2": image2_base64
        }
        
        times = []
        success_count = 0
        
        for i in range(num_requests):
            try:
                start_time = time.time()
                response = requests.post(
                    self.api_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                elapsed_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    times.append(elapsed_time)
                    success_count += 1
                    print(f"请求 {i+1}/{num_requests}: ✓ {elapsed_time:.2f}ms")
                else:
                    print(f"请求 {i+1}/{num_requests}: ✗ 失败")
            
            except Exception as e:
                print(f"请求 {i+1}/{num_requests}: ✗ 错误: {e}")
        
        # 统计结果
        if times:
            print("\n性能统计:")
            print(f"  成功率: {success_count}/{num_requests} ({success_count/num_requests*100:.1f}%)")
            print(f"  平均耗时: {sum(times)/len(times):.2f}ms")
            print(f"  最小耗时: {min(times):.2f}ms")
            print(f"  最大耗时: {max(times):.2f}ms")
            print(f"  QPS: {1000/(sum(times)/len(times)):.2f} 请求/秒")


def main():
    """主函数"""
    tester = FaceRecognitionAPITester()
    
    print("\n" + "🚀 开始测试人脸识别API" + "\n")
    
    # 基础功能测试
    tester.test_health()
    tester.test_root()
    tester.test_info()
    
    # 人脸对比测试
    # 注意：请替换为实际的测试图片路径
    print("\n" + "="*60)
    print("⚠️  人脸对比测试需要提供测试图片")
    print("请在代码中修改 image1_path 和 image2_path 变量")
    print("="*60)
    
    # 示例（取消注释并修改路径）:
    # tester.test_compare_faces("test_images/person1_a.jpg", "test_images/person1_b.jpg")
    # tester.test_compare_faces("test_images/person1.jpg", "test_images/person2.jpg")
    
    # 性能测试（取消注释并修改路径）:
    # tester.test_performance("test_images/person1.jpg", "test_images/person2.jpg", num_requests=10)
    
    print("\n" + "✅ 测试完成！" + "\n")


if __name__ == "__main__":
    main()

