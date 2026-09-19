import { error } from '@sveltejs/kit';
import { workspacePages } from '$lib/workspace-pages';
export function load({ params }: { params: { feature: string } }) {
    const feature = workspacePages.find(item => item.slug === params.feature);
    if (!feature) error(404, 'Page not found');
    return { feature };
}
