import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import de from './locales/de.json'
import es from './locales/es.json'
import fr from './locales/fr.json'
import it from './locales/it.json'
import pl from './locales/pl.json'
import sv from './locales/sv.json'

export type MessageSchema = typeof en

const i18n = createI18n<{ message: MessageSchema }, 'en' | 'de' | 'es' | 'fr' | 'it' | 'pl' | 'sv'>({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en,
    de,
    es,
    fr,
    it,
    pl,
    sv,
  },
})

export default i18n
