# PDF文档特征分析系统

## 功能概述

在PDF解析和预标注完成后，自动分析文档的版面特征，提取并保存有助于后续处理的布局参数和统计信息。

## 核心功能

### 1. 强段落宽度分析 (Paragraph Width Analysis)

**目标**：识别文档中具有统一宽度的"强段落"，为标题元素的宽度调整提供参考。

**分析逻辑**：
- 统计所有宽度 > 30% 页面宽度的文本元素
- 对宽度进行聚类分析（5%精度分桶）
- 找到出现次数最多的宽度簇
- 判断是否为"强段落"：出现次数 ≥10 或 占比 >30%

**应用场景**：
- 对于学术论文，段落宽度往往是相同的
- 标题元素可能宽度不一致，但应该匹配段落宽度
- 双语PDF生成时，可以使用这个宽度作为标题的最大宽度限制

**输出参数**：
```json
{
  "has_strong_paragraph": true,
  "strong_paragraph_width_ratio": 0.7234,
  "strong_paragraph_width_px": 483.67,
  "occurrence_count": 245,
  "total_samples": 312,
  "confidence": 0.7853,
  "width_distribution": {
    "0.70": 245,
    "0.50": 43,
    "0.85": 24
  }
}
```

### 2. 布局统计 (Layout Statistics)

**目标**：提供文档整体布局的统计信息。

**统计内容**：
- 总页数、总元素数
- 已标注元素数量
- 各标注类型的数量分布
- 平均页面尺寸
- 元素类型（text/image）统计

**输出参数**：
```json
{
  "total_pages": 14,
  "avg_page_size": {
    "width": 595.27,
    "height": 841.89
  },
  "total_elements": 1234,
  "annotated_elements": 856,
  "annotation_type_counts": {
    "paragraph": 345,
    "section_title": 45,
    "figure": 23
  }
}
```

### 3. 字体使用分析 (Font Usage Analysis)

**目标**：分析文档中字体和字号的使用情况。

**分析内容**：
- 唯一字体数量
- 最常用的字体、字号
- 最常用的字体+字号组合
- 字体和字号的分布统计

**应用场景**：
- 识别正文字体和标题字体
- 为文本渲染提供参考
- 检测异常字体使用

**输出参数**：
```json
{
  "unique_fonts": 8,
  "total_font_usage": 1234,
  "most_common_font": {
    "font": "Times-Roman",
    "count": 856,
    "percentage": 0.6938
  },
  "most_common_size": {
    "size": 10.0,
    "count": 789,
    "percentage": 0.6394
  },
  "most_common_font_size": {
    "font": "Times-Roman",
    "size": 10.0,
    "count": 745,
    "percentage": 0.6037
  }
}
```

## 架构设计

### 模块化设计

```python
DocumentAnalyzer
├── analyze_document()           # 主入口，协调所有分析器
├── _analyze_paragraph_width()   # 分析器1：段落宽度
├── _analyze_layout_statistics() # 分析器2：布局统计
├── _analyze_font_usage()        # 分析器3：字体使用
└── [扩展] _analyze_xxx()        # 未来可添加更多分析器
```

### 可扩展性

1. **新增分析器**：在 `DocumentAnalyzer` 类中添加 `_analyze_xxx()` 方法
2. **在主函数中调用**：在 `analyze_document()` 中调用新分析器
3. **记录到元数据**：将结果保存到 `metadata` 字典中
4. **更新版本号**：修改 `metadata["version"]` 字段

示例：
```python
def analyze_document(self, pdf_name: str, force: bool = False) -> Dict:
    # ... 现有代码 ...
    
    # 4. 新增：分析表格布局
    table_analysis = self._analyze_table_layout(parsed_data)
    metadata["table_layout_analysis"] = table_analysis
    metadata["analyzers"].append("table_layout")
    
    # ... 现有代码 ...
```

## 数据存储

### 存储位置
```
storage/parsed/{pdf_id}/document_metadata.json
```

### 数据结构
```json
{
  "pdf_name": "example.pdf",
  "version": "1.0",
  "analyzers": [
    "paragraph_width",
    "layout_statistics",
    "font_usage"
  ],
  "paragraph_width_analysis": { ... },
  "layout_statistics": { ... },
  "font_analysis": { ... }
}
```

### 版本控制

- `version` 字段标识元数据格式版本
- 未来格式变更时可以基于版本号进行兼容处理
- `analyzers` 数组记录已运行的分析器

## 触发机制

### 自动触发
- 在 DPS 预标注完成后自动执行
- 位置：`annotation_service.py::preannotate_from_dps()`
- 如果元数据已存在，则跳过（除非 `force=True`）

### 手动触发
- API 接口：`GET /api/v1/annotation/{pdf_name}/metadata?force=true`
- 测试脚本：`python backend/test_document_analyzer.py`

## API 接口

### 获取文档元数据
```http
GET /api/v1/annotation/{pdf_name}/metadata
Query Parameters:
  - force: bool (default: false) - 是否强制重新分析

Response:
{
  "code": 200,
  "message": "success",
  "data": {
    "pdf_name": "example.pdf",
    "version": "1.0",
    "analyzers": [...],
    "paragraph_width_analysis": {...},
    "layout_statistics": {...},
    "font_analysis": {...}
  }
}
```

### 便捷方法
```python
# 在代码中使用
from app.services.document_analyzer import DocumentAnalyzer

analyzer = DocumentAnalyzer()

# 获取强段落宽度信息
strong_width = analyzer.get_strong_paragraph_width("example.pdf")
if strong_width and strong_width.get("has_strong_paragraph"):
    width_ratio = strong_width["strong_paragraph_width_ratio"]
    print(f"标题建议宽度: {width_ratio:.2%}")
```

## 使用示例

### 测试脚本

运行测试脚本查看分析结果：

```bash
cd backend
python test_document_analyzer.py
```

输出示例：
```
📄 找到已解析的PDF: example.pdf
================================================================================

🔍 开始分析文档特征...
✅ 分析完成！
================================================================================

📊 段落宽度分析:
--------------------------------------------------------------------------------
  是否有强段落: ✅ 是
  强段落宽度比例: 72.34%
  强段落宽度(像素): 483.67px
  出现次数: 245/312
  置信度: 78.53%

  宽度分布（前5）:
    1. 70.00% 宽度 -> 245次
    2. 50.00% 宽度 -> 43次
    3. 85.00% 宽度 -> 24次

📐 布局统计:
--------------------------------------------------------------------------------
  总页数: 14
  总元素数: 1234
  已标注元素: 856
  平均页面尺寸: 595.27 x 841.89

  标注类型统计:
    - paragraph: 345
    - section_title: 45
    - figure: 23

🔤 字体分析:
--------------------------------------------------------------------------------
  唯一字体数: 8
  字体使用总次数: 1234

  最常用字体:
    字体名: Times-Roman
    使用次数: 856
    占比: 69.38%

================================================================================
📁 元数据已保存到: storage/parsed/abc123/document_metadata.json
📋 已运行分析器: paragraph_width, layout_statistics, font_usage
```

## 未来扩展方向

1. **表格结构分析**
   - 统计表格的行列数分布
   - 识别常见的表格模式

2. **公式密度分析**
   - 统计公式元素的分布
   - 识别数学密集型章节

3. **图表位置模式**
   - 分析图表在页面中的位置偏好
   - 为图表排版提供参考

4. **段落间距分析**
   - 统计段落间的垂直间距
   - 为排版提供间距参考

5. **标题层级推断**
   - 基于字体大小和位置推断标题层级
   - 辅助自动标注

## 性能考虑

- **执行时机**：预标注完成后自动执行，不阻塞主流程
- **缓存机制**：元数据文件持久化，避免重复计算
- **增量更新**：已存在的元数据默认不重新计算（除非 force=True）
- **失败容错**：分析失败不影响预标注结果的保存

## 注意事项

1. 文档分析依赖于预标注结果，必须先完成 DPS 预标注
2. 分析结果保存为独立的 JSON 文件，不影响原始解析数据
3. 强段落判断阈值可根据实际情况调整（当前：出现≥10次或占比>30%）
4. 宽度聚类精度为5%，可根据需要调整桶大小
