import { resolve } from 'path'
import { defineConfig } from 'vite'
import react from "@vitejs/plugin-react";
import copy from 'rollup-plugin-copy';
import css from 'rollup-plugin-css-only';

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'archilyse-ui-components',
      fileName: 'index.js',
      formats: ['umd'],
    },
    rollupOptions: {
      external: ['react'],
      output: {
        globals: {
          react: 'React',
        },
      },
      plugins: [
        react(),
        copy({
          targets: [{ src: resolve(__dirname, 'src/theme.scss'), dest: resolve(__dirname, 'dist') }],
          hook: 'writeBundle',
        }),
        css({ output: 'styles.css' }),
      ]
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
})
