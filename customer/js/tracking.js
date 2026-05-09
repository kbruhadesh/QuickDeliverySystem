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

    initTracker: async function () {
        const urlParams = new URLSearchParams(window.location.search);
        const orderId = urlParams.get('id');
        let order = null;

        if (orderId) {
            // Fetch from API for global persistence
            try {
                const res = await fetch(`http://localhost:8000/api/orders/${orderId}`);
                if (res.ok) {
                    order = await res.json();
                }
            } catch (e) {
                console.error("Failed to fetch order from API", e);
            }
        }

        if (!order) {
            const latestStr = localStorage.getItem('hdl_latest_order');
            if (!latestStr) {
                document.getElementById('empty-track').style.display = 'block';
                document.getElementById('active-track').style.display = 'none';
                return;
            }
            order = JSON.parse(latestStr);
        }

        document.getElementById('empty-track').style.display = 'none';
        document.getElementById('active-track').style.display = 'block';

        // Fallback coords using both object formats (stored as {lat,lng} by order.js)
        this.pickup = { 
            lat: order.pickup?.lat || order.pickup_latitude || 17.3850, 
            lng: order.pickup?.lng || order.pickup_longitude || 78.4867 
        };
        this.delivery = { 
            lat: order.delivery?.lat || order.delivery_latitude || 17.4450, 
            lng: order.delivery?.lng || order.delivery_longitude || 78.3867 
        };

        // Use stored RRT* path or fall back to a straight 2-point line
        if (order.route_path && order.route_path.length > 0) {
            this.routeCoords = order.route_path;
        } else if (order.route && order.route.length > 0) {
            this.routeCoords = order.route;
        } else {
            this.routeCoords = [
                [this.pickup.lat, this.pickup.lng],
                [this.delivery.lat, this.delivery.lng]
            ];
        }

        // Sync delivery point to last waypoint
        if (this.routeCoords.length > 0) {
            const last = this.routeCoords[this.routeCoords.length - 1];
            this.delivery = {
                lat: Array.isArray(last) ? last[0] : last.lat,
                lng: Array.isArray(last) ? last[1] : last.lng
            };
        }

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

        this.routeLine = L.polyline(this.routeCoords, { color: '#0055FF', weight: 4, opacity: 0.5 }).addTo(this.map);
        
        // If route exists, the last point is the actual landing point (may be adjusted for NFZ)
        if (this.routeCoords.length > 0) {
            const lastPoint = this.routeCoords[this.routeCoords.length - 1];
            const landingLat = Array.isArray(lastPoint) ? lastPoint[0] : lastPoint.lat;
            const landingLon = Array.isArray(lastPoint) ? lastPoint[1] : lastPoint.lng;
            
            // Add a specific "Landing Point" marker if it's different from the house
            const distToHouse = window.HDL_CUSTOMER.UI.haversineDistance(landingLat, landingLon, this.delivery.lat, this.delivery.lng);
            if (distToHouse > 0.05) { // If more than 50m away
                L.marker([landingLat, landingLon], {
                    icon: L.divIcon({
                        className: 'landing-icon',
                        html: '<div style="background: #F59E0B; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div>',
                        iconSize: [12, 12]
                    })
                }).addTo(this.map).bindPopup("<b>Safety Landing Point</b><br>Required due to No-Fly Zone restrictions near your address.");
            }
        }

        this.map.fitBounds(this.routeLine.getBounds(), { padding: [30, 30] });

        // Custom drone SVG icon matching the simulation (green marker)
        const droneIconUrl = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png';
        const droneIcon = L.icon({ iconUrl: droneIconUrl, iconSize: [30, 46], iconAnchor: [15, 46] });

        this.droneMarker = L.marker(this.routeCoords[0], { icon: droneIcon }).addTo(this.map);

        // ETA countdown - synchronized with backend ETA
        const totalSeconds = (order.eta_minutes || order.eta || 5) * 60;
        this.order = order;

        // If already delivered, show delivered state immediately
        if (order.status === 'DELIVERED') {
            this.handleDelivered(true);
            return;
        }

        // Calculate elapsed time if flight was already in progress
        let elapsedSeconds = 0;
        // Check if the order has a startTime in DB (ISO string) or localStorage (Timestamp)
        const startTimeRaw = order.start_time || order.startTime;
        
        if (startTimeRaw) {
            const startTime = new Date(startTimeRaw).getTime();
            elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
            if (elapsedSeconds >= totalSeconds) {
                this.handleDelivered(true);
                return;
            }
        } else {
            // First time loading this order, set start time locally and optionally sync to DB
            this.order.startTime = Date.now();
            localStorage.setItem('hdl_latest_order', JSON.stringify(this.order));
            
            // For true persistence, we should update the DB with start_time
            if (order.id) {
                fetch(`http://localhost:8000/api/orders/${order.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ start_time: new Date().toISOString(), status: 'IN_TRANSIT' })
                }).catch(e => console.error("Could not sync start_time to DB"));
            }
        }
        
        const remainingSeconds = totalSeconds - elapsedSeconds;
        window.HDL_CUSTOMER.UI.animateCountdown(remainingSeconds, 'eta-timer', () => {
            if (this.order.status !== 'DELIVERED') this.handleDelivered();
        });

        // Start simulations with offset
        this.startSimulation(elapsedSeconds, totalSeconds);
    },




    startSimulation: function (offsetSeconds = 0, totalDurationSeconds = 300) {
        const DRONE_SPEED_MS = 15.0; // 15 m/s
        const SIMULATION_INTERVAL_MS = 100; // 100ms
        
        // Calculate where the drone should be based on elapsed time
        // We estimate total path length to find the starting node index
        let totalPathDistance = 0;
        for (let i = 0; i < this.routeCoords.length - 1; i++) {
            const s = this.routeCoords[i];
            const e = this.routeCoords[i+1];
            totalPathDistance += window.HDL_CUSTOMER.UI.haversineDistance(
                Array.isArray(s) ? s[0] : s.lat, Array.isArray(s) ? s[1] : s.lng,
                Array.isArray(e) ? e[0] : e.lat, Array.isArray(e) ? e[1] : e.lng
            );
        }

        const distanceToSkip = (offsetSeconds / totalDurationSeconds) * totalPathDistance;
        
        let currentSegmentIndex = 0;
        let currentSegmentProgress = 0;
        let accumulatedDistance = 0;

        if (offsetSeconds > 0) {
            for (let i = 0; i < this.routeCoords.length - 1; i++) {
                const s = this.routeCoords[i];
                const e = this.routeCoords[i+1];
                const segDist = window.HDL_CUSTOMER.UI.haversineDistance(
                    Array.isArray(s) ? s[0] : s.lat, Array.isArray(s) ? s[1] : s.lng,
                    Array.isArray(e) ? e[0] : e.lat, Array.isArray(e) ? e[1] : e.lng
                );
                
                if (accumulatedDistance + segDist >= distanceToSkip) {
                    currentSegmentIndex = i;
                    currentSegmentProgress = (distanceToSkip - accumulatedDistance) / segDist;
                    break;
                }
                accumulatedDistance += segDist;
            }
        }
        this.moveInterval = setInterval(() => {
            if (currentSegmentIndex >= this.routeCoords.length - 1) {
                clearInterval(this.moveInterval);
                this.droneMarker.setLatLng(this.routeCoords[this.routeCoords.length - 1]);
                this.handleDelivered(); // Trigger delivery when drone arrives visually
                return;
            }

            const start = this.routeCoords[currentSegmentIndex];
            const end = this.routeCoords[currentSegmentIndex + 1];
            
            // Handle coordinate arrays [lat, lon, alt] or [lat, lon]
            const startLat = Array.isArray(start) ? start[0] : start.lat;
            const startLon = Array.isArray(start) ? start[1] : start.lng;
            const endLat = Array.isArray(end) ? end[0] : end.lat;
            const endLon = Array.isArray(end) ? end[1] : end.lng;
            
            let segmentDistance = window.HDL_CUSTOMER.UI.haversineDistance(startLat, startLon, endLat, endLon);
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
                // Smoothly pan map to follow drone
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

    handleDelivered: function (alreadyDelivered = false) {
        clearInterval(this.moveInterval);
        clearInterval(this.dataInterval);

        // Update local order status
        if (this.order) {
            this.order.status = 'DELIVERED';
            localStorage.setItem('hdl_latest_order', JSON.stringify(this.order));
            
            // Sync status to backend database
            if (this.order.id) {
                fetch(`http://localhost:8000/api/orders/${this.order.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: 'DELIVERED', actual_delivery_time: new Date().toISOString() })
                }).catch(e => console.error("Could not sync delivery status to DB", e));
            }
        }

        document.getElementById('step-track-1').classList.add('completed');
        document.getElementById('step-track-2').classList.add('completed');
        document.getElementById('step-track-3').classList.replace('active', 'completed');
        document.getElementById('step-track-4').classList.add('completed');

        document.getElementById('delivery-overlay').style.display = 'flex';
        document.getElementById('eta-timer').parentElement.innerHTML = '<h2 style="color:var(--success); font-size: 2.5rem;">Order Delivered!</h2>';
        
        const rateBtn = document.getElementById('rate-btn-container');
        if (rateBtn) rateBtn.style.display = 'block';

        if (!alreadyDelivered) {
            window.HDL_CUSTOMER.UI.showToast("Drone has landed! Package delivered.", "success");
        }

        document.getElementById('tel-batt').textContent = '--';
        document.getElementById('tel-alt').textContent = '--';
        document.getElementById('tel-wind').textContent = '--';
    }
};
