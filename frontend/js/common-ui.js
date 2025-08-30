/**
 * Common UI Components and Utilities
 * Shared functionality across all frontend pages
 */

/**
 * Creates the standard page header structure
 * @param {string} title - Page title
 * @param {string} icon - Icon emoji
 * @param {string} backUrl - URL for back button (optional)
 * @returns {HTMLElement} Header element
 */
export function createPageHeader(title, icon, backUrl = '/app/dashboard.html') {
    const header = document.createElement('div');
    header.innerHTML = `
        <a href="${backUrl}" class="btn btn-link mb-4">← Back</a>
        <div class="card">
            <div class="card-body">
                <div class="d-flex align-items-center mb-4">
                    <div class="icon-placeholder icon-topic me-3">${icon}</div>
                    <h1 class="h4 mb-0 fw-semibold">${title}</h1>
                </div>
                <div id="alert" class="alert d-none" role="alert"></div>
                <div id="form"></div>
            </div>
        </div>
    `;
    return header;
}

/**
 * Creates action buttons for forms
 * @param {Array} buttons - Array of button configurations
 * @returns {HTMLElement} Button container
 */
export function createActionButtons(buttons) {
    const container = document.createElement('div');
    container.className = 'd-grid gap-2 mt-4';

    buttons.forEach(btn => {
        const button = document.createElement('button');
        button.id = btn.id;
        button.className = btn.className || 'btn btn-primary';
        button.textContent = btn.text;
        if (btn.onclick) button.onclick = btn.onclick;
        container.appendChild(button);
    });

    return container;
}

/**
 * Standard alert handling
 */
export class AlertManager {
    constructor(alertElementId = 'alert') {
        this.alertEl = document.getElementById(alertElementId);
    }

    show(message, type = 'danger') {
        if (!this.alertEl) return;
        this.alertEl.textContent = message;
        this.alertEl.className = `alert alert-${type}`;
    }

    hide() {
        if (!this.alertEl) return;
        this.alertEl.className = 'alert d-none';
    }

    success(message) {
        this.show(message, 'success');
    }

    error(message) {
        this.show(message, 'danger');
    }
}

/**
 * Standard form field creation
 */
export function createFormField(config) {
    const { id, label, type = 'text', placeholder = '', required = false, rows, options } = config;

    const wrapper = document.createElement('div');
    wrapper.className = 'mb-4';

    // Create label
    const labelEl = document.createElement('label');
    labelEl.className = 'form-label';
    labelEl.setAttribute('for', id);
    labelEl.innerHTML = `${label}${required ? ' <span class="text-secondary">(required)</span>' : ''}`;

    // Create input/textarea/select
    let inputEl;
    if (type === 'textarea') {
        inputEl = document.createElement('textarea');
        inputEl.rows = rows || 4;
    } else if (type === 'select') {
        inputEl = document.createElement('select');
        if (options) {
            options.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt.value || opt;
                option.textContent = opt.label || opt;
                if (opt.selected) option.selected = true;
                if (opt.disabled) option.disabled = true;
                inputEl.appendChild(option);
            });
        }
    } else {
        inputEl = document.createElement('input');
        inputEl.type = type;
    }

    inputEl.className = type === 'select' ? 'form-select' : 'form-control';
    inputEl.id = id;
    if (placeholder) inputEl.placeholder = placeholder;
    if (required) inputEl.required = true;

    wrapper.appendChild(labelEl);
    wrapper.appendChild(inputEl);

    return { wrapper, label: labelEl, input: inputEl };
}

/**
 * Frequency converter utilities
 */
export class FrequencyConverter {
    static fromMinutes(minutes) {
        if (minutes >= 1440 && minutes % 1440 === 0) {
            return { value: minutes / 1440, unit: 'days' };
        } else if (minutes >= 60 && minutes % 60 === 0) {
            return { value: minutes / 60, unit: 'hours' };
        } else {
            return { value: minutes, unit: 'minutes' };
        }
    }

    static toMinutes(value, unit) {
        const numValue = parseInt(value, 10) || 1;
        switch (unit) {
            case 'days': return numValue * 24 * 60;
            case 'hours': return numValue * 60;
            case 'minutes': return numValue;
            default: return 1440; // Default to 1 day
        }
    }

    static ensureMinimum(minutes) {
        return Math.max(minutes, 1440); // Minimum 1 day
    }
}

/**
 * Standard delete confirmation with improved UX
 */
export async function confirmDelete(itemName, itemType, deleteFunction) {
    const confirmed = confirm(
        `⚠️ Are you sure you want to delete "${itemName}"?\n\n` +
        `This action cannot be undone${itemType === 'topic' ? ' and will also delete all associated feeds and events' : itemType === 'feed' ? ' and will stop all scheduled scraping for this feed' : ''}.`
    );

    if (!confirmed) return false;

    try {
        await deleteFunction();
        return true;
    } catch (error) {
        throw error;
    }
}

/**
 * Standard navigation after successful operations
 */
export function navigateAfterSuccess(delay = 1500) {
    setTimeout(() => {
        window.location.href = '/app/dashboard.html';
    }, delay);
}

/**
 * Initialize common page functionality
 */
export async function initializePage() {
    const { getToken } = await import('./config.js');

    // Check authentication
    if (!getToken()) {
        window.location.href = '/app/login.html';
        return false;
    }

    return true;
}

/**
 * Standard patch computation for forms
 */
export function computePatch(currentData, originalData) {
    const patch = {};
    for (const [key, value] of Object.entries(currentData)) {
        if (JSON.stringify(value) !== JSON.stringify(originalData[key] ?? null)) {
            patch[key] = value;
        }
    }
    return patch;
}
