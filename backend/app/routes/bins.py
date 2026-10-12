from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.database import db
from app.models import SmartBin, WasteType, BinStatus

router = APIRouter(prefix="/api/bins", tags=["Smart Bins"])


@router.get("", response_model=List[SmartBin])
def list_bins(
    waste_type: Optional[WasteType] = None,
    status: Optional[BinStatus] = None,
    zone: Optional[str] = None,
):
    bins = db.get_all_bins()
    if waste_type:
        bins = [b for b in bins if b.waste_type == waste_type]
    if status:
        bins = [b for b in bins if b.status == status]
    if zone:
        bins = [b for b in bins if b.zone.lower() == zone.lower()]
    return bins


@router.get("/{bin_id}", response_model=SmartBin)
def get_bin(bin_id: str):
    b = db.get_bin(bin_id)
    if not b:
        raise HTTPException(status_code=404, detail=f"Bin {bin_id} not found")
    return b


@router.post("", response_model=SmartBin, status_code=201)
def create_bin(bin_payload: SmartBin):
    if db.get_bin(bin_payload.id):
        raise HTTPException(status_code=400, detail=f"Bin with ID {bin_payload.id} already exists")
    db.update_bin(bin_payload)
    db.log_agent_action(
        agent_name="Smart Bin Monitoring Agent",
        action="NEW_BIN_REGISTERED",
        details={"bin_id": bin_payload.id, "name": bin_payload.name, "zone": bin_payload.zone},
    )
    return bin_payload


@router.put("/{bin_id}", response_model=SmartBin)
def update_bin(bin_id: str, bin_payload: SmartBin):
    existing = db.get_bin(bin_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Bin {bin_id} not found")
    db.update_bin(bin_payload)
    return bin_payload


@router.delete("/{bin_id}")
def delete_bin(bin_id: str):
    if bin_id not in db.bins:
        raise HTTPException(status_code=404, detail=f"Bin {bin_id} not found")
    del db.bins[bin_id]
    return {"message": f"Bin {bin_id} deleted successfully"}
