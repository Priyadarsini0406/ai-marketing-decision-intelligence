import { workspacePages } from './workspace-pages';
export const adminPages = [
    { href: '/admin/dashboard', label: 'Dashboard' },
    { href: '/admin/students', label: 'Students' },
    { href: '/admin/managers', label: 'Managers' },
    { href: '/admin/users', label: 'User Accounts' },
    { href: '/admin/courses', label: 'Courses / Programs' },
    { href: '/admin/institutions', label: 'Institutions' },
    { href: '/admin/datasets', label: 'Datasets' },
    { href: '/admin/data-import', label: 'Data Import' },
    { href: '/admin/activity', label: 'System Activity' },
    { href: '/admin/audit-logs', label: 'Audit Logs' },
    { href: '/admin/notifications', label: 'Notifications' },
    { href: '/admin/profile', label: 'Profile' },
    { href: '/admin/settings', label: 'Settings' }
];

export function adminDestination(value: string | null): string {
<<<<<<< HEAD
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
=======
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
>>>>>>> 2b474db99b96dfd413a3dcbba57429394ce9d29d
}
