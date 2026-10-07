/**
 * Shared chrome for the signed-in shells.
 *
 * Student, manager and admin all render the same header, so the role
 * differences are data: one letter for the avatar, a label, and the
 * destinations the profile menu points at. Keeping them here means a
 * change to the header only has to be made once.
 */

export type ShellRole = 'student' | 'manager' | 'admin';

export type HeaderNotice = {
	title: string;
	detail: string;
	when: string;
	unread?: boolean;
	href?: string;
	icon?: string;
};

export type ShellLinks = {
	notifications: string;
	profile: string;
	settings: string;
};

const LINKS: Record<ShellRole, ShellLinks> = {
	student: {
		notifications: '/student/notifications',
		profile: '/student/profile',
		settings: '/student/settings'
	},
	manager: {
		notifications: '/notifications',
		profile: '/profile',
		settings: '/settings'
	},
	admin: {
		notifications: '/admin/notifications',
		profile: '/admin/profile',
		settings: '/admin/settings'
	}
};

const NOTICES: Record<ShellRole, HeaderNotice[]> = {
	student: [
		{
			title: 'Application updated',
			detail: 'Your application status has been updated.',
			when: 'Today',
			unread: true,
			icon: 'application',
			href: '/student/application'
		},
		{
			title: 'Counselling scheduled',
			detail: 'Your counselling session has been scheduled.',
			when: 'Yesterday',
			unread: true,
			icon: 'enquiry-status',
			href: '/student/enquiries/status'
		},
		{
			title: 'Profile reminder',
			detail: 'Keep your profile details current for smoother communication.',
			when: '10 Sep',
			icon: 'profile',
			href: '/student/profile'
		}
	],
	manager: [
		{
			title: 'High-intent lead',
			detail: 'A new enquiry scored above 90% admission probability.',
			when: 'Today',
			unread: true,
			icon: 'enquiries',
			href: '/student-leads'
		},
		{
			title: 'Budget recommendation ready',
			detail: 'AI has rebalanced spend across your top channels.',
			when: 'Today',
			unread: true,
			icon: 'briefcase',
			href: '/budget-optimization'
		},
		{
			title: 'Model retrained',
			detail: 'XGBoost reached 91% admission prediction accuracy.',
			when: 'Yesterday',
			icon: 'chart',
			href: '/admission-prediction'
		}
	],
	admin: [
		{
			title: 'New account created',
			detail: 'A student account is pending review.',
			when: 'Today',
			unread: true,
			icon: 'users',
			href: '/admin/students'
		},
		{
			title: 'Dataset import finished',
			detail: 'Campaign rows were added to the live dataset.',
			when: 'Today',
			unread: true,
			icon: 'clipboard',
			href: '/admin/datasets'
		},
		{
			title: 'Course catalogue updated',
			detail: 'Two programmes were published.',
			when: 'Yesterday',
			icon: 'book',
			href: '/admin/courses'
		}
	]
};

export function shellLinks(role: ShellRole): ShellLinks {
	return LINKS[role];
}

export function shellNotices(role: ShellRole): HeaderNotice[] {
	return NOTICES[role];
}

/** The single letter shown in the header avatar. */
export function roleInitial(role: ShellRole): 'S' | 'M' | 'A' {
	return role === 'student' ? 'S' : role === 'manager' ? 'M' : 'A';
}

/** Human-readable role name shown above the name in the profile menu. */
export function roleLabel(role: ShellRole): string {
	return role === 'student' ? 'Student' : role === 'manager' ? 'Admission Manager' : 'Administrator';
}
