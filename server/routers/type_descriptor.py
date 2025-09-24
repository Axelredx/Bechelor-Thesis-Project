from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from ai_microservices import claude_interpreter
from controllers import doc_category_operations

router = APIRouter()
interpreter = claude_interpreter.ClaudeInterpreter()
doc_category_ops = doc_category_operations.DocCategoryOperations()

class CategoryRequest(BaseModel):
    text: str

@router.post("/create-category")
async def create_category(request: CategoryRequest):
    try:
        category = interpreter.interpret_file_categories(request.text)
        if category.strip().upper() == "NO":
            return {
                "message": "Non è stato possibile comprendere la richiesta di eliminazione.",
                "query": 'NO'
            }
        full_descr_parsed = interpreter.interpret_file_descr(request.text)

        doc_category_ops.update_file_category_str(full_descr_parsed, category)

        return {
            "message": "Categoria creata con successo",
            "description": full_descr_parsed,
            "category": category
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la creazione della categoria: {str(e)}"
        )
        
@router.put("/update-category")
async def update_category(request: CategoryRequest):
    try:
        old_category, old_descr = doc_category_ops.get_file_category_str()
        category = interpreter.interpret_file_categories(request.text)
        if category.strip().upper() == "NO":
            return {
                "message": "Non è stato possibile comprendere la richiesta di eliminazione.",
                "query": 'NO'
            }
        full_descr_parsed = interpreter.interpret_file_descr(request.text)
        if old_category == "":
            doc_category_ops.save_file_categories_str(full_descr_parsed, category)
        else:
            new_category = old_category + ", " + category
            new_descr = old_descr + ", " + full_descr_parsed
            doc_category_ops.delete_all_categories()
            doc_category_ops.save_file_categories_str(new_category, new_descr)
            
        categ, full_desc = doc_category_ops.get_file_category_str()

        return {
            "message": "Categoria aggiornata con successo",
            "description": full_desc,
            "category": categ
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'aggiornamento della categoria: {str(e)}"
        )

@router.get("/get-category")
async def get_category():
    try:
        category, full_descr = doc_category_ops.get_file_category_str()
        if category == "":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nessuna categoria trovata nel database."
            )
        return {
            "category": category,
            "description": full_descr
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il recupero della categoria: {str(e)}"
        )
        
@router.delete("/delete-all-categories")
async def delete_all_categories():
    try:
        success = doc_category_ops.delete_all_categories()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore durante la cancellazione delle categorie."
            )
        return {
            "message": "Tutte le categorie sono state cancellate con successo."
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la cancellazione delle categorie: {str(e)}"
        )