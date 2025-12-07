import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { VitePWA } from 'vite-plugin-pwa'

// Change defineConfig to accept a function with { mode }
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  // The third parameter '' loads all env vars regardless of the `VITE_` prefix.
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      react(),
      VitePWA({ registerType: 'autoUpdate' }),
    ],
    server: {
      proxy: {
        "/api": {
          // Access the variable here
          target: env.VITE_BACKEND_URL || "http://127.0.0.1:8000",
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, ""),
        }
      }
    }
  }
})