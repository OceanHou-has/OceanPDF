import request from '../utils/request'

const BASE_URL = 'http://127.0.0.1:8000/api/v1'

/**
 * 获取工具处理结果的下载地址
 * @param {string} filename - 输出文件名
 * @returns {string}
 */
export function getToolDownloadUrl(filename) {
  return `${BASE_URL}/tools/download/${encodeURIComponent(filename)}`
}

/**
 * 上传单个文件 + 附加表单字段的通用封装
 */
function uploadWithFields(url, file, fields = {}) {
  const formData = new FormData()
  formData.append('file', file)
  Object.entries(fields).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      formData.append(key, value)
    }
  })
  return request({
    url,
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000
  })
}

/**
 * 合并多个 PDF
 * @param {File[]} files - 按顺序排列的文件列表
 */
export function mergePDFs(files) {
  const formData = new FormData()
  files.forEach((f) => formData.append('files', f))
  return request({
    url: '/tools/merge',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000
  })
}

/**
 * 拆分 PDF
 * @param {File} file
 * @param {{mode: string, spec?: string, every?: number}} params
 */
export function splitPDF(file, params = {}) {
  return uploadWithFields('/tools/split', file, {
    mode: params.mode || 'ranges',
    spec: params.spec,
    every: params.every
  })
}

/**
 * 提取页面
 * @param {File} file
 * @param {string} spec - 页码范围，如 "1-3,5"
 */
export function extractPages(file, spec) {
  return uploadWithFields('/tools/extract', file, { spec })
}

/**
 * 删除页面
 * @param {File} file
 * @param {string} spec - 要删除的页码范围
 */
export function deletePages(file, spec) {
  return uploadWithFields('/tools/delete', file, { spec })
}

/**
 * 旋转页面
 * @param {File} file
 * @param {{angle: number, pages?: string}} params
 */
export function rotatePages(file, params = {}) {
  return uploadWithFields('/tools/rotate', file, {
    angle: params.angle,
    pages: params.pages
  })
}

/**
 * 重排页面
 * @param {File} file
 * @param {string} spec - 新的页面顺序，如 "3,1,2"
 */
export function reorderPages(file, spec) {
  return uploadWithFields('/tools/reorder', file, { spec })
}
