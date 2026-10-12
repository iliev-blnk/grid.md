import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/grid.md/",
  build: { rollupOptions: { input: { index: resolve(__dirname, "index.html"), story: resolve(__dirname, "story.html") } } },
});
