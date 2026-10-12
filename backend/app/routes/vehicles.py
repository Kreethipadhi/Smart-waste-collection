from typing import List, Optional
from fastapi import APIRouter, HTTPException
from app.database import db
from app.models import Vehicle, VehicleStatus

router = APIRouter(prefix="/api/vehicles", tags=["Fleet & Vehicles"])


@router.get("", response_model=List[Vehicle])
def list_vehicles(status: Optional[VehicleStatus] = None):
    vehicles = db.get_all_vehicles()
    if status:
        vehicles = [v for v in vehicles if v.status == status]
    return vehicles


@router.get("/{vehicle_id}", response_model=Vehicle)
def get_vehicle(vehicle_id: str):
    v = db.get_vehicle(vehicle_id)
    if not v:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
    return v


@router.put("/{vehicle_id}", response_model=Vehicle)
def update_vehicle(vehicle_id: str, payload: Vehicle):
    if not db.get_vehicle(vehicle_id):
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
    db.update_vehicle(payload)
    return payload
