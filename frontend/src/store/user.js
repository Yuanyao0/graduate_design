import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    access_token: '',
    refresh_token: '',
    refresh_token_expiry: ''
  }),
  actions: {
    setUser(user, access_token, refresh_token, refresh_token_expiry) {
      this.user = user
      this.access_token = access_token
      this.refresh_token = refresh_token
      this.refresh_token_expiry = refresh_token_expiry
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      localStorage.setItem('refresh_token_expiry', refresh_token_expiry)
    },
    updateAccessToken(newToken) {
      this.access_token = newToken
      localStorage.setItem('access_token', newToken)
    },
    logout() {
      this.user = null
      this.access_token = ''
      this.refresh_token = ''
      this.refresh_token_expiry = ''
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('refresh_token_expiry')
    }
  },
  persist: true
})


// export const useUserStore = defineStore('user', {
//   state: () => ({
//     user: null,
//     token: ''
//   }),
//   actions: {
//     setUser(user, token) {
//       this.user = user
//       this.token = token
//     },
//     logout() {
//       this.user = null
//       this.token = ''
//       localStorage.removeItem('access_token')
//     }
//   },
//   persist: true
// })
