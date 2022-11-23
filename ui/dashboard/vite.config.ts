import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import EnvironmentPlugin from 'vite-plugin-environment';

export default ({ mode }) => {
  process.env = {
    ...process.env,
    ...loadEnv(mode, path.resolve(__dirname), ''),
  };
  return defineConfig({
    build: { sourcemap: true },
    plugins: [react(), { ...EnvironmentPlugin('all', { prefix: '' }), apply: 'build' }],
    define: {
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV),
    },
    server: {
      port: 8080,
      open: '/dashboard',
    },
  });
};
