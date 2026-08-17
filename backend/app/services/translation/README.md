# DeepSeek 翻译服务使用说明

## 概述
本项目已集成 DeepSeek API 翻译功能，支持学术论文的高质量翻译。

## 功能特点
- ✅ 异步批量翻译，支持并发控制
- ✅ 按优先级分组翻译（标题 > 正文 > 注释）
- ✅ 智能上下文处理（区分标题、段落、图表标题等）
- ✅ 翻译结果自动保存
- ✅ 支持 Python 和 DPS 两种解析模式
- ✅ 翻译进度追踪（可选）

## 配置步骤

### 1. 获取 DeepSeek API Key
访问 [DeepSeek 官网](https://platform.deepseek.com/) 注册并获取 API Key

### 2. 配置环境变量
在 `backend/.env` 文件中添加：
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TEMPERATURE=0.3
DEEPSEEK_MAX_TOKENS=4096
DEEPSEEK_TIMEOUT=60
```

### 3. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

新增依赖：
- `openai==1.54.5`（DeepSeek API 与 OpenAI 兼容）

## API 接口

### 1. 测试 API 连接
```bash
POST /api/v1/translation/test?api_key=your_api_key
```

**响应示例**：
```json
{
  "code": 200,
  "message": "DeepSeek API 连接正常",
  "data": {
    "success": true,
    "model": "deepseek-chat",
    "response": "Hello! How can I assist you today?"
  }
}
```

### 2. 生成预翻译文件
```bash
POST /api/v1/translation/prepare/sample_paper?source_lang=en&target_lang=zh-CN&use_dps=false
```

**参数说明**：
- `pdf_name`: PDF文件名（路径参数）
- `source_lang`: 源语言代码（默认 "en"）
- `target_lang`: 目标语言代码（默认 "zh-CN"）
- `aggregate_titles`: 是否聚合标题（默认 false）
- `use_dps`: 是否使用DPS模式（默认 false）
- `force`: 是否强制重新生成（默认 false）

**响应示例**：
```json
{
  "code": 200,
  "message": "Python模式预翻译任务准备完成",
  "data": {
    "total_pages": 15,
    "total_elements": 104,
    "ordered_elements": 85,
    "aggregated_tasks": 10,
    "single_tasks": 15,
    "unordered_tasks": 19
  }
}
```

### 3. 执行翻译
```bash
POST /api/v1/translation/translate
Content-Type: application/json

{
  "pdf_name": "sample_paper",
  "api_key": "your_deepseek_api_key",
  "use_dps": false,
  "max_concurrent": 5
}
```

**请求参数**：
- `pdf_name`: PDF文件名
- `api_key`: DeepSeek API Key
- `use_dps`: 是否使用DPS模式（默认 false）
- `max_concurrent`: 最大并发数（1-20，默认 5）

**响应示例**：
```json
{
  "code": 200,
  "message": "翻译完成",
  "data": {
    "total_tasks": 44,
    "translated_tasks": 44,
    "success_count": 44,
    "failed_count": 0,
    "success_rate": "100.00%"
  }
}
```

### 4. 获取翻译结果
```bash
GET /api/v1/translation/result/sample_paper?use_dps=false
```

**响应示例**：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "pdf_name": "sample_paper",
    "source_lang": "en",
    "target_lang": "zh-CN",
    "parse_mode": "python",
    "translated_at": "2026-01-10T20:30:00",
    "statistics": {
      "total_tasks": 44,
      "translated_tasks": 44,
      "success_count": 44,
      "failed_count": 0,
      "success_rate": "100.00%"
    },
    "translation_tasks": [...]
  }
}
```

## 翻译流程

### 完整流程
```
1. 上传PDF → /api/v1/upload
2. 生成预翻译文件 → /api/v1/translation/prepare/{pdf_name}
3. 执行翻译 → /api/v1/translation/translate
4. 获取结果 → /api/v1/translation/result/{pdf_name}
```

### 使用示例（Python）
```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
PDF_NAME = "sample_paper"
API_KEY = "your_deepseek_api_key"

# 1. 测试连接
response = requests.post(f"{BASE_URL}/translation/test", params={"api_key": API_KEY})
print(response.json())

# 2. 生成预翻译文件
response = requests.post(
    f"{BASE_URL}/translation/prepare/{PDF_NAME}",
    params={
        "source_lang": "en",
        "target_lang": "zh-CN",
        "use_dps": False
    }
)
print(response.json())

# 3. 执行翻译
response = requests.post(
    f"{BASE_URL}/translation/translate",
    json={
        "pdf_name": PDF_NAME,
        "api_key": API_KEY,
        "use_dps": False,
        "max_concurrent": 5
    }
)
print(response.json())

# 4. 获取翻译结果
response = requests.get(
    f"{BASE_URL}/translation/result/{PDF_NAME}",
    params={"use_dps": False}
)
print(response.json())
```

## 文件存储结构
```
storage/parsed/{pdf_name}/
├── {pdf_name}_parsed.json          # Python解析结果
├── {pdf_name}_dps.json             # DPS解析结果
├── {pdf_name}_pretranslation.json  # Python模式预翻译文件
├── {pdf_name}_pretranslation_dps.json  # DPS模式预翻译文件
├── {pdf_name}_translation.json     # Python模式翻译结果
└── {pdf_name}_translation_dps.json # DPS模式翻译结果
```

## 翻译结果格式

翻译结果JSON包含以下字段：

```json
{
  "pdf_name": "sample_paper",
  "source_lang": "en",
  "target_lang": "zh-CN",
  "parse_mode": "python",
  "translated_at": "2026-01-10T20:30:00",
  "statistics": {
    "total_tasks": 44,
    "translated_tasks": 44,
    "success_count": 44,
    "failed_count": 0,
    "success_rate": "100.00%"
  },
  "translation_tasks": [
    {
      "task_id": "t_single_0_10",
      "is_aggregated": false,
      "page_num": 0,
      "block_id": 47,
      "reading_order": 10,
      "element_type": "section_title",
      "source_text": "Introduction",
      "translated_text": "引言",
      "context": "heading",
      "translate": true,
      "priority": "high",
      "status": "success"
    },
    {
      "task_id": "t_agg_0_11",
      "is_aggregated": true,
      "aggregated_blocks": [...],
      "element_type": "paragraph",
      "aggregated_text": "...",
      "translated_text": "...",
      "context": "body",
      "translate": true,
      "priority": "normal",
      "status": "success"
    }
  ]
}
```

## 注意事项

### 1. API Key 安全
- ⚠️ **不要在前端代码中硬编码 API Key**
- ⚠️ **不要将 `.env` 文件提交到 Git**
- ✅ 建议在前端提供 API Key 输入框，由用户自行配置
- ✅ 或者在后端配置文件中统一管理

### 2. 并发控制
- 建议并发数设置为 3-5，避免触发 API 限流
- DeepSeek API 有 RPM（每分钟请求数）限制
- 大文档可以分批翻译

### 3. 翻译质量
- `DEEPSEEK_TEMPERATURE=0.3`：较低温度适合翻译任务，保证稳定性
- 标题类元素使用更简洁的提示词
- 正文段落强调学术语言风格

### 4. 错误处理
- 翻译失败的任务会记录在 `translation_tasks` 中，`status` 字段为 `"failed"`
- 可以重新翻译失败的任务

### 5. 费用控制
- DeepSeek API 按 token 计费，建议查看官方定价
- 预估费用 = 输入 token 数 + 输出 token 数
- 可以先用小文档测试

## 后续优化方向

### 短期（可选）
- [ ] 添加 WebSocket 实时进度推送
- [ ] 支持翻译任务暂停/恢复
- [ ] 翻译结果人工校对接口

### 中期（规划中）
- [ ] 支持多种大模型（OpenAI、Claude、国内模型）
- [ ] 术语词典功能（专业术语自定义翻译）
- [ ] 翻译记忆功能（复用已翻译的段落）

### 长期（未来）
- [ ] 双语PDF生成
- [ ] 翻译质量评分
- [ ] 批量翻译管理

## 常见问题

### Q1: 提示 "DeepSeek API Key is required"
A: 请确保在 `.env` 文件中配置了 `DEEPSEEK_API_KEY`，或在请求中传入 `api_key` 参数。

### Q2: 翻译速度慢
A: 可以适当提高 `max_concurrent` 参数（建议不超过10），但注意不要触发 API 限流。

### Q3: 翻译结果不理想
A: 可以调整 `DEEPSEEK_TEMPERATURE` 参数，或修改 `deepseek_service.py` 中的提示词。

### Q4: 预翻译文件不存在
A: 请先调用 `/translation/prepare` 接口生成预翻译文件。

### Q5: 支持哪些语言？
A: 理论上支持所有 DeepSeek 支持的语言，但翻译质量取决于模型能力。目前测试过中英互译效果良好。

## 技术支持
如有问题，请参考：
- DeepSeek 官方文档：https://platform.deepseek.com/docs
- OpenAI SDK 文档：https://github.com/openai/openai-python
