// src/app/main.js

import { createApp } from 'vue';
import App from '@app/App.vue';
import router from '@app/router';
import { baseURL } from '@app/config/config';

// Global Material 3 Styles
import '@shared/styles/tokens.css';

// Material Web - Import only the components actually used
import '@shared/material-web.js';
import { styles as typescaleStyles } from '@material/web/typography/md-typescale-styles.js';

// Local fonts (replace Google Fonts CDN)
import '@fontsource/roboto/400.css';
import '@fontsource/roboto/500.css';
import '@fontsource/roboto/700.css';
import '@fontsource/open-sans/400.css';
import '@fontsource/open-sans/600.css';
import '@fontsource/roboto-mono/400.css';
// Optional: Material Symbols Outlined as local font (if <md-icon> uses glyphs)
import '@fontsource/material-symbols-outlined/400.css';

const app = createApp(App);

app.provide('baseURL', baseURL);

app.use(router);

// Add the Material Design typescale styles to the document.
// adoptedStyleSheets is a modern and efficient way to apply global styles.
try {
  document.adoptedStyleSheets.push(typescaleStyles.styleSheet);
} catch {
  // Older browsers without constructable stylesheets support: no-op
}

app.mount('#app');
