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
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: '&copy; Esri' }).addTo(this.pickupMap);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; OpenStreetMap', opacity: 0.4 }).addTo(this.pickupMap);

        this.deliveryMap = L.map('delivery-map', { zoomControl: false }).setView(HYD_COORDS, 12);
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: '&copy; Esri' }).addTo(this.deliveryMap);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; OpenStreetMap', opacity: 0.4 }).addTo(this.deliveryMap);

        this.previewMap = L.map('preview-map', { zoomControl: false }).setView(HYD_COORDS, 12);
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: '&copy; Esri' }).addTo(this.previewMap);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; OpenStreetMap', opacity: 0.4 }).addTo(this.previewMap);

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
        document.getElementById('calc-eta-btn').addEventListener('click', async (e) => {
            window.HDL_CUSTOMER.UI.showSpinner(e.target);

            try {
                // Parse weight
                const weightSelect = document.getElementById('package-weight');
                let weightKg = 1.0;
                if (weightSelect && weightSelect.value) {
                    if (weightSelect.value.includes('1-2')) weightKg = 1.5;
                    else if (weightSelect.value.includes('2-3')) weightKg = 2.5;
                    else if (weightSelect.value.includes('3-5')) weightKg = 4.0;
                }

                const res = await fetch(`http://localhost:8000/orders/calculate_eta`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        pickup_latitude: this.pickupLatlng.lat,
                        pickup_longitude: this.pickupLatlng.lng,
                        delivery_latitude: this.deliveryLatlng.lat,
                        delivery_longitude: this.deliveryLatlng.lng,
                        weight_kg: weightKg
                    })
                });

                const data = await res.json();

                if (res.ok) {
                    // Show ETA Card
                    const etaCard = document.getElementById('eta-card');
                    if (etaCard) {
                        etaCard.innerHTML = `
                            <div class="eta-card">
                                <h3>Estimated delivery: ${data.eta_min} minutes</h3>
                                <p>Distance: ${data.distance_km} km · Est. Battery Drop: ${data.battery_drop}%</p>
                            </div>
                        `;
                        etaCard.style.display = 'block';
                    }

                    document.getElementById('confirm-order-btn').disabled = false;

                    // Save calculated path temporarily
                    this.calculatedPath = data.path;
                    this.calculatedEta = data.eta_min;

                    // Draw the ACTUAL RRT* path on the preview map
                    if (this.previewRoute) this.previewMap.removeLayer(this.previewRoute);
                    this.previewRoute = L.polyline(this.calculatedPath, { color: 'var(--accent)', weight: 4 }).addTo(this.previewMap);
                    this.previewMap.fitBounds(this.previewRoute.getBounds(), { padding: [40, 40] });
                } else {
                    alert("Failed to calculate ETA: " + (data.detail || ""));
                }
            } catch (err) {
                alert("API connection failed.");
            } finally {
                window.HDL_CUSTOMER.UI.hideSpinner(e.target);
            }
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
                    body: JSON.stringify({
                        items: [],
                        pickup_latitude: this.pickupLatlng.lat,
                        pickup_longitude: this.pickupLatlng.lng,
                        delivery_latitude: this.deliveryLatlng.lat,
                        delivery_longitude: this.deliveryLatlng.lng
                    })
                });
                const data = await res.json();

                if (res.ok) {
                    localStorage.setItem('hdl_latest_order', JSON.stringify({
                        id: data.order_id,
                        pickup: this.pickupLatlng,
                        delivery: this.deliveryLatlng,
                        eta: this.calculatedEta || 22,
                        drone: 'D-07',
                        type: 'PACKAGE',
                        route: this.calculatedPath // Store the exact RRT* path!
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
