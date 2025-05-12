import { createI18n } from "vue-i18n";
import en from "./locales/en.js";
import es from "./locales/es.js";
import de from "./locales/de.js";
import it from "./locales/it.js";
import fr from "./locales/fr.js";
import ja from "./locales/ja.js";
import zh from "./locales/zh.js";
import pt from "./locales/pt.js";
import ru from "./locales/ru.js";
import ar from "./locales/ar.js";

export default createI18n({
    locale: import.meta.env.VITE_DEFAULT_LOCALE,
    fallbackLocale: import.meta.env.VITE_FALLBACK_LOCALE,
    legacy: false,
    messages: {
        en,
        es,
        de,
        it,
        fr,
        ja,
        zh,
        pt,
        ru,
        ar
    },
    globalInjection: true
});