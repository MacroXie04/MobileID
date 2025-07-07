import './assets/css/main.css'

// Importing the Bootstrap CSS
import "bootstrap/dist/css/bootstrap.min.css"
import 'cropperjs/dist/cropper.css';

import {createApp} from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(router)

app.mount('#app')
