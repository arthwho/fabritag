/** @type {import('./$types').LayoutServerLoad} */
export function load({ locals }) {
    return {
        currentUser: locals.currentUser || null
    };
}
