// Local acceptance entry: preserve the original 8012 service and product config.
import { fileURLToPath } from 'node:url';
import { createServer } from '../../../frontend/node_modules/vite/dist/node/index.js';

const frontendRoot = fileURLToPath(new URL('../../../frontend/', import.meta.url));
const server = await createServer({
  root: frontendRoot,
  configFile: `${frontendRoot}/vite.config.ts`,
  server: {
    host: '127.0.0.1',
    port: 8446,
    strictPort: true,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8015' },
      '/media': { target: 'http://127.0.0.1:8015' },
    },
  },
});
await server.listen();
console.log('Local acceptance backend: http://127.0.0.1:8015');
server.printUrls();
