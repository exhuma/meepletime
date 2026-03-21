import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import router from './router'
import App from './App.vue'
import { setUnauthorizedHandler } from './api'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#4CAF50',
          secondary: '#FF9800',
        },
      },
    },
  },
})

const app = createApp(App)
app.use(router)
app.use(vuetify)
setUnauthorizedHandler(() => router.push('/login'))
app.mount('#app')
