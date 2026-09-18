import { adminDestination, loginDestination } from './admin-navigation';

export type User = { id: string; name: string; email: string; role: string; active: boolean };

export async function api(path: string, options: RequestInit = {}) {
    const headers = new Headers(options.headers);
    const token = sessionStorage.getItem('session');
    if (token) headers.set('Authorization', `Bearer ${token}`);
    if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
    const response = await fetch(`/api${path}`, { ...options, headers });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
        if (response.status === 401 && path !== '/auth/login') {
            sessionStorage.removeItem('session');
            window.location.assign(loginDestination(window.location.pathname));
        }
        throw new Error(typeof data?.detail === 'string' ? data.detail : Array.isArray(data?.detail) ? data.detail.map((e: {msg: string}) => e.msg).join('; ') : 'Request failed. Check that the backend is running.');
    }
    return data;
}

export async function signIn(email: string, password: string, adminOnly = false) {
    const result = await api('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    sessionStorage.setItem('session', result.token);
    if (adminOnly && result.user.role !== 'admin') {
        await signOut();
        throw new Error('Administrator access required');
    }
    const destination = roleDestination(result.user.role, new URLSearchParams(window.location.search).get('next'));
    window.location.assign(destination);
}

function roleDestination(role: string, next: string | null): string {
    if (role === 'admin') return adminDestination(next ?? '/admin/dashboard');
    if (role === 'student') {
        if (next && (next === '/student/dashboard' || (next.startsWith('/student') && next.length > 7))) return next;
        return '/student/dashboard';
    }
    if (next && next.startsWith('/dashboard')) return next;
    return '/dashboard';
}

export async function signOut() {
    await api('/auth/logout', { method: 'POST' });
    sessionStorage.removeItem('session');
}
