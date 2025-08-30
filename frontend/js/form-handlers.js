/**
 * Form Handlers
 * Specialized form creation and handling for topics and feeds
 */

import { createFormField, FrequencyConverter, AlertManager, computePatch } from './common-ui.js';
import { populateSelect, fetchLanguageOptions, fetchSourceTypeOptions } from './choices.js';
import { apiBase, authHeaders } from './config.js';
import { addHelpIcon, addSelectDynamicHelp, HELP_TEXTS } from './field-help.js';

/**
 * Topic form generator and handler
 */
export class TopicFormHandler {
    constructor(formContainer, isEdit = false) {
        this.formContainer = formContainer;
        this.isEdit = isEdit;
        this.alertManager = new AlertManager();
        this.original = null;
    }

    createForm() {
        const nameField = createFormField({
            id: 'name',
            label: '📝 Name',
            placeholder: 'e.g., Law & Legislation in Germany',
            required: !this.isEdit
        });

        const descField = createFormField({
            id: 'description',
            label: '📄 Description',
            type: 'textarea',
            placeholder: 'Describe what kinds of events you are interested in...'
        });

        this.formContainer.appendChild(nameField.wrapper);
        this.formContainer.appendChild(descField.wrapper);

        // Setup help text
        this.setupHelp();

        return {
            name: nameField.input,
            description: descField.input
        };
    }

    setupHelp() {
        const helpTexts = {
            name: 'A succinct name for the topic about which upcoming events shall be gathered, e.g. "Law & Legislation in Germany", "International developments in artificial intelligence", "Anything and everything having to do with UFOS". The value in this field will be passed to the LLM that assists in the event extraction, and will directly impact the results that you see in your dashboard.',
            description: 'A more detailed description of the topic and the kinds of events you are interested in, e.g.: "Court cases and legislative proceedings in Germany that are significant enough to be of interest to the general public", "Only focus on A.I. developments that are likely to impact the job market for software engineers within the next 12 months", "I particularly care about UFO- and Alien-related Festivals and conventions". The value in this field will be passed to the LLM that assists in the event extraction, and will directly impact the results that you see in your dashboard'
        };

        Object.entries(helpTexts).forEach(([field, text]) => {
            addHelpIcon(`label[for="${field}"]`, text);
        });
    }

    async loadData(topicId) {
        if (!this.isEdit) return;

        try {
            const resp = await fetch(`${apiBase}/topics/${topicId}`, { headers: authHeaders() });
            if (!resp.ok) throw new Error('Failed to load topic');

            this.original = await resp.json();
            document.getElementById('name').value = this.original.name || '';
            document.getElementById('description').value = this.original.description || '';
        } catch (err) {
            this.alertManager.error('Failed to load topic');
            throw err;
        }
    }

    async save(topicId = null) {
        this.alertManager.hide();

        const data = {
            name: document.getElementById('name').value.trim(),
            description: document.getElementById('description').value.trim() || null,
            is_active: true
        };

        // Validation
        if (!data.name) {
            this.alertManager.error('Name is required');
            return false;
        }

        try {
            let resp;
            if (this.isEdit && topicId) {
                const patch = computePatch(data, this.original);
                resp = await fetch(`${apiBase}/topics/${topicId}`, {
                    method: 'PUT',
                    headers: authHeaders(),
                    body: JSON.stringify(patch)
                });
            } else {
                resp = await fetch(`${apiBase}/topics/`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify(data)
                });
            }

            if (!resp.ok) throw new Error('Failed to save topic');
            return true;
        } catch (err) {
            this.alertManager.error(err.message || 'Failed to save topic');
            return false;
        }
    }

    async delete(topicId) {
        this.alertManager.hide();

        try {
            const resp = await fetch(`${apiBase}/topics/${topicId}`, {
                method: 'DELETE',
                headers: authHeaders()
            });

            if (!resp.ok) {
                const error = await resp.text();
                throw new Error(error || 'Failed to delete topic');
            }

            this.alertManager.success('✅ Topic deleted successfully. Redirecting...');
            return true;
        } catch (err) {
            this.alertManager.error(err.message || 'Failed to delete topic');
            return false;
        }
    }
}

/**
 * Feed form generator and handler
 */
export class FeedFormHandler {
    constructor(formContainer, isEdit = false) {
        this.formContainer = formContainer;
        this.isEdit = isEdit;
        this.alertManager = new AlertManager();
        this.original = null;
    }

    async createForm() {
        // Create basic fields
        const nameField = createFormField({
            id: 'name',
            label: '📝 Name',
            placeholder: 'e.g., Presseschau der LTO',
            required: !this.isEdit
        });

        const urlField = createFormField({
            id: 'base_url',
            label: '🔗 Base URL',
            type: 'url',
            placeholder: 'https://example.com',
            required: !this.isEdit
        });

        const typeField = createFormField({
            id: 'source_type',
            label: '🔧 Source Type',
            type: 'select',
            required: !this.isEdit
        });

        const langField = createFormField({
            id: 'language',
            label: '🗣️ Language',
            type: 'select'
        });

        const degreeField = createFormField({
            id: 'degrees_of_separation',
            label: '🔗 Degrees of separation',
            type: 'select',
            options: [
                { value: '1', label: '1' },
                { value: '2', label: '2', selected: true },
                { value: '3', label: '3' }
            ]
        });

        // Create frequency fields
        const freqWrapper = document.createElement('div');
        freqWrapper.className = 'mb-4';
        freqWrapper.innerHTML = `
            <label class="form-label" for="scraping_frequency">⏱️ Scraping frequency</label>
            <div class="row g-2">
                <div class="col-8">
                    <input class="form-control" id="scraping_frequency_value" type="number" min="1" value="1" />
                </div>
                <div class="col-4">
                    <select class="form-select" id="scraping_frequency_unit">
                        <option value="days" selected>Days</option>
                        <option value="hours">Hours</option>
                        <option value="minutes">Minutes</option>
                    </select>
                </div>
            </div>
        `;

        // Append all fields
        [nameField, urlField, typeField, langField, degreeField].forEach(field => {
            this.formContainer.appendChild(field.wrapper);
        });
        this.formContainer.appendChild(freqWrapper);

        // Populate select options
        await this.populateSelects();

        // Setup help text
        this.setupHelp();

        return {
            name: nameField.input,
            base_url: urlField.input,
            source_type: typeField.input,
            language: langField.input,
            degrees_of_separation: degreeField.input
        };
    }

    async populateSelects() {
        const [languageOptions, sourceTypeOptions] = await Promise.all([
            fetchLanguageOptions(true),
            fetchSourceTypeOptions()
        ]);

        const langEl = document.getElementById('language');
        const typeEl = document.getElementById('source_type');

        if (langEl) populateSelect(langEl, languageOptions);
        if (typeEl) populateSelect(typeEl, sourceTypeOptions);
    }

    setupHelp() {
        const helpTexts = {
            name: 'Source name, e.g. "Presseschau der LTO", "Politikressort der F.A.Z.", "Pressemitteilungen des Bundesgerichtshofs"',
            base_url: 'Webpage or RSS feed URL that will contain the news, e.g. https://www.bundesgerichtshof.de/DE/Presse/Pressemitteilungen/pressemitteilungen_node.html, https://www.lto.de/presseschau-rss/rss/feed.xml',
            scraping_frequency: 'How often this feed shall be scraped for new events (minimum: 1 day / 24 hours / 1440 minutes)',
            degrees_of_separation: 'Where information about upcoming events is expected to be found, relative to the base url.<br><br><strong>1</strong> = News content found DIRECTLY ON THE BASE URL, such as with a long-running liveblog. This option is rare / exotic)<br><br><strong>2</strong> = News content LINKED TO FROM THE BASE URL, such as with the base url or specific subsections (politics, business, etc) of any online news outlet. This option is by far the most common<br><br><strong>3</strong> = News content LINKED TO FROM THE BASE URL, but contains further links, which must also be scraped. Use this option for press reviews or similar types of curated overviews, e.g. https://www.lto.de/recht/presseschau'
        };

        Object.entries(helpTexts).forEach(([field, text]) => {
            addHelpIcon(`label[for="${field}"]`, text);
        });

        // Dynamic help for source type
        addSelectDynamicHelp('#source_type', HELP_TEXTS.SOURCE_TYPES, 'Select how you want to monitor this source for new content.');
    }

    async loadData(feedId) {
        if (!this.isEdit) return;

        try {
            const resp = await fetch(`${apiBase}/scraping-sources/${feedId}`, { headers: authHeaders() });
            if (!resp.ok) throw new Error('Failed to load source');

            this.original = await resp.json();

            // Populate form fields
            document.getElementById('name').value = this.original.name || '';
            document.getElementById('base_url').value = this.original.base_url || '';
            document.getElementById('degrees_of_separation').value = this.original.degrees_of_separation ?? 2;

            // Set language and source type
            if (this.original.language_code) {
                document.getElementById('language').value = this.original.language_code;
            }
            if (this.original.source_type) {
                document.getElementById('source_type').value = this.original.source_type;
            }

            // Convert and set frequency
            const frequency = FrequencyConverter.fromMinutes(this.original.scraping_frequency ?? 1440);
            document.getElementById('scraping_frequency_value').value = frequency.value;
            document.getElementById('scraping_frequency_unit').value = frequency.unit;

        } catch (err) {
            this.alertManager.error('Failed to load source');
            throw err;
        }
    }

    _gatherFormData(topicId = null) {
        const languageEl = document.getElementById('language');
        const freqValue = parseInt(document.getElementById('scraping_frequency_value').value, 10) || 1;
        const freqUnit = document.getElementById('scraping_frequency_unit').value;
        const scrapingFrequency = FrequencyConverter.ensureMinimum(
            FrequencyConverter.toMinutes(freqValue, freqUnit)
        );

        const data = {
            name: document.getElementById('name').value.trim(),
            base_url: document.getElementById('base_url').value.trim(),
            source_type: document.getElementById('source_type').value,
            language: languageEl.options[languageEl.selectedIndex]?.dataset?.name || (languageEl.value || null),
            language_code: languageEl.value || null,
            degrees_of_separation: parseInt(document.getElementById('degrees_of_separation').value, 10) || 2,
            scraping_frequency: scrapingFrequency,
            is_active: true
        };

        if (!this.isEdit && topicId) {
            data.topic_id = topicId;
        }

        return data;
    }

    async save(feedId = null, topicId = null) {
        this.alertManager.hide();

        const data = this._gatherFormData(topicId);

        // Validation
        if (!data.name || !data.base_url || !data.source_type) {
            this.alertManager.error('Name, Base URL, and Source Type are required');
            return false;
        }

        try {
            const isUpdate = this.isEdit && feedId;
            const url = isUpdate ? `${apiBase}/scraping-sources/${feedId}` : `${apiBase}/scraping-sources/`;
            const method = isUpdate ? 'PUT' : 'POST';
            const body = isUpdate ? computePatch(data, this.original) : data;

            const resp = await fetch(url, {
                method,
                headers: authHeaders(),
                body: JSON.stringify(body)
            });

            if (!resp.ok) throw new Error('Failed to save source');
            return true;
        } catch (err) {
            this.alertManager.error(err.message || 'Failed to save source');
            return false;
        }
    }

    async delete(feedId) {
        this.alertManager.hide();

        try {
            const resp = await fetch(`${apiBase}/scraping-sources/${feedId}`, {
                method: 'DELETE',
                headers: authHeaders()
            });

            if (!resp.ok) {
                const error = await resp.text();
                throw new Error(error || 'Failed to delete feed');
            }

            this.alertManager.success('✅ Feed deleted successfully. Redirecting...');
            return true;
        } catch (err) {
            this.alertManager.error(err.message || 'Failed to delete feed');
            return false;
        }
    }
}
