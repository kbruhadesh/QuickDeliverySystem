// auth.js
window.HDL_CUSTOMER = window.HDL_CUSTOMER || {};

window.HDL_CUSTOMER.Auth = {
    login: async function (email, password, btn) {
        window.HDL_CUSTOMER.UI.showSpinner(btn);
        const errorEl = document.getElementById('login-error');
        if (errorEl) errorEl.style.display = 'none';

        try {
            const res = await fetch(`http://localhost:8000/auth/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`, {
                method: 'POST'
            });

            const data = await res.json();
            window.HDL_CUSTOMER.UI.hideSpinner(btn);

            if (res.ok && data.access_token) {
                // Fetch user details
                const meRes = await fetch(`http://localhost:8000/auth/me?token=${data.access_token}`);
                const user = await meRes.json();

                localStorage.setItem('hdl_customer_token', data.access_token);
                localStorage.setItem('hdl_customer', JSON.stringify({ id: user.id, name: user.full_name, email: user.email }));
                window.location.href = 'my-orders.html';
            } else {
                if (errorEl) {
                    errorEl.style.display = 'block';
                    errorEl.textContent = data.detail || 'Incorrect email or password.';
                }
                btn.closest('.card').classList.add('shake');
                setTimeout(() => btn.closest('.card').classList.remove('shake'), 400);
            }
        } catch (err) {
            window.HDL_CUSTOMER.UI.hideSpinner(btn);
            if (errorEl) {
                errorEl.style.display = 'block';
                errorEl.textContent = 'Server connection failed.';
            }
        }
    },

    register: async function (name, email, phone, password, btn) {
        window.HDL_CUSTOMER.UI.showSpinner(btn);

        try {
            const res = await fetch('http://localhost:8000/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ full_name: name, email, phone, password })
            });

            const data = await res.json();
            
            if (res.ok) {
                // Auto-login after register
                await this.login(email, password, btn);
                localStorage.setItem('hdl_show_welcome', 'true');
            } else {
                window.HDL_CUSTOMER.UI.hideSpinner(btn);
                alert(data.detail || "Registration failed");
            }
        } catch (err) {
            window.HDL_CUSTOMER.UI.hideSpinner(btn);
            alert("Server connection failed.");
        }
    },

    logout: function () {
        localStorage.removeItem('hdl_customer');
        localStorage.removeItem('hdl_customer_token');
        window.location.href = '../index.html';
    }
};
