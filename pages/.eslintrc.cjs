const aliasMap = require('./path-aliases.json');

module.exports = {
  root: true,
  env: { browser: true, es2022: true, node: true },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-recommended',
    'plugin:import/recommended',
    'prettier',
  ],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  plugins: ['import'],
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
    'vue/multi-word-component-names': 'off',
    // Allow alias-based imports resolved by Vite
    'vue/no-reserved-component-names': 'off',
    'vue/no-deprecated-slot-attribute': 'off',
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
};
