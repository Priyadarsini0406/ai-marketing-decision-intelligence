import { workspacePages } from './workspace-pages';
export const adminPages = [
    { href: '/admin/dashboard', label: 'Dashboard' },
    { href: '/admin/students', label: 'Students' },
    { href: '/admin/managers', label: 'Managers' },
    { href: '/admin/users', label: 'User Accounts' },
    { href: '/admin/courses', label: 'Courses / Programs' },
    { href: '/admin/institutions', label: 'Institutions' },
    { href: '/admin/datasets', label: 'Datasets' },
    { href: '/admin/configuration', label: 'Configuration' },
    { href: '/admin/reports', label: 'Analytics & reports' },
    { href: '/admin/account', label: 'My account' },
    { href: '/admin/data-import', label: 'Data Import' },
    { href: '/admin/activity', label: 'System Activity' },
    { href: '/admin/audit-logs', label: 'Audit Logs' },
    { href: '/admin/notifications', label: 'Notifications' },
    { href: '/admin/profile', label: 'Profile' },
    { href: '/admin/settings', label: 'Settings' }
];

export function adminDestination(value: string | null): string {
    return adminPages.some((item) => item.href === value) ? value! : '/admin/dashboard';
}

export function loginDestination(pathname: string): string {
    if (pathname === '/admin' || pathname.startsWith('/admin/')) {
        return `/login?next=${encodeURIComponent(adminDestination(pathname))}`;
    }
    if (pathname === '/student' || pathname.startsWith('/student/')) {
        return `/login?next=${encodeURIComponent(pathname)}`;
    }
    return pathname === '/dashboard' || pathname.startsWith('/dashboard/') ? `/login?next=${encodeURIComponent(pathname)}` : '/login';
}

export function dashboardDestination(value: string | null): string {
    return ['/dashboard', '/dashboard/leads', '/dashboard/analytics', '/dashboard/budget', '/dashboard/datasets', '/dashboard/account', ...workspacePages.map(item => `/dashboard/${item.slug}`)].includes(value || '') ? value! : '/dashboard';
}
