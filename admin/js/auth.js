// auth.js — Admin portal auth helpers

window.HDL = window.HDL || {};
window.HDL.Auth = {

    init: function () {
        const logoutBtns = document.querySelectorAll('.btn-logout');
        logoutBtns.forEach(btn => {
            btn.addEventListener('click', this.logout.bind(this));
        });
    },

    logout: function () {
        localStorage.removeItem('hdl_admin_token');
        localStorage.removeItem('hdl_admin_user');
        window.location.href = 'login.html';
    },

    getToken: function () {
        return localStorage.getItem('hdl_admin_token');
    },

    getUser: function () {
        const data = localStorage.getItem('hdl_admin_user');
        return data ? JSON.parse(data) : null;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    window.HDL.Auth.init();
});
