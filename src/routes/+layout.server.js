/**
 * Disponibiliza o usuário autenticado para todas as páginas.
 *
 * @param {object} input - Contexto do layout.
 * @param {App.Locals} input.locals - Dados preenchidos pelo hook server-side.
 * @returns {{currentUser: object|null}} Usuário atual ou null.
 * @type {import('./$types').LayoutServerLoad}
 */
export function load({ locals }) {
    return {
        currentUser: locals.currentUser || null
    };
}
