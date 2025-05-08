import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../store/user'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Download from '../views/Download.vue'
import Userinfo from '../views/Userinfo.vue'
import { ElMessage } from 'element-plus'

const routes = [
  { path: '/', component: Home, meta: { requiresAuth: true } }, // 需要登录
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/download', component: Download, meta: { requiresAuth: true } },
  { path: '/userinfo', component: Userinfo, meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // 获取 refresh_token 过期时间
  const getRefreshTokenExpiry = () => {
    const expiry = localStorage.getItem('refresh_token_expiry')
    return expiry ? new Date(expiry) : null
  }

  // 判断 refresh_token 是否过期
  const isRefreshTokenExpired = () => {
    const expiry = getRefreshTokenExpiry()
    return expiry ? new Date() > expiry : true
  }

  if (to.path === '/login') {
    next()
    return
  }

  // 如果需要认证的页面且用户未登录，跳转到登录页
  if (to.meta.requiresAuth && !userStore.access_token) {
    next('/login')
  } else {
    // 如果 refresh_token 过期，强制用户重新登录
    if (!getRefreshTokenExpiry()) {
      next()
    }
    else if (isRefreshTokenExpired()) {
      ElMessage.info('token已过期, 请重新登录')
      userStore.logout()  // 清除用户信息和 token
      next('/login')  // 跳转到登录页面
    } else {
      next()  // 正常跳转
    }
  }
})


export default router
