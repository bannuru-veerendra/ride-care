import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      // Same-origin /api in dev: skips CORS preflight and Windows
      // localhost → IPv6 fallback (~2s per request).
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (url) => url.replace(/^\/api/, ""),
      },
    },
  },
});