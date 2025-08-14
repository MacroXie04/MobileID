// src/main.js

import {createApp} from 'vue';
import App from './App.vue';
import router from './router';
import {baseURL} from './config';

// Cropper.js
import 'cropperjs/dist/cropper.css';

// Material Web - Import all components and the typescale styles
import '@material/web/all.js';
import {styles as typescaleStyles} from '@material/web/typography/md-typescale-styles.js';

const app = createApp(App);

// --- KEY CONFIGURATION ---
// Tell Vue to recognize all tags starting with "md-" as custom elements.
// This prevents Vue from trying to resolve them as Vue components.
app.config.compilerOptions.isCustomElement = (tag) => tag.startsWith('md-');

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