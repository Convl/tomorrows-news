// Minimal name maps covering the codes present in countries.json and languages.json
const COUNTRY_NAME_BY_CODE = {
    US: 'United States', GB: 'United Kingdom', DE: 'Germany', FR: 'France', ES: 'Spain', IT: 'Italy', NL: 'Netherlands',
    SE: 'Sweden', NO: 'Norway', FI: 'Finland', DK: 'Denmark', IE: 'Ireland', PL: 'Poland', AT: 'Austria', CH: 'Switzerland',
    BE: 'Belgium', PT: 'Portugal', GR: 'Greece', CZ: 'Czechia', HU: 'Hungary', RO: 'Romania', BG: 'Bulgaria', HR: 'Croatia',
    SI: 'Slovenia', SK: 'Slovakia', EE: 'Estonia', LV: 'Latvia', LT: 'Lithuania', CA: 'Canada', AU: 'Australia', NZ: 'New Zealand',
    JP: 'Japan', KR: 'South Korea', CN: 'China', IN: 'India', BR: 'Brazil', MX: 'Mexico', AR: 'Argentina', ZA: 'South Africa',
    EG: 'Egypt', TR: 'Turkey', IL: 'Israel', AE: 'United Arab Emirates', SA: 'Saudi Arabia'
};

const LANGUAGE_NAME_BY_CODE = {
    en: 'English', de: 'German', fr: 'French', es: 'Spanish', it: 'Italian', nl: 'Dutch', sv: 'Swedish', no: 'Norwegian',
    fi: 'Finnish', da: 'Danish', pl: 'Polish', pt: 'Portuguese', el: 'Greek', cs: 'Czech', hu: 'Hungarian', ro: 'Romanian',
    bg: 'Bulgarian', hr: 'Croatian', sl: 'Slovenian', sk: 'Slovak', et: 'Estonian', lv: 'Latvian', lt: 'Lithuanian',
    ru: 'Russian', tr: 'Turkish', ar: 'Arabic', he: 'Hebrew', zh: 'Chinese', ja: 'Japanese', ko: 'Korean', hi: 'Hindi'
};
export async function fetchCountryOptions(includeBlank = true) {
    try {
        const response = await fetch('/app/js/countries.json', { cache: 'no-store' });
        if (!response.ok) throw new Error('countries fetch failed');
        const data = await response.json();
        const options = (Array.isArray(data) ? data : [])
            .map(entry => {
                if (typeof entry === 'string') {
                    const code = entry.toUpperCase();
                    const name = COUNTRY_NAME_BY_CODE[code] || code;
                    return { value: code, label: `${name} (${code})`, name };
                } else {
                    const code = String(entry.code || '').toUpperCase();
                    const name = String(entry.name || COUNTRY_NAME_BY_CODE[code] || code);
                    return { value: code, label: `${name} (${code})`, name };
                }
            })
            .sort((a, b) => a.label.localeCompare(b.label));
        if (includeBlank) options.unshift({ value: '', label: '—' });
        return options;
    } catch {
        return [{ value: '', label: '—' }];
    }
}

export async function fetchLanguageOptions(includeBlank = true) {
    try {
        const response = await fetch('/app/js/languages.json', { cache: 'no-store' });
        if (!response.ok) throw new Error('languages fetch failed');
        const data = await response.json();
        const options = (Array.isArray(data) ? data : [])
            .map(entry => {
                if (typeof entry === 'string') {
                    const code = String(entry);
                    const name = LANGUAGE_NAME_BY_CODE[code] || code;
                    return { value: code, label: `${name} (${code})`, name };
                } else {
                    const code = String(entry.code || '');
                    const name = String(entry.name || LANGUAGE_NAME_BY_CODE[code] || code);
                    return { value: code, label: `${name} (${code})`, name };
                }
            })
            .sort((a, b) => a.label.localeCompare(b.label));
        if (includeBlank) options.unshift({ value: '', label: '—' });
        return options;
    } catch {
        return [{ value: '', label: '—' }];
    }
}

export async function fetchSourceTypeOptions() {
    try {
        const res = await fetch('/openapi.json', { cache: 'no-store' });
        if (!res.ok) throw new Error('openapi fetch failed');
        const spec = await res.json();
        const comp = spec?.components?.schemas || {};
        let schema = comp?.ScrapingSourceBase?.properties?.source_type || comp?.ScrapingSourceCreate?.properties?.source_type;
        let values = [];
        if (schema?.enum && Array.isArray(schema.enum)) {
            values = schema.enum;
        } else if (schema?.$ref) {
            const ref = schema.$ref; // e.g. '#/components/schemas/ScrapingSourceEnum'
            const parts = ref.split('/');
            const name = parts[parts.length - 1];
            const refSchema = comp[name];
            if (refSchema?.enum && Array.isArray(refSchema.enum)) {
                values = refSchema.enum;
            }
        }
        if (!values.length && comp?.ScrapingSourceEnum?.enum) {
            values = comp.ScrapingSourceEnum.enum;
        }
        if (!values.length) {
            // Fallback
            values = ['Webpage', 'Rss', 'Api'];
        }
        return values.map(v => ({ value: v, label: v }));
    } catch {
        return [
            { value: 'Webpage', label: 'Webpage' },
            { value: 'Rss', label: 'Rss' },
            { value: 'Api', label: 'Api' },
        ];
    }
}

export function populateSelect(selectEl, options, selectedValue = '') {
    selectEl.innerHTML = '';
    for (const opt of options) {
        const o = document.createElement('option');
        o.value = opt.value;
        o.textContent = opt.label;
        if (opt.name) o.dataset.name = opt.name;
        if (opt.value === selectedValue) o.selected = true;
        selectEl.appendChild(o);
    }
}


