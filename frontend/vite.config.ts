import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 서버 연결 방식은 팀과 정한 뒤 여기 proxy 설정을 추가합니다.
export default defineConfig({
  plugins: [react()],
});
