// Main JavaScript for Tomorrow's News
// Simple API client and utilities

class ApiClient {
    constructor() {
        this.baseURL = '/api/v1';
        this.token = localStorage.getItem('tn_token');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        // Add auth token if available
        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                if (response.status === 401) {
                    this.logout();
                    throw new Error('Authentication required');
                }
                if (response.status === 403) {
                    // Check if it's a verification issue
                    const errorText = await response.text();
                    if (errorText.includes('not verified') || errorText.includes('verified')) {
                        throw new Error('EMAIL_NOT_VERIFIED');
                    }
                    throw new Error('Access forbidden');
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            return response;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async get(endpoint) {
        return this.request(endpoint);
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE',
        });
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('tn_token', token);
    }

    logout() {
        this.token = null;
        localStorage.removeItem('tn_token');
        navigateTo('auth/login.html');
    }

    isAuthenticated() {
        return !!this.token;
    }
}

// Global API client instance
const api = new ApiClient();

// Routing utilities
function getBasePath() {
    // Get the base path for frontend routes
    const path = window.location.pathname;
    if (path.includes('/frontend/')) {
        const frontendIndex = path.indexOf('/frontend/');
        return path.substring(0, frontendIndex + '/frontend/'.length);
    }
    return '/frontend/';
}

function navigateTo(relativePath) {
    // Navigate to a path relative to the frontend base
    const basePath = getBasePath();
    window.location.href = basePath + relativePath;
}

// Utility functions
function showToast(message, type = 'info') {
    // Simple toast notification
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    toast.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
    document.body.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

function showLoading(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    button.disabled = true;
    return () => {
        button.innerHTML = originalText;
        button.disabled = false;
    };
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

// Check authentication on protected pages
function requireAuth() {
    console.log('Checking auth, token:', !!api.token);
    if (!api.isAuthenticated()) {
        console.log('Not authenticated, redirecting...');
        navigateTo('auth/login.html');
        return false;
    }
    console.log('Authenticated, proceeding...');
    return true;
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Add logout functionality to navbar
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function (e) {
            e.preventDefault();
            api.logout();
        });
    }
});