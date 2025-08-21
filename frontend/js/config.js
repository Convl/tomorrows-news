export const apiBase = `/api/v1`;

export function setToken(token) { localStorage.setItem('tn_token', token); }
export function getToken() { return localStorage.getItem('tn_token'); }
export function clearToken() { localStorage.removeItem('tn_token'); }
export function authHeaders() {
    const t = getToken();
    return t ? { 'Authorization': `Bearer ${t}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

// Global fetch wrapper: on 401, clear token and redirect to login
const __originalFetch = window.fetch.bind(window);
function __shouldBypass401(url) {
    try {
        const href = typeof url === 'string' ? url : (url?.url || '');
        if (href.includes('/auth/jwt/login')) return true;
    } catch { }
    if (window.location && window.location.pathname.endsWith('/app/login.html')) return true;
    return false;
}

export async function authedFetch(input, init) {
    const resp = await __originalFetch(input, init);
    if (resp && resp.status === 401 && !__shouldBypass401(input)) {
        clearToken();
        try { window.location.href = '/app/login.html'; } catch { }
    }
    return resp;
}

// Patch window.fetch so all calls benefit
window.fetch = authedFetch;


