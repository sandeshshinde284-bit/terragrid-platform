# Routes initialization
from .disaster_data import router as disaster_router
from .polling import router as polling_router
from .zones import router as zones_router

__all__ = ["disaster_router", "polling_router", "zones_router"]

