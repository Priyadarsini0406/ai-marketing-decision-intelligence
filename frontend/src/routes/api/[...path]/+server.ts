import { env } from '$env/dynamic/private';
import type { RequestHandler } from './$types';

const proxy: RequestHandler = async ({ request, url }) => {
    const base = (env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
    const headers = new Headers();
    for (const name of ['authorization', 'content-type']) {
        const value = request.headers.get(name);
        if (value) headers.set(name, value);
    }
    try {
        const response = await fetch(base + url.pathname.slice(4) + url.search, {
            method: request.method, headers,
            body: ['GET', 'HEAD'].includes(request.method) ? undefined : await request.arrayBuffer(),
            redirect: 'manual'
        });
        return new Response(response.body, { status: response.status, headers: { 'content-type': response.headers.get('content-type') || 'application/json', 'cache-control': 'no-store' } });
    } catch {
        return Response.json({ detail: 'Backend unavailable. Start the API server and try again.' }, { status: 502 });
    }
};
export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const DELETE = proxy;
