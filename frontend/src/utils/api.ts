/**
 * API 请求封装
 * 后端未就绪时自动使用 Mock 数据
 */

import { useUserStore } from '../store/user'

const BASE_URL = '/api/v1'
// 通过环境变量 VITE_USE_MOCK 控制，开发时默认 true，构建时可指定 false
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'

interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: any
  header?: Record<string, string>
  timeout?: number // 毫秒，默认 30000
}

// 从本地存储获取 token
function getToken(): string {
  return uni.getStorageSync('token') || ''
}

// 通用请求方法
export function request<T = any>(options: RequestOptions): Promise<ApiResponse<T>> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}${options.url}`,
      method: options.method || 'GET',
      data: options.data,
      timeout: options.timeout || 30000,
      header: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
        ...options.header,
      },
      success: (res: any) => {
        console.log('[api] statusCode:', res.statusCode, 'data type:', typeof res.data)
        if (typeof res.data === 'string') {
          try { res.data = JSON.parse(res.data) } catch {}
        }
        if (res.statusCode === 200) {
          console.log('[api] response code:', res.data?.code, 'has data:', !!res.data?.data)
          resolve(res.data as ApiResponse<T>)
        } else if (res.statusCode === 401) {
          // 任务 11：401 时清理完整登录状态
          try {
            useUserStore().logout()
          } catch {
            // store 未初始化时降级处理
            uni.removeStorageSync('token')
            uni.removeStorageSync('nickname')
            uni.removeStorageSync('userLevel')
          }
          uni.redirectTo({ url: '/pages/login/index' })
          reject(new Error('未登录或登录已过期'))
        } else {
          reject(new Error(res.data?.message || '请求失败'))
        }
      },
      fail: (err: any) => {
        reject(new Error(err.errMsg || '网络错误'))
      },
    })
  })
}

// 文件上传
export function uploadFile(options: {
  url: string
  filePath: string
  name?: string
  formData?: Record<string, string>
}): Promise<any> {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${BASE_URL}${options.url}`,
      filePath: options.filePath,
      name: options.name || 'file',
      formData: options.formData,
      header: {
        'Authorization': `Bearer ${getToken()}`,
      },
      success: (res: any) => {
        if (res.statusCode === 200) {
          resolve(JSON.parse(res.data))
        } else {
          reject(new Error('上传失败'))
        }
      },
      fail: (err: any) => {
        reject(new Error(err.errMsg || '上传失败'))
      },
    })
  })
}

export { USE_MOCK }
