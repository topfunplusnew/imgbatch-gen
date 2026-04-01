import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
const workspaceRoot = fileURLToPath(new URL('..', import.meta.url))
const webRoot = fileURLToPath(new URL('.', import.meta.url))

function normalizeOrigin(rawUrl, fallback) {
  const value = String(rawUrl || '').trim()
  if (!value) {
    return fallback
  }

  try {
    return new URL(value).origin
  } catch {
    return fallback
  }
}

export default defineConfig(({ mode }) => {
  const rootEnv = loadEnv(mode, workspaceRoot, '')
  const webEnv = loadEnv(mode, webRoot, '')
  const env = { ...rootEnv, ...webEnv, ...process.env }

  const apiTarget = normalizeOrigin(env.VITE_API_BASE_URL, 'http://127.0.0.1:8888')
  const storageType = String(env.STORAGE_TYPE || '').trim().toLowerCase()
  const minioPort = String(env.MINIO_API_PORT || '9000').trim()
  const minioTarget = normalizeOrigin(env.VITE_MINIO_BASE_URL, `http://127.0.0.1:${minioPort}`)
  const useMinioStorageProxy = storageType === 'minio'

  return {
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
          target: apiTarget,
          changeOrigin: true,
        },
        '/health': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/storage': {
          target: useMinioStorageProxy ? minioTarget : apiTarget,
          changeOrigin: true,
          rewrite: useMinioStorageProxy
            ? (path) => path.replace(/^\/storage(?=\/|$)/, '/images')
            : undefined,
        },
        '/images': {
          target: minioTarget,
          changeOrigin: true,
        },
        // SSE 连接需要特殊配置
        '/api/v1/notifications/stream': {
          target: apiTarget,
          changeOrigin: true,
          ws: false, // 不使用WebSocket（SSE不是WebSocket）
          configure: (proxy) => {
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
  }
})
