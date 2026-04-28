// auth.js
// Handles login, logout and local storage token management

window.HDL = window.HDL || {};
window.HDL.Auth = {

    init: function () {
        // If we're on login page with a form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', this.handleLogin.bind(this));
        }

        // Hook up logout buttons (in layout)
        const logoutBtns = document.querySelectorAll('.btn-logout');
        logoutBtns.forEach(btn => {
            btn.addEventListener('click', this.logout.bind(this));
        });
    },

    handleLogin: function (e) {
        e.preventDefault();

        const emailInput = document.getElementById('email').value;
        const passwordInput = document.getElementById('password').value;
        const errorMsg = document.getElementById('login-error');
        const submitBtn = document.getElementById('login-btn');
        const spinnerId = 'login-spinner';

        errorMsg.style.display = 'none';

        // Add spinner to button
        const ogText = submitBtn.innerHTML;
        submitBtn.innerHTML = `<span class="spinner" id="${spinnerId}"></span> Processing...`;
        submitBtn.disabled = true;

        setTimeout(() => {
            submitBtn.innerHTML = ogText;
            submitBtn.disabled = false;

            let user = null;
            if (emailInput === "admin@hdl.com" && passwordInput === "admin123") {
                user = { name: "Admin User", role: "admin", token: "mock-token-admin" };
            } else if (emailInput === "user@hdl.com" && passwordInput === "user123") {
                user = { name: "System Researcher", role: "researcher", token: "mock-token-researcher" };
            }

            if (user) {
                localStorage.setItem('hdl_user', JSON.stringify(user));
                window.location.href = 'dashboard.html';
            } else {
                errorMsg.textContent = "Invalid email or password";
                errorMsg.style.display = 'block';
            }
        }, 800);
    },

    logout: function () {
        localStorage.removeItem('hdl_user');
        window.location.href = '../index.html';
    },

    getUser: function () {
        const data = localStorage.getItem('hdl_user');
        return data ? JSON.parse(data) : null;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    window.HDL.Auth.init();
});
