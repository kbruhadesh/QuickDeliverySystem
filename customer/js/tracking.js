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

        // Generate fake route points between pickup and delivery
        this.routeCoords = this.generateFakeRoute(this.pickup, this.delivery, 40);

        this.map = L.map('track-map', { zoomControl: false }).setView([this.pickup.lat, this.pickup.lng], 13);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(this.map);

        L.circleMarker(this.pickup, { radius: 6, fillColor: '#10B981', color: '#fff', weight: 2, fillOpacity: 1 }).addTo(this.map);
        L.circleMarker(this.delivery, { radius: 6, fillColor: '#EF4444', color: '#fff', weight: 2, fillOpacity: 1 }).addTo(this.map);

        this.routeLine = L.polyline(this.routeCoords, { color: 'var(--accent)', weight: 4, opacity: 0.5 }).addTo(this.map);
        this.map.fitBounds(this.routeLine.getBounds(), { padding: [30, 30] });

        // Custom drone SVG icon
        const droneIconUrl = 'data:image/svg+xml;base64,' + btoa(`<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="#0055FF"><path d="M12 2L2 7l10 5 10-5-10-5zm0 10l-10 5 10 5 10-5-10-5zm0 10l-10 5 10 5 10-5-10-5z"/></svg>`);
        const droneIcon = L.icon({ iconUrl: droneIconUrl, iconSize: [24, 24], iconAnchor: [12, 12] });

        this.droneMarker = L.marker(this.routeCoords[0], { icon: droneIcon }).addTo(this.map);

        // Start simulations
        this.startSimulation();

        // ETA countdown (sync with route duration loosely)
        // 40 steps at 2000ms = 80 seconds
        window.HDL_CUSTOMER.UI.animateCountdown(80, 'eta-timer', () => {
            this.handleDelivered();
        });
    },

    generateFakeRoute: function (start, end, steps) {
        const pts = [];
        for (let i = 0; i <= steps; i++) {
            const lat = start.lat + (end.lat - start.lat) * (i / steps);
            const lng = start.lng + (end.lng - start.lng) * (i / steps);
            // add slight curve/noise
            const noise = i > 0 && i < steps ? (Math.random() - 0.5) * 0.005 : 0;
            pts.push([lat + noise, lng + noise]);
        }
        return pts;
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
