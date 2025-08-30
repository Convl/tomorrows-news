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
function processOptionsData(data, nameByCode, isCountry = false) {
    return (Array.isArray(data) ? data : [])
        .map(entry => {
            if (typeof entry === 'string') {
                const code = isCountry ? entry.toUpperCase() : String(entry);
                const name = nameByCode[code] || code;
                return { value: code, label: `${name} (${code})`, name };
            } else {
                const code = isCountry ? String(entry.code || '').toUpperCase() : String(entry.code || '');
                const name = String(entry.name || nameByCode[code] || code);
                return { value: code, label: `${name} (${code})`, name };
            }
        })
        .sort((a, b) => a.label.localeCompare(b.label));
}

async function fetchOptions(url, nameByCode, isCountry = false, includeBlank = true) {
    try {
        const response = await fetch(url, { cache: 'no-store' });
        if (!response.ok) throw new Error(`${url} fetch failed`);
        const data = await response.json();
        const options = processOptionsData(data, nameByCode, isCountry);
        if (includeBlank) options.unshift({ value: '', label: '—' });
        return options;
    } catch {
        return [{ value: '', label: '—' }];
    }
}

export async function fetchCountryOptions(includeBlank = true) {
    return fetchOptions('/app/js/countries.json', COUNTRY_NAME_BY_CODE, true, includeBlank);
}

export async function fetchLanguageOptions(includeBlank = true) {
    return fetchOptions('/app/js/languages.json', LANGUAGE_NAME_BY_CODE, false, includeBlank);
}

function extractEnumValues(comp) {
    // Try multiple schema paths
    const schemaPaths = [
        comp?.ScrapingSourceBase?.properties?.source_type,
        comp?.ScrapingSourceCreate?.properties?.source_type
    ];

    for (const schema of schemaPaths) {
        if (schema?.enum && Array.isArray(schema.enum)) {
            return schema.enum;
        }
        if (schema?.$ref) {
            const refName = schema.$ref.split('/').pop();
            const refSchema = comp[refName];
            if (refSchema?.enum && Array.isArray(refSchema.enum)) {
                return refSchema.enum;
            }
        }
    }

    // Direct enum fallback
    if (comp?.ScrapingSourceEnum?.enum) {
        return comp.ScrapingSourceEnum.enum;
    }

    return ['Webpage', 'Rss', 'Api']; // Final fallback
}

export async function fetchSourceTypeOptions() {
    const fallback = [
        { value: 'Webpage', label: 'Webpage', disabled: false },
        { value: 'Rss', label: 'Rss', disabled: false },
        { value: 'Api', label: 'Api (Coming Soon)', disabled: true },
    ];

    try {
        const res = await fetch('/openapi.json', { cache: 'no-store' });
        if (!res.ok) throw new Error('openapi fetch failed');
        
        const spec = await res.json();
        const values = extractEnumValues(spec?.components?.schemas || {});
        
        return values.map(v => ({
            value: v,
            label: v === 'Api' ? 'Api (Coming Soon)' : v,
            disabled: v === 'Api'
        }));
    } catch {
        return fallback;
    }
}

export function populateSelect(selectEl, options, selectedValue = '') {
    selectEl.innerHTML = '';
    for (const opt of options) {
        const o = document.createElement('option');
        o.value = opt.value;
        o.textContent = opt.label;
        if (opt.name) o.dataset.name = opt.name;
        if (opt.disabled) {
            o.disabled = true;
            o.style.color = '#6b7280'; // Grey color for disabled options
            o.style.fontStyle = 'italic';
        }
        if (opt.value === selectedValue && !opt.disabled) o.selected = true;
        selectEl.appendChild(o);
    }
}


