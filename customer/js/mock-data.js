// mock-data.js
window.HDL_CUSTOMER = window.HDL_CUSTOMER || {};

window.HDL_CUSTOMER.MOCK_CUSTOMERS = [
    { id: "C001", name: "Aryan Sharma", email: "aryan@demo.com", password: "demo123", phone: "+91 98765 43210" },
    { id: "C002", name: "Priya Nair", email: "priya@demo.com", password: "demo456", phone: "+91 91234 56789" }
];

window.HDL_CUSTOMER.MOCK_ORDERS = [
    { id: "HDL-2847", status: "IN_TRANSIT", pickup: "Rajiv Gandhi Nagar Store", delivery: "Home", weight: "1-2 kg", drone: "D-07", eta_min: 18, distance_km: 2.4, created: "2025-04-11T11:30:00Z", route: [[10.120, 76.450], [10.124, 76.454], [10.128, 76.458], [10.133, 76.462]] },
    { id: "HDL-2831", status: "DELIVERED", pickup: "Central Store", delivery: "Office", weight: "Under 1 kg", drone: "D-03", delivered_at: "2025-04-10T14:22:00Z", delivery_time_min: 21 },
    { id: "HDL-2815", status: "DELIVERED", pickup: "MG Road Store", delivery: "Home", weight: "2-3 kg", drone: "D-05", delivered_at: "2025-04-09T10:10:00Z", delivery_time_min: 24 },
    { id: "HDL-2802", status: "DELIVERED", pickup: "North Hub", delivery: "Friend's place", weight: "Under 1 kg", drone: "D-02", delivered_at: "2025-04-08T16:40:00Z", delivery_time_min: 17 },
    { id: "HDL-2789", status: "CANCELLED", pickup: "South Store", delivery: "Home", weight: "3-5 kg", drone: null, cancelled_at: "2025-04-07T09:00:00Z", reason: "No drones available" }
];

window.HDL_CUSTOMER.MOCK_LIVE_STATS = {
    active_deliveries: 12,
    available_drones: 3,
    avg_delivery_min: 18
};
