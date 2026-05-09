# 🚁 Hyperlocal Drone Delivery System (HDL)

A production-ready, full-stack drone delivery simulation and management system. Features RRT* path planning, physics-based battery prediction, and real-time fleet synchronization.

---

## 🚀 **Quick Setup (Recommended for New Systems)**

The fastest way to get the entire system (Database, Backend, and Frontend) running on any new computer is using **Docker**.

### **1. Prerequisites**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- [Git](https://git-scm.com/downloads) installed.

### **2. One-Command Setup**
```bash
# Clone the repository
git clone https://github.com/kbruhadesh/QuickDeliverySystem.git
cd QuickDeliverySystem

# Start all services (Database, Redis, Backend, Frontend)
docker-compose up -d --build
```

### **3. Initialize Data (Crucial)**
Once the containers are running, you must seed the database with operational hubs, drones, and an admin user.
```bash
# Seed the database (Hubs and Drones)
docker exec -it drone_delivery_backend python final_seed_all.py

# Create the default Admin user
docker exec -it drone_delivery_backend python insert_admin.py
```

---

## 🌐 **Accessing the System**

| Component | URL | Credentials |
| :--- | :--- | :--- |
| **Admin Dashboard** | [http://localhost/admin/login.html](http://localhost/admin/login.html) | `test@hdl.com` / `admin` |
| **Customer App** | [http://localhost/customer/login.html](http://localhost/customer/login.html) | Create new account |
| **API Documentation** | [http://localhost:8000/docs](http://localhost:8000/docs) | - |
| **Database** | `localhost:5432` | `postgres` / `postgres` |

---

## 🛠️ **Manual Setup (Developer Mode)**

If you want to run the backend locally for development without Docker:

### **1. Database Setup**
1. Install PostgreSQL and PostGIS.
2. Create a database named `drone_delivery`.
3. Update `backend/app/database.py` with your credentials.

### **2. Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### **3. Frontend Setup**
You can use any local server (Live Server, http-server, or Python's built-in server):
```bash
# From the root directory
python3 -m http.server 80
```

---

## 🏗️ **Core Technology Stack**

- **Backend**: FastAPI (Python 3.10+), SQLAlchemy 2.0, GeoAlchemy2.
- **Database**: PostgreSQL with PostGIS (Spatial Data Support).
- **Optimization**: OR-Tools (Solver), RRT* (Path Planning).
- **Frontend**: HTML5, Vanilla CSS3, Javascript (ES6), Leaflet.js (Mapping).
- **Deployment**: Docker, Docker Compose, Nginx.

---

## 📋 **Key Features**

- **RRT* Path Planning**: Collision-aware pathfinding that avoids No-Fly Zones.
- **Battery Prediction**: Physics-based model accounting for payload, distance, and safety margins.
- **Simulation Engine**: Reset system state, generate test orders, and inject drone failures.
- **Live Tracking**: Real-time visualization of drone movements and battery status.
- **Role-Based Access**: Distinct portals for Fleet Administrators and Customers.

---

## ⚠️ **Troubleshooting**

- **CORS Errors**: Ensure the backend is running and the `API` constant in frontend JS files points to `http://localhost:8000/api`.
- **Database Connection**: If using Docker, ensure `DATABASE_URL` in `docker-compose.yml` uses the service name `postgres`.
- **Port Conflict**: Port 80 is used by Nginx (Frontend). If port 80 is busy, change the mapping in `docker-compose.yml`.

---

**Developed for Software Engineering Project - Team 16**
