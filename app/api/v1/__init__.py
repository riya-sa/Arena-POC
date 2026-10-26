# Add jobs router
from app.api.v1 import jobs

def include_routers(app):
    app.include_router(jobs.router)