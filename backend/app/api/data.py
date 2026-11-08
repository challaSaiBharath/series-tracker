import datetime as dt

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.data import ExportFile
from app.services.dataio import export_all, import_all

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/export")
def export(db: Session = Depends(get_db)):
    filename = f"series-tracker-backup-{dt.date.today().isoformat()}.json"
    return JSONResponse(export_all(db), headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.post("/import")
def import_backup(body: ExportFile, db: Session = Depends(get_db)):
    return {"imported": import_all(db, body)}
