import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: '/workshop/static/',  // 静态资源基础路径
  build: {
    outDir: '../static',  // 输出到Django static目录（不要包含workshop子目录）
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: fileURLToPath(new URL('./index.html', import.meta.url))
      }
    }
  },
  server: {
    port: 20003,
    strictPort: true,
    host: true,
    proxy: {
      '/workshop/api': {
        target: 'http://localhost:10003',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://localhost:10003',
        changeOrigin: true,
      },
    }
  }
})