import countries from "i18n-iso-countries";
import enLocale from "i18n-iso-countries/langs/en.json";
import clm from "country-locale-map";

// TODO: Support multiple display languages.
countries.registerLocale(enLocale);

export function fetchCountryOptions(includeBlank = false) {
  const codes = countries.getAlpha2Codes();
  const options = Object.keys(codes)
    .map((code) => ({
      value: code,
      name: countries.getName(code, "en"),
      label: `${countries.getName(code, "en")} (${code})`,
    }))
    .sort((a, b) => a.label.localeCompare(b.label));
  if (includeBlank) options.unshift({ value: "", label: "—" });
  return options;
}

export function fetchLanguageOptions(includeBlank = false) {
  const codes = countries.getSupportedLanguages();
  const displayNames = new Intl.DisplayNames(["en"], { type: "language" });
  const options = codes
    .map((code) => ({
      value: code,
      name: displayNames.of(code),
      label: `${displayNames.of(code)} (${code})`,
    }))
    .sort((a, b) => a.label.localeCompare(b.label));
  if (includeBlank) options.unshift({ value: "", label: "—" });
  return options;
}

export function fetchSourceTypeOptions() {
  return [
    { value: "Webpage", label: "Webpage", disabled: false },
    { value: "Rss", label: "Rss", disabled: false },
    { value: "Api", label: "Api (Coming Soon)", disabled: true },
  ];
}

export function fetchLanguage(code) {
  return clm.getCountryByAlpha2(code);
}
