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

        // Ensure we only have a real path 
        if (!order.route || order.route.length === 0) {
            alert("No live route available for this order yet.");
            return;
        }

        this.routeCoords = order.route;

        this.map = L.map('track-map', { zoomControl: false }).setView([this.pickup.lat, this.pickup.lng], 16);
        
        // ESRI Satellite
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            maxZoom: 19,
            attribution: '&copy; Esri'
        }).addTo(this.map);

        // OSM Labels Overlay
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap',
            opacity: 0.4
        }).addTo(this.map);

        L.circleMarker(this.pickup, { radius: 6, fillColor: '#10B981', color: '#fff', weight: 2, fillOpacity: 1 }).addTo(this.map);
        L.circleMarker(this.delivery, { radius: 6, fillColor: '#EF4444', color: '#fff', weight: 2, fillOpacity: 1 }).addTo(this.map);

        this.routeLine = L.polyline(this.routeCoords, { color: 'var(--accent)', weight: 4, opacity: 0.5 }).addTo(this.map);
        this.map.fitBounds(this.routeLine.getBounds(), { padding: [30, 30] });

        // Custom drone SVG icon matching the simulation (green marker)
        const droneIconUrl = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png';
        const droneIcon = L.icon({ iconUrl: droneIconUrl, iconSize: [30, 46], iconAnchor: [15, 46] });

        this.droneMarker = L.marker(this.routeCoords[0], { icon: droneIcon }).addTo(this.map);

        // Start simulations
        this.startSimulation();

        // ETA countdown (sync with route duration loosely)
        const totalSteps = this.routeCoords.length;
        const totalSeconds = totalSteps * 2; // 2 seconds per step
        
        window.HDL_CUSTOMER.UI.animateCountdown(totalSeconds, 'eta-timer', () => {
            this.handleDelivered();
        });
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
    },

    startSimulation: function () {
        const DRONE_SPEED_MS = 15.0; // 15 m/s
        const SIMULATION_INTERVAL_MS = 100; // 100ms
        
        let currentSegmentIndex = 0;
        let currentSegmentProgress = 0; // 0 to 1

        this.moveInterval = setInterval(() => {
            if (currentSegmentIndex >= this.routeCoords.length - 1) {
                clearInterval(this.moveInterval);
                this.droneMarker.setLatLng(this.routeCoords[this.routeCoords.length - 1]);
                return;
            }

            const start = this.routeCoords[currentSegmentIndex];
            const end = this.routeCoords[currentSegmentIndex + 1];
            
            // Handle coordinate arrays [lat, lon, alt] or [lat, lon]
            const startLat = Array.isArray(start) ? start[0] : start.lat;
            const startLon = Array.isArray(start) ? start[1] : start.lng;
            const endLat = Array.isArray(end) ? end[0] : end.lat;
            const endLon = Array.isArray(end) ? end[1] : end.lng;
            
            let segmentDistance = this.haversineDistance(startLat, startLon, endLat, endLon);
            if (segmentDistance < 0.1) segmentDistance = 0.1; // Prevent division by zero
            
            const distancePerInterval = DRONE_SPEED_MS * (SIMULATION_INTERVAL_MS / 1000);
            const progressIncrement = distancePerInterval / segmentDistance;
            
            currentSegmentProgress += progressIncrement;

            if (currentSegmentProgress >= 1.0) {
                currentSegmentProgress = 0;
                currentSegmentIndex++;
                if (currentSegmentIndex < this.routeCoords.length) {
                    const node = this.routeCoords[currentSegmentIndex];
                    const lat = Array.isArray(node) ? node[0] : node.lat;
                    const lon = Array.isArray(node) ? node[1] : node.lng;
                    this.droneMarker.setLatLng([lat, lon]);
                    this.currentIndex = currentSegmentIndex;
                }
            } else {
                const lat = startLat + (endLat - startLat) * currentSegmentProgress;
                const lon = startLon + (endLon - startLon) * currentSegmentProgress;
                this.droneMarker.setLatLng([lat, lon]);
                this.map.panTo([lat, lon], { animate: true, duration: 0.1 });
            }
        }, SIMULATION_INTERVAL_MS);

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
