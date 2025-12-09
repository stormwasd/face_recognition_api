# 人脸识别API接口文档

## 概述

本文档详细说明人脸识别API服务的关键接口。所有接口均使用RESTful风格，支持JSON格式的请求和响应。

**基础URL**: `http://localhost:8000`

**内容类型**: `application/json`

---

## 1. 人脸对比接口

### 接口信息

- **URL**: `/compare_faces`
- **方法**: `POST`
- **描述**: 比较两张人脸图片是否为同一个人，返回相似度分数和置信度等级

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| image1 | string | 是 | 第一张图片的base64编码字符串。支持带或不带data URI前缀（如 `data:image/jpeg;base64,`） |
| image2 | string | 是 | 第二张图片的base64编码字符串。支持带或不带data URI前缀 |

**支持的图片格式**: JPG, JPEG, PNG, WEBP

**文件大小限制**: 最大 10MB（base64编码前）

### 请求示例

#### cURL

```bash
curl -X POST "http://localhost:8000/compare_faces" \
  -H "Content-Type: application/json" \
  -d '{
    "image1": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "image2": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
  }'
```

#### Python

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

result = response.json()
print(f"是否同一人: {result['is_same_person']}")
print(f"相似度: {result['similarity']:.2%}")
```

#### JavaScript (Node.js)

```javascript
const fs = require('fs');
const axios = require('axios');

// 读取图片并转换为base64
const image1 = fs.readFileSync('person1.jpg').toString('base64');
const image2 = fs.readFileSync('person2.jpg').toString('base64');

// 发送请求
axios.post('http://localhost:8000/compare_faces', {
  image1: image1,
  image2: image2
})
.then(response => {
  console.log('结果:', response.data);
})
.catch(error => {
  console.error('错误:', error.response.data);
});
```

### 响应格式

#### 成功响应 (200 OK)

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

#### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| is_same_person | boolean | 是否为同一个人。true表示是同一个人，false表示不是 |
| similarity | float | 相似度分数，范围0-1。越接近1表示越相似 |
| confidence | string | 置信度等级。可能的值：`高`、`中`、`低`、`无` |
| face1_detected | boolean | 第一张图片是否检测到人脸 |
| face2_detected | boolean | 第二张图片是否检测到人脸 |
| message | string | 详细的结果说明信息 |
| processing_time | float | 服务器处理时间，单位毫秒 |

#### 错误响应

**400 Bad Request** - 请求参数错误

```json
{
  "detail": "base64解码失败: Invalid base64-encoded string"
}
```

**400 Bad Request** - 图片格式不支持

```json
{
  "detail": "不支持的图片格式。支持的格式: .jpg, .jpeg, .png, .webp"
}
```

**400 Bad Request** - 图片过大

```json
{
  "detail": "图片过大。最大支持 10MB"
}
```

**500 Internal Server Error** - 服务器内部错误

```json
{
  "detail": "服务器内部错误: [错误详情]"
}
```

### 相似度阈值说明

- **高置信度** (≥ 0.75): 非常高的相似度，几乎可以确定是同一个人
- **中置信度** (0.60 - 0.75): 中等相似度，可能是同一个人
- **低置信度** (< 0.60): 相似度较低，可能不是同一个人
- **判断阈值** (≥ 0.65): 默认判断为同一人的阈值

### 注意事项

1. **base64编码**: 图片必须进行base64编码，可以直接使用base64字符串，也可以使用data URI格式
2. **图片质量**: 建议使用清晰、正面的人脸图片，以获得最佳识别效果
3. **多人脸处理**: 如果图片中有多张人脸，系统会自动选择面积最大的人脸进行识别
4. **性能**: 单次请求处理时间通常在200-400ms之间，取决于图片大小和服务器性能

---

## 2. 服务信息接口

### 接口信息

- **URL**: `/info`
- **方法**: `GET`
- **描述**: 获取服务的配置信息和运行参数

### 请求示例

```bash
curl http://localhost:8000/info
```

### 响应格式

```json
{
  "model": "buffalo_l",
  "detection_size": [640, 640],
  "similarity_threshold": 0.65,
  "max_file_size_mb": 10,
  "supported_formats": [".jpg", ".jpeg", ".png", ".webp"],
  "thread_pool_workers": 8
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| model | string | 使用的InsightFace模型名称 |
| detection_size | array | 人脸检测尺寸 [宽度, 高度] |
| similarity_threshold | float | 判断同一人的相似度阈值 |
| max_file_size_mb | integer | 最大文件大小（MB） |
| supported_formats | array | 支持的图片格式列表 |
| thread_pool_workers | integer | 线程池工作线程数 |

---

## 3. 健康检查接口

### 接口信息

- **URL**: `/health`
- **方法**: `GET`
- **描述**: 检查服务运行状态和模型加载情况

### 请求示例

```bash
curl http://localhost:8000/health
```

### 响应格式

```json
{
  "status": "healthy",
  "service": "人脸识别API",
  "version": "1.0.0",
  "model_loaded": true,
  "model_name": "buffalo_l"
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| status | string | 服务状态，`healthy`表示正常 |
| service | string | 服务名称 |
| version | string | 服务版本号 |
| model_loaded | boolean | 模型是否已加载 |
| model_name | string | 模型名称 |

---

## 4. 服务根路径

### 接口信息

- **URL**: `/`
- **方法**: `GET`
- **描述**: 获取服务基本信息和可用接口列表

### 请求示例

```bash
curl http://localhost:8000/
```

### 响应格式

```json
{
  "service": "人脸识别API",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "比较人脸": "/compare_faces",
    "服务信息": "/info",
    "API文档": "/docs",
    "健康检查": "/health",
    "监控指标": "/metrics"
  },
  "documentation": "/docs"
}
```

---

## 5. 监控指标接口

### 接口信息

- **URL**: `/metrics`
- **方法**: `GET`
- **描述**: 获取Prometheus格式的监控指标

### 请求示例

```bash
curl http://localhost:8000/metrics
```

### 响应格式

Prometheus格式的文本数据，包含：
- `face_recognition_requests_total`: 总请求数
- `face_recognition_request_duration_seconds`: 请求耗时
- `face_comparison_results_total`: 对比结果统计

---

## 交互式API文档

启动服务后，可以通过以下地址访问交互式API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

这些文档提供了完整的接口说明、请求示例和在线测试功能。

---

## 错误码说明

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误（如base64格式错误、图片格式不支持、图片过大等） |
| 500 | 服务器内部错误 |

---

## 最佳实践

1. **图片预处理**: 建议在上传前对图片进行适当压缩，以减少传输时间和处理时间
2. **错误处理**: 始终检查HTTP状态码，并处理可能的错误响应
3. **超时设置**: 建议设置合理的请求超时时间（如5-10秒）
4. **重试机制**: 对于网络错误或临时服务器错误，可以实现重试机制
5. **批量处理**: 如需处理多组图片对比，建议使用异步方式或批量接口（如支持）

---

## 技术支持

如有问题或建议，请查看项目文档或提交Issue。

