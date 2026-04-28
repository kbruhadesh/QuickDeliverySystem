# Frontend Requirements Document
## Project: Simulation-Based System for Drone Delivery in Quick-Commerce (HDL)
### Version 1.0 | Prepared for Frontend Development Team

---

## TABLE OF CONTENTS

1. [Project Understanding](#1-project-understanding)
2. [Frontend Scope Breakdown](#2-frontend-scope-breakdown)
3. [Dashboards & Pages](#3-dashboards--pages)
4. [Component-Level Breakdown](#4-component-level-breakdown)
5. [User Flows](#5-user-flows)
6. [State & Data Handling](#6-state--data-handling)
7. [API Requirements (Frontend Perspective)](#7-api-requirements-frontend-perspective)
8. [Edge Cases & UX Considerations](#8-edge-cases--ux-considerations)
9. [Responsive & Platform Needs](#9-responsive--platform-needs)

---

## 1. PROJECT UNDERSTANDING

### Summary
HDL (Hyperlocal Drone Logistics) is a **web-based simulation platform** that mimics a quick-commerce drone delivery system (think Zepto/Blinkit but with drones instead of couriers). Users can place simulated delivery orders on a map, the system automatically assigns drones using optimization algorithms, and users can watch drones move in real-time on the map. No real drones are involved — it is purely a software simulation for research and testing.

### Target Users
| User Type | Description |
|---|---|
| **Researcher / Analyst** | Primary user. Creates orders, runs simulations, analyzes performance metrics |
| **System Administrator** | Manages drone fleet configuration, zone setup, system health |
| **Developer / Tester** | Runs benchmark tests, injects failures, evaluates algorithm performance |

> **Note:** The document currently defines a single user role (simulation operator). Inferred admin capabilities are described separately. There is NO multi-tenant or authentication-heavy setup required in v1.

### Main Goals of the System (Frontend Perspective)
- Allow users to **create delivery orders** by picking locations on an interactive map
- Show **real-time drone movement**, battery levels, and delivery status on a live map
- Visualize **optimization results** — which drone is assigned to which order, with the route drawn
- Display **analytics and benchmarking** dashboards with charts and tables
- Let users **inject failures** and observe system recovery behavior
- Provide **weather-aware battery predictions** and compliance status for each route

---

## 2. FRONTEND SCOPE BREAKDOWN

### All Frontend Modules / Features Required

| # | Module | Description |
|---|---|---|
| 1 | **Authentication Module** | Login / Register / Session management |
| 2 | **Order Management Module** | Create, view, and track delivery orders |
| 3 | **Drone Fleet Module** | View drone list, status, battery, availability |
| 4 | **Map & Route Visualization Module** | Interactive map with orders, drones, routes, zones |
| 5 | **Assignment Viewer Module** | Show optimization results (drone ↔ order mapping) |
| 6 | **Real-Time Telemetry Module** | Live-streaming drone position, battery, status via WebSocket |
| 7 | **Analytics & Metrics Dashboard** | Charts: delivery time, battery usage, compliance rate |
| 8 | **Failure Simulation Module** | Trigger drone failures, observe reassignment |
| 9 | **Benchmark / Load Test Module** | Generate bulk orders, run stress tests, see throughput metrics |
| 10 | **Weather Panel** | Display current weather conditions, impact on battery |
| 11 | **Airspace Zones Layer** | Display restricted/no-fly zones as polygons on map |
| 12 | **Notifications / Toast System** | Real-time alerts for assignments, failures, recoveries |
| 13 | **Settings / Configuration Panel** | Admin-level config (drone parameters, simulation speed) |

### User Roles & Feature Access Matrix

| Feature | Researcher/Analyst | Admin | Developer/Tester |
|---|---|---|---|
| Place orders on map | ✅ | ✅ | ✅ |
| View drone fleet | ✅ | ✅ | ✅ |
| View assignment results | ✅ | ✅ | ✅ |
| Live telemetry tracking | ✅ | ✅ | ✅ |
| Analytics dashboard | ✅ | ✅ | ✅ |
| Inject drone failures | ❌ | ✅ | ✅ |
| Run benchmark tests | ❌ | ✅ | ✅ |
| Manage drone fleet (CRUD) | ❌ | ✅ | ❌ |
| Manage airspace zones | ❌ | ✅ | ❌ |
| Configure simulation params | ❌ | ✅ | ✅ |
| View system health/logs | ❌ | ✅ | ✅ |

> **Inferred:** Role-based access is enforced through route guards on the frontend. Admin pages are not visible to Researcher role.

---

## 3. DASHBOARDS & PAGES

### 3.1 — Main Dashboard (Home)

**Purpose:** Command center. Overview of the entire system state at a glance.

**Key Components / Widgets:**
- Summary stat cards: Total Active Orders, Available Drones, Drones In-Flight, Completed Deliveries
- Mini live map (small preview of active drone movements)
- Recent assignments table (last 5–10 assignments with status)
- System health indicators (Backend status, WebSocket connection, Weather API status)
- Quick-action buttons: "Place New Order", "Run Simulation", "View Analytics"

**Data Displayed:**
- Active order count (from `/api/orders?status=active`)
- Drone fleet summary (from `/api/drones`)
- Recent assignment list (from `/api/assignments?limit=10`)
- System health (from `/api/health`)

---

### 3.2 — Order Management Page

**Purpose:** Create new delivery orders and view the list of all past/active orders.

**Key Components / Widgets:**
- Order creation form (location picker on map + package weight input + submit)
- Orders data table with columns: Order ID, Pickup Location, Delivery Location, Weight (kg), Status, Assigned Drone, Created At, ETA
- Status filter tabs: All / Pending / Assigned / In-Transit / Completed / Failed
- Search bar (filter by order ID or location)
- Order detail side panel (click an order row to see full detail)

**Data Displayed:**
- Order list (from `/api/orders`)
- Drone assignment per order (from `/api/assignments`)
- Order status (PENDING, ASSIGNED, IN_TRANSIT, DELIVERED, FAILED)

---

### 3.3 — Live Map & Tracking Page

**Purpose:** Core operational view. Shows everything happening spatially — drone positions, delivery routes, restricted zones.

**Key Components / Widgets:**
- Full-screen interactive Leaflet.js map (OpenStreetMap base)
- Drone markers (icon with battery % label, color-coded by status)
- Active route polylines (color: green = in-flight, yellow = assigned, red = failed)
- Pickup markers (store icon)
- Delivery destination markers (house icon)
- Airspace / no-fly zone polygons (semi-transparent red overlays)
- Drone info popup on marker click (ID, battery %, payload, status, ETA)
- Order info popup on destination click
- Layer toggle controls (show/hide: Drones, Routes, Zones, Orders)
- Live connection status badge (WebSocket connected / reconnecting)

**Data Displayed:**
- Real-time drone positions (via WebSocket: `drone:telemetry` events)
- Battery level per drone (live-streamed)
- Route polylines per active assignment
- Airspace zone polygons (from `/api/zones`)

---

### 3.4 — Drone Fleet Management Page

**Purpose:** View all drones in the fleet and their current status. Admin can add/edit/remove drones.

**Key Components / Widgets:**
- Drone fleet table with columns: Drone ID, Model, Max Payload (kg), Battery Capacity (mAh), Current Battery %, Status, Current Location, Last Updated
- Status filter: Available / Assigned / In-Flight / Charging / Offline / Failed
- Add Drone modal (Admin only)
- Edit Drone drawer (Admin only)
- Drone health card on row click (specs, maintenance history placeholder)

**Data Displayed:**
- Full drone list (from `/api/drones`)
- Battery levels (from `/api/telemetry/latest` or WebSocket)
- Operational status per drone

---

### 3.5 — Assignment Viewer Page

**Purpose:** Show the output of the optimization engine — which drone was assigned to which order, along with route details, compliance status, and predicted battery usage.

**Key Components / Widgets:**
- Assignment cards / table: Assignment ID, Drone, Order, Route Distance (km), Est. Delivery Time, Predicted Battery Used (%), Compliance Status (✅ / ❌), Weather Impact Score
- Route detail view (click assignment → see map with that route highlighted)
- Algorithm comparison toggle (Greedy vs OR-Tools — if benchmark mode enabled)
- Assignment score breakdown tooltip (distance weight + battery weight + compliance weight)
- Reassignment event log (shows if a drone was re-routed due to failure)

**Data Displayed:**
- Assignment list (from `/api/assignments`)
- Battery prediction per assignment (from `/api/predictions/battery`)
- Compliance status per route (from `/api/zones/validate`)
- Weather impact score (from `/api/weather/impact`)

---

### 3.6 — Analytics & Metrics Dashboard

**Purpose:** Performance analysis. Charts and tables evaluating system efficiency under various conditions.

**Key Components / Widgets:**
- Delivery Time chart — Line chart: avg delivery time over time
- Battery Utilization chart — Bar chart: battery used per drone per session
- Order Volume chart — Bar chart: orders per hour/day
- Compliance Rate gauge — Donut chart: % routes compliant vs. non-compliant (should be 100%)
- Algorithm Comparison table — Greedy vs OR-Tools: delivery time, battery efficiency, constraint violations
- Failure Recovery metrics — Card: Avg reassignment time (seconds), % orders impacted by failure
- Weather Impact panel — Table: weather condition → battery penalty applied
- Date range filter (Last 1h / 6h / 24h / Custom)
- Export button (CSV download of current table data)

**Data Displayed:**
- Aggregated delivery metrics (from `/api/analytics/summary`)
- Per-drone battery stats (from `/api/analytics/battery`)
- Algorithm benchmark results (from `/api/benchmarks/results`)
- Failure recovery stats (from `/api/analytics/failures`)

---

### 3.7 — Simulation Control Page

**Purpose:** Control the digital twin simulator — start, pause, speed up, inject failures, and run batch scenarios.

**Key Components / Widgets:**
- Simulation controls: Start / Pause / Stop / Reset buttons
- Speed multiplier selector (1x, 2x, 5x, 10x)
- Batch order generator (input: number of orders → click "Generate" → random orders placed on map)
- Failure injection panel:
  - "Inject Failure" button with drone selector
  - Auto-inject toggle with failure rate input (e.g., 5% probability)
- Active simulation status panel (Simulation running ● / Paused ⏸)
- Event log feed (scrollable, real-time log of simulation events: "Drone D3 assigned to Order #42", "Drone D3 FAILED — reassigning…")
- Simulation summary on stop (orders completed, failures occurred, avg delivery time)

**Data Displayed:**
- Simulation state (from `/api/simulation/status` via WebSocket)
- Real-time event log (WebSocket: `simulation:event` channel)
- Failure injection response (from `/api/simulation/inject-failure`)

---

### 3.8 — Benchmark & Load Test Page (Developer / Admin Only)

**Purpose:** Stress-test the backend optimization engine with large order volumes and measure performance.

**Key Components / Widgets:**
- Benchmark config form: Number of orders (10 / 50 / 100 / 200), Algorithm selector (Greedy / OR-Tools / Both), Run button
- Progress indicator (spinner + "Processing 47/100 orders…")
- Results panel after completion:
  - Table: Orders count → Solve time (ms) → Avg delivery time → Battery efficiency → Violations
  - Bar chart: Algorithm comparison across metrics
- Previous benchmark runs history table (timestamp, config, key results)

**Data Displayed:**
- Benchmark run results (from `/api/benchmarks/run` — POST + poll)
- Historical benchmark records (from `/api/benchmarks/history`)

---

### 3.9 — Auth Pages

#### Login Page
- Email + Password fields
- "Login" button
- Error display for invalid credentials
- (No Sign-up for v1 — use seeded admin credentials)

#### (Optional) Register / Invite Page
- Name, Email, Password, Role selector
- Requires admin to create new accounts

---

### 3.10 — Settings / Configuration Page (Admin Only)

**Purpose:** Configure simulation parameters and drone specs.

**Key Components / Widgets:**
- Drone default parameters (max payload, battery capacity, speed)
- Simulation defaults (failure rate, weather penalty weights)
- Weather API config (API key input, cache TTL)
- Zone management: Upload/draw no-fly zones on map, delete zones

---

### COMPLETE PAGE INVENTORY

| Page | Route | Access |
|---|---|---|
| Login | `/login` | Public |
| Main Dashboard | `/` | All roles |
| Order Management | `/orders` | All roles |
| Live Map & Tracking | `/map` | All roles |
| Drone Fleet | `/drones` | All roles (Admin: edit) |
| Assignment Viewer | `/assignments` | All roles |
| Analytics Dashboard | `/analytics` | All roles |
| Simulation Control | `/simulation` | Admin, Developer |
| Benchmark / Load Test | `/benchmarks` | Admin, Developer |
| Settings | `/settings` | Admin only |
| 404 Not Found | `*` | All |

---

## 4. COMPONENT-LEVEL BREAKDOWN

### 4.1 — Reusable Base Components

| Component | Description | Props |
|---|---|---|
| `<Button>` | Primary, secondary, danger, ghost variants | `variant`, `size`, `disabled`, `loading`, `onClick` |
| `<Card>` | Container with optional header, border, shadow | `title`, `subtitle`, `actions`, `children` |
| `<StatCard>` | KPI display tile (number + label + trend) | `label`, `value`, `unit`, `trend`, `icon`, `color` |
| `<DataTable>` | Sortable, filterable table with pagination | `columns`, `data`, `loading`, `onRowClick`, `pageSize` |
| `<Modal>` | Centered overlay with title, body, action buttons | `isOpen`, `onClose`, `title`, `children`, `size` |
| `<Drawer>` | Slide-in side panel | `isOpen`, `onClose`, `title`, `position`, `children` |
| `<Badge>` | Status indicators (color-coded) | `label`, `color`, `variant` |
| `<Spinner>` | Loading state indicator | `size`, `color` |
| `<Toast/Alert>` | Notification messages (success/error/warning/info) | `type`, `message`, `duration`, `onClose` |
| `<Input>` | Text, number, email inputs with validation display | `type`, `label`, `error`, `placeholder`, `onChange` |
| `<Select>` | Dropdown select | `options`, `value`, `onChange`, `label`, `error` |
| `<Tabs>` | Tabbed content switcher | `tabs`, `activeTab`, `onTabChange` |
| `<ProgressBar>` | Linear progress indicator | `value` (0–100), `color`, `label` |
| `<Tooltip>` | Hover info popover | `content`, `position`, `children` |
| `<EmptyState>` | Placeholder when no data available | `icon`, `title`, `description`, `action` |
| `<ErrorBoundary>` | Catches React rendering errors | `fallback` |
| `<ConfirmDialog>` | Confirmation modal for destructive actions | `isOpen`, `onConfirm`, `onCancel`, `message` |

---

### 4.2 — Domain-Specific Components

| Component | Description | Complexity |
|---|---|---|
| `<DroneMarker>` | Leaflet map marker with drone icon, battery label, color by status | High |
| `<RoutePolyline>` | Leaflet polyline for a drone's route, color by status | Medium |
| `<ZonePolygon>` | Leaflet polygon for no-fly zone rendering with tooltip | Medium |
| `<OrderMarker>` | Map marker for pickup/delivery locations | Low |
| `<MapLayerToggle>` | Checkbox controls to show/hide map layers | Medium |
| `<TelemetryCard>` | Drone telemetry display: battery %, speed, altitude, status | Medium |
| `<AssignmentCard>` | Compact assignment summary: drone ↔ order, compliance badge, battery | Medium |
| `<EventLogFeed>` | Scrollable real-time simulation event stream | High (WebSocket) |
| `<WeatherWidget>` | Current conditions: temp, wind, rain, impact score badge | Medium |
| `<BatteryIndicator>` | Visual battery bar (green/yellow/red based on %) | Low |
| `<StatusBadge>` | Drone/order status chips with color coding | Low |
| `<AlgorithmCompareTable>` | Side-by-side metrics for greedy vs OR-Tools | Medium |
| `<BenchmarkProgressBar>` | Animated progress for active benchmark run | Medium |
| `<FailureInjector>` | Drone selector + inject button panel | Medium |
| `<SimulationControls>` | Play/Pause/Stop/Speed buttons with state reflection | High |
| `<ConnectionStatusBadge>` | WebSocket live/reconnecting/disconnected indicator | Medium |

---

### 4.3 — Chart Components (Using Recharts or Chart.js)

| Component | Chart Type | Data Source |
|---|---|---|
| `<DeliveryTimeChart>` | Line chart over time | `/api/analytics/summary` |
| `<BatteryUsageChart>` | Bar chart per drone | `/api/analytics/battery` |
| `<OrderVolumeChart>` | Bar chart by hour/day | `/api/analytics/summary` |
| `<ComplianceRateDonut>` | Donut chart: compliant vs. violation | `/api/analytics/compliance` |
| `<AlgorithmBenchmarkBar>` | Grouped bar: greedy vs OR-Tools | `/api/benchmarks/results` |
| `<FailureRecoveryLine>` | Line: reassignment times over simulations | `/api/analytics/failures` |

---

### 4.4 — Layout Components

| Component | Description |
|---|---|
| `<AppShell>` | Main layout: sidebar + topbar + content area |
| `<Sidebar>` | Navigation menu with role-based link visibility |
| `<TopBar>` | App title, WebSocket status badge, user menu |
| `<PageHeader>` | Page title + breadcrumb + action buttons |
| `<SplitView>` | Left panel (table) + Right panel (detail/map) layout |

---

## 5. USER FLOWS

### Flow 1: Place a Delivery Order

1. User navigates to **Order Management** (`/orders`)
2. Clicks **"Place New Order"** button
3. Order Creation Modal opens with embedded mini-map
4. User clicks a location on map → Pickup point set (green pin)
5. User clicks another location → Delivery point set (red pin)
6. User enters package weight in kg (validated: 0.1–5.0 kg)
7. User clicks **"Submit Order"**
8. Frontend POSTs to `/api/orders`
9. On success: Toast notification "Order #42 created", modal closes
10. Orders table refreshes — new order appears with status `PENDING`

---

### Flow 2: Assign Drones to Orders (Optimization)

1. User navigates to **Assignment Viewer** (`/assignments`)
2. Clicks **"Run Assignment"** (or assignment is auto-triggered after order creation)
3. Frontend POSTs to `/api/assignments/run` with order IDs
4. Loading spinner shown ("Optimizing…")
5. Response returns assignment list (drone ↔ order pairs, routes, battery predictions, compliance)
6. Assignment cards appear: each shows Drone ID, Order ID, Route Distance, Battery Predicted, Compliance ✅
7. User can click any assignment card → map opens showing that specific route
8. Drone markers on live map now show route polylines

---

### Flow 3: Monitor Live Drone Tracking

1. User navigates to **Live Map** (`/map`)
2. Map loads with OpenStreetMap base tiles
3. WebSocket connection established (Socket.IO connects to backend)
4. Every 2 seconds, backend emits `drone:telemetry` events per drone
5. Frontend updates drone marker positions in real-time on map
6. Battery % label on each marker updates dynamically
7. Marker color reflects status: green (in-flight), yellow (assigned), gray (available), red (failed)
8. User clicks drone marker → info popup: Drone ID, Battery %, Payload, Current Speed, ETA
9. User can toggle layer visibility using layer controls (hide zones, hide routes, etc.)

---

### Flow 4: Inject Drone Failure & Observe Recovery

1. User navigates to **Simulation Control** (`/simulation`)
2. Clicks **"Inject Failure"** button
3. Drone selector dropdown appears → User picks "Drone D3"
4. Clicks **"Confirm Failure"**
5. Frontend POSTs to `/api/simulation/inject-failure` with `{ droneId: "D3" }`
6. Event log feed shows: "⚠️ Drone D3 FAILURE detected"
7. System automatically reassigns D3's order to next available drone
8. Event log shows: "✅ Order #42 reassigned to Drone D7 — recalculating route"
9. Map updates: D3 marker turns red/grey; D7's route polyline updates
10. Analytics panel shows reassignment time in milliseconds

---

### Flow 5: Run Benchmark Test

1. User navigates to **Benchmarks** (`/benchmarks`)
2. Selects number of orders: e.g., "100 orders"
3. Selects algorithm: "Both (Greedy + OR-Tools)"
4. Clicks **"Run Benchmark"**
5. Progress bar updates: "Processing 34/100 orders…"
6. On completion: Results table appears showing comparison metrics
7. Bar chart renders algorithm comparison (solve time, delivery time, battery efficiency, violations)
8. User can click **"Export CSV"** to download results

---

### Flow 6: Admin Adds a Drone

1. Admin navigates to **Drone Fleet** (`/drones`)
2. Clicks **"Add Drone"** button (visible only for Admin role)
3. "Add Drone" modal opens
4. Admin fills: Drone ID, Model, Max Payload (kg), Battery Capacity (mAh), Initial Location (map picker)
5. Clicks **"Save"**
6. Frontend POSTs to `/api/drones`
7. Toast: "Drone D11 added successfully"
8. Drone fleet table refreshes with new drone (status: "Available")

---

## 6. STATE & DATA HANDLING

### 6.1 — Global Application State (Context / Redux / Zustand)

| State Slice | Contents | Update Trigger |
|---|---|---|
| `auth` | `{ user, role, token, isAuthenticated }` | Login/logout |
| `drones` | `DroneList[]` — all drones with current battery & status | API fetch + WebSocket telemetry |
| `orders` | `Order[]` — all orders with status | API fetch + WebSocket events |
| `assignments` | `Assignment[]` — current optimization output | API response |
| `simulation` | `{ running, paused, speed, eventLog[] }` | WebSocket `simulation:event` |
| `websocket` | `{ connected, reconnecting, error }` | Socket.IO connection lifecycle |
| `weather` | `{ temperature, windSpeed, humidity, rainMM, impact }` | API poll (every 10 min) |
| `notifications` | `Toast[]` | Backend events, API responses |
| `mapLayers` | `{ drones, routes, zones, orders }` (boolean toggles) | User interaction |

---

### 6.2 — Real-Time WebSocket Events

| Event Name | Direction | Payload | Frontend Action |
|---|---|---|---|
| `drone:telemetry` | Server → Client | `{ droneId, lat, lng, battery, speed, status }` | Update drone marker position & battery |
| `drone:assigned` | Server → Client | `{ droneId, orderId, route }` | Update assignment state, draw route on map |
| `drone:failed` | Server → Client | `{ droneId, reason }` | Mark drone red on map, show toast alert |
| `drone:reassigned` | Server → Client | `{ droneId, oldOrderId, newDroneId }` | Update map markers, show recovery in event log |
| `order:delivered` | Server → Client | `{ orderId, droneId, deliveryTime }` | Update order status to DELIVERED, show confetti/toast |
| `simulation:event` | Server → Client | `{ type, message, timestamp }` | Append to event log feed |
| `simulation:started` | Server → Client | `{}` | Update simulation state to RUNNING |
| `simulation:stopped` | Server → Client | `{ summary }` | Show simulation summary panel |

---

### 6.3 — Forms & Inputs

| Form | Fields | Validation |
|---|---|---|
| **Create Order** | Pickup location (map click), Delivery location (map click), Weight (number, 0.1–5.0 kg) | Both locations required and within operational bounds; weight must be within drone capacity |
| **Add Drone** | Drone ID (string), Model (string), Max Payload (0.1–5.0 kg), Battery Capacity (mAh), Initial lat/lng | All fields required; ID must be unique |
| **Inject Failure** | Drone selector (dropdown, only in-flight drones) | Drone must be in ASSIGNED or IN_FLIGHT state |
| **Run Benchmark** | Order count (10/50/100/200), Algorithm (Greedy/OR-Tools/Both) | At least one algorithm selected |
| **Login** | Email, Password | Email format valid; password min 6 chars |
| **Simulation Speed** | Speed multiplier (1x / 2x / 5x / 10x) | Radio group, one required |

---

### 6.4 — Data Fetching Strategy

| Data | Strategy | Frequency |
|---|---|---|
| Drone fleet list | REST API + polling | On mount, then every 30s |
| Order list | REST API | On mount + after each order creation |
| Assignment list | REST API | On mount + after each optimization run |
| Drone telemetry positions | WebSocket (real-time push) | Every 2 seconds (server-side emit) |
| Weather data | REST API + Redis cache | On mount, then every 10 min |
| Airspace zones | REST API | On mount only (static-ish data) |
| Analytics summary | REST API | On mount + date filter change |
| Benchmark results | REST API (polling after run) | Poll every 2s until `status === "complete"` |

---

## 7. API REQUIREMENTS (FRONTEND PERSPECTIVE)

### 7.1 — Orders API

| Endpoint | Method | Request Body | Response | Page Used |
|---|---|---|---|---|
| `/api/orders` | GET | `?status=&limit=&offset=` | `Order[]` | Orders, Dashboard |
| `/api/orders` | POST | `{ pickup_lat, pickup_lng, delivery_lat, delivery_lng, weight_kg }` | `Order` | Order creation modal |
| `/api/orders/:id` | GET | — | `Order` | Order detail panel |
| `/api/orders/:id` | PATCH | `{ status }` | `Order` | Admin management |
| `/api/orders/:id` | DELETE | — | `204` | Admin management |

**Expected Order Object:**
```json
{
  "id": "ORD-042",
  "pickup_lat": 10.123,
  "pickup_lng": 76.456,
  "delivery_lat": 10.133,
  "delivery_lng": 76.466,
  "weight_kg": 2.3,
  "status": "ASSIGNED",
  "created_at": "2025-04-10T12:00:00Z",
  "assigned_drone_id": "D3",
  "estimated_delivery_time": "2025-04-10T12:20:00Z"
}
```

---

### 7.2 — Drones API

| Endpoint | Method | Request Body | Response | Page Used |
|---|---|---|---|---|
| `/api/drones` | GET | `?status=` | `Drone[]` | Fleet, Map, Dashboard |
| `/api/drones` | POST | `{ id, model, max_payload_kg, battery_capacity_mah, lat, lng }` | `Drone` | Admin - Add Drone |
| `/api/drones/:id` | GET | — | `Drone` | Drone detail |
| `/api/drones/:id` | PATCH | `{ status?, battery? }` | `Drone` | Admin management |
| `/api/drones/:id` | DELETE | — | `204` | Admin management |

**Expected Drone Object:**
```json
{
  "id": "D3",
  "model": "DJI Matrice 300",
  "max_payload_kg": 5.0,
  "battery_capacity_mah": 9800,
  "battery_pct": 78,
  "status": "IN_FLIGHT",
  "current_lat": 10.125,
  "current_lng": 76.458,
  "last_updated": "2025-04-10T12:15:00Z"
}
```

---

### 7.3 — Assignments API

| Endpoint | Method | Request Body | Response | Page Used |
|---|---|---|---|---|
| `/api/assignments` | GET | `?limit=&offset=` | `Assignment[]` | Assignment Viewer |
| `/api/assignments/run` | POST | `{ order_ids[], algorithm }` | `Assignment[]` | Assignment Viewer |
| `/api/assignments/:id` | GET | — | `Assignment` with `route_coords[]` | Route detail view |

**Expected Assignment Object:**
```json
{
  "id": "ASN-021",
  "drone_id": "D3",
  "order_id": "ORD-042",
  "algorithm": "OR_TOOLS",
  "route_coords": [[10.123, 76.456], [10.128, 76.461], [10.133, 76.466]],
  "distance_km": 1.8,
  "estimated_time_min": 12,
  "predicted_battery_pct": 22.5,
  "compliance_status": "COMPLIANT",
  "weather_impact_score": 0.15,
  "score": 0.87,
  "created_at": "2025-04-10T12:02:00Z"
}
```

---

### 7.4 — Zones API

| Endpoint | Method | Request Body | Response | Page Used |
|---|---|---|---|---|
| `/api/zones` | GET | — | `Zone[]` (with polygon coords) | Map, Settings |
| `/api/zones` | POST | `{ name, polygon_coords[], type }` | `Zone` | Admin - Settings |
| `/api/zones/validate` | POST | `{ route_coords[] }` | `{ compliant: bool, violations: Zone[] }` | Assignment viewer |
| `/api/zones/:id` | DELETE | — | `204` | Admin - Settings |

---

### 7.5 — Telemetry API

| Endpoint | Method | Description | Page Used |
|---|---|---|---|
| `/api/telemetry/latest` | GET | Latest telemetry snapshot for all drones | Map on initial load |
| WebSocket `drone:telemetry` | — | Real-time push every 2s | Map (live tracking) |

---

### 7.6 — Weather API

| Endpoint | Method | Response | Page Used |
|---|---|---|---|
| `/api/weather/current` | GET | `{ temp_c, wind_kmh, rain_mm, humidity, impact_score }` | Weather widget, everywhere |
| `/api/weather/impact` | POST | `{ route_id }` → `{ battery_penalty_pct, route_safe }` | Assignment viewer |

---

### 7.7 — Simulation API

| Endpoint | Method | Request Body | Response | Page Used |
|---|---|---|---|---|
| `/api/simulation/status` | GET | — | `{ running, paused, speed, active_drones }` | Simulation page |
| `/api/simulation/start` | POST | `{ speed_multiplier }` | `{ status: "started" }` | Simulation control |
| `/api/simulation/pause` | POST | — | `{ status: "paused" }` | Simulation control |
| `/api/simulation/stop` | POST | — | `{ summary }` | Simulation control |
| `/api/simulation/generate-orders` | POST | `{ count, area_bounds }` | `Order[]` | Simulation control |
| `/api/simulation/inject-failure` | POST | `{ drone_id }` | `{ reassigned_to, recovery_time_ms }` | Simulation page |

---

### 7.8 — Analytics API

| Endpoint | Method | Params | Response | Page Used |
|---|---|---|---|---|
| `/api/analytics/summary` | GET | `?from=&to=` | `{ orders_total, avg_delivery_time_min, success_rate }` | Analytics dashboard |
| `/api/analytics/battery` | GET | `?from=&to=` | `BatteryStatPerDrone[]` | Analytics dashboard |
| `/api/analytics/compliance` | GET | `?from=&to=` | `{ compliant, violations }` | Analytics dashboard |
| `/api/analytics/failures` | GET | `?from=&to=` | `{ failures_count, avg_recovery_ms }` | Analytics dashboard |

---

### 7.9 — Benchmarks API

| Endpoint | Method | Request Body | Response | Page Used |
|---|---|---|---|---|
| `/api/benchmarks/run` | POST | `{ order_count, algorithms[] }` | `{ job_id }` | Benchmarks page |
| `/api/benchmarks/status/:job_id` | GET | — | `{ status, progress, results? }` | Benchmarks (polling) |
| `/api/benchmarks/history` | GET | — | `BenchmarkRun[]` | Benchmarks page |

---

### 7.10 — Auth API

| Endpoint | Method | Request Body | Response |
|---|---|---|---|
| `/api/auth/login` | POST | `{ email, password }` | `{ token, user: { id, name, role } }` |
| `/api/auth/me` | GET | — | `{ id, name, email, role }` |
| `/api/auth/logout` | POST | — | `204` |

---

## 8. EDGE CASES & UX CONSIDERATIONS

### 8.1 — Loading States

| Scenario | UI Behavior |
|---|---|
| Orders table loading | Skeleton rows (3–5 rows of grey animated placeholders) |
| Map tiles loading | Leaflet default loading spinner |
| Assignment optimization running | Full-button spinner + disabled state + "Optimizing…" label |
| Benchmark running | Progress bar with order count ("Processing 47/100") |
| Drone telemetry initial load | Skeleton drone markers (grey circles) until first WebSocket event |
| Analytics charts loading | Chart area shows shimmer animation |
| Battery prediction loading | Spinner inline in assignment card |

---

### 8.2 — Empty States

| Scenario | UI Behavior |
|---|---|
| No orders placed yet | Empty state illustration + "No orders yet. Place your first order!" + CTA button |
| No drones in fleet | Empty state + "No drones configured. Add a drone to get started." + Admin CTA |
| No assignments run yet | Empty state + "No assignments yet. Run optimization to assign drones." |
| No benchmark history | Empty state + "No benchmarks run. Start a benchmark test above." |
| Simulation not started | Empty event log + "Start the simulation to see events here." |
| Weather API unavailable | "Weather data unavailable" placeholder card with warning icon |

---

### 8.3 — Error States

| Scenario | UI Behavior |
|---|---|
| API request fails (network error) | Toast notification: "Unable to connect. Please try again." + retry button |
| Order creation fails (validation) | Inline field errors below each invalid input |
| Optimization fails (no drones available) | Toast error: "No drones available for assignment" + drone fleet link |
| Route compliance violation | Red badge on assignment card: "⚠ Route violates restricted zone" |
| Drone battery too low to assign | Assignment card badge: "❌ Insufficient battery for this route" |
| WebSocket disconnects | Yellow banner at top: "Connection lost. Reconnecting…" with spinner |
| Weather API down | Weather widget shows: "Weather data unavailable — battery predictions may be inaccurate" |
| Map tiles fail to load | "Map unavailable" placeholder with retry button |
| Login fails | Error message below password field: "Invalid email or password" |

---

### 8.4 — Permissions & Restricted Access

| Scenario | UI Behavior |
|---|---|
| Researcher visits `/simulation` | Redirect to `/` + toast: "Access restricted" |
| Researcher visits `/benchmarks` | Redirect to `/` + toast: "Access restricted" |
| Researcher visits `/settings` | Redirect to `/` + toast: "Access restricted" |
| Non-admin sees Drone Fleet page | Page visible but "Add Drone" and "Delete" buttons are hidden/disabled |
| Unauthenticated user visits any route | Redirect to `/login` |
| Token expires mid-session | Intercept 401 response → auto-redirect to `/login` with message "Session expired. Please log in again." |

---

### 8.5 — Additional UX Notes

- **Drone marker clustering:** When too many drones are in close proximity on the map, cluster them to avoid visual clutter. Show individual markers on zoom-in.
- **Assignment confirmation:** Before running optimization, show a quick summary: "You are about to assign drones to 8 pending orders. Proceed?"
- **Failure injection warning:** Show a `<ConfirmDialog>` before injecting failure: "This will simulate Drone D3 crashing mid-delivery. Are you sure?"
- **Map auto-pan:** When a new assignment is created, auto-pan the map to show the assigned route.
- **Real-time debouncing:** WebSocket telemetry fires every 2s. Batch UI updates using `requestAnimationFrame` to avoid performance drops with many drones.
- **Battery warnings:** If a drone's battery drops below 20%, automatically highlight it with a pulsing red glow on the map.
- **Simulation speed feedback:** When speed is changed to 10x, show a subtle badge: "⚡ 10x Speed" in corner of map.

---

## 9. RESPONSIVE & PLATFORM NEEDS

### 9.1 — Target Platforms & Responsive Breakpoints

| Breakpoint | Label | Width | Layout Notes |
|---|---|---|---|
| xs | Mobile | < 640px | Stack layout, simplified map, collapsible sidebar |
| sm | Tablet Portrait | 640–768px | Two-column layout where possible |
| md | Tablet Landscape | 768–1024px | Sidebar collapses to icon-only mode |
| lg | Desktop | 1024–1280px | Full sidebar, split views enabled |
| xl | Large Desktop | > 1280px | Full layout, wider table columns, larger charts |

### 9.2 — Mobile-Specific Adaptations

- The **Live Map page** should be the primary mobile view (most impactful on small screens)
- **Sidebar** collapses to a bottom navigation bar on mobile (max 5 tabs)
- **DataTable** transforms to card-list view on mobile (each row becomes a card)
- **Modal** becomes a **bottom sheet** on mobile
- **Map controls** (layer toggles) collapse into a floating action button menu on mobile
- Touch gestures supported on map (pinch-to-zoom, drag)

### 9.3 — Browser Compatibility

- Chrome (latest) ✅ — primary target
- Firefox (latest) ✅
- Safari (latest) ✅
- Edge (latest) ✅
- IE / old browsers ❌ — not required

### 9.4 — Performance Targets

| Metric | Target |
|---|---|
| First Contentful Paint (FCP) | < 1.5s |
| Time to Interactive (TTI) | < 3s |
| WebSocket message handling | < 50ms per frame update |
| Map re-render with 20+ drones | < 100ms |
| API response display (on arrival) | Immediate (optimistic updates where applicable) |

### 9.5 — Accessibility (a11y) Basics

- All interactive elements must be keyboard-navigable (Tab, Enter, Escape)
- ARIA labels on all icon-only buttons
- Color is never the only differentiator (use icons + text alongside color for status badges)
- Form inputs have associated `<label>` elements
- Contrast ratio ≥ 4.5:1 for all text (WCAG AA)

---

## TECH STACK SUMMARY (FRONTEND)

| Technology | Purpose |
|---|---|
| **React.js + TypeScript** | Core UI framework |
| **Leaflet.js** | Interactive map (OpenStreetMap base layer) |
| **Socket.IO Client** | WebSocket-based real-time telemetry |
| **Material-UI (MUI)** | Base component library (buttons, tables, modals) |
| **Recharts or Chart.js** | Analytics charts (line, bar, donut) |
| **Axios** | HTTP API calls |
| **React Router v6** | Client-side routing with role-based guards |
| **Zustand or Redux Toolkit** | Global state management |
| **React Query (TanStack Query)** | API data fetching, caching, and background polling |

---

## FOLDER STRUCTURE (Recommended)

```
/src
  /components
    /base         ← Button, Card, Modal, Table, Toast, etc.
    /map          ← DroneMarker, RoutePolyline, ZonePolygon, MapLayerToggle
    /charts       ← All chart components
    /domain       ← TelemetryCard, AssignmentCard, WeatherWidget, etc.
    /layout       ← AppShell, Sidebar, TopBar, PageHeader
  /pages
    /auth         ← LoginPage
    /dashboard    ← DashboardPage
    /orders       ← OrdersPage
    /map          ← LiveMapPage
    /drones       ← DroneFleetPage
    /assignments  ← AssignmentViewerPage
    /analytics    ← AnalyticsDashboardPage
    /simulation   ← SimulationControlPage
    /benchmarks   ← BenchmarkPage
    /settings     ← SettingsPage
  /services       ← API calls (orders.service.ts, drones.service.ts, etc.)
  /hooks          ← useWebSocket, useDroneTracker, useOrders, etc.
  /store          ← Zustand/Redux slices (auth, drones, orders, simulation, etc.)
  /types          ← TypeScript interfaces (Order, Drone, Assignment, Zone, etc.)
  /utils          ← formatters, validators, haversine, color-by-status, etc.)
  /constants      ← API_BASE_URL, STATUS_COLORS, MAP_CENTER, etc.
  /assets         ← drone icon SVGs, map marker images
```

---

*Document prepared for: Frontend Development Team | Project: HDL Simulation System | Status: Ready for Sprint Planning*
