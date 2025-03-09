import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000, // ✅ 这里是你的前端端口
    proxy: {
      "/api": {
        target: "http://localhost:8000", // ✅ 代理到后端 API
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});