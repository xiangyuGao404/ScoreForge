/**
 * API 请求封装
 * 后端未就绪时自动使用 Mock 数据
 */

const BASE_URL = '/api/v1'
const USE_MOCK = true // 后端就绪后改为 false

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
      header: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
        ...options.header,
      },
      success: (res: any) => {
        if (res.statusCode === 200) {
          resolve(res.data as ApiResponse<T>)
        } else if (res.statusCode === 401) {
          uni.removeStorageSync('token')
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
