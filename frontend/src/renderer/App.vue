<template>
  <router-view />
  <Toast ref="toastRef" />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Toast from './components/Toast.vue'

const toastRef = ref(null)

// 应用初始化逻辑
onMounted(() => {
  // 将 toast 方法挂载到全局
  window.$toast = {
    success: (msg, duration) => toastRef.value?.show(msg, 'success', duration),
    error: (msg, duration) => toastRef.value?.show(msg, 'error', duration),
    warning: (msg, duration) => toastRef.value?.show(msg, 'warning', duration),
    info: (msg, duration) => toastRef.value?.show(msg, 'info', duration)
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}
</style>
