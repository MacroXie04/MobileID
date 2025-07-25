// src/main.js
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { baseURL } from './config';

// Bootstrap 5
// import 'bootstrap/dist/css/bootstrap.min.css'; // Removed to avoid conflicts with Material Web
import 'bootstrap/dist/js/bootstrap.bundle.min.js';

// Font Awesome
import '@fortawesome/fontawesome-free/css/all.min.css';

// Cropper.js
import 'cropperjs/dist/cropper.css';

// Material Web
import '@material/web/all.js';
import {styles as typescaleStyles} from '@material/web/typography/md-typescale-styles.js';

const app = createApp(App);

app.provide('baseURL', baseURL);

app.use(router);

document.adoptedStyleSheets.push(typescaleStyles.styleSheet);

app.mount('#app');