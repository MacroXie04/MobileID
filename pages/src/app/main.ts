// src/app/main.ts

import { createApp } from 'vue';
import App from '@app/App.vue';
import router from '@app/router';
import { baseURL } from '@shared/config/config';

// Global Material 3 Styles
import '@shared/styles/tokens.css';

// Material Web - Import only the components actually used
import '@shared/material-web';
import { styles as typescaleStyles } from '@material/web/typography/md-typescale-styles.js';

// Local fonts (replace Google Fonts CDN) — latin subset only; UI is English-only
import '@fontsource/roboto/latin-400.css';
import '@fontsource/roboto/latin-500.css';
import '@fontsource/roboto/latin-700.css';
import '@fontsource/open-sans/latin-400.css';
import '@fontsource/open-sans/latin-600.css';
import '@fontsource/roboto-mono/latin-400.css';
// Material Symbols Outlined (latin-only; used by <md-icon>)
import '@fontsource/material-symbols-outlined/latin-400.css';

const app = createApp(App);

app.provide('baseURL', baseURL);

app.use(router);

// Add the Material Design typescale styles to the document.
// adoptedStyleSheets is a modern and efficient way to apply global styles.
try {
  if (typescaleStyles.styleSheet) {
    document.adoptedStyleSheets.push(typescaleStyles.styleSheet);
  }
} catch {
  // Older browsers without constructable stylesheets support: no-op
}

app.mount('#app');
