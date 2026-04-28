// mock-data.js
// Hardcoded mock data for HDL Quick-Commerce Drone Delivery System

window.HDL = window.HDL || {};

window.HDL.mockData = {
  currentUser: {
    id: "A-001",
    name: "Admin User",
    role: "Operator"
  },

  darkStores: [
    { id: "DS-1", name: "Banjara Hills Node", pincodes: ["500034", "500004", "500028"], lat: 17.412, lng: 78.448, stock: 4500, maxStock: 5000, activeOrders: 14, dronesStationed: 4, status: "Active" },
    { id: "DS-2", name: "Gachibowli Hub", pincodes: ["500032", "500081", "500019"], lat: 17.440, lng: 78.348, stock: 800, maxStock: 4000, activeOrders: 27, dronesStationed: 6, status: "Active" },
    { id: "DS-3", name: "Hi-Tech City Express", pincodes: ["500081", "500084"], lat: 17.447, lng: 78.376, stock: 2100, maxStock: 3000, activeOrders: 8, dronesStationed: 2, status: "Active" },
    { id: "DS-4", name: "Jubilee Hills Center", pincodes: ["500033", "500045"], lat: 17.432, lng: 78.407, stock: 150, maxStock: 2500, activeOrders: 2, dronesStationed: 1, status: "Restocking" }
  ],

  drones: [
    { id: 'D1', model: 'AeroSwift V1', maxPayload: 2.5, battery: 94, status: 'available', lastUpdated: '2026-04-10T12:00:00Z' },
    { id: 'D2', model: 'AeroSwift V2', maxPayload: 5.0, battery: 85, status: 'assigned', lastUpdated: '2026-04-10T12:01:00Z' },
    { id: 'D3', model: 'SkyCarry X', maxPayload: 1.5, battery: 42, status: 'in-flight', lastUpdated: '2026-04-10T12:02:00Z' },
    { id: 'D4', model: 'AeroSwift V1', maxPayload: 2.5, battery: 100, status: 'available', lastUpdated: '2026-04-10T12:03:00Z' },
    { id: 'D5', model: 'SkyCarry XL', maxPayload: 7.0, battery: 18, status: 'failed', lastUpdated: '2026-04-10T11:50:00Z' },
    { id: 'D6', model: 'AeroSwift V2', maxPayload: 5.0, battery: 92, status: 'available', lastUpdated: '2026-04-10T12:00:00Z' },
    { id: 'D7', model: 'HeavyLift Pro', maxPayload: 10.0, battery: 78, status: 'in-flight', lastUpdated: '2026-04-10T12:04:00Z' },
    { id: 'D8', model: 'AeroSwift V1', maxPayload: 2.5, battery: 55, status: 'in-flight', lastUpdated: '2026-04-10T12:05:00Z' }
  ],

  orders: [
    { id: 'ORD-1001', pickup: [17.3828, 78.4740], delivery: [17.3900, 78.4700], weight: 1.2, status: 'completed', assignedDrone: 'D1', createdAt: '2026-04-10T09:00:00Z' },
    { id: 'ORD-1002', pickup: [17.3830, 78.4750], delivery: [17.3880, 78.4780], weight: 4.0, status: 'in-transit', assignedDrone: 'D3', createdAt: '2026-04-10T11:45:00Z' },
    { id: 'ORD-1003', pickup: [17.3850, 78.4690], delivery: [17.4000, 78.4900], weight: 0.8, status: 'pending', assignedDrone: null, createdAt: '2026-04-10T12:01:00Z' },
    { id: 'ORD-1004', pickup: [17.3810, 78.4690], delivery: [17.3950, 78.4850], weight: 2.1, status: 'assigned', assignedDrone: 'D2', createdAt: '2026-04-10T12:00:00Z' },
    { id: 'ORD-1005', pickup: [17.3790, 78.4650], delivery: [17.3850, 78.4800], weight: 6.5, status: 'failed', assignedDrone: 'D5', createdAt: '2026-04-10T11:30:00Z' },
    { id: 'ORD-1006', pickup: [17.3900, 78.4900], delivery: [17.4000, 78.5000], weight: 1.5, status: 'in-transit', assignedDrone: 'D7', createdAt: '2026-04-10T11:55:00Z' },
    { id: 'ORD-1007', pickup: [17.3950, 78.4800], delivery: [17.4100, 78.4950], weight: 2.3, status: 'pending', assignedDrone: null, createdAt: '2026-04-10T12:02:00Z' },
    { id: 'ORD-1008', pickup: [17.3800, 78.4600], delivery: [17.3900, 78.4650], weight: 1.0, status: 'in-transit', assignedDrone: 'D8', createdAt: '2026-04-10T11:58:00Z' },
    { id: 'ORD-1009', pickup: [17.4000, 78.4700], delivery: [17.4150, 78.4800], weight: 3.2, status: 'completed', assignedDrone: 'D6', createdAt: '2026-04-10T10:15:00Z' },
    { id: 'ORD-1010', pickup: [17.3880, 78.4750], delivery: [17.3920, 78.4850], weight: 0.5, status: 'pending', assignedDrone: null, createdAt: '2026-04-10T12:03:00Z' },
    { id: 'ORD-1011', pickup: [17.3800, 78.4800], delivery: [17.3850, 78.4900], weight: 1.8, status: 'completed', assignedDrone: 'D4', createdAt: '2026-04-10T09:45:00Z' },
    { id: 'ORD-1012', pickup: [17.3900, 78.4650], delivery: [17.3950, 78.4750], weight: 0.9, status: 'assigned', assignedDrone: 'D1', createdAt: '2026-04-10T12:04:00Z' },
    { id: 'ORD-1013', pickup: [17.4000, 78.5000], delivery: [17.4100, 78.5100], weight: 2.0, status: 'pending', assignedDrone: null, createdAt: '2026-04-10T12:05:00Z' },
    { id: 'ORD-1014', pickup: [17.3850, 78.4600], delivery: [17.3900, 78.4700], weight: 1.1, status: 'pending', assignedDrone: null, createdAt: '2026-04-10T12:06:00Z' },
    { id: 'ORD-1015', pickup: [17.3950, 78.4900], delivery: [17.4050, 78.5000], weight: 4.5, status: 'pending', assignedDrone: null, createdAt: '2026-04-10T12:07:00Z' }
  ],

  assignments: [
    { droneId: 'D2', orderId: 'ORD-1004', distance: 2.4, eta: '12 mins', batteryPred: 75, compliance: true, weatherImpact: 'Low', algorithm: 'OR-Tools', route: [[17.3810, 78.4690], [17.3880, 78.4770], [17.3950, 78.4850]] },
    { droneId: 'D3', orderId: 'ORD-1002', distance: 1.8, eta: '8 mins', batteryPred: 38, compliance: true, weatherImpact: 'Medium', algorithm: 'Greedy', route: [[17.3830, 78.4750], [17.3860, 78.4760], [17.3880, 78.4780]] },
    { droneId: 'D7', orderId: 'ORD-1006', distance: 3.5, eta: '18 mins', batteryPred: 60, compliance: false, weatherImpact: 'High', algorithm: 'OR-Tools', route: [[17.3900, 78.4900], [17.3950, 78.4950], [17.4000, 78.5000]] },
    { droneId: 'D8', orderId: 'ORD-1008', distance: 2.1, eta: '10 mins', batteryPred: 48, compliance: true, weatherImpact: 'Low', algorithm: 'Greedy', route: [[17.3800, 78.4600], [17.3850, 78.4620], [17.3900, 78.4650]] },
    { droneId: 'D1', orderId: 'ORD-1012', distance: 1.2, eta: '5 mins', batteryPred: 89, compliance: true, weatherImpact: 'Low', algorithm: 'OR-Tools', route: [[17.3900, 78.4650], [17.3930, 78.4700], [17.3950, 78.4750]] }
  ],

  zones: [
    { id: 'Z1', name: 'Downtown Restricted', type: 'No-Fly', area: 1.2, coordinates: [[17.3850, 78.4720], [17.3880, 78.4760], [17.3840, 78.4800], [17.3820, 78.4740]] },
    { id: 'Z2', name: 'Airport Approach', type: 'No-Fly', area: 3.5, coordinates: [[17.4050, 78.4900], [17.4150, 78.5000], [17.4100, 78.5100], [17.4000, 78.4950]] },
    { id: 'Z3', name: 'Stadium Event', type: 'Temporary Restriction', area: 0.8, coordinates: [[17.3920, 78.4620], [17.3950, 78.4680], [17.3900, 78.4700], [17.3880, 78.4650]] }
  ],

  analytics: {
    deliveryTimes: [14.2, 13.5, 12.8, 14.5, 15.2, 13.8, 12.5],
    batteryUsed: { 'D1': 15, 'D2': 22, 'D3': 40, 'D4': 10, 'D5': 80, 'D6': 18, 'D7': 35, 'D8': 28 },
    hourlyVolumes: [4, 8, 12, 25, 30, 20, 15, 10, 5, 2]
  },

  benchmarks: [
    { timestamp: '2026-04-09T10:00:00Z', config: '100 Orders, OR-Tools', result: 'Solve Time: 120ms' },
    { timestamp: '2026-04-09T14:30:00Z', config: '200 Orders, Greedy', result: 'Solve Time: 15ms' },
    { timestamp: '2026-04-10T09:15:00Z', config: '50 Orders, OR-Tools', result: 'Solve Time: 45ms' },
    { timestamp: '2026-04-10T11:00:00Z', config: '10 Orders, Greedy', result: 'Solve Time: 2ms' }
  ],

  eventLog: [
    '[11:58:10] ℹ️ System started. Connected to 8 drones.',
    '[11:59:05] ✅ Drone D1 completed ORD-1001',
    '[12:00:00] ✅ Drone D2 assigned to ORD-1004',
    '[12:00:15] ℹ️ New order ORD-1003 received',
    '[12:01:30] ℹ️ Drone D6 returned to base for charging',
    '[12:02:10] ℹ️ New order ORD-1007 received',
    '[12:03:00] ℹ️ New order ORD-1010 received',
    '[12:04:15] ✅ Drone D1 assigned to ORD-1012',
    '[12:05:00] ℹ️ New order ORD-1013 received',
    '[12:05:11] ⚠️ Drone D5 FAILURE — reassigning...'
  ]
};
