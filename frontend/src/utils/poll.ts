/**
 * 轮询直到条件满足或超时
 * @param fn 每次轮询执行的异步函数，返回数据
 * @param check 判断是否完成的函数，返回 true 表示停止轮询
 * @param interval 轮询间隔（毫秒），默认 2500
 * @param maxAttempts 最大轮询次数，默认 60（约 2.5 分钟）
 */
export function poll<T>(
  fn: () => Promise<T>,
  check: (data: T) => boolean,
  interval = 2500,
  maxAttempts = 60
): Promise<T> {
  return new Promise((resolve, reject) => {
    let attempts = 0
    let stopped = false

    const run = async () => {
      if (stopped) return
      attempts++
      try {
        const data = await fn()
        if (stopped) return
        if (check(data)) {
          stopped = true
          resolve(data)
        } else if (attempts >= maxAttempts) {
          stopped = true
          reject(new Error('处理超时，请稍后重试'))
        } else {
          setTimeout(run, interval)
        }
      } catch (e) {
        if (stopped) return
        stopped = true
        reject(e)
      }
    }

    // 首次立即执行
    run()
  })
}
