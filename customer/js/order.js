// order.js
window.HDL_CUSTOMER = window.HDL_CUSTOMER || {};

window.HDL_CUSTOMER.OrderFlow = {
    pickupLatlng: null,
    deliveryLatlng: null,
    pickupMap: null,
    deliveryMap: null,
    previewMap: null,
    pickupMarker: null,
    deliveryMarker: null,
    previewMarkers: [],
    previewRoute: null,

    initPlaceOrder: function () {
        // Basic setup for maps. Default to Hyderabad coordinates
        const HYD_COORDS = [17.3850, 78.4867];
        this.pickupMap = L.map('pickup-map', { zoomControl: false }).setView(HYD_COORDS, 12);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(this.pickupMap);

        this.deliveryMap = L.map('delivery-map', { zoomControl: false }).setView(HYD_COORDS, 12);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(this.deliveryMap);

        this.previewMap = L.map('preview-map', { zoomControl: false }).setView(HYD_COORDS, 12);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(this.previewMap);

        // Interactions
        this.pickupMap.on('click', (e) => {
            this.pickupLatlng = e.latlng;
            if (this.pickupMarker) this.pickupMap.removeLayer(this.pickupMarker);
            this.pickupMarker = L.circleMarker(e.latlng, { radius: 6, fillColor: '#10B981', color: '#fff', weight: 2, fillOpacity: 1 }).addTo(this.pickupMap);
            document.getElementById('pickup-coords').value = `${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)}`;
            this.updatePreview();
            this.checkStepStatus();
        });

        this.deliveryMap.on('click', (e) => {
            this.deliveryLatlng = e.latlng;
            if (this.deliveryMarker) this.deliveryMap.removeLayer(this.deliveryMarker);
            this.deliveryMarker = L.circleMarker(e.latlng, { radius: 6, fillColor: '#EF4444', color: '#fff', weight: 2, fillOpacity: 1 }).addTo(this.deliveryMap);
            document.getElementById('delivery-coords').value = `${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)}`;
            this.updatePreview();
            this.checkStepStatus();
        });

        // ETA btn
        document.getElementById('calc-eta-btn').addEventListener('click', (e) => {
            window.HDL_CUSTOMER.UI.showSpinner(e.target);
            setTimeout(() => {
                window.HDL_CUSTOMER.UI.hideSpinner(e.target);
                document.getElementById('eta-card').style.display = 'block';
                document.getElementById('confirm-order-btn').disabled = false;
            }, 1200);
        });

        // Confirm Btn
        document.getElementById('confirm-order-btn').addEventListener('click', async (e) => {
            window.HDL_CUSTOMER.UI.showSpinner(e.target);
            
            const token = localStorage.getItem('hdl_customer_token');
            if (!token) {
                alert("Please login first.");
                window.location.href = 'login.html';
                return;
            }
            
            try {
                const res = await fetch(`http://localhost:8000/orders/?token=${token}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ items: [] }) // Package delivery has no products
                });
                const data = await res.json();
                
                if (res.ok) {
                    localStorage.setItem('hdl_latest_order', JSON.stringify({
                        id: data.order_id,
                        pickup: this.pickupLatlng,
                        delivery: this.deliveryLatlng,
                        eta: 22,
                        drone: 'D-07',
                        type: 'PACKAGE'
                    }));
                    window.location.href = 'order-confirmed.html';
                } else {
                    window.HDL_CUSTOMER.UI.hideSpinner(e.target);
                    alert("Order creation failed: " + (data.detail || ""));
                }
            } catch (err) {
                window.HDL_CUSTOMER.UI.hideSpinner(e.target);
                alert("API connection failed.");
            }
        });

        // Welcome toast check
        if (localStorage.getItem('hdl_show_welcome') === 'true') {
            window.HDL_CUSTOMER.UI.showToast('Welcome! Place your first order.', 'success');
            localStorage.removeItem('hdl_show_welcome');
        }
    },

    searchLocation: async function (type) {
        const query = document.getElementById(type + '-search').value;
        if (!query) return;

        const btn = document.querySelector(`#${type}-search`).nextElementSibling;
        window.HDL_CUSTOMER.UI.showSpinner(btn);

        try {
            const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query + ', Hyderabad')}`);
            const data = await res.json();
            if (data && data.length > 0) {
                const latlng = L.latLng(parseFloat(data[0].lat), parseFloat(data[0].lon));

                const map = type === 'pickup' ? this.pickupMap : this.deliveryMap;
                map.flyTo(latlng, 15);

                // Emulate click to place marker automatically
                map.fireEvent('click', { latlng: latlng });
            } else {
                window.HDL_CUSTOMER.UI.showToast("Location not found", "error");
            }
        } catch (e) {
            window.HDL_CUSTOMER.UI.showToast("Search failed", "error");
        } finally {
            window.HDL_CUSTOMER.UI.hideSpinner(btn);
        }
    },

    updatePreview: function () {
        this.previewMarkers.forEach(m => this.previewMap.removeLayer(m));
        if (this.previewRoute) this.previewMap.removeLayer(this.previewRoute);
        this.previewMarkers = [];

        let bounds = [];
        if (this.pickupLatlng) {
            const pm = L.circleMarker(this.pickupLatlng, { radius: 6, fillColor: '#10B981', color: '#fff', weight: 2, fillOpacity: 1 }).addTo(this.previewMap);
            this.previewMarkers.push(pm);
            bounds.push(this.pickupLatlng);
        }
        if (this.deliveryLatlng) {
            const dm = L.circleMarker(this.deliveryLatlng, { radius: 6, fillColor: '#EF4444', color: '#fff', weight: 2, fillOpacity: 1 }).addTo(this.previewMap);
            this.previewMarkers.push(dm);
            bounds.push(this.deliveryLatlng);
        }

        if (this.pickupLatlng && this.deliveryLatlng) {
            this.previewRoute = L.polyline([this.pickupLatlng, this.deliveryLatlng], { color: 'var(--accent)', weight: 3, dashArray: '8, 8' }).addTo(this.previewMap);
        }

        if (bounds.length > 0) {
            this.previewMap.fitBounds(L.latLngBounds(bounds), { padding: [40, 40], maxZoom: 14 });
        }
    },

    checkStepStatus: function () {
        const s1 = document.getElementById('step-1');
        const s2 = document.getElementById('step-2');
        const s3 = document.getElementById('step-3');

        if (this.pickupLatlng) s1.classList.add('completed');
        if (this.pickupLatlng && !this.deliveryLatlng) s2.classList.add('active');

        if (this.deliveryLatlng) s2.classList.add('completed');
        if (this.pickupLatlng && this.deliveryLatlng) {
            s3.classList.add('active');
            document.getElementById('calc-eta-btn').disabled = false;
        }
    }
};
