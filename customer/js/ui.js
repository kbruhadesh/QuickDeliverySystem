// ui.js
window.HDL_CUSTOMER = window.HDL_CUSTOMER || {};

window.HDL_CUSTOMER.UI = {
    showToast: function (message, type = 'info') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast`; // base style
        if (type === 'success') toast.style.background = 'var(--success)';
        if (type === 'error') toast.style.background = 'var(--danger)';
        if (type === 'warning') toast.style.background = 'var(--warning)';

        let icon = 'ℹ️';
        if (type === 'success') icon = '✅';
        if (type === 'error') icon = '❌';

        toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400);
        }, 3000);
    },

    showSpinner: function (btn) {
        if (!btn) return;
        btn.dataset.originalText = btn.innerHTML;
        btn.innerHTML = `<span class="spinner"></span>`;
        btn.disabled = true;
    },

    hideSpinner: function (btn) {
        if (!btn) return;
        btn.innerHTML = btn.dataset.originalText || 'Submit';
        btn.disabled = false;
    },

    requireLogin: function () {
        const user = localStorage.getItem('hdl_customer');
        if (!user) {
            window.location.href = 'login.html';
            return false;
        }
        return JSON.parse(user);
    },

    formatDateTime: function (isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const m = months[date.getMonth()];
        const d = date.getDate();
        let hr = date.getHours();
        const min = date.getMinutes().toString().padStart(2, '0');
        const ampm = hr >= 12 ? 'PM' : 'AM';
        hr = hr % 12;
        hr = hr ? hr : 12;
        return `${m} ${d}, ${hr}:${min} ${ampm}`;
    },

    getStatusBadge: function (status) {
        const s = status.toUpperCase();
        if (s === 'DELIVERED') return `<span class="badge badge-success">Delivered</span>`;
        if (s === 'IN_TRANSIT') return `<span class="badge badge-warning">In Transit</span>`;
        if (s === 'CONFIRMED' || s === 'ASSIGNED') return `<span class="badge badge-info">${s}</span>`;
        if (s === 'CANCELLED') return `<span class="badge badge-danger">Cancelled</span>`;
        return `<span class="badge badge-neutral">${s}</span>`;
    },

    animateCountdown: function (seconds, elementId, onComplete) {
        const el = document.getElementById(elementId);
        if (!el) return;

        let remaining = seconds;
        const interval = setInterval(() => {
            const m = Math.floor(remaining / 60);
            const s = remaining % 60;
            el.textContent = `${m}:${s.toString().padStart(2, '0')}`;

            remaining--;
            if (remaining < 0) {
                clearInterval(interval);
                if (onComplete) onComplete();
            }
        }, 1000);
        return interval;
    },

    initMobileNav: function () {
        const hamburger = document.getElementById('hamburger');
        const overlay = document.getElementById('mobile-nav-overlay');
        if (hamburger && overlay) {
            hamburger.addEventListener('click', () => {
                overlay.classList.toggle('open');
            });
        }

        // Auth navbar toggle
        const user = localStorage.getItem('hdl_customer');
        if (user) {
            document.querySelectorAll('.guest-only').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.auth-only').forEach(el => el.style.display = 'flex');

            const parsed = JSON.parse(user);
            document.querySelectorAll('.user-greeting').forEach(el => el.textContent = parsed.name.split(' ')[0]);
        } else {
            document.querySelectorAll('.auth-only').forEach(el => el.style.display = 'none');
        }
    },

    haversineDistance: function(lat1, lon1, lat2, lon2) {
        const R = 6371000; // Earth radius in meters
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
          Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
          Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }
};

// Global init block
document.addEventListener('DOMContentLoaded', () => {
    window.HDL_CUSTOMER.UI.initMobileNav();
});
