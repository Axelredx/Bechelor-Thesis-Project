from fastapi import APIRouter, File, UploadFile, HTTPException
import shutil
import sys
import os
from pathlib import Path
from ai_microservices import claude_doc_classificator
router = APIRouter()

# relative Path
BASE_DIR = Path(__file__).resolve().parent.parent
DUMP_FOLDER = BASE_DIR / "DUMP"
DUMP_FOLDER.mkdir(parents=True, exist_ok=True)
classificator = claude_doc_classificator.ClaudeDocClassificator()

@router.post("/upload-file/")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nessun file selezionato")
        
        file_path = DUMP_FOLDER / file.filename
        
        # Save file DUMP in DUMP_FOLDER
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        classificator.main_preprocessing()

        return {
            "message": "File caricato con successo"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante il caricamento: {str(e)}")
