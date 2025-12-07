import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
//import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(),
      VitePWA({ registerType: 'autoUpdate' }),
      //tailwindcss(),
  ],
    server: {
      proxy: {
          "/backend": {
              target: "http://127.0.0.1:8000",
              changeOrigin: true,
              secure: false,
              rewrite: (path) => path.replace(/^\/backend/, ""),
          }
      }
    }
})
