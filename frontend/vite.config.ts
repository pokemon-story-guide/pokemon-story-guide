import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

/**
 * 백엔드 API 연결: `/api/...` 요청은 백엔드 서버로 넘깁니다.
 * 기본 주소는 http://127.0.0.1:8000 이고, 환경 변수 API_TARGET으로 바꿀 수 있습니다
 * (예: API_TARGET=http://192.168.0.10:8000, 또는 frontend/.env.local에 적기).
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const proxy = {
    "/api": { target: env.API_TARGET || "http://127.0.0.1:8000", changeOrigin: true },
  };
  return {
    plugins: [react()],
    // 개발 서버(npm run dev)와 시연 서버(npm run preview) 모두 같은 연결을 씁니다.
    server: { proxy },
    preview: { proxy },
  };
});
