import React, { useEffect, useState } from "react";
import { useForm, FormProvider } from "react-hook-form";
import {
  TextFieldElement,
  SelectElement,
  CheckboxElement,
  FormContainer,
  AutocompleteElement,
} from "react-hook-form-mui";
import {
  Box,
  Grid,
  Typography,
  Tooltip,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
} from "@mui/material";
import InfoIcon from "@mui/icons-material/Info";
import EditNoteIcon from "@mui/icons-material/EditNote";
import LinkIcon from "@mui/icons-material/Link";
import RssFeedIcon from "@mui/icons-material/RssFeed";
import PublicIcon from "@mui/icons-material/Public";
import TranslateIcon from "@mui/icons-material/Translate";
import TimelineIcon from "@mui/icons-material/Timeline";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import BadgeIcon from "@mui/icons-material/Badge";
import {
  fetchCountryOptions,
  fetchLanguageOptions,
  fetchSourceTypeOptions,
  fetchLanguage,
} from "../api/choices";
import FieldWithTooltip from "./FieldWithTooltip";

const tooltips = {
  name: "Source name, e.g. 'Presseschau der LTO', 'Politikressort der F.A.Z.', 'Pressemitteilungen des Bundesgerichtshofs'",
  base_url:
    "Webpage or RSS feed URL that will contain the news, e.g. https://www.bundesgerichtshof.de/DE/Presse/Pressemitteilungen/pressemitteilungen_node.html, https://www.lto.de/presseschau-rss/rss/feed.xml",
  source_type:
    "Whether the base url you provided points to a web page like https://www.lto.de/recht/presseschau or a Rss feed like https://www.lto.de/presseschau-rss/rss/feed.xml or a REST Api (coming soon)",
  country:
    'The country where this feed resides, e.g. "United States" for the New York Times, or "Germany" for the F.A.Z.',
  language:
    'The language in which events extracted from this feed should appear. This should typically be the same language that is used by the feed itself, and correspond to the feed\'s country, i.e. "English (en)" for the New York Times or "German (de)" for the F.A.Z.',
  degrees_of_separation:
    "Where information about upcoming events is expected to be found, relative to the base url.\n1 = News content found DIRECTLY ON THE BASE URL, such as with a long-running liveblog. This option is rare / exotic\n2 = News content LINKED TO FROM THE BASE URL, such as with the base url or specific subsections (politics, business, etc) of any online news outlet. This option is by far the most common\n3 = News content LINKED TO FROM THE BASE URL, but contains further links, which must also be scraped. Use this option for press reviews or similar types of curated overviews, e.g. https://www.lto.de/recht/presseschau",
  scraping_frequency:
    "How often this feed shall be scraped for new events (minimum: 1 day / 24 hours / 1440 minutes)",
  is_active:
    "Whether the topic is active or not. The value in this field will be passed to the LLM that assists in the event extraction, and will directly impact the results that you see in your dashboard.",
};

export default function ScrapingSourceForm({
  onSubmit,
  defaultValues,
  formActions,
}) {
  // Set default values, merge with incoming values
  const baseDefaults = {
    name: "",
    base_url: "",
    source_type: "Webpage",
    country_code: "",
    language_code: "",
    degrees_of_separation: 1,
    scraping_frequency: 1440,
    is_active: true,
  };

  const mergedDefaults = {
    ...baseDefaults,
    ...(defaultValues || {}),
  };

  // Convert scraping frequency (provided in minutes) to the highest unit to which it can be converted
  const freqInMinutes = mergedDefaults.scraping_frequency;
  let initialFreq = freqInMinutes;
  let initialUnit = "minutes";
  if (freqInMinutes >= 1440 && freqInMinutes % 1440 === 0) {
    initialFreq = freqInMinutes / 1440;
    initialUnit = "days";
  } else if (freqInMinutes >= 60 && freqInMinutes % 60 === 0) {
    initialFreq = freqInMinutes / 60;
    initialUnit = "hours";
  }

  // Need to save both to state to calculate frequency in minutes on form submission
  const [frequencyValue, setFrequencyValue] = useState(initialFreq);
  const [frequencyUnit, setFrequencyUnit] = useState(initialUnit);

  // Needed for autocomplete elements
  const countryOptions = fetchCountryOptions();
  const languageOptions = fetchLanguageOptions();
  const sourceTypeOptions = fetchSourceTypeOptions();

  // Language is auto-set based on country, unless it has been manually set before
  const [languageTouched, setLanguageTouched] = useState(false);

  // Select styles
  const selectEllipsisSx = {
    "& .MuiSelect-select": {
      whiteSpace: "nowrap",
      overflow: "hidden",
      textOverflow: "ellipsis",
    },
  };

  // Auto-set language based on country
  function autoSetLanguage(country) {
    const { languages } = fetchLanguage(country.value);
    if (languages.length > 0) {
      const languageCode = languages[0];
      const languageName = languageOptions.find(
        (opt) => opt.value === languageCode
      )?.name;
      setValue("language_code", languageCode);
      setValue("language", languageName);
    }
  }

  // Convert frequency display value to minutes on form submission
  const handleSubmit = async (data) => {
    const payload = {
      ...data,
      scraping_frequency:
        frequencyUnit === "minutes"
          ? frequencyValue
          : frequencyUnit === "hours"
          ? frequencyValue * 60
          : frequencyValue * 1440,
    };
    await onSubmit(payload);
  };

  // Form context
  const formContext = useForm({
    defaultValues: mergedDefaults,
  });
  const { setValue } = formContext;

  return (
    <FormContainer formContext={formContext} onSuccess={handleSubmit}>
      <Grid container spacing={3}>
        <Grid size={4}>
          <Box>
            <FieldWithTooltip
              tooltip={tooltips.name}
              icon={<BadgeIcon />}
              label="Name (required)"
            >
              <TextFieldElement
                name="name"
                fullWidth
                required
                placeholder="Enter source name..."
              />
            </FieldWithTooltip>
          </Box>
        </Grid>

        <Grid size={4}>
          <FieldWithTooltip
            tooltip={tooltips.base_url}
            icon={<LinkIcon />}
            label="Base URL (required)"
            required
          >
            <TextFieldElement
              name="base_url"
              type="url"
              fullWidth
              required
              placeholder="https://example.com"
            />
          </FieldWithTooltip>
        </Grid>

        <Grid size={4}>
          <FieldWithTooltip
            tooltip={tooltips.source_type}
            icon={<RssFeedIcon />}
            label="Source Type (required)"
          >
            <SelectElement
              name="source_type"
              fullWidth
              required
              options={sourceTypeOptions}
              valueKey="value"
              sx={selectEllipsisSx}
            />
          </FieldWithTooltip>
        </Grid>

        <Grid size={6}>
          <FieldWithTooltip
            tooltip={tooltips.country}
            icon={<PublicIcon />}
            label="Country"
          >
            <AutocompleteElement
              name="country_code"
              options={countryOptions}
              transform={{
                // need this to display the countryOptions.label when a country code is set by the mergedDefaults
                input: (value) =>
                  countryOptions.find((opt) => opt.value === value) || null,
              }}
              textFieldProps={{ fullWidth: true }}
              autocompleteProps={{
                autoHighlight: true,
                // set country name and code manually, auto-set language unless already touched
                onChange: (_e, opt) => {
                  if (!opt) return;
                  setValue("country_code", opt.value);
                  setValue("country", opt.name);
                  if (!languageTouched) autoSetLanguage(opt);
                },
              }}
            />
          </FieldWithTooltip>
        </Grid>

        <Grid size={6}>
          <FieldWithTooltip
            tooltip={tooltips.language}
            icon={<TranslateIcon />}
            label="Language"
          >
            <AutocompleteElement
              name="language_code"
              options={languageOptions}
              transform={{
                // need this to display the languageOptions.label when a language code is set by the mergedDefaults, or assigned by autoSetLanguage
                input: (value) =>
                  languageOptions.find((opt) => opt.value === value) || null,
              }}
              textFieldProps={{ fullWidth: true }}
              autocompleteProps={{
                autoHighlight: true,
                // set language name and code manually and mark language selector as touched
                onChange: (_e, opt) => {
                  if (!opt) return;
                  setValue("language_code", opt.value);
                  setValue("language", opt.name);
                  setLanguageTouched(true);
                },
              }}
            />
          </FieldWithTooltip>
        </Grid>

        <Grid size={6}>
          <FieldWithTooltip
            tooltip={tooltips.degrees_of_separation}
            icon={<TimelineIcon />}
            label="Degrees of separation (required)"
          >
            <SelectElement
              required
              name="degrees_of_separation"
              fullWidth
              options={[
                { value: 0, label: "0 (rare, use e.g. for live-blogs)" },
                {
                  value: 1,
                  label: "1 (most common, use for most news websites)",
                },
                {
                  value: 2,
                  label:
                    "2 (rare, use for listings of press reviews or similar types of curated overviews)",
                },
              ]}
              valueKey="value"
              sx={selectEllipsisSx}
            />
          </FieldWithTooltip>
        </Grid>

        <Grid size={6}>
          <FieldWithTooltip
            tooltip={tooltips.scraping_frequency}
            icon={<AccessTimeIcon />}
            label="Scraping frequency (required)"
          >
            <Box sx={{ display: "flex", gap: 1, alignItems: "flex-start" }}>
              <TextField
                type="number"
                fullWidth
                required
                slotProps={{ htmlInput: { min: 1 } }}
                value={frequencyValue}
                onChange={(e) =>
                  setFrequencyValue(parseInt(e.target.value) || 1)
                }
              />
              <FormControl sx={{ minWidth: 120 }}>
                <Select
                  value={frequencyUnit}
                  sx={selectEllipsisSx}
                  required
                  onChange={(e) => setFrequencyUnit(e.target.value)}
                >
                  <MenuItem value="minutes">Minutes</MenuItem>
                  <MenuItem value="hours">Hours</MenuItem>
                  <MenuItem value="days">Days</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </FieldWithTooltip>
        </Grid>

        <Grid size={12}>
          <Box sx={{ display: "flex", alignItems: "center", mb: 0.0 }}>
            <CheckboxElement name="is_active" label="Active" sx={{ mr: 0 }} />
            <Tooltip title={tooltips.is_active} arrow sx={{ ml: 0, pl: 0 }}>
              <IconButton size="small">
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Grid>
      </Grid>
      {formActions}
    </FormContainer>
  );
}
