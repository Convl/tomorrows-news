import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // TODO: Edit server below for remote deployment
  server: {
    host: true, // TODO: Remove before deploying
    allowedHosts: true, // TODO: Remove before deploying
    proxy: {
      "/api/v1": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
