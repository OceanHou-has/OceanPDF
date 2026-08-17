---
trigger: always_on
---

 OceanPDF 2.0 桌面端PDF论文翻译软件

## 项目概述
桌面端PDF论文翻译软件，支持PDF文档的智能解析、AI翻译和双语对照排版。

## 当前开发状态 (2026-01-17)

### 已完成功能模块

#### ✅ 1. 前端界面框架
- **主页面布局** (Home.vue)
  - 左侧深色导航栏（Logo、菜单项、版本信息）
  - 顶部导航栏（页面标题、描述、操作按钮）
  - 主内容区域（动态切换视图）
  - 支持"上传翻译"和"已解析PDF"两个视图切换

#### ✅ 2. PDF上传功能
- **上传组件** (UploadPanel.vue)
  - 拖拽上传支持
  - 文件选择上传
  - 支持批量选择/拖拽多个PDF加入队列
  - 文件格式验证（仅PDF）
  - **智能进度显示**（优化后）
    - 上传阶段（0-20%）：文件上传到服务器，蓝色进度条
    - 解析阶段（20-95%）：模拟后端解析进度，紫色渐变进度条
    - 完成阶段（95-100%）：快速跳转到100%
    - 根据文件大小和OCR选项智能估算解析时间
    - 使用缓动函数使进度更平滑自然
    - 不同阶段显示不同状态文本（"文件上传中" / "OCR识别中" / "版面分析中"）
  - 响应式布局（动态高度调整）
  - **OCR开关**：每个PDF条目提供独立OCR开关（默认关闭）
    - 开启：上传时携带 `with_ocr=true`，触发DPS执行OCR并聚合文本
    - 关闭：上传时携带 `with_ocr=false`，只执行版面分析（不做OCR）
  - **并行度设置**：在主页面顶部栏提供并行度设置（默认2，可调），用于控制批量解析并发数
  - **单/多文件完成交互**
    - 单文件：解析完成后跳转到标注页面
    - 多文件：批量结束后切换到“已解析PDF”列表视图
  
- **重复检测**
  - 上传前检查是否已解析过同名PDF
  - 如已存在，直接跳转到标注页面，无需重复解析
  - 提示消息区分新上传和已存在
  - **OCR补齐策略**：若开启OCR，会触发DPS结果补齐/校验（确保OCR文本可用）

#### ✅ 3. PDF解析功能（基础版）
- **后端解析服务** (pdf_parser.py)
  - 使用PyMuPDF进行行级文本提取
  - 提取bbox坐标、字体信息（名称、大小、颜色）
  - 按页面组织数据结构
  - 保存为JSON格式：`storage/parsed/{pdf_id}/parsed.json`（{pdf_id} 为8位短ID）

- **DPS版面分析 + OCR**（已完整实现）
  - 调用外部DPS服务获取版面框与OCR聚合文本
  - 保存为JSON格式：`storage/parsed/{pdf_id}/dps.json`（{pdf_id} 为8位短ID）
  - 已解析PDF若缺少DPS结果，会在上传/重复检测路径中自动补齐
  - OCR文本按空格连接（非换行符），适合后续翻译处理
  - 支持模块化架构，启动性能优化（并行加载/懒加载）
  - **阅读顺序标记**：每个box包含 `DPS_block_id` 和 `reading_order` 字段（每页从1开始）

- **存储结构**
  ```
  storage/
  ├── uploads/           # PDF原文件
  │   └── {uuid}_{filename}.pdf
  ├── pdf_mappings.json  # {pdf_id} <-> {pdf_name} 映射（解决长路径/长文件名）
  └── parsed/            # 解析结果
      └── {pdf_id}/      # 按短ID分组
          ├── parsed.json
          ├── dps.json
          ├── pretranslation.json / pretranslation_dps.json
          ├── translation.json / translation_dps.json
          └── document_metadata.json
  ```

#### ✅ 4. PDF标注查看界面
- **标注页面** (PDFAnnotation.vue)
  - 顶部工具栏：返回、PDF名称、翻页控制、缩放控制、保存按钮、解析结果切换开关（Python / DPS）
  - PDF图片显示（PyMuPDF渲染，2倍缩放）
  - 透明遮罩层：防止点击穿透到PDF图片
  - 文本框标注：点击选中，显示黄色高亮边框
  - 已标注元素：显示对应类型颜色边框+右上角标签
  - 悬停显示文本内容（黑色半透明tooltip）
  - 支持Ctrl+滚轮缩放（0.5x - 3.0x）
  - 页码显示和翻页功能
  - **批量框选功能**
    - 支持拖拽框选多个元素
    - 实时显示半透明选择框
    - 完全包含策略：只选中完全在框内的元素
    - 自适应缩放：任意缩放级别下坑位准确
  - **坐标对齐**
    - 不再依赖固定“bbox乘2”的假设，改为基于“页面参考宽高 -> 当前渲染图片宽高”的动态缩放映射
  - **DPS模式**
    - DPS结果支持在前端进行标注与手动排序
    - 保存时通过 `POST /api/v1/annotation/batch` 携带 `use_dps=true` 写入 `storage/parsed/{pdf_id}/dps.json`
    - 限制：DPS模式不支持合并/拆解操作（后端会拒绝）

- **浮动标注面板** (AnnotationPanel.vue)
  - 可拖动的浮动面板，位置可自由调整
  - 12种标注类型按钮（2列网格布局）
  - 每个按钮显示颜色块+中文标签
  - 实时显示待保存数量和选中数量
  - 支持单选和多选模式
  - 清除标注按钮

- **批量保存机制**
  - 所有标注操作立即在前端显示效果
  - 暂存在前端 pendingAnnotations 数组
  - 点击“保存标注”按钮使用批量 API 一次性提交
  - 智能去重：同一元素多次标注只保留最后一次
  - 性能优化：100个标注从 20秒 → 0.5秒（提升40倍）

#### ✅ 5. 已解析PDF管理
- **列表界面** (ParsedList.vue)
  - 全宽一条一条展示已解析的PDF
  - 每条显示：图标、PDF名称、页数、解析时间
  - **OCR状态显示**：绿色徽章（已OCR）/ 灰色徽章（未OCR）
  - **翻译状态显示**：
    - 绿色徽章：已完成 (10/10)
    - 蓝色脉冲徽章：正在翻译中 85% (8/10)
    - 橙色徽章：翻译中 (5/10)
    - 灰色徽章：未翻译
  - **状态实时更新机制**：
    - 后端明确返回 `translation_status`: "none" | "in_progress" | "completed"
    - 后端准确统计翻译进度（使用 translation_tasks 结构）
    - 前端轮询 active_translations 检查活跃任务（2秒间隔）
    - 翻译完成后继续刷新2次确保数据同步
    - 状态判断优先级：已完成 > 正在翻译 > 翻译中 > 未翻译
  - 操作按钮：查看标注、**查看翻译**、删除（立即删除，不询问）
  - 顶部导航栏集成刷新按钮（仅在此视图显示）
  - 点击任意位置打开标注页面
  - **查看翻译功能**：
    - 只要有翻译结果文件就可以点击查看
    - 跳转到翻译执行界面（只读模式）
    - 不需要传递 API Key，直接加载已有翻译结果
    - 支持刷新查看最新进度
  - **自动刷新**
    - 切换到“已解析PDF”视图时自动刷新列表
    - 批量解析过程中每完成一个PDF，会触发列表刷新（无需手动点刷新）

- **删除功能**
  - 删除解析结果目录
  - 删除原始PDF文件
  - 自动刷新列表

#### ✅ 6. PDF元素标注功能
- **标注服务** (backend/app/services/annotation/)
  - annotation_service.py: 核心标注业务逻辑
  - paper_analyzer.py: 论文版面分析器（基于DPS结果分析论文布局）
  - 支持12种标注类型
  - 每种类型配有独特的颜色代码

- **论文版面分析器** (paper_analyzer.py)
  - **数据来源**: 基于DPS版面分析结果（dps.json）进行聚类分析
  - **两次聚类算法**:
    - 第一次：对宽度>10%的元素按宽度聚类（5%精度分桶），识别最常见宽度类别（强段落）
    - 第二次：仅对强段落元素按X坐标聚类（10像素精度分桶），识别栏数
  - **强段落识别**: 最常见宽度类别±2.5%容差范围内的元素
  - **显著簇阈值**: 10%的样本数量
  - **栏数判断**: 根据显著X坐标簇数量判断单栏/双栏/三栏
  - **栏位置信息**: 只记录X坐标和样本数（不包含Y坐标）
  - **元数据存储**: 分析结果保存到 `document_metadata.json`
  - **自动/手动触发**: 首次解析后自动分析，也可通过API手动触发
  - **前端展示**: 在详情面板显示强段落宽度、栏数、栏位置信息

- **标注类型**
  - document_title: 文档标题 (#FF6B6B 红色)
  - section_title: 章节标题 (#4ECDC4 青色)
  - paragraph: 段落 (#45B7D1 蓝色)
  - list: 列表 (#96CEB4 绿色)
  - display_formula: 公式 (#7C3AED 紫色)
  - formula_caption: 公式标题 (#A78BFA 浅紫)
  - figure: 图片 (#FD79A8 粉色)
  - figure_caption: 图片标题 (#FDCB6E 橙色)
  - table: 表格 (#A29BFE 紫色)
  - table_caption: 表格标题 (#74B9FF 浅蓝)
  - table_footnote: 表格注释 (#81ECEC 浅青)
  - abandon: 废弃 (#B2BEC3 深灰)

- **标注流程**
  1. 单选模式：点击PDF元素框 → 元素高亮（黄色发光边框）
  2. 批量模式：在PDF空白处拖拽 → 显示选择框 → 选中多个元素
  3. 点击面板上的类型按钮 → 立即显示对应颜色和标签
  4. 继续标注其他元素...
  5. 点击"保存标注"按钮 → 批量提交到后端保存

- **数据存储**
  - 标注信息直接保存在解析结果JSON文件中
  - 每个line对象包含 type 字段（默认为null）
  - **阅读顺序字段**：`reading_order` 字段来自DPS版面分析，在预标注时写入
  - 合并元素框的数据结构：
    - `block_id`: 全局唯一标识（格式：p{page_num}_merged_{8位随机码}）
    - `bbox`: 所有源元素的最小包围矩形 [x0, y0, x1, y1]
    - `text`: 按顺序合并的所有源元素文本（空格分隔）
    - `type`: 标注类型
    - `is_merged`: true（标识为合并元素）
    - `source_ids`: 源元素的block_id数组（按原顺序）
    - `dps_label`: DPS原始标签
    - `reading_order`: 阅读顺序（来自DPS）
  - 被合并的源元素会添加：
    - `is_merged`: true
    - `parent_id`: 合并元素的block_id

#### ✅ 7. 元素框合并与拆解功能
- **合并标注对话框** (dialogs/MergeAnnotationDialog.vue)
  - 多选元素后点击标注按钮时弹出
  - 提供「合并标注」和「单独标注」两个选项
  - 卡片式交互设计，直观易用

- **合并逻辑**
  - 计算所有源元素的最小包围矩形作为合并框的bbox
  - 按顺序合并所有源元素的文本（空格分隔）
  - 生成唯一的合并元素ID：`p{page_num}_merged_{8位随机码}`
  - 自动为源元素添加 `is_merged=true` 和 `parent_id` 属性
  - 合并元素添加到页面元素列表末尾
  - 前端立即显示合并效果，无需等待保存

- **拆解逻辑**
  - 点击「清除标注」按钮拆解合并元素
  - 还原所有源元素状态（删除 `is_merged` 和 `parent_id`）
  - 从元素列表中删除合并元素
  - 前端立即显示拆解效果，保存后同步到后端

- **特殊情况处理**
  - 嵌套合并：选中的元素中包含已合并元素时，先自动拆解再重新合并
  - 去重处理：避免同一元素被重复合并
  - 临时合并：未保存的合并可直接取消，无需后端操作
  - 已保存合并：清除标注时向后端发送拆解请求

- **前端显示规则**
  - 隐藏已被合并的源元素（`parent_id` 不为空）
  - 只显示合并后的元素框和未被合并的普通元素
  - 合并元素框显示对应的标注类型颜色和标签

- **数据一致性**
  - 前端批量提交，后端统一处理
  - 单次文件读写，保证性能
  - 保存后重新加载数据确保与后端同步

- **API字段处理**
  - 前端使用 `unmerge_from` 字段（不带下划线）
  - 后端接收后转换为 `_unmerge_from` 进行处理
  - Pydantic模型正确处理字段验证

#### ✅ 8. 阶段管理系统
- **阶段指示器** (dialogs/StageIndicator.vue)
  - 玻璃拟态设计，固定在右侧中间位置
  - 默认宽度 72px，鼠标悬停展开至 200px
  - 显示三个阶段：1-标注、2-排序、3-翻译
  - SVG圆环装饰，当前阶段高亮显示
  - 已完成阶段显示对勾标记
  - 默认解锁标注阶段，可随时进入排序阶段

- **阶段切换逻辑**
  - 通过 `currentStage` 控制界面显示
  - 阶段1：显示标注面板和所有元素框
  - 阶段2：只显示可排序元素（章节标题、段落、列表）
  - 阶段3：翻译配置（弹窗模式，不改变当前阶段显示）
  - **特殊处理**：点击阶段3只触发事件不更新currentStage，保持当前界面显示

#### ✅ 9. PDF阅读顺序功能
- **DPS阅读顺序来源**
  - DPS版面分析返回的boxes已按PP-DocLayoutV2模型的阅读顺序排列
  - 每个box包含 `DPS_block_id` 和 `reading_order` 字段（每页从1开始）
  - 可排序类型：doc_title、paragraph_title、abstract、text
  - 其他类型（图表、公式、页眉页脚等）的 reading_order 为 None

- **预标注时写入阅读顺序**
  - 在DPS预标注阶段，直接从DPS结果获取 `reading_order` 并写入
  - 单独标注：直接保存 `reading_order` 到元素
  - 合并标注：将 `reading_order` 赋值给新创建的合并元素框
  - 首次解析完成后，Python解析结果即包含正确的阅读顺序

- **自动排序服务** (backend/app/services/sorting/)
  - reading_order_service.py: 阅读顺序计算逻辑
  - 每页从1开始，按 block_id 自上而下排序
  - 合并元素使用第一个 source_ids 指向的元素 block_id
  - 只对可排序类型分配顺序：section_title、paragraph、list
  - document_title 不参与排序
  - **仅在用户操作后调用**：用户标注、合并、拆解元素后重新计算

- **手动排序模式**
  - 点击"手动排序"按钮进入模式（Python/DPS均支持）
  - 元素框变为绿色边框，带呼吸动画
  - 依次点击元素设置阅读顺序（1、2、3...）
  - 再次点击已设置元素可取消顺序
  - 取消后自动重排后续元素的顺序
  - 部分排序支持：未设置的元素自动按 block_id 排序并补全
  - 保存使用 `POST /api/v1/annotation/batch` 写入 `reading_order`（DPS模式需 `use_dps=true`）
  
- **DPS模式阅读顺序**
  - 默认：显示DPS生成的 `reading_order`
  - 手动排序：进入手动排序模式后可修改并保存到 `dps.json`

- **退出确认机制**
  - 手动排序中点击返回/翻页/切换阶段时弹窗确认
  - SaveSortingDialog.vue: 美化的确认对话框
  - 提供三个选项：取消操作、不保存、保存排序
  - 渐变背景、SVG图标、动画效果

- **排序元素显示**
  - 圆形徽章显示阅读顺序数字
  - 尺寸：42px x 42px，字体 18px
  - 配色：普通模式为紫色渐变，选中为橙色渐变
  - 手动排序模式为翠绿色渐变
  - 悬停放大、1.1倍缩放效果

#### ✅ 11. 翻译配置与执行系统
- **翻译配置对话框** (dialogs/TranslationConfigDialog.vue)
  - 现代化蓝绿渐变设计（#4facfe → #00f2fe）
  - 自定义标题栏，显示PDF名称
  - 玻璃拟态卡片式布局
  - **解析模式选择**
    - Python解析（推荐）：使用人工标注结果
    - DPS/OCR解析（快速）：直接使用OCR识别结果
    - 卡片式交互，可点击切换
  - **语言设置**
    - 源语言选择（支持英语、中文、日语、韩语等）
    - 目标语言选择（支持中文简体、繁体、英语等）
    - 旗帜emoji增强视觉识别
    - 中间渐变箭头动画效果
  - **高级选项**
    - 聚合标题开关（可选，不推荐）
    - 开启时显示警告提示框
  - **API Key 配置**
    - 输入框支持密码显示/隐藏
    - 测试连接按钮：快速验证 API Key 有效性（使用 models.list 接口，0.3-1秒）
    - 测试状态：默认/测试中/成功/失败，带颜色和图标提示
    - 自动保存：测试成功后自动保存到后端 `storage/config/translation_config.json`
    - 自动加载：每次打开对话框自动加载已保存的 API Key
    - watch 监听对话框打开状态，确保重复打开时也能加载
  - **翻译执行**
    - 点击「开始翻译」跳转到翻译执行页面
    - SSE实时推送翻译进度（事件队列机制，避免并发更新覆盖导致的漏推送）
    - 翻译结果逐条写入 `storage/parsed/{pdf_id}/translation.json`（DPS模式为 `translation_dps.json`）
    - **聚合块译文拆分回填**：优先使用 `<<<OCEANPDF_SPLIT>>>` 分隔标记直接切分；若标记缺失或段数不匹配，则按原始块原文字数比例切分（切点吸附标点/空白），不再二次调用模型

- **翻译执行界面** (views/TranslationExecution.vue)
  - 顶部导航栏：返回、PDF名称、翻译状态指示器、**刷新按钮**
  - 控制按钮：刷新、暂停、继续、停止、导出
  - 实时进度条：显示翻译进度百分比和完成数量
  - 统计信息：成功数、失败数
  - **刷新功能**（新增）
    - 在只读模式下（从列表点击查看翻译进入）可以刷新翻译结果
    - 重新加载 `storage/parsed/{pdf_id}/translation*.json` 文件内容
    - 更新译文显示和进度统计
    - 刷新时图标旋转动画
    - 防止重复刷新（isRefreshing 状态控制）
    - Toast 提示刷新结果（进度 / 已完成）
  - **双栏布局优化**
    - 左右两侧PDF在各自区域内水平居中显示
    - 默认宽度占满半个区域（根据容器宽度自动计算 displayWidth/displayHeight）
    - PDF图片保持纵横比，响应式调整
  - **滚动同步优化**
    - 使用 @wheel 事件替代 @scroll 事件
    - 左右两侧同时响应鼠标滚轮信号，流畅无卡顿
    - 无需防重入标志，消除了被动滚动的延迟
  - **换页性能优化**
    - 预加载相邻页面：换页后自动预加载前后页，下次换页无等待
    - 样式计算缓存：overlay 样式计算结果缓存，避免重复计算
    - 换页速度提升 70-80%，几乎无卡顿感
  - 元素级白板遮罩：按元素bbox在右侧覆盖同大小白板
  - 翻译中显示loading：未完成元素显示同bbox遮罩与loading动画
  - 翻译完成覆盖译文：完成后将译文直接渲染到对应bbox位置
  - **翻译控制功能**（已完整实现）
    - 暂停：暂停前端进度推送（断开SSE），后端任务继续执行
    - 继续：同步已完成译文后重新连接SSE继续接收进度
    - 停止：调用停止接口终止任务并清理结果文件
  - **队列模式翻译**：边执行边创建任务，支持真正的暂停/停止
  - **加载已有翻译**：页面初始化时检查并加载已完成的翻译结果
  - **只读模式支持**：从列表点击查看翻译时，不需要 API Key，直接加载已有结果

- **预翻译文件生成**
  - 服务端点：`POST /api/v1/translation/prepare/{pdf_name}`
  - 支持参数：source_lang, target_lang, aggregate_titles, use_dps
  - 返回统计信息：总页数、可翻译元素、聚合任务、独立任务、跨页聚合
  - 生成位置：`storage/parsed/{pdf_id}/pretranslation.json` 或 `pretranslation_dps.json`

- **交互流程**
  1. 点击阶段3 → 打开配置对话框（当前阶段不变）
  2. 对话框自动加载已保存的 API Key
  3. 选择配置参数 → 点击「测试连接」验证 API Key（0.3-1秒快速响应）
  4. 测试成功后自动保存 API Key 到本地
  5. 点击「生成预翻译文件」→ Toast提示统计信息 + 标记阶段2完成 + 切换到阶段3
  6. 点击「开始翻译」→ 跳转到翻译执行页面
  7. 双栏对照显示，左右滚动同步，换页流畅无卡顿
  8. 对话框保持打开，用户可继续调整或手动关闭
#### ✅ 10. 全局Toast系统
  - 玻璃拟态设计，半透明白色背景
  - 支持四种类型：success、error、warning、info
  - 每种类型有独特的颜色和SVG图标
  - 从右侧滑入动画
  - 默认显示 2 秒，可自定义时长

- **全局集成**
  - 在 App.vue 中挂载全局 Toast
  - 通过 `window.$toast` 调用
  - 替换所有 Element Plus 的 ElMessage
  - 统一项目中的提示信息风格

### 12. API Key 配置管理
- **后端配置存储**
  - 配置文件：`storage/config/translation_config.json`
  - 保存 DeepSeek API Key 到本地，持久化存储
  - 提供保存和读取接口
  - 返回脱敏版本（masked_key）用于日志记录

- **前端交互流程**
  - 打开翻译配置对话框时自动加载已保存的 API Key
  - 使用 watch 监听对话框打开状态，确保重复打开也能加载
  - 输入 API Key 后点击「测试连接」按钮
  - 测试使用轻量级 models.list 接口（0.3-1秒响应）
  - 测试成功后自动保存到后端
  - 下次打开自动填充，无需重复输入

- **错误识别优化**
  - 401/Unauthorized: "API Key 无效或已过期"
  - 403/Forbidden: "API Key 没有权限访问该服务"
  - 429/Rate limit: "API 请求频率过高，请稍后再试"
  - Timeout: "连接超时，请检查网络连接"

### 13. UI/UX体验优化

#### 后端接口 (端口: 8000)
✅ `POST /api/v1/upload?with_ocr={true|false}` - 上传PDF并解析（支持重复检测，可控是否执行OCR）
✅ `GET /api/v1/pdf/{pdf_name}/page/{page_num}` - 获取PDF页面图片（Base64，zoom=3.0高清渲染）
✅ `GET /api/v1/pdf/{pdf_name}/parsed` - 获取解析数据JSON
✅ `GET /api/v1/pdf/{pdf_name}/dps` - 获取DPS版面分析+OCR结果JSON
✅ `GET /api/v1/parsed-list` - 获取已解析PDF列表
✅ `DELETE /api/v1/pdf/{pdf_name}` - 删除已解析PDF及原文件
✅ `GET /api/v1/annotation/types` - 获取所有标注类型和颜色配置
✅ `POST /api/v1/annotation/annotate` - 标注PDF元素（单个）
✅ `POST /api/v1/annotation/clear` - 清除元素标注
✅ `POST /api/v1/annotation/batch` - 批量标注PDF元素（支持合并标注；DPS写入需 use_dps=true）
✅ `GET /api/v1/annotation/{pdf_name}/page/{page_num}` - 获取页面标注统计
✅ `GET /api/v1/annotation/{pdf_name}/metadata` - 获取文档元数据（包含论文版面分析结果）
✅ `POST /api/v1/annotation/{pdf_name}/analyze` - 手动触发论文版面分析
✅ `POST /api/v1/translation/prepare/{pdf_name}` - 生成预翻译文件（支持Python/DPS模式）
✅ `POST /api/v1/translation/test?api_key=...` - 测试DeepSeek API连通性（使用 models.list，0.3-1秒快速响应）
✅ `POST /api/v1/translation/config/api-key?api_key=...` - 保存 API Key 到本地配置
✅ `GET /api/v1/translation/config/api-key` - 获取已保存的 API Key
✅ `GET /api/v1/translation/pretranslation/{pdf_name}` - 获取预翻译任务清单
✅ `POST /api/v1/translation/translate` - 同步翻译（一次性返回统计）
✅ `POST /api/v1/translation/translate/async` - 创建异步翻译任务（返回task_id）
✅ `GET /api/v1/translation/progress/{task_id}` - SSE推送翻译进度与单条结果
✅ `GET /api/v1/translation/result/{pdf_name}?use_dps=...` - 获取翻译结果文件内容
✅ `POST /api/v1/translation/control/{task_id}/pause` - 暂停翻译任务
✅ `POST /api/v1/translation/control/{task_id}/resume` - 继续翻译任务
✅ `POST /api/v1/translation/control/{task_id}/stop` - 停止翻译任务（删除翻译文件）
✅ `GET /api/v1/translation/control/{task_id}/status` - 获取翻译任务控制状态
✅ `POST /api/v1/export/{pdf_name}` - 导出PDF（overlay / side_by_side / interleaved / translation_only）
✅ `GET /api/v1/export/{pdf_name}/status` - 获取导出状态
✅ `GET /api/v1/export/modes` - 获取导出模式列表
✅ `GET /api/v1/export/list?pdf_name=...` - 列出导出文件
✅ `GET /api/v1/export/download/{filename}` - 下载导出PDF
✅ `DELETE /api/v1/export/{filename}` - 删除导出PDF
✅ `GET /api/v1/export/fonts/status` - 字体可用状态

### 待开发功能

#### 🔲 翻译模块
- 多模型适配（在DeepSeek之外扩展到OpenAI/Claude/国内模型）
- 翻译任务管理
- 流式翻译输出（逐token级别到前端）
- 术语词典支持

**已完成**：
- ✅ 翻译配置界面
- ✅ 预翻译文件生成服务
- ✅ 元素聚合逻辑
- ✅ 双模式支持（Python/DPS）
- ✅ DeepSeek翻译执行（并发控制）
- ✅ SSE实时进度推送（任务级，事件队列防漏推送）
- ✅ 翻译结果逐条落盘（storage/parsed/{pdf_id}/translation.json 实时更新）
- ✅ 翻译执行界面（双栏对照显示）
- ✅ 翻译控制功能（暂停/继续/停止）
- ✅ 加载已有翻译结果
- ✅ 队列模式翻译（支持真正的暂停/停止）
- ✅ 聚合块译文拆分回填：优先 `<<<OCEANPDF_SPLIT>>>`，失败回退比例切分（无需二次模型请求）

**测试脚本（仓库内已有）**：
- `backend/test_title_adjustment.py`
- `DPS/test_ocr.py` / `DPS/test_layout_analysis.py`
  
**本地校验命令**：
- `python -m compileall backend\\app`

#### ✅ PDF导出
- overlay：先删除原文区域再写入译文
- side_by_side：左右对照（原文左，译文右）
- interleaved：交替排列（原文页后跟译文页）
- translation_only：纯译文PDF

#### 🔲 其他功能
- 任务列表页面
- 设置页面
- 批量翻译
- 翻译历史记录
- 标注数据导出功能
- 标注统计图表

### 技术架构

### 前端技术栈
- **框架**: Electron + Vue 3 (Composition API)
- **构建工具**: Vite
- **UI组件库**: Element Plus
- **状态管理**: Pinia
- **HTTP客户端**: Axios
- **样式**: SCSS
- **开发工具**: electron-builder (打包), electron-vite (开发)

### 后端架构（微服务）

#### 1. 主后端服务 (端口: 8000)
**技术栈**:
- 框架: FastAPI
- 异步支持: asyncio, aiohttp
- 数据验证: Pydantic
- 文件处理: python-multipart
- 数据库: （规划）SQLite/PostgreSQL（存储任务记录）
- ORM: （规划）SQLAlchemy

**职责（已实现）**:
- 接收前端文件上传请求
- 使用PyMuPDF进行基础行级解析（bbox+文本）
- 调度DPS服务进行版面分析与OCR（可用时自动补齐DPS结果）
- 提供解析结果与标注相关接口
- 调用大模型API执行翻译任务
- 管理翻译任务状态和进度
- 提供SSE实时进度推送

**职责（规划）**:
- 生成双语对照PDF

#### 2. DPS服务 (端口: 8001)
**技术栈**:
- 框架: FastAPI
- PDF处理: PyMuPDF (fitz)
- 版面分析: PP-DocLayoutV2 模型
- OCR引擎: PaddleOCR
- 图像处理: OpenCV, NumPy

**职责**:
- PDF版面分析（返回页面框与类别label）
- OCR文字识别（可按框聚合文本）
- 返回结构化解析结果（JSON格式，含 pages[].boxes[].coordinate + ocr_text）
- 支持并行模型加载和懒加载模式
- 健康检查接口规范（layout_status, ocr_status）

**模块化架构**:
```
DPS/
├── core/                    # 核心模块
│   ├── config.py           # 配置管理（设备、zoom、启用选项）
│   ├── logger.py           # 日志系统
│   └── model_loader.py     # 模型加载器（并行/懒加载）
├── services/                # 业务服务
│   ├── layout_service.py   # 版面分析服务
│   └── ocr_service.py      # OCR识别服务
├── utils/                   # 工具函数
│   ├── bbox_utils.py       # 边界框处理工具
│   ├── env_utils.py        # 环境变量工具
│   └── import_utils.py     # 动态导入工具
├── pp_doclayoutv2_api.py   # 旧版主文件（保留兼容）
└── pp_doclayoutv2_api_new.py  # 新版模块化主文件（推荐）
```

**性能优化**:
- **并行加载**: 版面分析和OCR模型同时加载，启动时间减半
- **懒加载模式**: 启动时不加载模型，首次请求时加载，启动瞬间完成
- **双重检查锁**: 线程安全的模型加载机制
- **健康检查**: 规范的状态返回，支持主后端服务发现

#### 3. MinerU服务 (端口: 8002，可选，未实现)
**状态**: 占位
**职责**: 更高级的结构化解析能力（待接入）

#### 3. PDF生成服务（集成在主后端）
**技术栈**:
- PyMuPDF (fitz): PDF读取和操作
- ReportLab: PDF生成
- Pillow: 图像处理

**职责**:
- 双语对照排版设计
- PDF文档生成
- 保持原文格式和样式

**TextWriter自动字体回退机制**:
- 使用 `fitz.TextWriter` 替代 `insert_textbox` 实现自动字体回退
- 当字符不被当前字体支持时，自动搜索替代字体
- 内置CJK字体 `fitz.Font("cjk")` 作为基础字体
- 自动回退到已注册字体（如NotoSansMath-Regular用于数学符号）
- 解决Unicode数学斜体字符（U+1D400-U+1D7FF区块）渲染乱码问题
- 核心代码位于 `backend/app/services/pdf_export/pdf_generator.py`:
  - `_draw_segmented_text()`: 多段落文本绘制入口
  - `_draw_text_with_textwriter()`: TextWriter实现自动字体回退

## 核心功能模块

### 1. 文件上传模块
- 支持拖拽上传
- 文件格式验证（仅PDF）
- 文件大小限制（建议100MB以内）
- 上传进度显示

### 2. PDF解析模块
**当前已实现**:
- **PyMuPDF行级文本提取**: bbox+文本+字体信息，保存 `storage/parsed/{pdf_id}/parsed.json`
- **DPS版面分析**: PP-DocLayoutV2模型识别文档结构（标题、段落、图表等）
- **DPS OCR识别**: PaddleOCR识别版面框内的文字内容
- **OCR文本聚合**: 按版面框聚合OCR结果，用空格连接（非换行符）
- **自动补齐机制**: 已解析PDF若缺少DPS结果，上传时自动补齐
- **数据存储**: 保存 `storage/parsed/{pdf_id}/parsed.json` 与 `storage/parsed/{pdf_id}/dps.json`

**规划**:
- MinerU结构化解析（占位，可选接入更高级的解析能力）

### 3. 翻译模块
- 支持多种大模型API（OpenAI、Claude、国内大模型等）
- 流式翻译输出
- 翻译上下文管理
- 专业术语词典支持
- 翻译质量优化（保持学术语言风格）

### 4. PDF生成模块
- 双语对照布局（左右或上下）
- 保持原文格式
- 图表位置保持
- 页眉页脚自定义
- 水印支持（可选）

### 5. 任务管理模块
- 任务队列管理
- 实时进度显示
- 任务历史记录
- 支持暂停/继续/取消
- 错误重试机制

## 开发规范

### 前端开发规范
1. **组件命名**: 使用PascalCase，如 `UploadPanel.vue`
2. **组合式函数**: 使用 `use` 前缀，如 `useFileUpload.js`
3. **API封装**: 统一在 `src/api` 目录下管理
4. **状态管理**: 使用Pinia store，按功能模块划分
5. **错误处理**: 统一使用axios拦截器和全局错误处理
6. **类型安全**: 尽可能使用TypeScript或JSDoc类型注释

### 后端开发规范
1. **代码风格**: 遵循PEP 8规范
2. **API设计**: RESTful风格，使用FastAPI的自动文档
3. **异步优先**: 耗时操作使用async/await
4. **错误处理**: 使用HTTPException，返回标准错误格式
5. **日志记录**: 使用loguru，记录关键操作和错误
6. **配置管理**: 使用pydantic的Settings，支持环境变量
7. **接口响应格式**:
```python
{
    "code": 200,
    "message": "success",
    "data": {...}
}
```

### Git提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 代码重构
- test: 测试相关
- chore: 构建/工具配置

## 项目结构 (当前实际结构)

```
OceanPDF2.0/
├── frontend/                 # Electron + Vue前端
│   ├── src/
│   │   ├── main/            # Electron主进程
│   │   │   └── index.js
│   │   ├── renderer/        # Vue渲染进程
│   │   │   ├── api/         # API封装
│   │   │   │   └── pdf.js   # PDF相关API
│   │   │   ├── components/  # 组件
│   │   │   │   ├── UploadPanel.vue      # 上传组件
│   │   │   │   └── AnnotationPanel.vue  # 浮动标注面板
│   │   │   ├── views/       # 页面
│   │   │   │   ├── Home.vue           # 主页面
│   │   │   │   ├── ParsedList.vue     # 已解析PDF列表
│   │   │   │   └── PDFAnnotation.vue  # PDF标注页面
│   │   │   ├── router/      # 路由配置
│   │   │   │   └── index.js
│   │   │   ├── styles/      # 样式文件
│   │   │   │   └── index.scss
│   │   │   ├── utils/       # 工具函数
│   │   │   │   └── request.js
│   │   │   ├── App.vue
│   │   │   └── main.js
│   │   └── preload/         # 预加载脚本
│   │       └── index.js
│   ├── .npmrc              # npm配置（淡宝镜像）
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── backend/                  # 主后端服务
│   ├── app/
│   │   ├── api/             # API路由
│   │   │   ├── __init__.py
│   │   │   ├── upload.py    # 上传接口（已实现）
│   │   │   ├── pdf.py       # PDF相关接口（已实现）
│   │   │   ├── annotation.py # 标注接口（已实现）
│   │   │   ├── translate.py # 翻译接口（已实现）
│   │   │   ├── export.py    # 导出接口（已实现）
│   │   │   └── task.py      # 任务接口（已实现）
│   │   ├── core/            # 核心配置
│   │   │   ├── __init__.py
│   │   │   └── config.py    # 配置管理（含DPS服务配置）
│   │   ├── services/        # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── pdf_parser.py  # PDF解析服务（已实现）
│   │   │   ├── dps_service.py # DPS服务调度（已实现）
│   │   │   ├── annotation/    # 标注服务（已实现）
│   │   │   │   ├── __init__.py
│   │   │   │   └── annotation_service.py
│   │   │   ├── sorting/       # 排序服务（已实现）
│   │   │   │   ├── __init__.py
│   │   │   │   └── reading_order_service.py
│   │   │   ├── translation/   # 翻译服务（已实现）
│   │   │   └── pdf_export/    # 导出服务（已实现）
│   │   ├── models/          # 数据模型
│   │   │   └── __init__.py
│   │   ├── utils/           # 工具函数
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI应用入口
│   ├── storage/             # 数据存储目录
│   │   ├── uploads/         # PDF原文件
│   │   └── parsed/          # 解析结果
│   ├── .env.example
│   └── requirements.txt
├── DPS/                      # DPS服务（独立模块）
│   ├── core/                # 核心模块
│   │   ├── config.py        # 配置管理
│   │   ├── logger.py        # 日志系统
│   │   └── model_loader.py  # 模型加载器
│   ├── services/            # 业务服务
│   │   ├── layout_service.py  # 版面分析
│   │   └── ocr_service.py     # OCR识别
│   ├── utils/               # 工具函数
│   │   ├── bbox_utils.py    # 边界框处理
│   │   ├── env_utils.py     # 环境变量
│   │   └── import_utils.py  # 动态导入
│   ├── pp_doclayoutv2_api.py     # 旧版主文件
│   ├── pp_doclayoutv2_api_new.py # 新版主文件（推荐）
│   └── requirements.txt
├── .gitignore
└── README.md
```

## 核心API设计

### 主后端服务 (8000) - 已实现部分

```
✅ POST   /api/v1/upload                    # 上传PDF文件并解析（支持重复检测）
✅ GET    /api/v1/pdf/{pdf_name}/page/{page_num}  # 获取PDF页面图片
✅ GET    /api/v1/pdf/{pdf_name}/parsed    # 获取PDF解析数据
✅ GET    /api/v1/pdf/{pdf_name}/dps       # 获取DPS版面分析+OCR结果JSON
✅ GET    /api/v1/parsed-list              # 获取已解析PDF列表
✅ DELETE /api/v1/pdf/{pdf_name}         # 删除已解析PDF
✅ GET    /api/v1/annotation/types         # 获取所有标注类型和颜色配置
✅ POST   /api/v1/annotation/annotate      # 标注PDF元素（单个）
✅ POST   /api/v1/annotation/clear         # 清除元素标注
✅ POST   /api/v1/annotation/batch         # 批量标注PDF元素（支持合并标注；DPS写入需 use_dps=true）
✅ GET    /api/v1/annotation/{pdf_name}/page/{page_num}  # 获取页面标注统计
✅ POST   /api/v1/translation/prepare/{pdf_name}  # 生成预翻译文件
       ?source_lang=en                 # 源语言
       &target_lang=zh-CN              # 目标语言
       &aggregate_titles=false         # 是否聚合标题
       &use_dps=false                  # 使用Python或DPS解析结果
       &force=false                    # 强制重新生成

✅ POST   /api/v1/translation/test?api_key=...           # 测试DeepSeek API连通性
✅ GET    /api/v1/translation/pretranslation/{pdf_name}  # 获取预翻译任务清单
✅ POST   /api/v1/translation/translate                 # 同步翻译（一次性返回统计）
✅ POST   /api/v1/translation/translate/async            # 创建异步翻译任务（返回task_id）
✅ GET    /api/v1/translation/progress/{task_id}         # SSE推送翻译进度与单条结果
✅ GET    /api/v1/translation/result/{pdf_name}?use_dps=...  # 获取翻译结果文件内容
✅ POST   /api/v1/translation/control/{task_id}/pause    # 暂停翻译任务
✅ POST   /api/v1/translation/control/{task_id}/resume   # 继续翻译任务
✅ POST   /api/v1/translation/control/{task_id}/stop     # 停止翻译任务并删除结果文件
✅ GET    /api/v1/translation/control/{task_id}/status   # 获取任务控制状态
```

### DPS服务 (8001) - 已完整实现（独立服务）

```
✅ GET    /health                         # 健康检查（含layout_status/ocr_status）
✅ POST   /analyze                        # PDF版面分析（支持OCR参数）
       ?with_ocr=true                   # 是否附带OCR识别
       &ocr_min_conf=0.0                # OCR最低置信度阈值
       &ocr_return_regions=false        # 是否返回OCR文本区域详情
✅ POST   /ocr                            # 图片/PDF OCR识别
```

**DPS `/analyze` 接口返回格式**:
```json
{
  "status": "success",
  "req_id": "请求ID",
  "filename": "文件名",
  "elapsed_sec": 1.23,
  "pages": [
    {
      "page_index": 0,
      "width": 1654,
      "height": 2339,
      "boxes": [
        {
          "coordinate": [x0, y0, x1, y1],
          "label": "text/title/figure/table...",
          "ocr_text": "识别到的文本内容",
          "ocr_avg_confidence": 0.95
        }
      ]
    }
  ]
}
```

## 数据流程

### 当前已实现流程

1. **用户上传PDF** → 前端发送到主后端 (8000)
2. **后端检查重复** → 如已存在直接返回，否则继续
3. **保存文件** → storage/uploads/{uuid}_{filename}.pdf
4. **PyMuPDF解析** → 行级文本提取
5. **保存JSON** → storage/parsed/{pdf_id}/parsed.json（短ID目录）
6. **调用DPS服务** → 获取版面框（可选OCR：由 `with_ocr` 控制）
7. **DPS标记阅读顺序** → 每个box添加 `DPS_block_id` 和 `reading_order` 字段
8. **保存DPS JSON** → storage/parsed/{pdf_id}/dps.json（短ID目录）
9. **DPS预标注** → 匹配Python元素并标注，同时写入 `reading_order`
10. **标题层级分析** → 细化标题类型（section_title_2/3）
11. **返回前端** → 解析结果数据（包含阅读顺序）
12. **跳转标注页** → 显示PDF图片 + 元素框（支持Python/DPS切换）
13. **批量标注** → 支持单选/框选，批量保存优化性能（Python写入 parsed.json；DPS写入 dps.json，需 use_dps=true）
14. **用户修改后重算** → 用户标注/合并/拆解后，调用Python阅读顺序计算器

### 规划中的完整流程

1. **用户上传PDF** → 前端发送到主后端 (8000)
2. **主后端保存文件** → 创建任务记录
3. **调用DPS/MinerU服务** → 获取结构化解析结果（可选）
4. **接收解析结果** → 结构化数据（JSON）
5. **分段调用大模型API** → 执行翻译
6. **生成双语PDF** → 排版和渲染
7. **通知前端完成** → SSE推送
8. **用户下载结果** → 提供下载链接

## 关键技术点

### 1. Electron与后端通信
- 渲染进程使用 axios 调用本地后端API（`/api/v1/...`）
- 预加载脚本通过 `contextBridge` 暴露IPC能力（如文件选择）给渲染进程
- 渲染进程不直接访问 Node.js API（需要的能力通过预加载桥接）

### 2. 大文件上传优化
- 使用 `multipart/form-data` 直传（当前未实现分片/断点续传）
- 通过 SSE 推送后端解析进度，前端显示阶段化进度条

### 3. 翻译性能优化
- 并发翻译多个段落（控制并发数）
- 使用流式响应提升体验
- 缓存翻译结果

### 4. PDF排版
- 保持原文字体和大小
- 双语对齐策略
- 图表和公式的位置保持
- 分页算法优化

### 5. 标注性能优化
- 批量标注API：一次HTTP请求处理多个标注
- 文件操作优化：JSON文件只读取/写入一次
- 前端批量提交：所有标注累积后一次性发送
- 性能提升：100个标注从 20秒 → 0.5秒（40倍提升）

### 6. 缩放自适应
- 坐标转换：考虑transform: scale()的影响
- getBoundingClientRect()返回缩放后尺寸，需除以scale还原
- 框选功能支持任意缩放级别（0.5x - 3.0x）

### 7. 合并与拆解逻辑
- 合并元素框：多个元素框合并为一个新的元素框
- 拆解合并元素：还原所有源元素并删除合并元素
- 嵌套合并处理：自动检测并拆解已合并元素
- 前端立即显示，保存后同步后端
- 字段命名兼容：前端 unmerge_from，后端 _unmerge_from

### 8. DPS服务性能优化
- **并行模型加载**: 版面分析和OCR模型同时加载，启动速度提升2倍
- **懒加载模式**: 启动时不加载模型，首次请求时按需加载
- **双重检查锁**: 线程安全的模型加载机制
- **模块化架构**: 清晰的代码结构，便于维护和扩展
- **健康检查规范**: 标准化的服务状态返回格式

### 9. 错误处理
- 后端服务不可用时的降级方案
- 翻译API限流处理
- 大文件解析超时处理
- 用户友好的错误提示

### 10. 阅读顺序管理
- **DPS初始阅读顺序**：首次解析时直接从DPS版面分析结果获取并写入
- **预标注阶段写入**：在构建merge_annotations时携带reading_order字段
- **合并元素处理**：新创建的合并元素框也保存reading_order
- **用户操作重算**：用户标注/合并/拆解元素后调用Python的阅读顺序计算器
- **手动排序**：用户可以点击元素手动设置顺序
- **部分排序**：未设置的元素自动按默认逻辑排序
- **智能补全**：保证所有元素都有连续的阅读顺序
- **退出确认**：防止用户意外丢失未保存的排序
- **DPS模式可编辑**：DPS模式下可手动调整阅读顺序并写入 `dps.json`（`use_dps=true`）

### 12. 翻译任务控制机制
- **全局控制标志存储**：`translation_control_flags` 字典维护每个任务的控制状态
- **控制标志结构**：`{"paused": bool, "stopped": bool}`
- **队列模式翻译执行**
  - 使用 `asyncio.wait()` 和 `FIRST_COMPLETED` 模式
  - 边执行边创建任务，而非一次性启动所有任务
  - 支持动态控制任务创建和取消
- **暂停机制**
  - 设置 `paused=True` 标志
  - 主循环停止创建新任务
  - 正在执行的任务继续完成（内部检查暂停标志等待）
  - 点击继续后恢复任务创建
- **停止机制**
  - 设置 `stopped=True` 标志
  - 主循环检测到后立即取消所有正在执行的任务（`task.cancel()`）
  - 等待所有任务结束（`asyncio.gather(*active_tasks, return_exceptions=True)`）
  - 删除翻译结果文件（`translation_file.unlink()`）
  - 已翻译的进度被清除，可重新开始
- **任务取消处理**
  - 捕获 `asyncio.CancelledError` 异常
  - 返回 None 表示任务被取消
  - 不计入翻译结果统计
- **前端控制交互**
  - 暂停按钮：断开SSE，仅暂停进度推送
  - 继续按钮：从结果文件同步进度后重新连接SSE
  - 停止按钮：调用 `POST /translation/control/{task_id}/stop`
  - 后端已提供 pause/resume 接口（如需真正暂停后端任务可接入）

### 13. UI/UX体验优化
- 玻璃拟态设计：阶段指示器、Toast组件、确认对话框、翻译配置面板
- 渐变背景：蓝绿主题渐变（#4facfe → #00f2fe）
- 动画效果：悬停放大、点击缩小、滑入滑出、水波纹效果
- SVG图标：矢量图标，更精致和清晰
- 响应式设计：适应不同缩放级别和屏幕尺寸
- 卡片式交互：模式选择、选项配置等采用可点击卡片
- 翻译状态指示：idle（空闲）、translating（翻译中）、paused（已暂停）、completed（已完成）
- **双栏PDF布局**
  - PDF在各自区域内水平居中显示（flex布局）
  - 默认宽度占满半个区域，根据容器宽度自动计算
  - 保持纵横比，响应式调整
  - 窗口大小变化时自动重新计算显示尺寸
- **滚动同步优化**
  - 使用 @wheel 事件同时滚动左右两侧
  - 消除被动滚动延迟，流畅无卡顿
- **换页性能优化**
  - 预加载相邻页面，换页无等待
  - 样式计算缓存，避免重复计算
  - 换页速度提升 70-80%

## 部署说明

### 开发环境
0. 依赖安装
   - 前端依赖: `cd frontend; npm ci --registry=https://registry.npmmirror.com`
   - 后端依赖: `cd backend; python -m venv .venv; .\.venv\Scripts\python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
   - DPS依赖: `cd DPS; python -m venv .venv; .\.venv\Scripts\python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
1. 前端: `cd frontend; npm run electron:dev`
2. 主后端: `cd backend; uvicorn app.main:app --reload --port 8000`
3. DPS服务（推荐新版）: `cd DPS; .\.venv\Scripts\python .\pp_doclayoutv2_api_new.py --host 127.0.0.1 --port 8001`
4. DPS服务（旧版兼容）: `cd DPS; .\.venv\Scripts\python .\pp_doclayoutv2_api.py --host 127.0.0.1 --port 8001`

### 生产环境
1. 前端: 使用electron-builder打包成安装包
2. 后端: 使用Docker容器化部署或作为系统服务运行
3. 后端服务可以集成到Electron应用中（使用child_process启动）

## 安全考虑

1. **API密钥安全**: 大模型API密钥存储在加密配置中
2. **文件安全**: 上传文件验证，防止恶意文件
3. **进程隔离**: Electron的上下文隔离和沙箱模式
4. **后端认证**: 本地服务使用token认证防止外部访问
5. **数据清理**: 定期清理临时文件和过期任务

## 性能指标

- PDF上传响应时间: < 500ms
- DPS服务启动时间:
  - 并行加载模式: ~10秒（两个模型同时加载）
  - 懒加载模式: <1秒（启动时不加载模型）
- DPS版面分析耗时: 服务会返回 elapsed_sec（与机器/模型相关，通常3-10秒/页）
- DPS OCR识别耗时: 包含在版面分析时间内（if with_ocr=true）
- **PDF渲染清晰度**: zoom=3.0（300% DPI），确保文本图像锐利清晰
- 批量标注性能: 100个标注 ~0.5秒（相比单个请求提升40倍）
- **API Key测试速度**: 0.3-1秒（使用 models.list 接口，相比发送消息快3-5倍）
- **翻译界面换页速度**: 0.1-0.3秒（预加载+缓存优化，提升70-80%）
- 翻译速度: 取决于大模型API响应与并发配置
- PDF生成: < 5秒（50页文档，待实现）
- 内存占用: Electron主进程 < 200MB，渲染进程 < 300MB

## 后续扩展

1. 支持批量翻译
2. 自定义翻译模板
3. 术语库管理
4. 翻译记忆功能
5. 多语言支持（不仅限于中英）
6. 云端同步功能
7. 翻译质量评分
