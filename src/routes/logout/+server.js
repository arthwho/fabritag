import { redirect } from '@sveltejs/kit';
import { clearAuthCookie, logoutBackendSession } from '$lib/server/auth';

/** @type {import('./$types').RequestHandler} */
export async function GET(event) {
    await logoutBackendSession(event);
    clearAuthCookie(event.cookies);
    throw redirect(303, '/login');
}

/** @type {import('./$types').RequestHandler} */
export async function POST(event) {
    await logoutBackendSession(event);
    clearAuthCookie(event.cookies);
    throw redirect(303, '/login');
}
