import axios from 'axios'
import { useUserStore } from '../store/user'
import { ElMessage } from 'element-plus'

const instance = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 5000
})

instance.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, error => {
  return Promise.reject(error)
})


instance.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const res = await axios.post('http://localhost:5000/api/refresh', {
            refresh_token: refreshToken
          })
          const newAccessToken = res.data.access_token
          
          // 更新 Pinia
          const userStore = useUserStore()
          userStore.updateAccessToken(newAccessToken)

          // 重新设置 header 并重发原请求
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          return instance(originalRequest)
        } catch (err) {
          const userStore = useUserStore()
          userStore.logout()
          ElMessage.info("请重新登录")
          console.warn("刷新 token 失败，请重新登录")
        }
      }
    }
    return Promise.reject(error)
  }
)


export default instance
