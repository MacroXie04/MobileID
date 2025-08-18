// src/main.js

import {createApp} from 'vue';
import App from './App.vue';
import router from './router';
import {baseURL} from './config';

// Global Material 3 Styles
import '@/styles/global.css';

// Cropper.js
import 'cropperjs/dist/cropper.css';

// Local jQuery (for legacy jQuery animations used in HomeSchool)
import $ from 'jquery';
window.$ = $;
window.jQuery = $;

// Material Web - Import all components and the typescale styles
import '@material/web/all.js';
import {styles as typescaleStyles} from '@material/web/typography/md-typescale-styles.js';

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
} catch (_) {
    // Older browsers without constructable stylesheets support: no-op
}

app.mount('#app');