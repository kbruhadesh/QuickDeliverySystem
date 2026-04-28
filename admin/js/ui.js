// ui.js
// Shared UI functions for Modals, Toasts, Skeletons, Empty States, formatting

window.HDL = window.HDL || {};
window.HDL.UI = {

    // Toast notifications
    showToast: function (message, type = 'info') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        let icon = 'ℹ️';
        if (type === 'success') icon = '✅';
        if (type === 'error') icon = '❌';
        if (type === 'warning') icon = '⚠️';

        toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
        container.appendChild(toast);

        // Trigger animation
        setTimeout(() => { toast.classList.add('show'); }, 10);

        // Auto dismiss
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => { toast.remove(); }, 300);
        }, 3000);
    },

    // Modals
    openModal: function (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
        }
    },

    closeModal: function (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    },

    // Confirm Dialog Modal wrapper
    showConfirm: function (message, onConfirm) {
        // Check if confirm dialog exists
        let confirmModal = document.getElementById('confirm-modal');
        if (!confirmModal) {
            // Create dynamically
            const html = `
        <div class="modal-overlay" id="confirm-modal">
          <div class="modal-content">
            <div class="modal-header">
              <h2>Confirm Action</h2>
              <button class="btn-close" onclick="window.HDL.UI.closeModal('confirm-modal')">&times;</button>
            </div>
            <div class="modal-body">
              <p id="confirm-message"></p>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" onclick="window.HDL.UI.closeModal('confirm-modal')">Cancel</button>
              <button class="btn btn-primary" id="confirm-ok-btn">Confirm</button>
            </div>
          </div>
        </div>
      `;
            document.body.insertAdjacentHTML('beforeend', html);
            confirmModal = document.getElementById('confirm-modal');
        }

        document.getElementById('confirm-message').textContent = message;
        const okBtn = document.getElementById('confirm-ok-btn');

        // Clear old events
        const newBtn = okBtn.cloneNode(true);
        okBtn.parentNode.replaceChild(newBtn, okBtn);

        newBtn.addEventListener('click', () => {
            onConfirm();
            this.closeModal('confirm-modal');
        });

        this.openModal('confirm-modal');
    },

    // Skeleton loader for tables
    showSkeleton: function (tableId, cols, rows) {
        const tableBody = document.querySelector(`#${tableId} tbody`);
        if (!tableBody) return;

        let html = '';
        for (let i = 0; i < rows; i++) {
            html += '<tr>';
            for (let j = 0; j < cols; j++) {
                html += `<td><div style="height:20px; background:rgba(255,255,255,0.05); border-radius:4px; animation: pulse 1.5s infinite"></div></td>`;
            }
            html += '</tr>';
        }
        tableBody.innerHTML = html;

        if (!document.getElementById('skeleton-style')) {
            const style = document.createElement('style');
            style.id = 'skeleton-style';
            style.innerHTML = `@keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 0.3; } 100% { opacity: 0.6; } }`;
            document.head.appendChild(style);
        }
    },

    // Empty State Generator
    showEmptyState: function (containerId, icon, title, description, ctaLabel, ctaFn) {
        const container = document.getElementById(containerId);
        if (!container) return;

        let ctaHtml = '';
        if (ctaLabel) {
            window[`ctaFn_${containerId}`] = ctaFn;
            ctaHtml = `<button class="btn btn-primary" onclick="window.ctaFn_${containerId}()">
                   ${ctaLabel}
                 </button>`;
        }

        container.innerHTML = `
      <div class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M20 12H4M12 20V4"/></svg>
        <h3>${title}</h3>
        <p>${description}</p>
        ${ctaHtml}
      </div>
    `;

        // Replace SVG path playfully if needed, dummy path above
        const svgEl = container.querySelector('svg');
        if (icon) {
            svgEl.innerHTML = icon; // Assuming icon is inner contents of SVG <path> etc
        }
    },

    // Utility: get badge class for string
    setBadgeColor: function (status) {
        const s = (status || '').toLowerCase();
        if (['completed', 'available', 'compliant', 'online', 'connected', 'active'].includes(s)) return 'success';
        if (['in-transit', 'in-flight', 'running'].includes(s)) return 'info';
        if (['assigned', 'pending', 'paused', 'warning'].includes(s)) return 'warning';
        if (['failed', 'violation', 'offline', 'stopped'].includes(s)) return 'danger';
        return 'neutral';
    },

    // Format DateTime
    formatDateTime: function (isoString) {
        if (!isoString) return '';
        const date = new Date(isoString);
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const m = months[date.getMonth()];
        const d = date.getDate();
        const hr = date.getHours().toString().padStart(2, '0');
        const min = date.getMinutes().toString().padStart(2, '0');
        return `${m} ${d}, ${hr}:${min}`;
    }
};
