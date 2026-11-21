import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Em desenvolvimento, o Vite repassa /api para o Django (porta 8000).
// Em produção (AWS), o CloudFront faz o mesmo: /api/* vai para o load balancer do ECS.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": "http://localhost:8000" } },
  preview: { port: 4173, proxy: { "/api": "http://localhost:8000" } },
});
