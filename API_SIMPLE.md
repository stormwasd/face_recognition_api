# 人脸识别API接口文档

## 基础信息

- **基础URL**: `http://localhost:8000`
- **请求格式**: `application/json`
- **响应格式**: `application/json`

---

## 1. 人脸对比接口

### 接口信息

- **URL**: `/compare_faces`
- **方法**: `POST`
- **描述**: 比较两张人脸图片是否为同一个人

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| image1 | string | 是 | 第一张图片的base64编码字符串（支持带或不带data URI前缀） |
| image2 | string | 是 | 第二张图片的base64编码字符串（支持带或不带data URI前缀） |

**支持的图片格式**: JPG, JPEG, PNG, WEBP

**文件大小限制**: 最大 10MB（base64编码前）

### 响应字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| is_same_person | boolean | 是否为同一个人。true表示是同一个人，false表示不是 |
| similarity | float | 相似度分数，范围0-1。越接近1表示越相似 |
| confidence | string | 置信度等级。可能的值：`高`、`中`、`低`、`无` |
| face1_detected | boolean | 第一张图片是否检测到人脸 |
| face2_detected | boolean | 第二张图片是否检测到人脸 |
| message | string | 详细的结果说明信息 |
| processing_time | float | 服务器处理时间，单位毫秒 |

### 响应示例

**成功响应 (200 OK)**
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

### 错误响应

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

---

## 2. 服务信息接口

### 接口信息

- **URL**: `/info`
- **方法**: `GET`
- **描述**: 获取服务的配置信息和运行参数

### 响应字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| model | string | 使用的InsightFace模型名称 |
| detection_size | array | 人脸检测尺寸 [宽度, 高度] |
| similarity_threshold | float | 判断同一人的相似度阈值 |
| max_file_size_mb | integer | 最大文件大小（MB） |
| supported_formats | array | 支持的图片格式列表 |
| thread_pool_workers | integer | 线程池工作线程数 |

### 响应示例

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

---

## 3. 健康检查接口

### 接口信息

- **URL**: `/health`
- **方法**: `GET`
- **描述**: 检查服务运行状态和模型加载情况

### 响应字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| status | string | 服务状态，`healthy`表示正常 |
| service | string | 服务名称 |
| version | string | 服务版本号 |
| model_loaded | boolean | 模型是否已加载 |
| model_name | string | 模型名称 |

### 响应示例

```json
{
  "status": "healthy",
  "service": "人脸识别API",
  "version": "1.0.0",
  "model_loaded": true,
  "model_name": "buffalo_l"
}
```

---

## HTTP状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误（如base64格式错误、图片格式不支持、图片过大等） |
| 500 | 服务器内部错误 |

---

## 注意事项

1. **base64编码**: 图片必须进行base64编码，可以直接使用base64字符串，也可以使用data URI格式（如 `data:image/jpeg;base64,xxx`）
2. **图片质量**: 建议使用清晰、正面的人脸图片，以获得最佳识别效果
3. **多人脸处理**: 如果图片中有多张人脸，系统会自动选择面积最大的人脸进行识别
