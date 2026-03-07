"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from fastapi import FastAPI

app = FastAPI(title="Learning Service", version="1.0.0")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "learning-service"}
