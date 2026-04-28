// tracking.js
window.HDL_CUSTOMER = window.HDL_CUSTOMER || {};

window.HDL_CUSTOMER.Tracking = {
    map: null,
    droneMarker: null,
    routeLine: null,
    pickup: null,
    delivery: null,
    routeCoords: [],
    currentIndex: 0,
    moveInterval: null,
    dataInterval: null,

    initTracker: function () {
        const latestStr = localStorage.getItem('hdl_latest_order');
        if (!latestStr) {
            document.getElementById('empty-track').style.display = 'block';
            document.getElementById('active-track').style.display = 'none';
            return;
        }

        document.getElementById('empty-track').style.display = 'none';
        document.getElementById('active-track').style.display = 'block';

        const order = JSON.parse(latestStr);

        // Fallback coords if none strictly defined from localStorage
        this.pickup = order.pickup || { lat: 17.3850, lng: 78.4867 };
        this.delivery = order.delivery || { lat: 17.4450, lng: 78.3867 };

        this.map = L.map('track-map', { zoomControl: false }).setView([this.pickup.lat, this.pickup.lng], 13);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(this.map);

        L.circleMarker(this.pickup, { radius: 6, fillColor: '#10B981', color: '#fff', weight: 2, fillOpacity: 1 }).addTo(this.map);
        L.circleMarker(this.delivery, { radius: 6, fillColor: '#EF4444', color: '#fff', weight: 2, fillOpacity: 1 }).addTo(this.map);

        document.getElementById('eta-timer').textContent = "Calc...";
        
        if (order.battery_drop) {
            document.getElementById('ml-batt-pill').style.display = 'flex';
            document.getElementById('tel-ml-batt').textContent = `-${order.battery_drop}% Drop`;
            document.getElementById('tel-batt').parentElement.style.display = 'none'; // hide sample battery
        }

        if (order.path && order.path.length > 0) {
            this.routeCoords = order.path;
            this.drawAndStart();
        } else {
            this.fetchLiveRoute();
        }
    },

    renderZones: async function() {
        try {
            const res = await fetch("http://localhost:8000/api/nfz?min_lat=17.33&min_lon=78.43&max_lat=17.43&max_lon=78.53");
            const data = await res.json();
            data.features.forEach(f => {
                const buffer_m = f.properties.buffer_m || 50;
                const [lng, lat] = f.geometry.coordinates;
                L.circle([lat, lng], {
                    radius: buffer_m,
                    color: '#EF4444',
                    fillColor: '#EF4444',
                    fillOpacity: 0.15,
                    weight: 2
                }).addTo(this.map);
            });
        } catch (e) {
            console.error("Failed to load NFZs", e);
        }
    },

    fetchLiveRoute: async function() {
        const payload = {
            drones: [{ id: "D-CUST", max_payload: 5.0, battery_capacity: 100, latitude: 17.40, longitude: 78.45 }], // Fake drone starting point
            orders: [{
                id: "ORD-CUST", package_weight: 1.0, 
                pickup_latitude: this.pickup.lat, pickup_longitude: this.pickup.lng,
                delivery_latitude: this.delivery.lat, delivery_longitude: this.delivery.lng
            }],
            weather: { wind_speed: 10, temperature: 25, humidity: 60, rain: 0 }
        };

        try {
            const res = await fetch("http://localhost:8000/api/optimize_routes", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            this.pollTaskStatus(data.task_id);
        } catch (e) {
            console.error(e);
            this.routeCoords = [[this.pickup.lat, this.pickup.lng], [this.delivery.lat, this.delivery.lng]];
            this.drawAndStart();
        }
    },

    pollTaskStatus: async function(taskId) {
        try {
            const res = await fetch(`http://localhost:8000/api/tasks/${taskId}`);
            const data = await res.json();
            if (data.status === "pending") {
                setTimeout(() => this.pollTaskStatus(taskId), 1000);
            } else if (data.status === "success") {
                this.routeCoords = data.assignments[0].path;
                this.drawAndStart();
            } else {
                this.routeCoords = [[this.pickup.lat, this.pickup.lng], [this.delivery.lat, this.delivery.lng]];
                this.drawAndStart();
            }
        } catch (e) {
            this.routeCoords = [[this.pickup.lat, this.pickup.lng], [this.delivery.lat, this.delivery.lng]];
            this.drawAndStart();
        }
    },

    drawAndStart: function() {
        this.routeLine = L.polyline(this.routeCoords, { color: 'var(--accent)', weight: 4, opacity: 0.5 }).addTo(this.map);
        this.map.fitBounds(this.routeLine.getBounds(), { padding: [30, 30] });

        const droneIconUrl = 'data:image/svg+xml;base64,' + btoa(`<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="#0055FF"><path d="M12 2L2 7l10 5 10-5-10-5zm0 10l-10 5 10 5 10-5-10-5zm0 10l-10 5 10 5 10-5-10-5z"/></svg>`);
        const droneIcon = L.icon({ iconUrl: droneIconUrl, iconSize: [24, 24], iconAnchor: [12, 12] });

        this.droneMarker = L.marker(this.routeCoords[0], { icon: droneIcon }).addTo(this.map);

        this.startSimulation();

        // ETA countdown based on path length
        const steps = this.routeCoords.length;
        window.HDL_CUSTOMER.UI.animateCountdown(steps * 2, 'eta-timer', () => {
            this.handleDelivered();
        });
    },

    startSimulation: function () {
        this.moveInterval = setInterval(() => {
            this.currentIndex++;
            if (this.currentIndex >= this.routeCoords.length) {
                clearInterval(this.moveInterval);
                return;
            }
            this.droneMarker.setLatLng(this.routeCoords[this.currentIndex]);

            // Attempt Socket.io connection fallback via console log to simulate failure structure
            console.debug('Socket.io ping attempt...');
        }, 2000);

        this.dataInterval = setInterval(() => {
            const batt = Math.max(0, 74 - Math.floor(this.currentIndex / 4));
            const alt = 45 + Math.floor(Math.random() * 10);
            const wind = 10 + Math.floor(Math.random() * 5);

            document.getElementById('tel-batt').textContent = batt + '%';
            document.getElementById('tel-alt').textContent = alt + 'm';
            document.getElementById('tel-wind').textContent = wind + ' km/h';

            // Update tracker stepped bar automatically mapping to position
            if (this.currentIndex > 5) {
                document.getElementById('step-track-2').classList.replace('active', 'completed');
                document.getElementById('step-track-3').classList.add('active');
            }
        }, 5000);
    },

    handleDelivered: function () {
        clearInterval(this.moveInterval);
        clearInterval(this.dataInterval);

        document.getElementById('step-track-3').classList.replace('active', 'completed');
        document.getElementById('step-track-4').classList.add('completed');

        document.getElementById('delivery-overlay').style.display = 'flex';
        document.getElementById('rate-btn-container').style.display = 'block';

        document.getElementById('tel-batt').textContent = '--';
        document.getElementById('tel-alt').textContent = '--';
        document.getElementById('tel-wind').textContent = '--';
    }
};
