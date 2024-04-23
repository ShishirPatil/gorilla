import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import 'prismjs/themes/prism.css';
import store from './store';

import { createVuetify } from 'vuetify';
import 'vuetify/styles';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';

const vuetify = createVuetify({
    components,
    directives,
});

if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/apizoo/service-worker.js').then(function(registration) {
            console.log('ServiceWorker registration successful with scope: ', registration.scope);
        }, function(err) {
            console.log('ServiceWorker registration failed: ', err);
        });
    });
}

const app = createApp(App);
app.use(router);
app.use(vuetify);
app.use(store);
app.mount('#app');