import request from '../utils/request'

/**
 * 上传PDF文件
 * @param {File} file - PDF文件对象
 * @param {Object} options - 上传选项
 * @param {boolean} options.withOcr - 是否执行OCR
 * @param {string} options.taskId - 任务ID（用于SSE进度推送）
 * @param {(percent: number, progressEvent: any) => void} options.onProgress - 上传进度回调
 * @returns {Promise}
 */
export function uploadPDF(file, options = {}) {
  const formData = new FormData()
  formData.append('file', file)

  const withOcr = Boolean(options.withOcr)
  const taskId = options.taskId || ''
  const onProgress = typeof options.onProgress === 'function' ? options.onProgress : null
  
  return request({
    url: '/upload',
    method: 'post',
    data: formData,
    params: {
      with_ocr: withOcr,
      task_id: taskId  // 添加task_id参数
    },
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    // 上传和处理可能需要很长时间，设置为30分钟超时
    timeout: 1800000,  // 30分钟 = 1800秒 = 1800000毫秒
    // 上传进度回调
    onUploadProgress: (progressEvent) => {
      const total = progressEvent?.total || 0
      const loaded = progressEvent?.loaded || 0
      const percentCompleted = total > 0 ? Math.round((loaded * 100) / total) : 0
      console.log('上传进度:', percentCompleted + '%')
      if (onProgress) {
        try {
          onProgress(percentCompleted, progressEvent)
        } catch (e) {
          console.error('[uploadPDF] onProgress回调异常:', e)
        }
      }
    }
  })
}

/**
 * 创建翻译任务
 * @param {Object} data - 翻译任务参数
 * @param {string} data.file_id - 文件ID
 * @param {string} data.source_lang - 源语言
 * @param {string} data.target_lang - 目标语言
 * @returns {Promise}
 */
export function createTranslateTask(data) {
  return request({
    url: '/translate',
    method: 'post',
    data
  })
}

/**
 * 获取任务状态
 * @param {string} taskId - 任务ID
 * @returns {Promise}
 */
export function getTaskStatus(taskId) {
  return request({
    url: `/task/${taskId}`,
    method: 'get'
  })
}

/**
 * 获取任务列表
 * @returns {Promise}
 */
export function getTaskList() {
  return request({
    url: '/tasks',
    method: 'get'
  })
}

/**
 * 删除任务
 * @param {string} taskId - 任务ID
 * @returns {Promise}
 */
export function deleteTask(taskId) {
  return request({
    url: `/task/${taskId}`,
    method: 'delete'
  })
}

/**
 * 下载翻译结果
 * @param {string} taskId - 任务ID
 * @returns {Promise}
 */
export function downloadResult(taskId) {
  return request({
    url: `/download/${taskId}`,
    method: 'get',
    responseType: 'blob'
  })
}

/**
 * 获取标注类型列表
 * @returns {Promise}
 */
export function getAnnotationTypes() {
  return request({
    url: '/annotation/types',
    method: 'get'
  })
}

/**
 * 标注PDF元素
 * @param {Object} data - 标注数据
 * @param {string} data.pdf_name - PDF名称
 * @param {number} data.page_num - 页码
 * @param {number} data.line_index - 行索引
 * @param {string} data.element_type - 元素类型
 * @returns {Promise}
 */
export function annotateElement(data) {
  return request({
    url: '/annotation/annotate',
    method: 'post',
    data
  })
}

/**
 * 清除元素标注
 * @param {Object} data - 清除标注数据
 * @param {string} data.pdf_name - PDF名称
 * @param {number} data.page_num - 页码
 * @param {number} data.line_index - 行索引
 * @returns {Promise}
 */
export function clearAnnotation(data) {
  return request({
    url: '/annotation/clear',
    method: 'post',
    data
  })
}

/**
 * 获取页面标注统计
 * @param {string} pdfName - PDF名称
 * @param {number} pageNum - 页码
 * @returns {Promise}
 */
export function getPageAnnotations(pdfName, pageNum) {
  return request({
    url: `/annotation/${pdfName}/page/${pageNum}`,
    method: 'get'
  })
}

/**
 * 批量标注PDF元素（性能优化）
 * @param {Object} data - 批量标注数据
 * @param {string} data.pdf_name - PDF名称
 * @param {Array} data.annotations - 标注列表 [{page_num, line_index, element_type}, ...]
 * @returns {Promise}
 */
export function batchAnnotate(data) {
  return request({
    url: '/annotation/batch',
    method: 'post',
    data
  })
}

export function getPDFPageImage(pdfName, pageNum, renderScale) {
  return request({
    url: `/pdf/${pdfName}/page/${pageNum}`,
    method: 'get',
    params: renderScale ? { render_scale: renderScale } : undefined
  })
}

export function getPDFParsedData(pdfName) {
  return request({
    url: `/pdf/${pdfName}/parsed`,
    method: 'get'
  })
}

export function getPDFDpsData(pdfName) {
  return request({
    url: `/pdf/${pdfName}/dps`,
    method: 'get'
  })
}

/**
 * 获取已解析的PDF列表
 * @returns {Promise}
 */
export function getParsedList() {
  return request({
    url: '/parsed-list',
    method: 'get'
  })
}

/**
 * 删除已解析的PDF
 * @param {string} pdfName - PDF名称
 * @returns {Promise}
 */
export function deletePDF(pdfName) {
  return request({
    url: `/pdf/${pdfName}`,
    method: 'delete'
  })
}

/**
 * 自动计算阅读顺序
 * @param {Object} data - 请求数据
 * @param {string} data.pdf_name - PDF名称
 * @returns {Promise}
 */
export function autoSortReadingOrder(data) {
  return request({
    url: '/sorting/auto',
    method: 'post',
    data
  })
}

/**
 * 保存手动排序结果
 * @param {Object} data - 请求数据
 * @param {string} data.pdf_name - PDF名称
 * @param {number} data.page_num - 页码
 * @param {Object} data.reading_orders - 阅读顺序映射
 * @returns {Promise}
 */
export function saveManualSorting(data) {
  return request({
    url: '/sorting/save',
    method: 'post',
    data
  })
}

/**
 * 生成预翻译文件
 * @param {string} pdfName - PDF名称
 * @param {Object} params - 查询参数
 * @param {string} params.source_lang - 源语言
 * @param {string} params.target_lang - 目标语言
 * @param {boolean} params.aggregate_titles - 是否聚合标题
 * @param {boolean} params.use_dps - 是否使用DPS结果
 * @param {boolean} params.force - 是否强制重新生成
 * @returns {Promise}
 */
export function generatePretranslation(pdfName, params) {
  return request({
    url: `/translation/prepare/${pdfName}`,
    method: 'post',
    params
  })
}

/**
 * 测试大模型 API 连通性（支持多厂商）
 * @param {string|Object} apiKeyOrConfig - API密钥，或 {api_key, provider, base_url, model} 配置对象
 * @returns {Promise}
 */
export function testTranslationAPI(apiKeyOrConfig) {
  const params = typeof apiKeyOrConfig === 'string'
    ? { api_key: apiKeyOrConfig }
    : {
        api_key: apiKeyOrConfig.api_key,
        provider: apiKeyOrConfig.provider || undefined,
        base_url: apiKeyOrConfig.base_url || undefined,
        model: apiKeyOrConfig.model || undefined
      }
  return request({
    url: '/translation/test',
    method: 'post',
    params
  })
}

// 兼容旧版调用
export const testDeepSeekAPI = testTranslationAPI

/**
 * 获取支持的大模型厂商列表
 * @returns {Promise}
 */
export function getTranslationProviders() {
  return request({
    url: '/translation/providers',
    method: 'get'
  })
}

/**
 * 保存翻译模型配置（厂商/base_url/模型/API Key）
 * @param {Object} data - {provider, base_url, model, api_key}
 * @returns {Promise}
 */
export function saveTranslationModelConfig(data) {
  return request({
    url: '/translation/config/model-config',
    method: 'post',
    data
  })
}

/**
 * 获取已保存的翻译模型配置
 * @returns {Promise}
 */
export function getTranslationModelConfig() {
  return request({
    url: '/translation/config/model-config',
    method: 'get'
  })
}

/**
 * 获取预翻译任务清单
 * @param {string} pdfName - PDF名称
 * @param {boolean} useDps - 是否使用DPS结果
 * @returns {Promise}
 */
export function getPretranslationTasks(pdfName, useDps = false) {
  return request({
    url: `/translation/pretranslation/${pdfName}`,
    method: 'get',
    params: { use_dps: useDps }
  })
}

/**
 * 开始翻译（异步）
 * @param {Object} data - 翻译参数
 * @param {string} data.pdf_name - PDF名称
 * @param {string} data.api_key - API密钥
 * @param {boolean} data.use_dps - 是否使用DPS结果
 * @param {number} data.max_concurrent - 最大并发数
 * @param {boolean} data.enable_distribution - 是否启用分布式
 * @param {string} [data.provider] - 大模型厂商ID
 * @param {string} [data.base_url] - OpenAI兼容接口地址
 * @param {string} [data.model] - 模型名称
 * @returns {Promise}
 */
export function startTranslation(data) {
  return request({
    url: '/translation/translate/async',
    method: 'post',
    data
  })
}

/**
 * 连接翻译进度SSE
 * @param {string} taskId - 任务ID
 * @returns {EventSource}
 */
export function getTranslationProgress(taskId) {
  // 返回SSE连接，由调用方自行管理
  return new EventSource(`http://localhost:8000/api/v1/translation/progress/${taskId}`)
}

/**
 * 获取翻译结果
 * @param {string} pdfName - PDF名称
 * @param {boolean} useDps - 是否使用DPS结果
 * @returns {Promise}
 */
export function getTranslationResult(pdfName, useDps = false) {
  return request({
    url: `/translation/result/${pdfName}`,
    method: 'get',
    params: { use_dps: useDps }
  })
}

/**
 * 暂停翻译任务
 * @param {string} taskId - 任务ID
 * @returns {Promise}
 */
export function pauseTranslation(taskId) {
  return request({
    url: `/translation/control/${taskId}/pause`,
    method: 'post'
  })
}

/**
 * 继续翻译任务
 * @param {string} taskId - 任务ID
 * @returns {Promise}
 */
export function resumeTranslation(taskId) {
  return request({
    url: `/translation/control/${taskId}/resume`,
    method: 'post'
  })
}

/**
 * 停止翻译任务
 * @param {string} taskId - 任务ID
 * @returns {Promise}
 */
export function stopTranslation(taskId) {
  return request({
    url: `/translation/control/${taskId}/stop`,
    method: 'post'
  })
}

/**
 * 获取翻译任务控制状态
 * @param {string} taskId - 任务ID
 * @returns {Promise}
 */
export function getTranslationControlStatus(taskId) {
  return request({
    url: `/translation/control/${taskId}/status`,
    method: 'get'
  })
}

/**
 * 获取所有活跃的翻译任务
 * 用于在已解析PDF列表中实时显示翻译进度
 * @returns {Promise}
 */
export function getActiveTranslationTasks() {
  return request({
    url: '/translation/active-tasks',
    method: 'get'
  })
}

// ==================== PDF导出相关 ====================

/**
 * 导出PDF
 * @param {string} pdfName - PDF名称
 * @param {Object} options - 导出选项
 * @param {string} options.mode - 导出模式: overlay(覆盖), side_by_side(左右对照), interleaved(交替), translation_only(纯译文)
 * @param {boolean} options.use_dps - 是否使用DPS结果
 * @param {string} options.output_filename - 自定义输出文件名
 * @returns {Promise}
 */
export function exportPDF(pdfName, options = {}) {
  return request({
    url: `/export/${pdfName}`,
    method: 'post',
    data: {
      mode: options.mode || 'overlay',
      use_dps: options.use_dps || false,
      output_filename: options.output_filename || null
    }
  })
}

/**
 * 获取导出状态
 * @param {string} pdfName - PDF名称
 * @returns {Promise}
 */
export function getExportStatus(pdfName) {
  return request({
    url: `/export/${pdfName}/status`,
    method: 'get'
  })
}

/**
 * 获取导出模式列表
 * @returns {Promise}
 */
export function getExportModes() {
  return request({
    url: '/export/modes',
    method: 'get'
  })
}

/**
 * 获取已导出文件列表
 * @param {string} pdfName - PDF名称（可选）
 * @returns {Promise}
 */
export function getExportList(pdfName = null) {
  return request({
    url: '/export/list',
    method: 'get',
    params: pdfName ? { pdf_name: pdfName } : {}
  })
}

/**
 * 下载导出文件
 * @param {string} filename - 文件名
 * @returns {string} 下载URL
 */
export function getExportDownloadUrl(filename) {
  return `http://localhost:8000/api/v1/export/download/${filename}`
}

/**
 * 获取字体状态
 * @returns {Promise}
 */
export function getFontStatus() {
  return request({
    url: '/export/fonts/status',
    method: 'get'
  })
}

// ==================== 配置相关 ====================

/**
 * 保存 API Key
 * @param {string} apiKey - DeepSeek API Key
 * @returns {Promise}
 */
export function saveApiKey(apiKey) {
  return request({
    url: '/translation/config/api-key',
    method: 'post',
    params: { api_key: apiKey }
  })
}

/**
 * 获取已保存的 API Key
 * @returns {Promise}
 */
export function getApiKey() {
  return request({
    url: '/translation/config/api-key',
    method: 'get'
  })
}

/**
 * 保存最大并发数
 * @param {number} maxConcurrent - 最大并发数（1-20）
 * @returns {Promise}
 */
export function saveMaxConcurrent(maxConcurrent) {
  return request({
    url: '/translation/config/max-concurrent',
    method: 'post',
    params: { max_concurrent: maxConcurrent }
  })
}

/**
 * 获取已保存的最大并发数
 * @returns {Promise}
 */
export function getMaxConcurrent() {
  return request({
    url: '/translation/config/max-concurrent',
    method: 'get'
  })
}
