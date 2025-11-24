import { createRequire } from 'node:module';
import { fileURLToPath, URL } from 'node:url';

const require = createRequire(import.meta.url);
const aliasMap = require('./path-aliases.json');

export const pathAlias = Object.fromEntries(
  Object.entries(aliasMap).map(([key, relativePath]) => [
    key,
    fileURLToPath(new URL(relativePath, import.meta.url)),
  ])
);
