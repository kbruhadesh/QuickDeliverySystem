// router.js — Admin portal auth guard using hdl_admin_token

window.HDL = window.HDL || {};
window.HDL.Router = {

    init: function () {
        this.checkAuth();
        this.highlightNav();
        this.updateUserDetails();
    },

    checkAuth: function () {
        const currentPath = window.location.pathname;
        const isLoginPage = currentPath.endsWith('login.html');
        const token = localStorage.getItem('hdl_admin_token');

        if (!token && !isLoginPage) {
            window.location.href = 'login.html';
            return;
        }

        if (token && isLoginPage) {
            window.location.href = 'dashboard.html';
            return;
        }
    },

    highlightNav: function () {
        const currentPath = window.location.pathname;
        const pageName = currentPath.split('/').pop() || 'dashboard.html';

        document.querySelectorAll('.nav-item').forEach(link => {
            link.classList.remove('active');
            const href = link.getAttribute('href');
            if (href && href === pageName) {
                link.classList.add('active');
            }
        });
    },

    updateUserDetails: function () {
        const data = localStorage.getItem('hdl_admin_user');
        if (data) {
            const user = JSON.parse(data);
            document.querySelectorAll('.user-name').forEach(el => {
                el.textContent = user.full_name || user.email;
            });
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => window.HDL.Router.init(), 0);
});
