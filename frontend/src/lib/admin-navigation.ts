import { workspacePages } from './workspace-pages';
export const adminPages = [
    { href: '/admin', label: 'Overview' },
    { href: '/admin/users', label: 'Manage users' },
    { href: '/admin/datasets', label: 'Marketing datasets' },
    { href: '/admin/configuration', label: 'System / model configuration' },
    { href: '/admin/reports', label: 'Analytics & reports' }
];

export function adminDestination(value: string | null): string {
    if (value === '/admin/account') return value;
    return adminPages.some((item) => item.href === value) ? value! : '/admin';
}

export function loginDestination(pathname: string): string {
    return pathname === '/admin' || pathname.startsWith('/admin/')
        ? `/login?next=${encodeURIComponent(adminDestination(pathname))}`
        : `/login?next=${encodeURIComponent(dashboardDestination(pathname))}`;
}

export function dashboardDestination(value: string | null): string {
    return ['/dashboard', '/dashboard/leads', '/dashboard/analytics', '/dashboard/budget', '/dashboard/datasets', '/dashboard/account', ...workspacePages.map(item => `/dashboard/${item.slug}`)].includes(value || '') ? value! : '/dashboard';
}
