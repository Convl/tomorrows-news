/**
 * Field Help System
 * Provides reusable functions for adding contextual help to form fields
 */

/**
 * Add help icon with tooltip to a form label
 * @param {string} labelSelector - CSS selector for the label element
 * @param {string} helpText - The help text to display in the tooltip
 * @param {object} options - Optional configuration
 */
export function addHelpIcon(labelSelector, helpText, options = {}) {
    const label = document.querySelector(labelSelector);
    if (!label) return;

    // Make label flex container if not already
    if (!label.classList.contains('form-label-with-help')) {
        label.classList.add('form-label-with-help');
    }

    // Create help icon container
    const helpContainer = document.createElement('div');
    helpContainer.className = 'field-help-container';
    helpContainer.setAttribute('tabindex', '0');
    helpContainer.setAttribute('role', 'button');
    helpContainer.setAttribute('aria-label', 'Show field help');

    // Create help icon
    const helpIcon = document.createElement('div');
    helpIcon.className = 'help-icon';
    helpIcon.innerHTML = 'ℹ️';

    // Create tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'help-tooltip';
    tooltip.innerHTML = helpText;
    tooltip.setAttribute('role', 'tooltip');

    helpIcon.appendChild(tooltip);
    helpContainer.appendChild(helpIcon);
    label.appendChild(helpContainer);

    // Add keyboard support
    helpContainer.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            helpContainer.focus();
        }
    });
}

/**
 * Add help text below a form field
 * @param {string} fieldSelector - CSS selector for the field element
 * @param {string} helpText - The help text to display
 * @param {boolean} isDynamic - Whether this help text will change dynamically
 */
export function addHelpText(fieldSelector, helpText, isDynamic = false) {
    const field = document.querySelector(fieldSelector);
    if (!field) return;

    const helpDiv = document.createElement('div');
    helpDiv.className = `form-help-text${isDynamic ? ' dynamic' : ''}`;
    helpDiv.innerHTML = helpText;
    helpDiv.id = `${field.id}-help`;

    // Add aria-describedby to field for accessibility
    if (field.getAttribute('aria-describedby')) {
        field.setAttribute('aria-describedby', field.getAttribute('aria-describedby') + ' ' + helpDiv.id);
    } else {
        field.setAttribute('aria-describedby', helpDiv.id);
    }

    field.parentNode.insertBefore(helpDiv, field.nextSibling);
    return helpDiv;
}

/**
 * Update dynamic help text
 * @param {string} fieldSelector - CSS selector for the field element
 * @param {string} newHelpText - The new help text
 */
export function updateHelpText(fieldSelector, newHelpText) {
    const field = document.querySelector(fieldSelector);
    if (!field) return;

    const helpDiv = document.querySelector(`#${field.id}-help`);
    if (helpDiv) {
        helpDiv.innerHTML = newHelpText;
    }
}

/**
 * Add dynamic help for select dropdowns
 * @param {string} selectSelector - CSS selector for the select element
 * @param {object} helpMapping - Object mapping option values to help text
 * @param {string} defaultHelp - Default help text when no option is selected
 */
export function addSelectDynamicHelp(selectSelector, helpMapping, defaultHelp = '') {
    const select = document.querySelector(selectSelector);
    if (!select) return;

    // Add initial help text
    const helpDiv = addHelpText(selectSelector, defaultHelp, true);

    // Update help text when selection changes
    select.addEventListener('change', () => {
        const selectedValue = select.value;
        const helpText = helpMapping[selectedValue] || defaultHelp;
        if (helpDiv) {
            helpDiv.innerHTML = helpText;
        }
    });
}

/**
 * Predefined help text for common fields
 */
export const HELP_TEXTS = {
    SOURCE_TYPES: {
        'Webpage': 'Scrape content directly from web pages. Best for news sites, press release pages, and structured content.',
        'Rss': 'Monitor RSS/Atom feeds for new articles. More reliable and efficient than webpage scraping.',
        'Api': 'Connect to APIs for real-time data (coming soon).'
    },

    DEGREES_OF_SEPARATION: {
        icon: 'How many clicks away from the base URL should we look for relevant content? 0 = only the base page, 1 = base page + linked pages, 2 = base page + linked pages + their linked pages.',
        text: 'Higher numbers find more content but take longer to process.'
    },

    SCRAPING_FREQUENCY: {
        icon: 'How often should we check this source for new content? Minimum is 1440 minutes (24 hours) to avoid overwhelming source servers.',
        text: 'More frequent scraping uses more resources and may be blocked by some sites.'
    },

    COUNTRY_LANGUAGE: {
        icon: 'Help us understand the geographical and linguistic context of this source for better content analysis.',
        text: 'These fields help improve content classification and event relevance scoring.'
    },

    TOPIC_DESCRIPTION: {
        text: 'Describe what types of events and news this topic should track. This helps our AI understand what content is relevant.'
    }
};
