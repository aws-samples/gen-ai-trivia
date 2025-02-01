import i18n from "."
const Trans = {
    get defaultLocale() {
        return import.meta.env.VITE_DEFAULT_LOCALE
    },
    guessDefaultLocale() {
        const userPersistedLocale = Trans.getPersistedLocale()
        if (userPersistedLocale) {
            return userPersistedLocale
        }
        const userPreferredLocale = Trans.getUserLocale()
        if (Trans.isLocaleSupported(userPreferredLocale.locale)) {
            return userPreferredLocale.locale
        }
        if (Trans.isLocaleSupported(userPreferredLocale.localeNoRegion)) {
            return userPreferredLocale.localeNoRegion
        }

        return Trans.defaultLocale
    },
    isLocaleSupported(locale) {
        return Trans.supportedLocales.includes(locale)
    },
    getUserLocale() {
        const locale = window.navigator.language ||
            window.navigator.userLanguage ||
            Trans.defaultLocale
        return {
            locale: locale,
            localeNoRegion: locale.split('-')[0]
        }
    },

    getPersistedLocale() {
        const persistedLocale = this.getCookie("triviaLocale")
        if (Trans.isLocaleSupported(persistedLocale)) {
            return persistedLocale
        } else {
            return null
        }
    },
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    },
    get supportedLocales() {
        return import.meta.env.VITE_SUPPORTED_LOCALES.split(",")
    },
    set currentLocale(newLocale) {
        i18n.global.locale.value = newLocale
    },
    async switchLanguage(newLocale) {
        Trans.currentLocale = newLocale;
        document.querySelector("html").setAttribute("lang", newLocale);

        document.cookie(`triviaLocale=${newLocale}`)
        locaation.reload()
        // When the language is switched it's not rendering text with
        // computed values from mounted functions. Still need to figure
        // out the best way to do it. Trying to switch for local storage
        // to a persistent cookie for now, but probably a better way
    },
}

export default Trans