import { defineConfig } from "vitest/config";

export default defineConfig({
  base: "./",
  build: { outDir: "dist", target: "es2022", chunkSizeWarningLimit: 900 },
  test: { include: ["tests/**/*.test.ts"] },
});
