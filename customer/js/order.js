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
    finalPath: null,
    finalEta: 0,
    finalBatteryDrop: 0,

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
        document.getElementById('calc-eta-btn').addEventListener('click', async (e) => {
            const btn = e.target;
            window.HDL_CUSTOMER.UI.showSpinner(btn);
            
            try {
                const payload = {
                    drones: [{ id: "D-CUST", max_payload: 5.0, battery_capacity: 100, latitude: 17.40, longitude: 78.45 }],
                    orders: [{
                        id: "ORD-CUST", package_weight: 1.0, 
                        pickup_latitude: this.pickupLatlng.lat, pickup_longitude: this.pickupLatlng.lng,
                        delivery_latitude: this.deliveryLatlng.lat, delivery_longitude: this.deliveryLatlng.lng
                    }],
                    weather: { wind_speed: 10, temperature: 25, humidity: 60, rain: 0 }
                };

                const res = await fetch("http://localhost:8000/api/optimize_routes", {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                this.pollTaskForETA(data.task_id, btn);
            } catch (err) {
                console.error(err);
                window.HDL_CUSTOMER.UI.hideSpinner(btn);
                window.HDL_CUSTOMER.UI.showToast("Failed to connect to backend", "error");
            }
        });

        // Confirm Btn
        document.getElementById('confirm-order-btn').addEventListener('click', (e) => {
            window.HDL_CUSTOMER.UI.showSpinner(e.target);
            setTimeout(() => {
                // Mock save
                localStorage.setItem('hdl_latest_order', JSON.stringify({
                    id: 'HDL-' + Math.floor(1000 + Math.random() * 9000),
                    pickup: this.pickupLatlng,
                    delivery: this.deliveryLatlng,
                    path: this.finalPath,
                    eta: this.finalEta,
                    battery_drop: this.finalBatteryDrop,
                    drone: 'D-CUST'
                }));
                window.location.href = 'order-confirmed.html';
            }, 1000);
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
    },

    pollTaskForETA: async function(taskId, btn) {
        try {
            const res = await fetch(`http://localhost:8000/api/tasks/${taskId}`);
            const data = await res.json();
            
            if (data.status === "pending") {
                setTimeout(() => this.pollTaskForETA(taskId, btn), 1000);
            } else if (data.status === "success") {
                const assignment = data.assignments[0];
                const distanceKm = assignment.total_waypoints * 0.15; // rough distance approximation
                this.finalPath = assignment.path;
                this.predictBattery(distanceKm, btn);
            } else {
                window.HDL_CUSTOMER.UI.hideSpinner(btn);
                window.HDL_CUSTOMER.UI.showToast("Optimization failed", "error");
            }
        } catch (e) {
            console.error(e);
            window.HDL_CUSTOMER.UI.hideSpinner(btn);
        }
    },

    predictBattery: async function(distanceKm, btn) {
        try {
            const req = {
                distance_km: distanceKm,
                payload_weight_kg: 1.0,
                weather: { wind_speed: 10, temperature: 25, humidity: 60, rain: 0 }
            };
            
            const res = await fetch("http://localhost:8000/api/predict_battery", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify(req)
            });
            const data = await res.json();
            
            window.HDL_CUSTOMER.UI.hideSpinner(btn);
            
            // Update UI
            document.getElementById('eta-card').style.display = 'block';
            document.getElementById('confirm-order-btn').disabled = false;
            
            const etaMinutes = Math.max(5, Math.floor(distanceKm * 2.5)); // 2.5 mins per km roughly
            const batteryDrop = data.predicted_battery_drop_percent.toFixed(1);
            document.getElementById('eta-text').textContent = `Estimated delivery: ${etaMinutes} minutes`;
            document.getElementById('eta-distance').textContent = `📍 Distance: ${distanceKm.toFixed(2)} km`;
            document.getElementById('eta-battery').textContent = `⚡ Battery Drop: ${batteryDrop}% (ML Predicted)`;
            
            this.finalEta = etaMinutes;
            this.finalBatteryDrop = batteryDrop;
            
        } catch (e) {
            console.error(e);
            window.HDL_CUSTOMER.UI.hideSpinner(btn);
            window.HDL_CUSTOMER.UI.showToast("ML Prediction failed", "error");
        }
    }
};
