const AUTH_API_BASE = 'http://127.0.0.1:5000/api/auth';
export const AUTH_COOKIE_NAME = 'fabritag_auth_token';

export function setAuthCookie(cookies, token) {
    cookies.set(AUTH_COOKIE_NAME, token, {
        path: '/',
        httpOnly: true,
        sameSite: 'lax',
        secure: false,
        maxAge: 60 * 60 * 12
    });
}

export function clearAuthCookie(cookies) {
    cookies.delete(AUTH_COOKIE_NAME, {
        path: '/'
    });
}

export function getAuthToken(event) {
    return event.cookies.get(AUTH_COOKIE_NAME) || '';
}

function getAuthHeaders(token) {
    if (!token) return {};
    return {
        Authorization: `Bearer ${token}`
    };
}

export async function fetchCurrentUser(event) {
    const token = getAuthToken(event);
    if (!token) return null;

    const response = await event.fetch(`${AUTH_API_BASE}/session`, {
        headers: getAuthHeaders(token)
    });

    if (!response.ok) {
        return null;
    }

    const data = await response.json().catch(() => null);
    return data?.user || null;
}

export async function logoutBackendSession(event) {
    const token = getAuthToken(event);
    if (!token) return;

    await event.fetch(`${AUTH_API_BASE}/logout`, {
        method: 'POST',
        headers: getAuthHeaders(token)
    });
}
