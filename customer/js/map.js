// map.js
window.HDL_CUSTOMER = window.HDL_CUSTOMER || {};

// Place any general mapped utilities here if needed outside order.js and tracking.js.
// Leaflet instances are largely controlled by page-specific logic, but this wrapper
// satisfies the structural requirement for future generalization!
window.HDL_CUSTOMER.MapUtils = {
    flyTo: function (mapInstance, coords, zoom = 14) {
        mapInstance.flyTo(coords, zoom, {
            animate: true,
            duration: 1.5
        });
    }
};
