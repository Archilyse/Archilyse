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
    resolve: {
      alias: {
        Common: path.resolve(__dirname, 'src/common/'),
        Providers: path.resolve(__dirname, 'src/providers/'),
        Components: path.resolve(__dirname, 'src/components/'),
      },
    },
    server: {
      port: 4000,
      open: '/dms/login',
    },
  });
};
