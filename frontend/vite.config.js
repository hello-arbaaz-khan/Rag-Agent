import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Two backends sit behind the dev server:
//   /api/auth/*  -> Django   (signup, login, OTP, password, token refresh)
//   /api/v1/*    -> FastAPI  (documents, chat, search, Google Drive)
//
// Local Vite runs use localhost; Docker Compose overrides these with its
// internal service names in docker-compose.yml.
const DJANGO_URL = process.env.DJANGO_URL || "http://localhost:8000";
const API_URL = process.env.API_URL || "http://localhost:8001";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 3000,
    proxy: {
      "/api/auth": {
        target: DJANGO_URL,
        changeOrigin: true
      },
      "/api/v1": {
        target: API_URL,
        changeOrigin: true
      }
    }
  }
});