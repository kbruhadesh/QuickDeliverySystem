# COMPLETE DEPLOYMENT GUIDE - Drone Delivery System
## Step-by-Step Instructions to Fix All Issues

---

## 🚨 **CRITICAL: BACKUP YOUR CURRENT WORK FIRST!**

```bash
cd /path/to/QuickDeliverySystem-main
cp -r backend backend_backup_$(date +%Y%m%d)
cp -r admin admin_backup_$(date +%Y%m%d)
cp -r customer customer_backup_$(date +%Y%m%d)
```

---

## **PART 1: DATABASE SETUP** ✅

### Step 1.1: Install PostgreSQL with PostGIS

**macOS:**
```bash
brew install postgresql@15 postgis
brew services start postgresql@15
```

**Ubuntu/Linux:**
```bash
sudo apt-get update
sudo apt-get install postgresql-15 postgresql-15-postgis-3
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
- Download PostgreSQL 15 from https://www.postgresql.org/download/windows/
- During installation, select PostGIS extension
- Start PostgreSQL service

### Step 1.2: Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# In psql prompt:
CREATE DATABASE drone_delivery;
\c drone_delivery
CREATE EXTENSION postgis;
CREATE EXTENSION "uuid-ossp";
\q
```

### Step 1.3: Run Database Initialization

```bash
# Copy the init_database.sql file to your project
# Then run:
psql -U postgres -d drone_delivery -f init_database.sql
```

**Verify installation:**
```bash
psql -U postgres -d drone_delivery

# In psql:
SELECT COUNT(*) FROM drones;  -- Should return 5
SELECT COUNT(*) FROM no_fly_zones;  -- Should return 2
\dt  -- List all tables
\q
```

---

## **PART 2: BACKEND SETUP** ✅

### Step 2.1: Replace Backend Files

Navigate to your project:
```bash
cd /path/to/QuickDeliverySystem-main/backend
```

**Replace these files with the fixed versions:**

1. **models.py**
   ```bash
   # Copy from drone_delivery_fixes/models.py
   cp /path/to/fixes/models.py app/models.py
   ```

2. **main.py**
   ```bash
   cp /path/to/fixes/main.py .
   ```

3. **Routers** (create app/routers directory if it doesn't exist)
   ```bash
   mkdir -p app/routers
   cp /path/to/fixes/orders.py app/routers/
   cp /path/to/fixes/drones.py app/routers/
   cp /path/to/fixes/assignments.py app/routers/
   cp /path/to/fixes/telemetry.py app/routers/
   cp /path/to/fixes/admin.py app/routers/
   cp /path/to/fixes/__init__.py app/routers/
   ```

4. **Services** (create app/services directory if it doesn't exist)
   ```bash
   mkdir -p app/services
   cp /path/to/fixes/path_planner.py app/services/
   cp /path/to/fixes/battery_predictor.py app/services/
   ```

### Step 2.2: Update Database Configuration

Edit `app/database.py`:
```python
DATABASE_URL = "postgresql://postgres:yourpassword@localhost:5432/drone_delivery"
```

Replace `yourpassword` with your PostgreSQL password.

### Step 2.3: Install Python Dependencies

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# If any package fails, install individually:
pip install fastapi uvicorn sqlalchemy psycopg2-binary geoalchemy2
pip install pydantic numpy shapely
```

### Step 2.4: Test Backend

```bash
# Start the server
python main.py

# Or with uvicorn directly:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Test in browser:**
- Open: http://localhost:8000
- You should see: `{"message": "Drone Delivery System API v1.0", ...}`
- Open: http://localhost:8000/docs
- You should see the Swagger API documentation

**Test API endpoints:**
```bash
# Get all drones
curl http://localhost:8000/api/drones

# Get stats
curl http://localhost:8000/api/stats

# Health check
curl http://localhost:8000/health
```

---

## **PART 3: FRONTEND FIXES** ✅

### Step 3.1: Update API Base URL

Open `admin/admin.html` and search for the API base URL:

**Find and replace:**
```javascript
// Old (might be various URLs):
const API_BASE_URL = 'http://localhost:5000';
// or
const API_BASE_URL = 'http://127.0.0.1:5000';

// New (correct):
const API_BASE_URL = 'http://localhost:8000/api';
```

Do the same for:
- `customer/customer.html`
- `index.html`
- Any JavaScript files in `admin/js/` and `customer/js/`

### Step 3.2: Fix CORS Issues (Already done in main.py)

The fixed `main.py` already includes comprehensive CORS settings. No action needed!

### Step 3.3: Test Frontend-Backend Connection

1. **Start backend** (if not already running):
   ```bash
   cd backend
   python main.py
   ```

2. **Serve frontend** (open new terminal):
   ```bash
   cd /path/to/QuickDeliverySystem-main
   
   # Option 1: Python simple server
   python3 -m http.server 8080
   
   # Option 2: Node.js http-server
   npx http-server -p 8080
   
   # Option 3: VS Code Live Server extension (right-click index.html)
   ```

3. **Open in browser:**
   - Admin: http://localhost:8080/admin/admin.html
   - Customer: http://localhost:8080/customer/customer.html

4. **Check browser console** (F12):
   - Should NOT see CORS errors
   - Should see successful API calls

---

## **PART 4: TESTING THE SYSTEM** ✅

### Test 1: Create an Order

**Via API (curl):**
```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "pickup_latitude": 13.0827,
    "pickup_longitude": 80.2707,
    "delivery_latitude": 13.0878,
    "delivery_longitude": 80.2785,
    "package_weight": 1.5,
    "priority": 2
  }'
```

**Via Frontend:**
1. Open Customer UI: http://localhost:8080/customer/customer.html
2. Click on map to set pickup location
3. Click again to set delivery location
4. Enter package weight
5. Click "Create Order"
6. Check if order appears in order list

### Test 2: Assign Drone

**Via API:**
```bash
# First, get an order ID
curl http://localhost:8000/api/orders/ | grep '"id"'

# Then assign (replace ORDER_ID):
curl -X POST http://localhost:8000/api/assignments/assign \
  -H "Content-Type: application/json" \
  -d '{"order_id": "YOUR_ORDER_ID_HERE"}'
```

**Via Frontend:**
1. Open Admin UI: http://localhost:8080/admin/admin.html
2. Go to "Orders" tab
3. Find pending order
4. Click "Assign Drone"
5. Check if assignment was created

### Test 3: View Drones

```bash
# Get all drones
curl http://localhost:8000/api/drones/

# Get available drones
curl http://localhost:8000/api/drones/available

# Get specific drone telemetry
curl http://localhost:8000/api/drones/DRONE-001/telemetry
```

---

## **PART 5: COMMON ISSUES & SOLUTIONS** 🔧

### Issue 1: "Connection refused" or "CORS error"

**Solution:**
```bash
# Check if backend is running:
curl http://localhost:8000/health

# If not running, start it:
cd backend
python main.py

# Check CORS in main.py - should have:
allow_origins=["*"]  # For development
```

### Issue 2: "Table does not exist"

**Solution:**
```bash
# Re-run database initialization:
psql -U postgres -d drone_delivery -f init_database.sql

# Or drop and recreate:
dropdb drone_delivery
createdb drone_delivery
psql -U postgres -d drone_delivery -f init_database.sql
```

### Issue 3: "Module not found" errors

**Solution:**
```bash
cd backend

# Check virtual environment is activated
which python  # Should show venv path

# If not activated:
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Reinstall requirements
pip install -r requirements.txt
```

### Issue 4: Frontend not loading data

**Solution:**
1. Open browser console (F12)
2. Check Network tab
3. Look for failed API calls
4. Verify API_BASE_URL in HTML/JS files:
   ```javascript
   const API_BASE_URL = 'http://localhost:8000/api';
   ```

### Issue 5: "No available drones"

**Solution:**
```bash
# Check drone status:
curl http://localhost:8000/api/drones/

# Reset drones to idle:
curl -X POST http://localhost:8000/api/admin/reset-system

# Or manually via database:
psql -U postgres -d drone_delivery
UPDATE drones SET status='idle', current_battery=100.0;
\q
```

---

## **PART 6: VERIFICATION CHECKLIST** ✅

Run through this checklist:

- [ ] PostgreSQL is running
- [ ] Database `drone_delivery` exists with all tables
- [ ] Sample drones are in database (5 drones)
- [ ] Backend starts without errors
- [ ] Can access http://localhost:8000/docs
- [ ] Can access http://localhost:8000/health
- [ ] Frontend loads without errors
- [ ] Can create order via frontend
- [ ] Can see drones on map
- [ ] Can assign drone to order
- [ ] No CORS errors in browser console
- [ ] API calls return data (not 404 or 500)

---

## **PART 7: NEXT STEPS** 🚀

Once everything is working:

1. **Add Real Weather Integration**
   - Get OpenWeatherMap API key
   - Update weather service in backend

2. **Implement Real-time Simulation**
   - Add WebSocket support
   - Implement drone movement simulation
   - Update telemetry in real-time

3. **Add Authentication**
   - Implement JWT tokens
   - Add login/register pages
   - Protect admin routes

4. **Deploy to Production**
   - Use Docker Compose
   - Deploy to cloud (AWS, GCP, Azure)
   - Use proper environment variables

---

## **GETTING HELP** 💬

If you encounter issues:

1. **Check logs:**
   ```bash
   # Backend logs (terminal where you ran main.py)
   # Look for error messages
   
   # Browser console (F12 → Console tab)
   # Look for API errors
   
   # PostgreSQL logs
   tail -f /usr/local/var/log/postgresql@15.log  # macOS
   # or
   sudo tail -f /var/log/postgresql/postgresql-15-main.log  # Linux
   ```

2. **Test API directly:**
   ```bash
   # Test each endpoint
   curl http://localhost:8000/api/drones/
   curl http://localhost:8000/api/orders/
   curl http://localhost:8000/api/assignments/
   ```

3. **Database queries:**
   ```bash
   psql -U postgres -d drone_delivery
   
   SELECT * FROM drones;
   SELECT * FROM orders;
   SELECT * FROM assignments;
   ```

---

## **SUCCESS INDICATORS** 🎉

You'll know everything is working when:

1. ✅ Backend API responds at http://localhost:8000
2. ✅ Swagger docs load at http://localhost:8000/docs
3. ✅ Frontend loads and shows map
4. ✅ Can create orders via UI
5. ✅ Drones appear on map
6. ✅ Can assign drones to orders
7. ✅ Assignment creates path on map
8. ✅ No errors in browser console
9. ✅ Database has data in all tables

**Congratulations! Your drone delivery system is now operational!** 🚁✨
