from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

# ✅ import routers (NOT models)
from app.routers import auth, address, store

# ✅ import models (for table creation)
from app.models import user, address as address_model, store as store_model, product as product_model
from app.models import assignment
from app.routers import order
app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ include routers
app.include_router(auth.router)
app.include_router(address.router)
app.include_router(store.router)
app.include_router(order.router)
# ✅ create tables
Base.metadata.create_all(bind=engine)