import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(uni.getStorageSync('token') || '')
  const nickname = ref(uni.getStorageSync('nickname') || '')
  const userLevel = ref<'free' | 'paid'>(uni.getStorageSync('userLevel') || 'free')
  const isLoggedIn = ref(!!token.value)

  function setLogin(data: { token: string; nickname: string; user_level: 'free' | 'paid' }) {
    token.value = data.token
    nickname.value = data.nickname
    userLevel.value = data.user_level
    isLoggedIn.value = true
    uni.setStorageSync('token', data.token)
    uni.setStorageSync('nickname', data.nickname)
    uni.setStorageSync('userLevel', data.user_level)
  }

  function logout() {
    token.value = ''
    nickname.value = ''
    userLevel.value = 'free'
    isLoggedIn.value = false
    uni.removeStorageSync('token')
    uni.removeStorageSync('nickname')
    uni.removeStorageSync('userLevel')
  }

  return { token, nickname, userLevel, isLoggedIn, setLogin, logout }
})
