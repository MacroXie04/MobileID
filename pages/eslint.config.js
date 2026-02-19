import globals from 'globals';
import pluginVue from 'eslint-plugin-vue';
import eslintConfigPrettier from 'eslint-config-prettier';
import pluginImport from 'eslint-plugin-import';
import { readFileSync } from 'fs';

const aliasMap = JSON.parse(readFileSync(new URL('./path-aliases.json', import.meta.url), 'utf-8'));

export default [
  {
    ignores: ['dist/**', 'node_modules/**'],
  },

  // Base config for all JS/Vue files
  {
    files: ['src/**/*.{js,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.es2021,
        ...globals.node,
      },
    },
    plugins: {
      import: pluginImport,
    },
    settings: {
      'import/resolver': {
        alias: {
          map: Object.entries(aliasMap),
          extensions: ['.js', '.vue', '.json'],
        },
      },
    },
    rules: {
      'no-console':
        process.env.NODE_ENV === 'production' ? ['warn', { allow: ['warn', 'error'] }] : 'off',
      'no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
      'import/no-unresolved': 'error',
    },
  },

  // Vue recommended
  ...pluginVue.configs['flat/recommended'].map((config) => ({
    ...config,
    files: ['src/**/*.vue'],
  })),

  {
    files: ['src/**/*.vue'],
    rules: {
      'vue/multi-word-component-names': 'off',
      'vue/no-reserved-component-names': 'off',
      'vue/no-deprecated-slot-attribute': 'off',
    },
  },

  // Override for .setup.js files
  {
    files: ['src/**/*.setup.js'],
    languageOptions: {
      globals: {
        defineProps: 'readonly',
        defineEmits: 'readonly',
        defineExpose: 'readonly',
      },
    },
    rules: {
      'no-unused-vars': 'off',
    },
  },

  // Prettier must be last to override formatting rules
  eslintConfigPrettier,
];
