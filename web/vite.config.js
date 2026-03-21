import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8888',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8888',
        changeOrigin: true,
      },
      '/storage': {
        target: 'http://localhost:8888',
        changeOrigin: true,
      },
      // SSE 连接需要特殊配置
      '/api/v1/notifications/stream': {
        target: 'http://localhost:8888',
        changeOrigin: true,
        ws: false, // 不使用WebSocket（SSE不是WebSocket）
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // 保持请求头
            proxyReq.setHeader('Cache-Control', 'no-cache')
            proxyReq.setHeader('Connection', 'keep-alive')
          })
          proxy.on('proxyRes', (proxyRes, req, res) => {
            // 禁用缓冲，让SSE消息实时传输
            res.flushHeaders()
            proxyRes.pause()
            proxyRes.on('data', (chunk) => {
              res.write(chunk)
              res.flush()
            })
            proxyRes.on('end', () => {
              res.end()
            })
          })
        }
      }
    }
  }
})
