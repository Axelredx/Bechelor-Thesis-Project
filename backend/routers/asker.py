from fastapi import APIRouter, HTTPException, status, Query, Response
from pydantic import BaseModel
from ai_microservices import claude_query_creator, claude_interpreter
from controllers import file_operations
from models.document import DocumentModel

router = APIRouter()
interpreter = claude_interpreter.ClaudeInterpreter()
query_creator = claude_query_creator.ClaudeQueryCreator()
file_op = file_operations.FileOperations()
class NLPRequest(BaseModel):
    text: str

@router.get("/ask-docs-info")
async def ask_question(text: str = Query(..., description="Domanda in linguaggio naturale")):
    try:
        wants_files = interpreter.wants_files(text)
        query = query_creator.create_db_query(text)
        if query.strip().upper() == "NO":
            return {
                "message": "Non è stato possibile comprendere la richiesta.",
                "query": query,
                "result": None
            }
        # NOTE: result can be a list of dicts (if wants_files) otherwise a string in nlp
        result = file_op.execute_query(query, wants_files, text)

        return {
            "message": "Query eseguita con successo",
            "query": query,
            "result": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'esecuzione della query: {str(e)}"
        )

'''Delete documents based on user nlp request'''
@router.delete("/delete-docs")
async def delete_info(request: NLPRequest):
    try:
        query = query_creator.create_db_query(request.text)
        if query.strip().upper() == "NO":
            return {
                "message": "Non è stato possibile comprendere la richiesta di eliminazione.",
                "query": query,
                "result": None
            }
            
        result = file_op.delete_documents(query)

        return {
            "message": "Eliminazione completata con successo",
            "query": query,
            "result": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'eliminazione: {str(e)}"
        )

'''Get number of documents in the DB'''
@router.get("/count-docs")
async def count_documents():
    try:
        result = file_op.count_documents()
        return {
            "message": "Conteggio documenti eseguito con successo",
            "result": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il conteggio dei documenti: {str(e)}"
        )
        
@router.get("/download-file/{file_id}")
async def download_file(file_id: str):
    try:
        document = DocumentModel.objects(id=file_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="File non trovato")
        
        return Response(
            content=document.binary_file_content,
            media_type=document.mime_type,
            headers={"Content-Disposition": f"attachment; filename={document.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore download: {str(e)}")