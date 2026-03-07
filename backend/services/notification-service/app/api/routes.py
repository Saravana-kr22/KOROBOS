"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Notification Service is running"}
