import globals from 'globals';
import pluginVue from 'eslint-plugin-vue';
import eslintConfigPrettier from 'eslint-config-prettier';
import pluginImport from 'eslint-plugin-import';
import tsParser from '@typescript-eslint/parser';
import tsPlugin from '@typescript-eslint/eslint-plugin';
import { readFileSync } from 'fs';

const aliasMap = JSON.parse(readFileSync(new URL('./path-aliases.json', import.meta.url), 'utf-8'));
const featureAliases = ['@auth', '@barcode', '@dashboard', '@home', '@mobile-id', '@profile'];
const legacyAliasPatterns = [
  {
    group: ['@school/*', '@user/*', '@app/config/*'],
    message: 'Use the current frontend aliases: @mobile-id, @profile, or @shared/config.',
  },
];
const appLayerPattern = {
  group: ['@app/*'],
  message: 'Feature code must not depend on the app layer.',
};
const featureDeepImportPattern = (currentAlias) => ({
  group: featureAliases.filter((alias) => alias !== currentAlias).map((alias) => `${alias}/*`),
  message:
    'Cross-feature imports must use the feature public entrypoint, for example @auth instead of @auth/...',
});
const featureBoundaryRule = (currentAlias) => ({
  'no-restricted-imports': [
    'error',
    {
      patterns: [...legacyAliasPatterns, appLayerPattern, featureDeepImportPattern(currentAlias)],
    },
  ],
});

export default [
  {
    ignores: ['dist/**', 'node_modules/**'],
  },

  // Base config for TypeScript files
  {
    files: ['src/**/*.ts'],
    languageOptions: {
      parser: tsParser,
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
      '@typescript-eslint': tsPlugin,
    },
    settings: {
      'import/resolver': {
        alias: {
          map: Object.entries(aliasMap),
          extensions: ['.ts', '.vue', '.json'],
        },
      },
    },
    rules: {
      // Direct console use is banned in app code; route through the shared logger
      // (@shared/utils/logger). The logger module itself is exempted below.
      'no-console': 'error',
      // Explicit `any` is banned to keep the type surface honest. Prefer concrete
      // types, or `unknown` + a narrow cast when a precise type is impossible.
      '@typescript-eslint/no-explicit-any': 'error',
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
      'import/no-unresolved': 'error',
      'no-restricted-imports': [
        'error',
        {
          patterns: legacyAliasPatterns,
        },
      ],
    },
  },

  {
    files: ['src/shared/**/*.{ts,vue}'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            ...legacyAliasPatterns,
            {
              group: [
                '@app',
                '@app/*',
                ...featureAliases,
                ...featureAliases.map((alias) => `${alias}/*`),
              ],
              message:
                'Shared code must remain domain-neutral; move feature-specific logic into a feature.',
            },
          ],
        },
      ],
    },
  },

  {
    files: ['src/features/**/*.{ts,vue}'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [...legacyAliasPatterns, appLayerPattern],
        },
      ],
    },
  },

  {
    files: ['src/features/auth/**/*.{ts,vue}'],
    rules: featureBoundaryRule('@auth'),
  },

  {
    files: ['src/features/barcode/**/*.{ts,vue}'],
    rules: featureBoundaryRule('@barcode'),
  },

  {
    files: ['src/features/dashboard/**/*.{ts,vue}'],
    rules: featureBoundaryRule('@dashboard'),
  },

  {
    files: ['src/features/home/**/*.{ts,vue}'],
    rules: featureBoundaryRule('@home'),
  },

  {
    files: ['src/features/mobile-id/**/*.{ts,vue}'],
    rules: featureBoundaryRule('@mobile-id'),
  },

  {
    files: ['src/features/profile/**/*.{ts,vue}'],
    rules: featureBoundaryRule('@profile'),
  },

  // Vue recommended
  ...pluginVue.configs['flat/recommended'].map((config) => ({
    ...config,
    files: ['src/**/*.vue'],
  })),

  {
    files: ['src/**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: tsParser,
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      'vue/multi-word-component-names': 'off',
      'vue/no-reserved-component-names': 'off',
      'vue/no-deprecated-slot-attribute': 'off',
      // Same gates as TS files, applied inside <script setup> blocks.
      'no-console': 'error',
      '@typescript-eslint/no-explicit-any': 'error',
    },
  },

  // The shared logger is the ONE place app code may call console.* directly.
  {
    files: ['src/shared/utils/logger.ts'],
    rules: {
      'no-console': 'off',
    },
  },

  // Test files may reference/spy on console and use loosened typing.
  {
    files: ['src/**/*.spec.ts', 'src/test/**/*.ts'],
    rules: {
      'no-console': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },

  // Override for .setup.ts files
  {
    files: ['src/**/*.setup.ts'],
    languageOptions: {
      globals: {
        defineProps: 'readonly',
        defineEmits: 'readonly',
        defineExpose: 'readonly',
      },
    },
    rules: {
      '@typescript-eslint/no-unused-vars': 'off',
    },
  },

  // Prettier must be last to override formatting rules
  eslintConfigPrettier,
];
