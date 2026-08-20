// electron-vite 构建配置（桌面端打包所需）
// 本项目 index.html 位于 frontend 根目录（非默认的 src/renderer）；
// 产物平铺到 dist-electron/，与 package.json 的 main: dist-electron/main.js 对齐
// （主进程内 preload 引用 ../preload/index.js、页面引用 ../renderer/index.html 亦与之匹配）
import { defineConfig } from 'electron-vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  main: {
    build: {
      outDir: 'dist-electron',
      rollupOptions: {
        input: resolve(__dirname, 'src/main/index.js'),
        output: {
          // 输出为 dist-electron/main.js；package.json 的 type:module 决定其为 ESM
          // （Electron 28+ 支持 ESM 主进程）
          format: 'es',
          entryFileNames: 'main.js',
          inlineDynamicImports: true
        }
      }
    }
  },
  preload: {
    build: {
      outDir: 'dist-electron/preload',
      rollupOptions: {
        input: resolve(__dirname, 'src/preload/index.js'),
        output: {
          // 预加载脚本必须以 CJS 运行（沙箱模式不支持 ESM 预加载），
          // package.json 的 type:module 下需用 .cjs 扩展名
          format: 'cjs',
          entryFileNames: 'index.cjs',
          inlineDynamicImports: true
        }
      }
    }
  },
  renderer: {
    root: '.',
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src/renderer')
      }
    },
    plugins: [vue()],
    build: {
      outDir: 'dist-electron/renderer',
      emptyOutDir: false,
      rollupOptions: {
        input: resolve(__dirname, 'index.html')
      }
    }
  }
})
