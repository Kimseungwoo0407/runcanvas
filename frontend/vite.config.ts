import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const repository = process.env.VITE_REPOSITORY_NAME || env.VITE_REPOSITORY_NAME || 'runcanvas';
  return {
    plugins: [react()],
    base: process.env.GITHUB_ACTIONS ? `/${repository}/` : '/',
    test: {
      environment: 'jsdom',
      setupFiles: './src/test-setup.ts',
      css: true,
      include: ['src/**/*.{test,spec}.{ts,tsx}'],
    },
  };
});
