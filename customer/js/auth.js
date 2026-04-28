// auth.js
window.HDL_CUSTOMER = window.HDL_CUSTOMER || {};

window.HDL_CUSTOMER.Auth = {
    login: function (email, password, btn) {
        window.HDL_CUSTOMER.UI.showSpinner(btn);
        // Hide old errors
        const errorEl = document.getElementById('login-error');
        if (errorEl) errorEl.style.display = 'none';

        setTimeout(() => {
            window.HDL_CUSTOMER.UI.hideSpinner(btn);

            // Check hardcoded mocks + local storage customers
            const lsCusts = JSON.parse(localStorage.getItem('hdl_customers_db') || '[]');
            const allUsers = [...window.HDL_CUSTOMER.MOCK_CUSTOMERS, ...lsCusts];

            const match = allUsers.find(u => u.email === email && u.password === password);

            if (match) {
                localStorage.setItem('hdl_customer', JSON.stringify({ id: match.id, name: match.name, email: match.email }));
                window.location.href = 'my-orders.html';
            } else {
                if (errorEl) {
                    errorEl.style.display = 'block';
                    errorEl.textContent = 'Incorrect email or password.';
                }
                btn.closest('.card').classList.add('shake');
                setTimeout(() => btn.closest('.card').classList.remove('shake'), 400);
            }
        }, 800);
    },

    register: function (name, email, phone, password, btn) {
        window.HDL_CUSTOMER.UI.showSpinner(btn);

        setTimeout(() => {
            window.HDL_CUSTOMER.UI.hideSpinner(btn);

            const newUser = {
                id: 'C' + Math.floor(Math.random() * 10000),
                name, email, phone, password
            };

            const lsCusts = JSON.parse(localStorage.getItem('hdl_customers_db') || '[]');
            lsCusts.push(newUser);
            localStorage.setItem('hdl_customers_db', JSON.stringify(lsCusts));

            localStorage.setItem('hdl_customer', JSON.stringify({ id: newUser.id, name: newUser.name, email: newUser.email }));

            // Store a flag so place-order shows the toast
            localStorage.setItem('hdl_show_welcome', 'true');
            window.location.href = 'place-order.html';
        }, 800);
    },

    logout: function () {
        localStorage.removeItem('hdl_customer');
        window.location.href = '../index.html';
    }
};
