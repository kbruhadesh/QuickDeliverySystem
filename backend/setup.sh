#!/bin/bash
# Quick Setup Script for Drone Delivery System
# Run this script to automatically set up the entire backend

set -e  # Exit on error

echo "🚁 Drone Delivery System - Quick Setup Script"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if PostgreSQL is running
echo "📦 Step 1: Checking PostgreSQL..."
if ! pg_isready -q; then
    echo -e "${RED}❌ PostgreSQL is not running!${NC}"
    echo "Please start PostgreSQL first:"
    echo "  macOS: brew services start postgresql@15"
    echo "  Linux: sudo systemctl start postgresql"
    exit 1
else
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
fi

# Check if database exists, if not create it
echo ""
echo "📦 Step 2: Setting up database..."
if psql -U postgres -lqt | cut -d \| -f 1 | grep -qw drone_delivery; then
    echo -e "${YELLOW}⚠️  Database 'drone_delivery' already exists${NC}"
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        dropdb -U postgres drone_delivery
        createdb -U postgres drone_delivery
        echo -e "${GREEN}✅ Database recreated${NC}"
    fi
else
    createdb -U postgres drone_delivery
    echo -e "${GREEN}✅ Database created${NC}"
fi

# Initialize database
echo ""
echo "📦 Step 3: Initializing database schema..."
if [ -f "init_database.sql" ]; then
    psql -U postgres -d drone_delivery -f init_database.sql > /dev/null
    echo -e "${GREEN}✅ Database schema initialized${NC}"
else
    echo -e "${RED}❌ init_database.sql not found!${NC}"
    exit 1
fi

# Check Python version
echo ""
echo "🐍 Step 4: Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed!${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Create virtual environment
echo ""
echo "🐍 Step 5: Setting up Python virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo ""
echo "📦 Step 6: Installing Python packages..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All packages installed${NC}"
else
    echo -e "${RED}❌ Package installation failed${NC}"
    exit 1
fi

# Verify database connection
echo ""
echo "🔌 Step 7: Testing database connection..."
python3 -c "
from app.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM drones'))
        count = result.scalar()
        print(f'✅ Database connected! Found {count} drones.')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Create .env file if it doesn't exist
echo ""
echo "⚙️  Step 8: Setting up environment variables..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
DATABASE_URL=postgresql://postgres@localhost:5432/drone_delivery
REDIS_URL=redis://localhost:6379
OPENWEATHER_API_KEY=your_api_key_here
ENVIRONMENT=development
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please update .env with your actual credentials${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists${NC}"
fi

# Summary
echo ""
echo "=============================================="
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Start the backend server:"
echo "   python main.py"
echo "   or"
echo "   uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "3. Open your browser:"
echo "   API Docs: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo ""
echo "4. Serve the frontend (in another terminal):"
echo "   python3 -m http.server 3000"
echo "   Then open: http://localhost:3000/admin/admin.html"
echo ""
echo "=============================================="
