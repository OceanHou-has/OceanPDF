import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src/renderer')
    }
  },
  // 使用 Sass 现代编译 API，避免 Dart Sass 的 legacy-js-api 弃用警告
  css: {
    preprocessorOptions: {
      scss: {
        api: 'modern'
      }
    }
  },
  server: {
    port: 5173
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
