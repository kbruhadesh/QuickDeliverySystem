// router.js
// Handles route protection, active link highlighting, and role-based UI toggles

window.HDL = window.HDL || {};
window.HDL.Router = {

    init: function () {
        this.checkAuth();
        this.highlightNav();
        this.applyRoleBasedUI();
        this.updateUserDetails();
    },

    checkAuth: function () {
        const currentPath = window.location.pathname;
        const isLoginPage = currentPath.endsWith('index.html') || currentPath === '/';
        const user = window.HDL.Auth ? window.HDL.Auth.getUser() : null;

        if (!user && !isLoginPage) {
            window.location.href = '../index.html';
            return;
        }

        if (user && isLoginPage) {
            window.location.href = 'dashboard.html';
            return;
        }

        // Check specific role-restricted pages
        if (user && user.role === 'researcher') {
            const restrictedPages = ['settings.html', 'simulation.html', 'benchmarks.html'];
            const pageName = currentPath.split('/').pop() || '';
            if (restrictedPages.includes(pageName)) {
                window.location.href = 'dashboard.html';
            }
        }
    },

    highlightNav: function () {
        const currentPath = window.location.pathname;
        const pageName = currentPath.split('/').pop() || 'dashboard.html'; // default

        document.querySelectorAll('.nav-item').forEach(link => {
            link.classList.remove('active');
            const href = link.getAttribute('href');
            if (href && href === pageName) {
                link.classList.add('active');
            }
        });
    },

    applyRoleBasedUI: function () {
        const user = window.HDL.Auth ? window.HDL.Auth.getUser() : null;
        if (!user) return;

        const role = user.role;

        if (role === 'researcher') {
            document.querySelectorAll('.admin-only, .dev-only').forEach(el => {
                el.style.display = 'none';
            });
        } else if (role === 'developer') {
            document.querySelectorAll('.admin-only').forEach(el => {
                el.style.display = 'none';
            });
            document.querySelectorAll('.dev-only').forEach(el => {
                el.style.display = '';
            });
        } else if (role === 'admin') {
            document.querySelectorAll('.admin-only, .dev-only').forEach(el => {
                el.style.display = ''; // default display
            });
        }
    },

    updateUserDetails: function () {
        const user = window.HDL.Auth ? window.HDL.Auth.getUser() : null;
        if (user) {
            const userEls = document.querySelectorAll('.user-name');
            userEls.forEach(el => {
                el.textContent = user.name;
            });
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Give priority to auth init if needed, though they don't strongly conflict
    setTimeout(() => window.HDL.Router.init(), 0);
});
