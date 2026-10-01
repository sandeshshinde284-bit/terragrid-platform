import { createApp } from 'vue'
import { createPinia } from 'pinia'
import type { App } from 'vue'

import AppComponent from './App.vue'
import router from '@/router'
import { loggerPlugin } from '@/plugins/logger'
import i18n from '@/i18n'

import './style.css'

const app: App = createApp(AppComponent)

app.use(createPinia())
app.use(router)
app.use(loggerPlugin)
app.use(i18n)

app.mount('#app')