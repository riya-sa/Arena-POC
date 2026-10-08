"""
app/api/v1/__init__.py

Copy this file directly to: app/api/v1/__init__.py
NO EDITING NEEDED
"""

from fastapi import APIRouter
from app.api.v1 import benchmarks

router = APIRouter(prefix="/v1", tags=["v1"])

router.include_router(benchmarks.router)