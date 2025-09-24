import os
import anthropic
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Union, Dict, Any
import sys
from utility.error_logger import Logger
from utility.ocr import OCR
import hashlib
import mimetypes
import datetime
import json
from models.document import DocumentModel
from mongoengine import get_db
from ai_microservices import claude_interpreter, claude_db_contexter
from dateutil import parser
import base64

def get_database():
    return get_db()


try:
    load_dotenv()
except Exception as e:
    raise e
class FileOperations:
    def __init__(self, script_path: Path = None) -> None:
        self.logger = Logger()
        self.interpreter = claude_interpreter.ClaudeInterpreter()
        self.db_contexter = claude_db_contexter.ClaudeQueryCreator()
        
    '''return codes: 0 = error, 1 = success, 2 = duplicate file'''
    def upload_to_db(self, file_path: Path, category: str, content_file_info: str, exact_time: str) -> int:
        from datetime import datetime, timezone
        try:
            # Get file info for document model
            file_name = file_path.name
            file_extension = file_path.suffix[1:]  # Remove the dot from the file extension

            # Binary reading
            with open(file_path, 'rb') as f:
                binary_file_content = f.read()
            file_size = len(binary_file_content)
            file_hash = hashlib.md5(binary_file_content).hexdigest()

            # Check for duplicate file based on hash
            if DocumentModel.objects(file_hash=file_hash).first():
                self.logger.write_info_in_log_file(f"(WARNING) Duplicate file upload attempt detected for file: {file_name}")
                self.logger.write_warning_in_log_file(f"Duplicate file upload attempt detected for file: {file_name}")
                return 2

            # Guess mime type or set default 
            mime_type, _ = mimetypes.guess_type(str(file_path))
            mime_type = mime_type or 'application/octet-stream'
            file_category = category 

            # Extract info from content_file_info
            data = json.loads(content_file_info)
            sender = data.get("sender", "")
            receiver = data.get("receiver", "")
            subject = data.get("subject", "")
            total_cost = data.get("total_cost", 0)
            document_date_str = data.get("document_date", "")

            # Convert document_date to string ISO YYYY-MM-DD
            document_date = None
            if document_date_str:
                try:
                    # Try ISO format first
                    dt = datetime.fromisoformat(document_date_str.replace('Z', '+00:00'))
                    document_date = dt.date().isoformat()
                except ValueError:
                    try:
                        # Try European format dd-mm-yyyy
                        dt = datetime.strptime(document_date_str, "%d-%m-%Y")
                        document_date = dt.date().isoformat()
                    except ValueError:
                        self.logger.write_warning_in_log_file(
                            f"Invalid date format for document_date: {document_date_str}"
                        )

            # Current upload date as string
            upload_date = exact_time

            # Create document
            document = DocumentModel(
                filename=file_name,
                file_extension=file_extension,
                binary_file_content=binary_file_content,
                file_size=file_size,
                file_hash=file_hash,
                mime_type=mime_type,
                file_category=file_category,
                upload_date=upload_date,
                sender=sender,
                receiver=receiver,
                subject=subject,
                total_cost=total_cost,
                document_date=document_date
            )

            document.save()
            self.logger.write_info_in_log_file(f"Successfully uploaded document: {file_name} (ID: {document.id})")

        except Exception as e:
            self.logger.write_error_in_log_file(f"Error (in upload_to_db()) uploading file {file_path} in DB: {e}")
            return 0

        return 1


    '''Safely parse the query string into a dictionary, converting each fields like transforming 
    date strings to datetime objects, to be directly executed on MongoDB'''
    def __safe_query_parse(self, query: str) -> Dict[str, Any]:
        import ast
        if query.strip().startswith('{'):
            try:
                q = json.loads(query)
            except json.JSONDecodeError:
                q = ast.literal_eval(query)
        else:
            q = ast.literal_eval(query)

        def convert(obj):
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert(v) for v in obj]
            return obj  # leave strings as-is, do not parse into datetime

        return convert(q)

    '''Execute the given query on the DB and return the results: List of Doc OR NLP str'''
    def execute_query(self, query: str, wants_files: bool, user_request: str) -> Union[List[Dict[str, Any]], str]:
        try:
            # Convert query string into dictionary safely
            query_dict = self.__safe_query_parse(query)

            # Execute query using __raw__, now dates are strings
            documents = DocumentModel.objects(__raw__=query_dict)

            # Convert to JSON
            documents_json = []
            for doc in documents:
                doc_dict = {
                    'id': str(doc.id),
                    'filename': doc.filename,
                    'file_extension': doc.file_extension,
                    'binary_file_content': "",
                    'file_size': doc.file_size,
                    'mime_type': doc.mime_type,
                    'file_category': doc.file_category,
                    'upload_date': getattr(doc, "upload_date", None),
                    'sender': getattr(doc, "sender", ""),
                    'receiver': getattr(doc, "receiver", ""),
                    'subject': getattr(doc, "subject", ""),
                    'total_cost': getattr(doc, "total_cost", 0),
                    'document_date': getattr(doc, "document_date", None),
                    #'file_hash': doc.file_hash
                }
                if wants_files:
                    doc_dict['binary_file_content'] = base64.b64encode(doc.binary_file_content).decode('utf-8')
                    
                documents_json.append(doc_dict)

            if wants_files:
                self.logger.write_info_in_log_file(f"Query returned {len(documents)} documents")
                return documents_json
            else:
                self.logger.write_info_in_log_file(f"Converting {len(documents_json)} documents to interpretation")
                interpretation = self.interpreter.interpret_response(documents_json, user_request)
                return interpretation

        except Exception as e:
            self.logger.write_error_in_log_file(f"(at execute_query) Error executing query '{query}': {e}")
            return [] if wants_files else "Error executing query"

    '''Delete documents matching the given query, return number string of deleted docs'''
    def delete_documents(self, query: str) -> str:
        try:
            query_dict = self.__safe_query_parse(query)
            documents = DocumentModel.objects(__raw__=query_dict)
            count = documents.count()
            
            if count == 0:
                return "Nessun documento trovato da eliminare"
            
            # Convert to JSON for update local schema logs
            documents_json = []
            for doc in documents:
                doc_dict = {
                    'id': str(doc.id),
                    'filename': doc.filename,
                    'file_extension': doc.file_extension,
                    'file_size': doc.file_size,
                    'mime_type': doc.mime_type,
                    'file_category': doc.file_category,
                    'upload_date': getattr(doc, "upload_date", None),
                    'sender': getattr(doc, "sender", ""),
                    'receiver': getattr(doc, "receiver", ""),
                    'subject': getattr(doc, "subject", ""),
                    'total_cost': getattr(doc, "total_cost", 0),
                    'document_date': getattr(doc, "document_date", None),
                    'file_hash': doc.file_hash
                }
                documents_json.append(doc_dict)
                
            self.db_contexter.delete_in_db_context(str(documents_json))

            result = documents.delete()
            self.logger.write_info_in_log_file(f"Deleted {result} documents matching query: {query}")
            return f"Eliminati: {result} documenti."
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at delete_documents) Error deleting documents with query '{query}': {e}")
            return "Error deleting documents."
        
    '''Return number of documents in the DB'''
    def count_documents(self) -> int:
        try:
            return DocumentModel.objects.count()
        except Exception as e:
            self.logger.write_error_in_log_file(f"(at count_documents) Error counting documents: {e}")
            return 0