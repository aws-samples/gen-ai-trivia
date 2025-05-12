<template>
    <select @change="switchLanguage" class="form-select" :value="locale">
        <option v-for="sLocale in supportedLocales" :key="`locale-${sLocale}`" :value="sLocale">
            {{ getLanguageName(sLocale) }}
        </option>
    </select>
</template>

<script>
import { useI18n } from 'vue-i18n';
import Tr from '../i18n/translation';

export default {
    setup() {
        const { t, locale } = useI18n();
        const supportedLocales = Tr.supportedLocales;
        
        // Map of language codes to their full names
        const languageNames = {
            'en': 'English',
            'es': 'Español',
            'de': 'Deutsch',
            'it': 'Italiano',
            'fr': 'Français',
            'ja': '日本語',
            'zh': '中文',
            'pt': 'Português',
            'ru': 'Русский',
            'ar': 'العربية'
        };
        
        const getLanguageName = (localeCode) => {
            // Try to get the language name from the current locale's translations
            const translatedName = t(`locale.${localeCode}`);
            
            // If the translation exists and is not in the format "locale.xx", use it
            if (translatedName && !translatedName.startsWith('locale.')) {
                return translatedName;
            }
            
            // Otherwise fall back to the predefined language names
            return languageNames[localeCode] || localeCode;
        };
        
        const switchLanguage = async (event) => {
            const newLocale = event.target.value;
            await Tr.switchLanguage(newLocale);
        };
        
        return { t, locale, supportedLocales, switchLanguage, getLanguageName };
    }
}
</script>