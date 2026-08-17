# DeepSeek 翻译功能快速开始

## 🚀 快速开始（5分钟）

### 1. 安装依赖
```bash
cd backend
pip install openai==1.54.5
```

### 2. 配置 API Key
在 `backend/.env` 文件中添加：
```env
DEEPSEEK_API_KEY=sk-your-api-key-here
```

### 3. 启动后端服务
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 4. 运行测试脚本
```bash
# 编辑 test_translation.py，设置 API_KEY
python test_translation.py
```

## 📝 API 使用示例

### 示例1: 测试连接
```bash
curl -X POST "http://localhost:8000/api/v1/translation/test?api_key=sk-xxx"
```

### 示例2: 生成预翻译文件
```bash
curl -X POST "http://localhost:8000/api/v1/translation/prepare/sample_paper?source_lang=en&target_lang=zh-CN&use_dps=false"
```

### 示例3: 执行翻译
```bash
curl -X POST "http://localhost:8000/api/v1/translation/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_name": "sample_paper",
    "api_key": "sk-xxx",
    "use_dps": false,
    "max_concurrent": 5
  }'
```

### 示例4: 获取翻译结果
```bash
curl "http://localhost:8000/api/v1/translation/result/sample_paper?use_dps=false"
```

## 📊 翻译流程

```
上传PDF → 生成预翻译文件 → 执行翻译 → 获取结果
   ↓              ↓              ↓          ↓
/upload   /translation/prepare  /translation/translate  /translation/result
```

## 💡 常用配置

### 并发数选择
- **小文档（<20页）**: `max_concurrent=3`
- **中等文档（20-50页）**: `max_concurrent=5`
- **大文档（>50页）**: `max_concurrent=3`（避免限流）

### 温度参数
- **翻译任务**: `temperature=0.3`（推荐，保证稳定性）
- **创意改写**: `temperature=0.7`（不推荐用于学术翻译）

### 模型选择
- **deepseek-chat**: 非思考模式，速度快，适合翻译
- **deepseek-reasoner**: 思考模式，速度慢，适合复杂推理

## 🔧 故障排查

### 问题1: "DeepSeek API Key is required"
**解决**: 检查 `.env` 文件中是否配置了 `DEEPSEEK_API_KEY`

### 问题2: "预翻译文件不存在"
**解决**: 先调用 `/translation/prepare` 接口生成预翻译文件

### 问题3: 翻译速度慢
**解决**: 
- 降低 `max_concurrent` 避免限流
- 检查网络连接
- 查看 DeepSeek API 状态

### 问题4: 部分任务翻译失败
**解决**: 
- 检查失败任务的错误信息
- 可能是 token 超限，尝试降低 `max_concurrent`
- 重新翻译失败的任务

## 📦 文件输出

翻译完成后，结果保存在：
```
storage/parsed/{pdf_name}/{pdf_name}_translation.json
```

包含：
- ✅ 所有任务的翻译结果
- ✅ 成功/失败状态
- ✅ 统计信息（成功率等）
- ✅ 错误信息（如果有）

## 🎯 下一步

1. **前端集成**: 在前端添加翻译按钮，调用翻译接口
2. **进度显示**: 添加 WebSocket 实时显示翻译进度
3. **结果展示**: 在PDF标注页面展示翻译结果
4. **双语PDF**: 生成中英对照的PDF文档

## 💰 费用预估

DeepSeek API 定价（参考官网）：
- **输入**: 约 ¥0.001/1K tokens
- **输出**: 约 ¥0.002/1K tokens

示例：15页论文，约50K tokens（输入+输出）
- 预估费用: ¥0.05 - ¥0.10

**提示**: 先用小文档测试，再处理大文档

## 🤝 获取帮助

- 📖 完整文档: [README.md](./README.md)
- 🌐 DeepSeek 官网: https://platform.deepseek.com/
- 💬 技术支持: 查看项目 Issues
