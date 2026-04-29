import { redirect } from '@sveltejs/kit';
import { clearAuthCookie, fetchCurrentUser } from '$lib/server/auth';

function isPublicRoute(pathname) {
    return pathname.startsWith('/login') || pathname.startsWith('/registro');
}

/** @type {import('@sveltejs/kit').Handle} */
export async function handle({ event, resolve }) {
    const { pathname } = event.url;
    const currentUser = await fetchCurrentUser(event);

    if (!currentUser) {
        clearAuthCookie(event.cookies);
    }

    event.locals.currentUser = currentUser;

    if (!currentUser && !isPublicRoute(pathname)) {
        throw redirect(303, '/login');
    }

    if (currentUser && (pathname === '/login' || pathname === '/registro')) {
        throw redirect(303, '/dashboard');
    }

    return resolve(event);
}
